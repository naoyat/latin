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

from dragoman.core import verb_flags as V
from dragoman.core.japanese import JaVerb
from . import grammar

CONTENT = {'名詞', '代名詞', '動詞', '形容詞', '形状詞', '副詞', '連体詞', '接続詞', '感動詞'}
AUX_VERBS = {'行く', '来る', '居る'}   # 連用形 + これらは「〜ていく・〜てくる・〜ている」(なりゆく → なっていく)
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

    def attach(self, word, kind='fixed'):
        """終止形の後ろに付ける (だろう、そうだ …)"""
        self.prefix += self.last
        self.last, self.kind = word, kind

    def final(self, how):
        """後ろに続くものに合わせた形: 'te' (〜て)、'adverbial' (連用中止・連用形)、'plain'"""
        if how == 'te':
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


def _predicate(b, nxt, after_quote):
    """用言の文節 → (現代語, 残りの助詞)"""
    tokens = b.tokens
    head = tokens[0]
    # 体言 + 動詞的接尾辞 (紫だつ → 紫がかる)
    suffix = next((t for t in tokens if t.pos == '接尾辞' and t.pos2 == '動詞的'), None)
    if head.pos == '動詞':
        m = Modern(vocabulary(head) or _modern_word(head), 'verb')
    elif head.pos == '形容詞':
        word = vocabulary(head) or _modern_word(head)
        m = Modern(word, 'adj' if word.endswith('い') else 'fixed')
    elif suffix is not None:
        m = Modern(head.surface + 'がかる', 'verb')
    else:
        return None
    rest = tokens[1:]
    auxes = [t for t in rest if t.pos == '助動詞']
    particles = [t for t in rest if t.pos == '助詞']
    kinds = [grammar.auxiliary(a)[1] for a in auxes]
    for k, kind in enumerate(kinds):
        later = kinds[k + 1:]
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
                m.perfect_then()
            elif not later:
                m.past()
        elif kind == 'past':
            m.past()
        elif kind == 'conjecture':
            if after_quote or (nxt is None and False):
                if m.kind == 'verb':
                    m.last, m.kind = Modern.volitional(m.last), 'fixed'
                else:
                    m.attach('だろう')
            else:
                m.attach('だろう')
        elif kind == 'present_conjecture':
            m.continuous()
            m.attach('だろう')
        elif kind == 'past_conjecture':
            m.past()
            m.attach('だろう')
        elif kind == 'should':
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
    # 後ろに続くもの
    last_cform = (auxes[-1] if auxes else head).form
    how = 'plain'
    if particles and particles[0].lemma == 'て':
        how = 'te'
    elif not particles and last_cform == '連用形' and nxt is not None and nxt.kind == 'verb' and \
            nxt.head.lemma in AUX_VERBS:
        how = 'te'  # なりゆく → なっていく
    elif not particles and last_cform == '連用形' and nxt is not None and nxt.kind in ('verb', 'adj') and \
            m.kind == 'adj':
        how = 'adverbial'  # 白くなる
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
            result = _predicate(b, nxt, after_quote)
            if result is not None:
                text, particles = result
                last_form = ([t for t in b.tokens if t.pos in ('助動詞', '動詞', '形容詞')] or [b.head])[-1].form
                b.modern = text + ''.join(_particle(p, b, nxt, last_form) for p in particles)
                continue
        # 体言・形容動詞・副詞など
        head = b.head
        word = vocabulary(head)
        if word is not None and b.kind == 'nadj':
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
