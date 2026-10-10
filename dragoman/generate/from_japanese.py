#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 日本語の文 → 文の枠 (frame.Clause) (MeCab + UniDic と手作りの規則。係り受け解析器は使わない)
#
#   1. 形態素 → 文節 (自立語 + 付属語: 助詞・助動詞・補助動詞「ている」)
#   2. 述語の文節 (動詞・形容詞・名詞 + だ / です) ごとに節を作る。名詞の文節は後ろの一番近い述語に係る
#      (日本語は述語が後ろ)。「は」の文節は文の最後の述語 (主節) に係る
#      述語が連体形で名詞の文節が続けば連体修飾節 (関係節): 空所は、節の中で欠けている格
#      (が が無ければ主語、他動詞で を が無ければ目的語。どちらでもなければ空所の無い連体修飾 → 扱わない)
#   3. 助詞 → 役割: が 主語、を 目的語、に 受け手 (移動の動詞なら ad + 対格)、で 場所 (in + 奪格) か手段、
#      から 起点 (ab / ex + 奪格)、へ・まで ad + 対格、と cum + 奪格、の 属格。
#      は は役割を示さないので、他動詞で が がほかにあれば目的語、無ければ主語
#   4. 助動詞 → 時制・態・否定: た 完了、ていた 未完了過去、ている 現在、う・よう・だろう 未来、れる・られる 受動、
#      ない・ぬ 否定、命令形 命令法
#   5. 節のつなぎ: て → et、ので・から → quod、と・ば・たら・なら → sī、が・けれど → sed、
#      連体形 + とき → ubi (cum)、ながら → dum
#   6. 語はラテン語の見出しに置き換える (ja_lexicon)。英語・ロシア語・サンスクリットはラテン語の見出しから
#
import functools
import os
import re
from dataclasses import dataclass, field

from . import ja_lexicon
from .frame import Clause, NP, Lex

try:
    import MeCab
    _tagger = MeCab.Tagger('')
except Exception:   # MeCab が無ければ日本語の文は扱えない
    _tagger = None

CONTENT = {'名詞', '動詞', '形容詞', '副詞', '代名詞', '連体詞', '形状詞', '接頭辞'}
PRONOUNS = {'私': ('ego', 1, 'sg'), '僕': ('ego', 1, 'sg'), '俺': ('ego', 1, 'sg'), 'あなた': ('tū', 2, 'sg'),
            '君': ('tū', 2, 'sg'), 'お前': ('tū', 2, 'sg'), '彼': ('is', 3, 'sg'), '彼女': ('is', 3, 'sg'),
            '私たち': ('ego', 1, 'pl'), '我々': ('ego', 1, 'pl'), 'あなたたち': ('tū', 2, 'pl'), '彼ら': ('is', 3, 'pl'),
            'これ': ('hic', 3, 'sg'), 'それ': ('is', 3, 'sg'), 'あれ': ('ille', 3, 'sg')}
DEMONSTRATIVES = {'この': 'hic', 'その': 'is', 'あの': 'ille'}
INTERROGATIVES = {'誰': 'quis', '何': 'quid', 'なぜ': 'cūr', 'どこ': 'ubi', 'いつ': 'quandō', 'どう': 'quōmodo'}
# 時の名詞 → 副詞 (昨日 → heri)。助詞が無くても目的語にしない
TIME_ADVERBS = {'昨日': 'heri', '今日': 'hodiē', '明日': 'crās', '今': 'nunc', '毎日': 'cotīdiē', 'いつも': 'semper',
                '朝': 'māne', '夜': 'nocte', '昔': 'ōlim', '後で': 'posteā', 'すぐ': 'statim'}
# 「に」が場所を表す動詞 (島に住む → in īnsulā habitat)
LOCATIVE_NI_VERBS = {'住む', 'いる', '居る', 'ある', '在る', '座る', '立つ', '寝る', '眠る', '残る', '隠れる', '生まれる'}
MOTION_VERBS = {'行く', '来る', '帰る', '入る', '向かう', '急ぐ', '走る', '逃げる', '着く', '運ぶ'}
PLACE_PARTICLE_PREP = {'で': ('in', 'Abl'), 'から': ('ex', 'Abl'), 'へ': ('ad', 'Acc'), 'まで': ('ad', 'Acc'),
                       'と': ('cum', 'Abl')}
CONNECTIVES = {'て': 'et', 'で': 'et', 'ので': 'quod', 'から': 'quod', 'ば': 'sī', 'たら': 'sī', 'なら': 'sī',
               'が': 'sed', 'けれど': 'sed', 'けど': 'sed', 'ながら': 'dum', 'と': 'sī'}
SUBORDINATE = {'quod', 'sī', 'dum', 'ubi'}
PREFERRED = {'見る': 'videō', '褒める': 'laudō', '美しい': 'pulcher', '大きい': 'magnus', '歌う': 'cantō',
             '言う': 'dīcō', '持つ': 'habeō', '住む': 'habitō', '働く': 'labōrō', '与える': 'dō', '良い': 'bonus',
             '小さい': 'parvus', '多い': 'multus', '戦う': 'pugnō', '呼ぶ': 'vocō', '恐れる': 'timeō', '男': 'vir',
             '女': 'fēmina', '人': 'homō', '神': 'deus', '友': 'amīcus', '友達': 'amīcus', '父': 'pater',
             '娘': 'fīlia', '息子': 'fīlius', '主人': 'dominus', '奴隷': 'servus', '兵士': 'mīles', '敵': 'hostis',
             'できる': 'possum', '渡る': 'trānseō', '人々': 'homō', '送る': 'mittō', '摘む': 'carpō', '帰る': 'redeō', '降る': 'cadō', '雨': 'imber', '知る': 'sciō', '書く': 'scrībō',
             '道': 'via', '家': 'domus', '国': 'patria', '島': 'īnsula', '川': 'flūmen', '水': 'aqua', '剣': 'gladius'}


@dataclass
class Token:
    surface: str
    pos: str
    pos2: str
    ctype: str
    cform: str
    lemma: str
    lexeme: str = ''   # 語彙素 (愛さ → 愛する。書字形の基本形 lemma は 愛す)


@dataclass
class Chunk:
    """文節: 自立語 (head) と付属語"""
    tokens: list = field(default_factory=list)

    @property
    def content(self):
        return [t for t in self.tokens if t.pos in CONTENT and not (t.pos == '動詞' and t.pos2 == '非自立可能' and
                                                                    self._after_te(t))]

    def _after_te(self, token):
        k = self.tokens.index(token)
        return k > 0 and self.tokens[k - 1].lemma in ('て', 'で')

    @property
    def head(self):
        content = self.content
        return content[-1] if content else self.tokens[0]

    @property
    def nouns(self):
        return [t for t in self.content if t.pos in ('名詞', '代名詞')]

    @property
    def particles(self):
        return [t.lemma for t in self.tokens if t.pos == '助詞']

    @property
    def is_predicate(self):
        head = self.head
        return head.pos in ('動詞', '形容詞') or (head.pos in ('名詞', '代名詞', '形状詞') and
                                               any(t.lemma in ('だ', 'です', 'である') for t in self.tokens))

    @property
    def attributive(self):
        """連体形で終わる (後ろの名詞を修飾する)"""
        last = [t for t in self.tokens if t.pos not in ('補助記号',)]
        return bool(last) and last[-1].cform.startswith('連体形') and last[-1].pos != '助詞' 

    @property
    def surface(self):
        return ''.join(t.surface for t in self.tokens)


def tokenize(text):
    out = []
    node = _tagger.parseToNode(text)
    while node:
        if node.surface:
            f = node.feature.split(',')
            f += [''] * (8 - len(f))
            f += [''] * (11 - len(f))
            base = f[10] if f[10] and f[10] != '*' else f[7]   # 書字形の基本形 (帰っ → 帰る。語彙素は 返る)
            out.append(Token(node.surface, f[0], f[1], f[4], f[5], base or node.surface,
                             re.sub(r'-.*$', '', f[7]) or base))
        node = node.next
    return out


def chunks(tokens):
    """形態素 → 文節。名詞の連続 (複合語)・接頭辞の後ろ・補助動詞 (て + いる) は同じ文節"""
    out = []
    for t in tokens:
        new = t.pos in CONTENT
        if out and new:
            prev = out[-1].tokens[-1]
            if prev.pos == '接頭辞' or (prev.pos == '名詞' and t.pos == '名詞' and prev.pos2 != '数詞') or \
                    (t.pos == '動詞' and t.pos2 == '非自立可能' and prev.lemma in ('て', 'で')) or \
                    (t.pos == '名詞' and t.pos2 == '普通名詞' and prev.pos == '名詞' and prev.pos2 == '固有名詞'):
                new = False
        if t.pos == '補助記号':
            new = False
        if new or not out:
            out.append(Chunk([t]))
        else:
            out[-1].tokens.append(t)
    return out


# ----------------------------------------------------------------------
# 語

def latin_lex(lemma, pos, lexeme=''):
    """日本語の見出し → (Lex, 性)。優先表 → 逆引き (無ければ語彙素 lexeme で)"""
    preferred = PREFERRED.get(lemma)
    if preferred:
        found = ja_lexicon._index().get(lemma, [])
        match = next(((lex, g) for _, lex, g in found if lex.lemma == preferred), None)
        if match:
            return match
        from dragoman.latin import latindic   # 優先表の語の辞書の項目 (訳語は別の書き方: laudō「称賛する,ほめる」)
        for item in latindic.lookup(preferred) or []:
            if (item.get('base') or item.get('pres1sg')) == preferred and item.get('pos') in ('noun', 'verb', 'adj'):
                gender = next((t[2] for t in item.get('_') or [] if len(t) > 2 and t[2]), '')
                return Lex(preferred, item['pos'], item.get('ja')), gender
    found = ja_lexicon.lookup(lemma, pos)
    if found is None and lexeme and lexeme != lemma:
        return latin_lex(lexeme, pos)   # 書字形で無ければ語彙素で (愛す → 愛する、返る → 帰る の逆も)
    if found is None and pos == 'verb' and lemma.endswith('す') and not lemma.endswith('する'):
        found = latin_lex(lemma[:-1] + 'する', pos)   # 愛す → 愛する (GiNZA の見出し)
    if found is None and pos == 'verb' and lemma.endswith('する'):
        found = ja_lexicon.lookup(lemma[:-2], 'verb') or ja_lexicon.lookup(lemma, 'verb')
    return found


def _gender(lex, gender):
    if gender or lex.pos != 'noun':
        return gender
    from . import latin
    for _, item in latin._forms(lex.lemma, 'noun', lex.ja):
        for tag in item.get('_') or []:
            if len(tag) > 2 and tag[2]:
                return tag[2]
    return 'm'


def noun_phrase(chunk, modifiers=()):
    """名詞の文節 → NP (修飾語: 連体詞・形容詞の文節)"""
    noun = chunk.nouns[-1] if chunk.nouns else chunk.head
    lemma = noun.lemma
    number = 'sg'
    if lemma.endswith(('たち', '達', 'ら')) and lemma not in PRONOUNS:
        lemma, number = re.sub('(たち|達|ら)$', '', lemma), 'pl'
    if lemma.endswith('々'):
        number = 'pl'   # 人々 (優先表で homō の複数)
    if any(t.lemma in ('たち', '達', 'ら') and t.pos == '接尾辞' for t in chunk.tokens):
        number = 'pl'
    if lemma in PRONOUNS:
        latin, person, number = PRONOUNS[lemma]
        np = NP(Lex(latin, 'pronoun', desc='人称代名詞' if latin in ('ego', 'tū', 'is') else '指示代名詞'),
                number=number, gender='f' if lemma == '彼女' else 'm', surface=chunk.surface)
        np.person = person
        return np
    if lemma in INTERROGATIVES and INTERROGATIVES[lemma] in ('quis', 'quid'):
        return NP(Lex(INTERROGATIVES[lemma], 'pronoun', desc='疑問代名詞'), number='sg',
                  gender='n' if lemma == '何' else 'm', interrogative=True, surface=chunk.surface)
    found = latin_lex(lemma, 'noun', noun.lexeme)
    if found is None:
        np = NP(Lex(noun.surface, 'noun', proper=noun.pos2 == '固有名詞'), number=number, surface=chunk.surface)
    else:
        lex, gender = found
        np = NP(lex, number=number, gender=_gender(lex, gender), surface=chunk.surface)
        # 人・動物: 訳語から、または日本語の語 (〜人・〜者・〜士・〜夫・人々・子)
        np.animate = _animate(lex) or bool(re.search('(人|者|士|夫|々|子|王|母|父|娘|女|男|師)$', noun.lemma))
    for m in modifiers:
        np.modifiers.append(m)
    return np


def _animate(lex):
    """人・動物か (core.animacy を訳語で)"""
    from dragoman.core.Item import Item
    from dragoman.core.animacy import is_animate
    return is_animate(Item({'surface': lex.lemma, 'pos': lex.pos, 'ja': lex.ja or ''}))


def modifier(chunk):
    """名詞を修飾する文節 (連体詞・形容詞の連体形) → Lex"""
    head = chunk.head
    if head.lemma in DEMONSTRATIVES or head.surface in DEMONSTRATIVES:
        latin = DEMONSTRATIVES.get(head.surface) or DEMONSTRATIVES[head.lemma]
        return Lex(latin, 'pronoun', desc='指示代名詞')
    found = latin_lex(head.lemma, 'adj')
    return found[0] if found else Lex(head.surface, 'adj')


# ----------------------------------------------------------------------
# 述語

def predicate(chunk):
    """述語の文節 → (Clause の土台, 他動詞か)"""
    tokens = chunk.tokens
    lemmas = [t.lemma for t in tokens]
    head = chunk.head
    negated = any(t.lemma in ('ない', 'ぬ', 'ず') and t.pos == '助動詞' for t in tokens)
    passive = any(t.ctype.startswith('助動詞-レル') or t.ctype.startswith('助動詞-ラレル') for t in tokens)
    past = 'た' in lemmas or 'だ' in [t.lemma for t in tokens if t.ctype == '助動詞-タ']
    progressive = any(t.lemma in ('居る', 'いる') for t in tokens if t.pos == '動詞' and t.pos2 == '非自立可能')
    if progressive and past:
        tense = 'imperfect'
    elif past:
        tense = 'perfect'
    elif any(t.lemma in ('う', 'よう', 'だろう') or t.cform.startswith('意志推量') for t in tokens):
        tense = 'future'
    else:
        tense = 'present'
    mood = 'imperative' if any(t.cform.startswith('命令形') for t in tokens if t.pos == '動詞') else 'indicative'
    if head.pos == '動詞':
        found = latin_lex(head.lemma, 'verb', head.lexeme)
        verb = found[0] if found else Lex(head.lemma, 'verb')
        clause = Clause(verb, tense=tense, mood=mood, voice='passive' if passive else 'active', negated=negated)
        clause.ja_verb = head.lemma
        return clause
    # 形容詞・名詞 + だ: 繋辞の文 (sum) と補語
    clause = Clause(Lex('sum', 'verb', 'ある,いる,〜である'), tense=tense, mood=mood, negated=negated, copula=True)
    if head.pos == '形容詞':
        found = latin_lex(head.lemma, 'adj', head.lexeme)
        complement = NP(found[0] if found else Lex(head.lemma, 'adj'), number='sg')
    else:
        complement = noun_phrase(chunk)
    clause.args.append(('complement', complement))
    return clause


@functools.lru_cache(maxsize=1)
def _transitivity():
    """日本語の動詞の自他 ($DRAGOMAN_DATA/ja-transitivity.tsv。tools/build_ja_transitivity.py)"""
    from dragoman.core import paths
    table = {}
    path = paths.data('ja-transitivity.tsv')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for line in f:
                word, _, kinds = line.rstrip('\n').partition('\t')
                table[word] = kinds.split(',')
    return table


def _transitive(clause):
    """他動詞か: 日本語の動詞の自他の表、無ければラテン語の辞書の訳語の「〜を」"""
    if clause.copula:
        return False
    kinds = _transitivity().get(getattr(clause, 'ja_verb', ''), [])
    if kinds:
        return 'vt' in kinds
    return 'を' in (clause.verb.ja or '')


ROLE_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Abl'}


def attach(clause, chunk, np, topic=False):
    """名詞句を助詞で節の役割に (名詞句の格も役割から)"""
    _attach(clause, chunk, np, topic)
    role, last = clause.args[-1]
    if last is np and role in ROLE_CASES and not np.prep:
        np.case = ROLE_CASES[role]


def _attach(clause, chunk, np, topic=False):
    particles = [p for p in chunk.particles if p not in ('は', 'も')] or (['は'] if 'は' in chunk.particles else [])
    p = particles[-1] if particles else ''
    head_lemma = clause.verb.ja or ''
    if p == 'が':
        clause.args.append(('subject', np))
    elif p == 'を':
        clause.args.append(('object', np))
    elif p == 'に':
        if clause.voice == 'passive':
            np.prep, np.case = Lex('ā', 'preposition'), 'Abl'   # 受動の動作主 (〜に褒められる → ā magistrō)
            clause.args.append(('prep', np))
        elif getattr(clause, 'ja_verb', '') in LOCATIVE_NI_VERBS:
            np.prep, np.case = Lex('in', 'preposition'), 'Abl'   # 島に住む → in īnsulā
            clause.args.append(('prep', np))
        elif any(v in head_lemma for v in MOTION_VERBS) or clause.verb.lemma in ('veniō', 'eō', 'redeō', 'currō'):
            np.prep, np.case = Lex('ad', 'preposition'), 'Acc'
            clause.args.append(('prep', np))
        else:
            np.case = 'Dat'
            clause.args.append(('recipient', np))
    elif p in PLACE_PARTICLE_PREP:
        prep, case = PLACE_PARTICLE_PREP[p]
        if p == 'で' and np.head is not None and not _place_like(np):
            np.case = 'Abl'
            clause.args.append(('means', np))   # 剣で → gladiō (手段の奪格)
            return
        if p == 'から' and getattr(np, 'person', 3) != 3 or (p == 'から' and np.head.pos == 'pronoun'):
            prep = 'ab'
        np.prep, np.case = Lex(prep, 'preposition'), case
        clause.args.append(('prep', np))
    elif p == 'は' or topic:
        role = 'object' if _transitive(clause) and clause.role('subject') else 'subject'
        clause.args.append((role, np))
        if role == 'subject':
            clause.topic_subject = True
    else:
        clause.args.append(('subject' if not clause.role('subject') else 'object', np))


PLACES = {'庭', '森', '家', '町', '都市', '海', '島', '国', '村', '川', '山', '道', '学校', '神殿', '野', '畑', '岸',
          '洞窟', '船', '部屋', '宮殿', '天', '空', '地'}


def _place_like(np):
    ja = np.head.ja or ''
    return any(p in ja.split(',')[0] for p in PLACES) or any(p == (np.surface or '')[:len(p)] for p in PLACES)


def _finish(clause):
    """主語の人称・数を動詞に"""
    subjects = clause.role('subject')
    if subjects:
        s = subjects[0]
        clause.person = getattr(s, 'person', 3)
        clause.number = 'pl' if s.members else s.number
    else:
        clause.person, clause.number = 3, 'sg'
    return clause


# ----------------------------------------------------------------------
# 文

QUOTE_VERBS = {'言う', '思う', '考える', '信じる', '答える', '書く', '告げる', '知らせる'}
PERCEPTION_VERBS = {'見る', '聞く', '感じる', '気付く'}
TIME_NOUNS = {'時', 'とき'}


def _marker(cs, k):
    """述語の文節の働き: rel (連体修飾節) / nominal (〜のを・〜ことを) / quote (〜と言う) / question (〜か) /
    sub_ubi (〜とき) / sub_quod (〜ので・〜から) / te (〜て) / final"""
    c = cs[k]
    tokens = [t for t in c.tokens if t.pos != '補助記号']
    lemmas = [t.lemma for t in tokens]
    if len(lemmas) >= 2 and lemmas[-2] == 'の' and lemmas[-1] in ('で', 'だ') or \
            any(t.lemma == 'から' and t.pos2 == '接続助詞' for t in tokens):
        return 'sub_quod'   # 降ったので (の + だ の連用形 で)、来るから
    if any(t.pos2 == '準体助詞' for t in tokens):
        return 'nominal'   # 歌うのを
    if any(t.lemma == 'か' and t.pos == '助詞' for t in tokens):
        return 'question'   # 誰が来たか
    if tokens and tokens[-1].lemma == 'と' and tokens[-1].pos2 == '格助詞':
        return 'quote'      # 来ると (言った)
    if c.attributive and k + 1 < len(cs):
        if cs[k + 1].head.lemma in TIME_NOUNS:
            return 'sub_ubi'
        if cs[k + 1].head.lemma in ('こと', '事') and cs[k + 1].particles:
            return 'nominal'
        if cs[k + 1].nouns:
            return 'rel'
    if any(t.lemma in ('て', 'で') and t.pos2 == '接続助詞' for t in tokens) and not \
            any(t.pos == '動詞' and t.pos2 == '非自立可能' for t in tokens[tokens.index(next(
                t for t in tokens if t.lemma in ('て', 'で') and t.pos2 == '接続助詞')) + 1:]):
        return 'te'
    conj = next((t.lemma for t in tokens if t.pos == '助詞' and t.pos2 == '接続助詞'), None)
    if conj in CONNECTIVES:
        return 'conj:' + conj
    return 'final'


@functools.lru_cache(maxsize=1)
def _ginza():
    """GiNZA (spaCy の日本語モデル ja_ginza)。無ければ None (MeCab と規則だけで)"""
    try:
        import spacy
        import ginza
        return spacy.load('ja_ginza'), ginza
    except Exception:
        return None


def ginza_available():
    return _ginza() is not None


def ginza_chunks(text):
    """GiNZA の文節と係り先: (文節の列, 係り先の文節の番号の列)。形態素は UniDic と同じ形の Token に"""
    nlp, ginza = _ginza()
    doc = nlp(text)
    spans = ginza.bunsetu_spans(doc)
    index_of = {}
    cs = []
    for k, span in enumerate(spans):
        tokens = []
        for t in span:
            if t.tag_.startswith('補助記号') and t.text not in ('、', '，'):
                continue
            parts = t.tag_.split('-')
            inflection = (t.morph.get('Inflection') or [';'])[0].split(';') + ['']
            tokens.append(Token(t.text, parts[0], parts[1] if len(parts) > 1 else '*', inflection[0], inflection[1],
                                t.lemma_, t.lemma_))
            index_of[t.i] = k
        cs.append(Chunk(tokens or [Token(span.text, '補助記号', '*', '', '', span.text, span.text)]))
    heads = []
    for k, span in enumerate(spans):
        head = span.root.head
        heads.append(index_of.get(head.i, k) if head.i not in range(span.start, span.end) else k)
    return cs, heads


def parse(text, backend=None):
    """日本語の文 → 文の枠 (Clause の列)。backend: 'ginza' (係り受けを GiNZA で) / 'mecab' (後ろの一番近い述語へ)。
    既定は GiNZA があれば GiNZA"""
    use_ginza = backend == 'ginza' or (backend is None and ginza_available())
    if use_ginza:
        cs, heads = ginza_chunks(text)
    else:
        tokens = [t for t in tokenize(text) if t.pos != '補助記号' or t.lemma in ('、', '，')]
        cs, heads = chunks(tokens), None
    return parse_chunks(cs, heads)


def parse_chunks(cs, heads=None):
    """文節の列 (と係り先) → 文の枠。係り先が無ければ、名詞の文節は後ろの一番近い述語へ"""
    def head_of(k):
        return heads[k] if heads is not None and heads[k] != k else None

    # 連体形の形容詞で、係り先 (無ければすぐ後ろ) が名詞の文節なら修飾語 (美しい薔薇)。述語にしない
    def modifies_noun(k):
        target = head_of(k) if heads is not None else k + 1
        return target is not None and target < len(cs) and bool(cs[target].nouns) and not cs[target].is_predicate
    preds = [k for k, c in enumerate(cs) if c.is_predicate and not (
        c.head.pos == '形容詞' and c.attributive and modifies_noun(k))]
    if not preds:
        return []
    roots = [k for k in preds if heads is not None and heads[k] == k]
    main_ix = roots[-1] if roots else preds[-1]
    built = {k: predicate(cs[k]) for k in preds}
    markers = {k: (_marker(cs, k) if k != main_ix else 'final') for k in preds}
    # 主題「は」の係り先: 後ろの、連体修飾節・名詞節・引用・疑問でない一番近い述語
    clause_final = [k for k in preds if markers[k] in ('final', 'te', 'sub_ubi', 'sub_quod') or
                    markers[k].startswith('conj:')]
    pending_mods = []
    owner_of, nps = {}, {}
    for k, c in enumerate(cs):
        if k in built:
            continue
        head = c.head
        if head.lemma in TIME_NOUNS and k > 0 and k - 1 in markers and markers[k - 1] == 'sub_ubi':
            continue   # 〜とき の「とき」は接続の語
        if head.lemma in ('こと', '事') and k > 0 and k - 1 in markers and markers[k - 1] == 'nominal':
            continue
        if head.lemma in TIME_ADVERBS and not ({'の', 'が', 'を', 'は'} & set(c.particles)):
            target = head_of(k) if head_of(k) in built else next((p for p in preds if p > k), None)
            if target is not None:   # 昨日 → heri (時の副詞)
                built[target].adverbs.append(Lex(TIME_ADVERBS[head.lemma], 'adv', surface=TIME_ADVERBS[head.lemma]))
            continue
        if c.nouns or head.lemma in PRONOUNS or head.surface in PRONOUNS:
            nps[k] = noun_phrase(c, pending_mods)
            pending_mods = []
            later = [p for p in preds if p > k]
            if head_of(k) in built:
                target = head_of(k)   # 係り受け解析の係り先
                if 'は' in c.particles:
                    # 主題「は」は主節のもの (私は少女が歌うのを見た の 私は → 見た、兵士たちは、敵が逃げたので、帰った
                    # の 兵士たちは → 帰った)。ただし主節に別の「は」があれば、その前の節のもの
                    later_topics = [j for j in range(k + 1, len(cs)) if 'は' in cs[j].particles and cs[j].nouns]
                    if not later_topics:
                        target = main_ix
                    else:
                        seen = set()
                        while target not in clause_final and head_of(target) is not None and target not in seen:
                            seen.add(target)
                            target = head_of(target)
                        if target not in built:
                            target = main_ix
                owner_of[k] = target
                continue
            if not later:
                continue
            if 'は' in c.particles:
                later_final = [p for p in clause_final if p > k]
                owner_of[k] = later_final[0] if later_final else main_ix
            else:
                owner_of[k] = later[0]
        elif head.pos in ('連体詞', '形容詞') or head.surface in DEMONSTRATIVES:
            pending_mods.append(modifier(c))
        elif head.pos == '副詞':
            later = [head_of(k)] if head_of(k) in built else [p for p in preds if p > k]
            if later:
                if head.lemma in INTERROGATIVES:
                    built[later[0]].question_word = INTERROGATIVES[head.lemma]
                    continue
                found = latin_lex(head.lemma, 'adv')
                built[later[0]].adverbs.append(found[0] if found else Lex(head.lemma, 'adv', surface=head.surface))
    # 名詞の文節を述語へ (の は次の名詞の属格)
    for k in sorted(nps):
        c = cs[k]
        target = head_of(k) if head_of(k) in nps else k + 1
        if c.particles and c.particles[-1] == 'の' and target in nps:
            nps[k].case = 'Gen'
            nps[target].genitives.append(nps[k])   # 係り先の名詞 (無ければすぐ後ろ) の属格
            continue
        if owner_of.get(k) is not None:
            attach(built[owner_of[k]], c, nps[k])
    main_tense = built[main_ix].tense
    out = []
    for k in preds:
        clause = _finish(built[k])
        marker = markers[k]
        following = [p for p in preds if p > k]
        governor = built[head_of(k)] if head_of(k) in built else built[following[0]] if following else None
        antecedent = head_of(k) if head_of(k) in nps else k + 1
        if heads is not None and marker == 'final' and k != main_ix and head_of(k) in nps and cs[k].attributive:
            marker = 'rel'   # 係り先が名詞の連体形の述語 (離れた先行詞も)
        if marker == 'rel' and antecedent in nps:
            gap = 'subject' if not clause.role('subject') else 'object' if _transitive(clause) and \
                not clause.role('object') else ''
            if gap:   # 空所の無い連体修飾 (魚を焼く匂い) は扱わない
                clause.gap = gap
                if gap == 'subject':
                    clause.number = nps[antecedent].number
                nps[antecedent].relatives.append(clause)
                continue
        if marker in ('nominal', 'quote') and governor is not None:
            # 名詞節・引用 → 不定詞句 (少女が歌うのを見た → puellam cantāre vīdit、来ると言った → venīre dīxit)
            verb = getattr(governor, 'ja_verb', '')
            clause.mood = 'infinitive'
            clause.infinitive_kind = 'perception' if verb in PERCEPTION_VERBS else \
                'saying' if marker == 'quote' or verb in QUOTE_VERBS else 'complement'
            clause.tense = 'perfect' if clause.tense in ('perfect', 'imperfect') else 'present'
            governor.infinitives.append(clause)
            continue
        if marker == 'question' and governor is not None:
            # 間接疑問 (誰が来たか知らない): 疑問詞の名詞句か疑問の副詞。動詞は接続法
            wh = next((np for _, np in clause.args if np.interrogative), None)
            clause.question_word = clause.question_word or (wh.head.lemma if wh else 'num')
            clause.mood = 'subjunctive'
            governor.questions.append(clause)
            continue
        if marker == 'sub_ubi':
            clause.subordinator = 'ubi'
            if main_tense in ('perfect', 'imperfect') and clause.tense == 'present':
                clause.tense = 'imperfect'   # 寝ているとき (過去の文) → dormiēbat
        elif marker == 'sub_quod':
            clause.subordinator = 'quod'
        elif marker == 'te':
            clause.connectives.append('et')
            if clause.tense == 'present':
                clause.tense = main_tense   # 来て、呼んだ → 来た (主節の時制)
        elif marker.startswith('conj:'):
            word = CONNECTIVES[marker[5:]]
            if word in SUBORDINATE:
                clause.subordinator = word
            else:
                clause.connectives.append(word)
        out.append(clause)
    # て でつないだ節に主語が無く、主節の主語が主題 (は) なら、主語を前の節へ (王は都市に来て、兵士を呼んだ:
    # Rēx ad urbem vēnit, et mīlitēs vocāvit)
    main = built[main_ix]
    for k in preds:
        if markers[k] == 'te' and not built[k].role('subject') and main.role('subject') and \
                getattr(main, 'topic_subject', False):
            subject = main.role('subject')[0]
            main.args = [(r, n) for r, n in main.args if n is not subject]
            built[k].args.insert(0, ('subject', subject))
            _finish(built[k])
            break
    # て・が でつないだ節は、つなぎの語を後ろの節の頭へ
    for i in range(len(out) - 1):
        for word in ('et', 'sed'):
            if word in out[i].connectives:
                out[i].connectives.remove(word)
                out[i + 1].connectives.insert(0, word)
    return out


def available():
    return _tagger is not None
