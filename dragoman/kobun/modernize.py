#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文を現代語に組み立て直す
#
#   1. 文節に分ける (自立語 + 助動詞・助詞・接尾辞)
#   2. 用言の文節は、助動詞の連なりの意味 (受身・使役・打消・存続・完了・過去・推量 …) を順に現代語の形にする
#      (いひけり → 言った、たなびきたる (雲) → たなびいている (雲)、見ざりけむ → 見なかっただろう)
#   3. 助詞は文脈で置き換える (述語の前の「の」→「が」、已然形 + ば →「ので」、未然形 + ば →「なら」、ど →「けれど」)
#   4. 体言は現代仮名遣いに (やうやう → ようよう)。重要古語は現代語訳 (grammar.VOCABULARY) に
#
from dataclasses import dataclass, field
from functools import lru_cache

from dragoman.core import animacy
from dragoman.core import verb_flags as V
from dragoman.core.japanese import JaVerb
from . import grammar

CONTENT = {'名詞', '代名詞', '動詞', '形容詞', '形状詞', '副詞', '連体詞', '接続詞', '感動詞'}
AUX_VERBS = {'行く', '来る', '居る'}
# 人を表す古文の名詞 (「あり」→「いる」、主語の手がかり)
HUMANS = {'翁', '嫗', '帝', '御門', '宮', '君', '女御', '更衣', '大臣', '法師', '僧', '尼', '殿', '主', '人', '男', '女',
          '子', '親', '妻', '夫', '童', '翁丸', '姫', '后', '中宮', '上', '大納言', '中納言', '少将', '中将'}


# 自発の「る・らる」をとりやすい心情・知覚の動詞 (語彙素)
EMOTION_VERBS = {'思う', '偲ぶ', '驚く', '嘆く', '泣く', '知る', '眺める', '案ずる', '待つ', '覚える', '思い出す', '見る',
                 '聞く', '忍ぶ'}
# 尊敬の「る・らる」をとりやすい、身分の高い主語
HONORED = {'帝', '御門', '宮', '君', '中宮', '后', '院', '上', '大臣', '殿', '女御', '大納言', '中納言'}
# 複合動詞 (前の動詞の語彙素, 後ろの動詞の語彙素) → 現代語 (思ひ出づ → 思い出す)
COMPOUND_VERBS = {('思う', '出でる'): '思い出す', ('見る', '出でる'): '見つける', ('言う', '出でる'): '言い出す',
                  ('泣く', '出でる'): '泣き出す', ('思う', '立つ'): '思い立つ', ('立つ', '出でる'): '立ち出る',
                  ('行く', '泥む'): '行き悩む', ('憧れる', '出でる'): 'さまよい出る'}
FIRST_PERSON = {'我', '我れ', '吾', 'われ', '己', 'おのれ', '自分', '私'}


@lru_cache(maxsize=None)
def _transitivity():
    """現代語の動詞の自他 (tools/build_ja_transitivity.py が JMdict から作る表)。無ければ空"""
    from dragoman.core import paths
    table = {}
    try:
        with open(paths.data('ja-transitivity.tsv')) as f:
            for line in f:
                word, kinds = line.rstrip('\n').split('\t')
                table[word] = set(kinds.split(','))
    except OSError:
        pass
    return table


def transitive_only(verb):
    """他動詞としてしか使わない動詞か (読む: はい、言う・開く: 自動詞にもなるので いいえ)"""
    return _transitivity().get(verb) == {'vt'}


def is_human(token):
    word = token.lemma if token.lemma not in ('*', '') else token.surface
    return word in HUMANS or token.surface in HUMANS or word in animacy.JAPANESE_WORDS or \
        word.endswith(animacy.JAPANESE_SUFFIXES)


def subject_of(bunsetsu, i):
    """i 番目の述語の主語らしい体言 (前の、助詞の無いか は・が・の・も の付いた体言)。「〜といふもの」は「〜」"""
    for j in range(i - 1, -1, -1):
        b = bunsetsu[j]
        if b.kind == 'punct':
            # 読点の前の、助詞の無い体言は主題 (帝、笑はれけり)
            before = bunsetsu[j - 1] if j > 0 else None
            if before is not None and before.kind == 'nominal' and not any(t.pos == '助詞' for t in before.tokens) \
                    and b.head.surface == '、':
                return before.head
            return None
        if b.kind != 'nominal':
            continue
        particles = [t.lemma for t in b.tokens if t.pos == '助詞']
        if particles and not set(particles) <= {'は', 'が', 'の', 'も'}:
            continue  # 「京へ」「人に」などは主語でない: さらに前を見る
        if b.head.lemma in ('物', '者') and j >= 2 and bunsetsu[j - 1].head.lemma == '言う':
            return bunsetsu[j - 2].head  # 竹取の翁といふもの → 翁
        return b.head
    return None   # 連用形 + これらは「〜ていく・〜てくる・〜ている」(なりゆく → なっていく)
KANJI = range(0x4e00, 0xa000)


@dataclass
class Bunsetsu:
    tokens: list = field(default_factory=list)
    modern: str = ''

    @property
    def head(self):
        return self.tokens[0]

    @property
    def kind(self):
        head = self.head
        if head.pos == '動詞' or any(t.pos == '接尾辞' and t.pos2 == '動詞的' for t in self.tokens):
            return 'verb'
        if head.pos == '形容詞':
            return 'adj'
        if head.pos == '形状詞':
            return 'nadj'
        if head.pos == '補助記号':
            return 'punct'
        return 'nominal'


def split(tokens):
    """[Token] → [Bunsetsu]"""
    out = []
    for i, t in enumerate(tokens):
        prev = tokens[i - 1] if i else None
        new = t.pos in CONTENT or t.pos in ('補助記号', '接頭辞') or out == [] or \
            (out and out[-1].head.pos == '補助記号')
        if t.pos == '名詞' and t.pos2 == '普通名詞' and prev is not None and prev.pos == '接頭辞':
            new = False
        if new:
            out.append(Bunsetsu([t]))
        else:
            out[-1].tokens.append(t)
    return out


def _has_kanji(text):
    return any(ord(c) in KANJI for c in text)


def _modern_word(token):
    """自立語の現代の綴り: 漢字を含む語は語彙素 (書字形)、かなだけの語は語彙素の読み (現代仮名遣い)"""
    from .mecab import hiragana
    if token.pos in ('動詞', '形容詞'):
        if token.lemma == '行く' and token.surface.startswith('ゆ'):
            return 'ゆく'
        if _has_kanji(token.surface) and _has_kanji(token.lemma):
            return token.lemma
        return hiragana(token.reading) if token.reading not in ('*', '') else token.lemma
    return None


def vocabulary(token):
    for key in (token.lemma, token.base_orth, token.surface):
        if key in grammar.VOCABULARY:
            return grammar.VOCABULARY[key]
    return None


def obsolete(token):
    """廃れた語の現代語訳 (明かる → 明るくなる)。印を付ける"""
    for key in (token.lemma, token.base_orth):
        if key in grammar.OBSOLETE:
            token.obsolete = 'table'
            return grammar.OBSOLETE[key]
    return None


@lru_cache(maxsize=None)
def modern_known(word, pos):
    """現代語の辞書で 1 語・同じ品詞・文語の活用でない語か (あかる は形容詞「明るい」に読まれるので無い語)"""
    from dragoman.core.japanese import mecab_parse
    parsed = mecab_parse(word)
    if parsed is None:
        return True  # 現代語の MeCab が無ければ調べない
    return len(parsed) == 1 and parsed[0][1][0] == pos and not parsed[0][1][4].startswith('文語')


def _plain_word(token):
    """表に無い自立語を形だけ現代語にする。現代語に無ければ印を付ける"""
    word = _modern_word(token)
    if word and not modern_known(word, token.pos):
        token.obsolete = 'unknown'
    return word


# ----------------------------------------------------------------------
# 現代語の用言の活用

class Derived(str):
    """受身・使役で作った一段動詞 (気づかれる・行かせる)。現代語の活用は一段として規則で"""


class Modern:
    """組み立て中の用言: prefix + last。last は活用する語 (verb / adj) か、活用しない形 (fixed)"""

    def __init__(self, last, kind):
        self.prefix, self.last, self.kind = '', last, kind

    def text(self):
        return self.prefix + self.last

    # 現代語の動詞の形
    @staticmethod
    def past_form(verb):
        if isinstance(verb, Derived):
            return verb[:-1] + 'た'
        out = JaVerb(verb).form(V.INDICATIVE | V.PAST, False)
        if '{' in out:  # 現代語の辞書に無い動詞 (あかる): 五段として規則で
            onbin = {'う': 'った', 'つ': 'った', 'る': 'った', 'む': 'んだ', 'ぶ': 'んだ', 'ぬ': 'んだ', 'く': 'いた',
                     'ぐ': 'いだ', 'す': 'した'}
            out = verb[:-1] + onbin.get(verb[-1], verb[-1] + 'た')
        return out

    @staticmethod
    def te(verb):
        p = Modern.past_form(verb)
        return p[:-1] + ('て' if p.endswith('た') else 'で')

    @staticmethod
    def neg_stem(verb):
        if isinstance(verb, Derived):
            return str(verb[:-1])
        out = JaVerb(verb).form(V.INDICATIVE, True)[:-2]
        if '{' in out:
            row = {'う': 'わ', 'く': 'か', 'ぐ': 'が', 'す': 'さ', 'つ': 'た', 'ぬ': 'な', 'ぶ': 'ば', 'む': 'ま', 'る': 'ら'}
            out = verb[:-1] + row.get(verb[-1], verb[-1])
        return out

    @staticmethod
    def masu_stem(verb):
        if isinstance(verb, Derived):
            return str(verb[:-1])
        jv = JaVerb(verb)
        t = jv.conjug_type or ''
        if verb.endswith('する'):
            return verb[:-2] + 'し'
        if verb.endswith('くる') or verb.endswith('来る'):
            return verb[:-1]
        if '一段' in t:
            return verb[:-1]
        row = {'う': 'い', 'く': 'き', 'ぐ': 'ぎ', 'す': 'し', 'つ': 'ち', 'ぬ': 'に', 'ぶ': 'び', 'む': 'み', 'る': 'り'}
        return verb[:-1] + row.get(verb[-1], verb[-1])

    @staticmethod
    def volitional(verb):
        jv = JaVerb(verb)
        t = jv.conjug_type or ''
        if verb.endswith('する'):
            return verb[:-2] + 'しよう'
        if '一段' in t or verb.endswith(('くる', '来る')):
            return verb[:-1] + 'よう'
        row = {'う': 'お', 'く': 'こ', 'ぐ': 'ご', 'す': 'そ', 'つ': 'と', 'ぬ': 'の', 'ぶ': 'ぼ', 'む': 'も', 'る': 'ろ'}
        return verb[:-1] + row.get(verb[-1], verb[-1]) + 'う'

    # 組み立て
    def verbify(self, last):
        self.prefix += self.last if self.kind == 'fixed' else ''
        self.last, self.kind = last, 'verb'

    def negative(self):
        if self.kind == 'masu':
            self.last, self.kind = 'ません', 'fixed'
            return
        if self.kind == 'verb':
            self.prefix += self.neg_stem(self.last)
        elif self.kind == 'adj':
            self.prefix += self.last[:-1] + 'く'
        else:
            self.prefix += self.last + 'では'
        self.last, self.kind = 'ない', 'adj'

    def continuous(self):
        if self.kind == 'verb':
            self.prefix += self.te(self.last)
            self.last = 'いる'

    def past(self):
        if self.kind == 'masu':
            self.last, self.kind = 'ました', 'fixed'
            return
        if self.kind == 'verb':
            self.last = Modern.past_form(self.last)
        elif self.kind == 'adj':
            self.last = self.last[:-1] + 'かった'
        else:
            self.last += 'だった'
        self.kind = 'fixed'

    def perfect_then(self):
        """完了 + 過去 (〜にけり): 〜てしまった"""
        if self.kind == 'verb':
            self.prefix += self.te(self.last)
            self.last = 'しまう'

    def attach_potential(self):
        """可能「〜ことができる」(打消が続けば「〜ことができない」)"""
        self.prefix += self.last + 'ことが'
        self.last, self.kind = 'できる', 'verb'

    def attach(self, word, kind='fixed'):
        """終止形の後ろに付ける (だろう、そうだ …)"""
        self.prefix += self.last
        self.last, self.kind = word, kind

    def final(self, how):
        """後ろに続くものに合わせた形: 'te' (〜て)、'adverbial' (連用中止・連用形)、'plain'"""
        if how == 'te':
            if self.kind == 'masu':
                return self.prefix + 'まして'
            if self.kind == 'verb':
                return self.prefix + self.te(self.last)
            if self.kind == 'adj':
                return self.prefix + self.last[:-1] + 'くて'
            return self.text() + 'て'
        if how == 'adverbial':
            if self.kind == 'adj':
                return self.prefix + self.last[:-1] + 'く'
            if self.kind == 'verb':
                return self.prefix + self.te(self.last)
        return self.text()


def m_is_set(local):
    return 'm' in local


def _agent_before(bunsetsu, i):
    """i 番目の述語の前 (句読点まで) に「人 + に」があるか (受身の動作主: 人に笑はる)"""
    for j in range(i - 1, -1, -1):
        b = bunsetsu[j]
        if b.kind == 'punct':
            return False
        if b.kind == 'nominal' and any(t.lemma == 'に' and t.pos == '助詞' for t in b.tokens) and is_human(b.head):
            return True
    return False


def _kakari_koso(bunsetsu, i):
    return any(t.lemma == 'こそ' for b in bunsetsu[:i + 1] for t in b.tokens)


def _predicate(b, nxt, after_quote, subject=None, ctx=None):
    """用言の文節 → (現代語, 残りの助詞)"""
    tokens = b.tokens
    head = tokens[0]
    # 体言 + 動詞的接尾辞 (紫だつ → 紫がかる)
    suffix = next((t for t in tokens if t.pos == '接尾辞' and t.pos2 == '動詞的'), None)
    bunsetsu_all, index_all = ctx if ctx else ([b], 0)
    prev = bunsetsu_all[index_all - 1] if index_all > 0 else None
    compound = None
    if head.pos == '動詞' and prev is not None and prev.kind == 'verb' and len(prev.tokens) == 1 and \
            (prev.head.lemma, head.lemma) in COMPOUND_VERBS:
        compound = COMPOUND_VERBS[(prev.head.lemma, head.lemma)]
        prev.modern = ''  # 前の動詞は複合動詞に含める
    honor = grammar.honorific(head)
    auxiliary_verb = prev is not None and prev.kind == 'verb' and head.pos2 == '非自立可能' and \
        not [t for t in prev.tokens if t.pos == '助詞'] and prev.tokens[-1].form in ('連用形', '未然形')
    if head.lemma == '為る' and prev is not None and prev.head.surface == '御覧':
        compound = 'ご覧になる'  # 御覧ず
        prev.modern = ''
    if head.pos == '動詞' and honor is not None and not compound:
        word = (honor[2] if auxiliary_verb and honor[2] else honor[1]) or _modern_word(head)
        head.chosen = honor[0] + '語' + ('の補助動詞' if auxiliary_verb else '')
        if word == 'ていらっしゃる':
            word = 'いらっしゃる'
        m = Modern(word, 'masu' if word == 'ます' else 'verb')
    elif head.pos == '動詞':
        word = compound or vocabulary(head) or obsolete(head) or _plain_word(head)
        if head.lemma == '有る' and subject is not None and is_human(subject):
            word = 'いる'  # 人が主語の「あり」(翁といふものありけり → 老人がいた)
        m = Modern(word, 'verb')
    elif head.pos == '形容詞':
        word = vocabulary(head) or obsolete(head) or _plain_word(head)
        m = Modern(word, 'adj' if word.endswith('い') else 'fixed')
    elif suffix is not None:
        m = Modern(head.surface + 'がかる', 'verb')
    else:
        return None
    rest = tokens[1:]
    auxes = [t for t in rest if t.pos == '助動詞']
    particles = [t for t in rest if t.pos == '助詞']
    kinds = [grammar.auxiliary(a)[1] for a in auxes]
    bunsetsu, index = ctx if ctx else ([b], 0)
    first_person = subject is not None and (subject.lemma in FIRST_PERSON or subject.surface in FIRST_PERSON)
    attributive = b_is_attributive(b, nxt)
    emphatic = False
    honor_masu = False
    for k, kind in enumerate(kinds):
        later = kinds[k + 1:]
        aux = auxes[k]
        if kind == 'perfect' and later and later[0] in ('conjecture', 'should'):
            emphatic = True  # 強意 (てむ・なむ・ぬべし): きっと〜
            aux.chosen = '強意'
            continue
        if kind == 'passive':
            if 'negative' in later or 'neg_conjecture' in later:
                aux.chosen = '可能'
                m.attach_potential()   # 〜ことができる (打消と組んで「〜できない」)
                continue
            if _agent_before(bunsetsu, index):
                aux.chosen = '受身'
            elif head.lemma in EMOTION_VERBS or (compound and prev.head.lemma in EMOTION_VERBS):
                aux.chosen = '自発'
                m.prefix = '自然と' + m.prefix
                continue
            elif subject is not None and (subject.lemma in HONORED or subject.surface in HONORED):
                aux.chosen = '尊敬'
                if m.kind == 'verb':
                    m.last = m.masu_stem(m.last) + 'なさる'
                continue
            else:
                aux.chosen = '受身'
        if kind == 'causative' and not later and nxt is not None and nxt.head.lemma == '給う-尊敬':
            aux.chosen = '尊敬 (せたまふ・させたまふ: 最高敬語)'
            honor_masu = True
            continue  # 使役でなく尊敬: 後ろの「たまふ」と合わせて「〜なさる」(言はせたまふ → 言いなさる)
        if kind in ('passive', 'causative'):
            if m.kind == 'verb':
                stem = m.neg_stem(m.last)
                ichidan = stem == m.last[:-1] and not m.last.endswith('う')
                if kind == 'passive':
                    m.last = Derived(stem + ('られる' if ichidan else 'れる'))
                else:
                    m.last = Derived(stem + ('させる' if ichidan else 'せる'))
        elif kind == 'negative':
            m.negative()
        elif kind == 'continuous':
            if 'past' in later or b_is_attributive(b, nxt) or not later:
                m.continuous()  # 存続「〜ている」
            else:
                m.past()
        elif kind == 'perfect':
            if 'past' in later:
                m.perfect_then() if m.kind != 'masu' else None
            elif not later:
                m.past()
        elif kind == 'past':
            m.past()
        elif kind == 'conjecture':
            if attributive and not later:
                aux.chosen = '婉曲'
                m.attach('ような')        # 思はむ子 → 思うような子
            elif aux.form == '連体形' and particles and not later:
                aux.chosen = '仮定・婉曲'
                m.attach('ようなこと')    # 準体法 (法師になしたらむこそ → 法師にしたようなことこそ)
            elif (after_quote or first_person) and m.kind == 'verb' and not emphatic:
                aux.chosen = '意志'
                m.last, m.kind = Modern.volitional(m.last), 'fixed'
            elif aux.form == '已然形' and _kakari_koso(bunsetsu, index):
                aux.chosen = '適当・勧誘'
                m.attach('のがよい')      # 〜こそ〜め
            else:
                aux.chosen = '推量'
                m.attach('だろう')
        elif kind == 'present_conjecture':
            m.continuous()
            m.attach('だろう')
        elif kind == 'past_conjecture':
            m.past()
            m.attach('だろう')
        elif kind == 'should':
            if 'negative' in later:
                aux.chosen = '可能 (打消と組んで不可能)'
                m.attach_potential()
            elif first_person and not later:
                aux.chosen = '意志'
                m.attach('つもりだ')
            elif attributive:
                aux.chosen = '当然'
                m.attach('はずの')
            else:
                aux.chosen = '当然・推量'
                m.attach('はずだ')
        elif kind == 'counterfactual':
            m.past()
            m.attach('だろうに')
        elif kind == 'neg_conjecture':
            m.negative()
            m.attach('だろう')
        elif kind in ('seems', 'like'):
            m.attach('ようだ')
        elif kind == 'seems_rashii':
            m.attach('らしい')
        elif kind == 'hearsay':
            m.attach('という' if b_is_attributive(b, nxt) else 'そうだ')  # すなる日記 → するという日記
        elif kind == 'copula':
            m.attach('のである')
        elif kind == 'want':
            if m.kind == 'verb':
                m.prefix += m.masu_stem(m.last)
                m.last, m.kind = 'たい', 'adj'
    if emphatic:
        m.prefix = 'きっと' + m.prefix
    if honor_masu and m.kind == 'verb':
        return m.prefix + m.masu_stem(m.last), particles
    # 後ろに続くもの
    last_cform = (auxes[-1] if auxes else head).form
    if particles and particles[0].lemma == 'で' and particles[0].pos2 == '接続助詞':
        m.negative()
        return m.text() + 'で', particles[1:]  # 打消の接続「で」(心にもあらで → 心にもないで)
    if m.kind == 'fixed' and head.pos == '形容詞' and not auxes and m.last.endswith('な'):
        # 形容動詞の形の訳 (あやし → 不思議な): 連用形は「に」(て が続けば「で」)、文末の終止形は「だ」
        if particles and particles[0].lemma == 'て':
            return m.prefix + m.last[:-1] + 'で', particles
        if last_cform == '連用形':
            return m.prefix + m.last[:-1] + 'に', particles
        if last_cform == '終止形' and not particles:
            return m.prefix + m.last[:-1] + 'だ', particles
    how = 'plain'
    if particles and particles[0].lemma == 'て':
        how = 'te'
    elif particles and particles[0].lemma == 'つつ' and m.kind == 'verb':
        return m.prefix + m.masu_stem(m.last), particles  # 取りつつ → 取りながら
    elif not particles and last_cform == '連用形' and nxt is not None and nxt.kind == 'verb' and \
            nxt.head.lemma in AUX_VERBS:
        how = 'te'  # なりゆく → なっていく
    elif not particles and last_cform == '連用形' and nxt is not None and nxt.kind in ('verb', 'adj') and \
            m.kind == 'adj':
        how = 'adverbial'  # 白くなる
    elif not particles and nxt is not None and nxt.kind == 'verb' and grammar.honorific(nxt.head) and \
            grammar.honorific(nxt.head)[2] == 'ていらっしゃる' and nxt.head.pos2 == '非自立可能':
        how = 'te'  # 〜ておはす → 〜ていらっしゃる
    elif not particles and last_cform in ('連用形', '未然形') and nxt is not None and nxt.kind == 'verb' and \
            grammar.honorific(nxt.head) and grammar.honorific(nxt.head)[2] == 'ます' and m.kind == 'verb':
        return m.prefix + m.masu_stem(m.last), particles  # 知りはべり → 知ります
    elif not particles and last_cform == '連用形' and nxt is not None and nxt.kind == 'verb' and \
            not auxes and head.pos == '動詞':
        return Modern.masu_stem(m.last) if m.kind == 'verb' else m.text(), particles  # 複合動詞 (見送る)
    text = m.final(how)
    return text, particles


def b_is_attributive(b, nxt):
    last = b.tokens[-1]
    return last.form == '連体形' and nxt is not None and nxt.kind == 'nominal'


def _particle(p, b, nxt, last_form):
    """助詞1つ → 現代語"""
    lemma = p.lemma
    if lemma == 'て':
        return ''  # 用言の形に含めた
    if lemma == 'の' and p.pos2 == '格助詞' and nxt is not None and nxt.kind in ('verb', 'adj', 'nadj'):
        return 'が'  # 主格の「の」(雲の細くたなびきたる → 雲が細くたなびいている)
    if lemma == 'ば':
        return 'ので' if last_form == '已然形' else 'なら'
    if lemma == 'を' and p.pos2 == '接続助詞':
        return 'を' if b.head.pos in ('名詞', '代名詞') else 'が'  # 体言の後ろは目的語の「を」
    if lemma in ('や', 'か') and p.pos2 == '係助詞':
        return 'か'
    if lemma in grammar.PARTICLES:
        return grammar.PARTICLES[lemma] or ''
    return p.kana if p.kana else p.surface


def _modern_kana_surface(token):
    """体言など: かなだけの語は現代仮名遣いの読み、漢字を含む語は書かれたまま (仮名の部分だけ直す)"""
    if not _has_kanji(token.surface):
        return token.kana
    out = token.surface
    for old, new in (('は', 'わ'), ('ひ', 'い'), ('ふ', 'う'), ('へ', 'え'), ('ほ', 'お'), ('ゐ', 'い'), ('ゑ', 'え')):
        if out.endswith(old) and len(out) > 1:
            out = out[:-1] + new
    return out


def modernize(tokens):
    """[Token] → ([Bunsetsu], 現代語の文, 注)"""
    bunsetsu = split(tokens)
    notes = []
    for i, b in enumerate(bunsetsu):
        nxt = next((x for x in bunsetsu[i + 1:] if x.kind != 'punct'), None) \
            if i + 1 < len(bunsetsu) and bunsetsu[i + 1].kind != 'punct' else None
        if b.kind == 'punct':
            b.modern = b.head.surface
            continue
        after_quote = any(t.lemma in ('と', 'とて') for t in (bunsetsu[i + 1].tokens if i + 1 < len(bunsetsu) else [])) \
            or any(t.lemma in ('と', 'とて') for t in b.tokens)
        if b.kind in ('verb', 'adj') and b.head.pos in ('動詞', '形容詞') or b.kind == 'verb':
            result = _predicate(b, nxt, after_quote, subject_of(bunsetsu, i), (bunsetsu, i))
            if result is not None:
                text, particles = result
                if b.head.obsolete == 'unknown':
                    text = '〔%s〕' % text  # 現代語に無い語を形だけ直したもの
                last_form = ([t for t in b.tokens if t.pos in ('助動詞', '動詞', '形容詞')] or [b.head])[-1].form
                b.modern = text + ''.join(_particle(p, b, nxt, last_form) for p in particles)
                continue
        # 体言・形容動詞・副詞など
        head = b.head
        word = vocabulary(head)
        copula = any(t.pos == '助動詞' and grammar.auxiliary(t)[1] == 'copula' for t in b.tokens)
        if word is not None and (b.kind == 'nadj' or word.endswith('い') and copula):
            # 形容動詞を表の語に: 形容詞 (むなしい) は活用させ、それ以外 (はっきり) は連用形を「と」に
            form = next((t.form for t in b.tokens if t.pos == '助動詞'), '')
            if word.endswith('い'):
                word = word[:-1] + {'連用形': 'く'}.get(form, 'い')
            elif form == '連用形':
                word += 'と'
            b.modern = word + ''.join(_particle(t, b, nxt, head.form) for t in b.tokens if t.pos == '助詞')
            continue
        if word is None:
            word = ''.join(_modern_kana_surface(t) for t in b.tokens if t.pos not in ('助詞', '助動詞'))
        rest = [t for t in b.tokens if t.pos in ('助詞', '助動詞')]
        out = word
        for t in rest:
            if t.pos == '助動詞':
                kind = grammar.auxiliary(t)[1]
                if kind == 'copula':
                    form = t.form
                    if b.kind == 'nadj':
                        out += {'連用形': 'に', '連体形': 'な'}.get(form, 'だ')
                    else:
                        out += {'連用形': 'で', '連体形': 'である'}.get(form, 'である')
                elif kind == 'past':
                    out += 'だった' if not out.endswith(('た', 'だ')) else ''
                elif kind == 'negative':
                    out += 'ではない'
                else:
                    out += grammar.auxiliary(t)[0].split('「')[-1].split('・')[0]
            else:
                out += _particle(t, b, nxt, head.form)
        b.modern = out
    notes += kakari_musubi(bunsetsu)
    notes += honorific_notes(bunsetsu)
    notes += obsolete_notes(bunsetsu)
    for i, b in enumerate(bunsetsu[:-1]):
        nxt = bunsetsu[i + 1]
        after = bunsetsu[i + 2] if i + 2 < len(bunsetsu) else None
        if b.kind == 'nominal' and b.head.pos in ('名詞', '代名詞') and is_human(b.head) and \
                all(t.pos in ('名詞', '代名詞', '接頭辞', '接尾辞') for t in b.tokens) and b.modern and \
                nxt.kind == 'nominal' and nxt.tokens[-1].lemma in ('を', 'に') and after is not None and after.kind == 'verb':
            b.modern += 'が'  # 人 + 目的語 + 動詞 (翁竹を取る → 老人が竹を取る)
            continue
        if b.kind == 'nominal' and b.head.pos in ('名詞', '代名詞') and b.head.pos3 != '副詞可能' and \
                all(t.pos in ('名詞', '代名詞', '接頭辞', '接尾辞') for t in b.tokens) and nxt.kind in ('verb', 'adj') \
                and not b.modern.endswith(('が', 'は', 'も')) and vocabulary(b.head) is None and b.modern:
            if transitive_only(nxt.head.lemma) and not is_human(b.head) and \
                    not any(grammar.auxiliary(t)[1] == 'passive' for t in nxt.tokens if t.pos == '助動詞'):
                b.modern += 'を'  # 他動詞の前の、人でない体言は目的語 (歌よむ → 歌を詠む)
            else:
                b.modern += 'が'  # 助詞の無い主語 (ものありけり → ものがいた)
        if nxt.head.lemma == '為る' and nxt.head.surface == 'し' and len(nxt.tokens) > 1 and \
                nxt.tokens[1].lemma == 'て' and b.modern.endswith('なく'):
            b.modern = b.modern[:-2] + 'ないで'  # 〜ずして → 〜ないで
            nxt.modern = ''
    text = ''
    for b in bunsetsu:
        if b.modern.startswith('ない') and text.endswith('で'):
            text += 'は'  # 〜にあらず → 〜ではない
        text += b.modern
    return bunsetsu, text, notes


def kakari_musubi(bunsetsu):
    """係り結び: 係助詞 ぞ・なむ・や・か (→ 連体形)、こそ (→ 已然形) と、句点までの最後の述語の活用形"""
    notes = []
    tokens = [t for b in bunsetsu for t in b.tokens]
    for i, t in enumerate(tokens):
        if t.pos == '助詞' and t.pos2 == '係助詞' and t.lemma in grammar.KAKARI:
            form, meaning = grammar.KAKARI[t.lemma]
            end = next((j for j in range(i + 1, len(tokens)) if tokens[j].surface in ('。', '」')), len(tokens))
            pred = next((tokens[j] for j in range(end - 1, i, -1) if tokens[j].pos in ('動詞', '形容詞', '助動詞')
                         and tokens[j].form), None)
            if pred is None:
                continue
            ok = pred.form == form
            notes.append('係り結び: 係助詞「%s」(%s) → 結びの「%s」は%s%s' % (
                t.surface, meaning, pred.surface, form, '' if ok else ' (ここでは %s: 結びの流れ・消滅か)' % pred.form))
    return notes


def obsolete_notes(bunsetsu):
    """現代語に無い語の注"""
    notes = []
    for b in bunsetsu:
        t = b.head
        if t.obsolete == 'table':
            notes.append('現代語に無い語: 「%s」(%s) →「%s」' % (t.surface, t.base_orth, obsolete(t)))
        elif t.obsolete == 'unknown':
            notes.append('現代語に無い語: 「%s」(%s)。表に無いので形だけ現代語にした (〔 〕の中)' % (t.surface, t.base_orth))
    return notes


def honorific_notes(bunsetsu):
    """敬語の注: 種類と、誰への敬意か。尊敬語があって主語が書かれていなければ、主語の手がかりを"""
    notes = []
    tokens = [t for b in bunsetsu for t in b.tokens]
    for i, t in enumerate(tokens):
        honor = grammar.honorific(t)
        if honor is None:
            continue
        kind = honor[0]
        notes.append('敬語: 「%s」は%s語 (%s)' % (t.surface, kind, grammar.HONORIFIC_NOTES[kind]))
        prev = tokens[i - 1] if i else None
        if prev is not None and kind == '尊敬' and grammar.honorific(prev) and grammar.honorific(prev)[0] == '謙譲':
            notes.append('二方面への敬語: 謙譲語「%s」+ 尊敬語「%s」で、動作を受ける人とする人の両方を敬う' % (prev.surface, t.surface))
        if prev is not None and kind == '尊敬' and prev.pos == '助動詞' and prev.base_orth in ('す', 'さす', 'しむ'):
            notes.append('最高敬語: 「%s%s」(尊敬の助動詞 + たまふ) は帝・中宮など最も身分の高い人の動作' % (prev.surface, t.surface))
    for i, b in enumerate(bunsetsu):
        if b.kind == 'verb' and any(grammar.honorific(t) and grammar.honorific(t)[0] == '尊敬' for t in b.tokens) \
                and subject_of(bunsetsu, i) is None and not any(
                    grammar.honorific(t) and grammar.honorific(t)[0] == '尊敬' for x in bunsetsu[:i] for t in x.tokens):
            notes.append('主語: 書かれていないが、尊敬語があるので身分の高い人 (場面の貴人) の動作')
            break
    return notes
