#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# マクロン (長音記号) の推定
#
#   macronize_text('Perseus filius erat Iovis') → 'Perseus fīlius erat Iovis'
#
# 1. 語ごとに、マクロンを除いた形が一致する辞書の形を候補として集める
#    (手作りの辞書と Wiktionary 由来の補助辞書。j/i、接頭辞の同化、-que も扱う)
# 2. 候補が複数あれば選ぶ (choose)
# 3. 選んだ候補のマクロンの位置だけを元の綴りに写す (大文字・小文字や j/i は入力のまま)
#
from dragoman.core import paths
import re
import unicodedata
from dataclasses import dataclass, field

from . import latindic
from . import wiktionary
from . import morpheus
from . import rftagger
from . import ldt
from . import hidden_quantity
from . import catalog
from . import orthography
from dragoman.core.wiktionary_import import flatten

MACRON = '\u0304'  # 結合マクロン
BREVE = '\u0306'   # 結合ブレーヴェ
LENGTHEN = {'a': 'ā', 'e': 'ē', 'i': 'ī', 'o': 'ō', 'u': 'ū', 'y': 'ȳ',
            'A': 'Ā', 'E': 'Ē', 'I': 'Ī', 'O': 'Ō', 'U': 'Ū', 'Y': 'Ȳ'}
ENCLITIC_EXCEPTIONS = {'neque', 'itaque', 'atque', 'quoque', 'usque', 'denique', 'undique',
                       'ubique', 'utique', 'quisque', 'quaeque', 'quodque', 'quemque', 'quique'}


def strip_macrons(text):
    text = unicodedata.normalize('NFD', text)
    return unicodedata.normalize('NFC', ''.join(c for c in text if unicodedata.category(c) != 'Mn'))


def has_macron(text):
    return MACRON in unicodedata.normalize('NFD', text)


def macron_count(text):
    return unicodedata.normalize('NFD', text).count(MACRON)


def _clean(surface):
    """マクロン以外の結合文字 (連結記号など) を含む形は候補にしない"""
    return all(unicodedata.category(c) != 'Mn' or c == MACRON
               for c in unicodedata.normalize('NFD', surface))


def _anceps_variants(surface):
    """長短どちらもありうる母音 (ī̆ = マクロン+ブレーヴェ) を含む形は、短い形と長い形の両方にする"""
    nfd = unicodedata.normalize('NFD', surface)
    if MACRON + BREVE not in nfd and BREVE + MACRON not in nfd:
        return [surface]
    long_form = nfd.replace(MACRON + BREVE, MACRON).replace(BREVE + MACRON, MACRON)
    short_form = nfd.replace(MACRON + BREVE, '').replace(BREVE + MACRON, '')
    return [unicodedata.normalize('NFC', short_form), unicodedata.normalize('NFC', long_form)]


def transfer_macrons(candidate, word):
    """候補のマクロンの位置を元の綴りに写す: ('iuvenī', 'juveni') → 'juvenī'"""
    candidate = unicodedata.normalize('NFC', candidate)
    if len(candidate) != len(word):
        return word
    return ''.join(LENGTHEN.get(w, w) if has_macron(c) else w for c, w in zip(candidate, word))


#
# 候補
#
@dataclass
class Candidate:
    surface: str            # 辞書の形 (マクロン付き)
    source: str             # 'hand' / 'wiktionary'
    items: list = field(default_factory=list)
    enclitic: str = ''      # '-que' を外して引いた場合 'que'

    @property
    def macronized(self):
        return self.surface + self.enclitic


_hand_index = None


def _hand_flat_index():
    """手作りの辞書: マクロンを除いた形 (小文字、i/j と u/v を同一視) → 辞書の形"""
    global _hand_index
    if _hand_index is None:
        _hand_index = {}
        for surface in latindic.LatinDic.dic:
            if ' ' not in surface:
                _hand_index.setdefault(orthography.flat(surface, merge_uv=True), []).append(surface)
    return _hand_index


def _same_spelling(surface, word):
    """綴りが同じとみなせるか: マクロンを除き、i/j を同一視。入力に v が無ければ u/v も同一視"""
    merge = orthography.may_merge_uv(word)
    return orthography.flat(surface, merge) == orthography.flat(word, merge)


USE_MORPHEUS = True   # Morpheus 由来の補助辞書を候補の供給元に使う (辞書ファイルがあれば)
USE_TAGGER = True     # RFTagger の品詞タグを手がかりに使う (RFTagger とモデルがあれば)


def _lookup_candidates(word):
    found = {}
    for surface in _hand_flat_index().get(orthography.flat(word, merge_uv=True), []):
        if _clean(surface):
            found.setdefault(surface, Candidate(surface, 'hand', latindic.lookup_hand(surface)))
    if latindic.LatinDic.use_wiktionary:
        for surface, items in wiktionary.lookup_flat(word).items():
            for variant in _anceps_variants(surface):
                if _clean(variant) and variant not in found:
                    found[variant] = Candidate(variant, 'wiktionary', items)
    if USE_MORPHEUS:
        for surface, items in morpheus.lookup_flat(word).items():
            if surface in found:
                found[surface].items = found[surface].items + items  # タグとの照合に使えるよう項目を足す
            else:
                found[surface] = Candidate(surface, 'morpheus', items)
    # i/j・u/v や接頭辞の同化を読み替えた綴りも一致とみなす (マクロンは元の綴りに写すので綴りは変わらない)
    spellings = wiktionary._variants(word)
    return [c for c in found.values()
            if len(c.surface) == len(word) and any(_same_spelling(c.surface, s) for s in spellings)]


def candidates(word):
    """語のマクロン付きの形の候補"""
    result = _lookup_candidates(word)
    if not result and word.lower().endswith('que') and word.lower() not in ENCLITIC_EXCEPTIONS:
        for c in _lookup_candidates(word[:-3]):
            c.enclitic = word[-3:]
            result.append(c)
    return result


#
# 候補の選択
#
@dataclass
class Choice:
    word: str                   # 入力の語
    macronized: str             # 推定結果
    candidates: list            # Candidate のリスト
    reason: str = ''            # 選んだ理由 (評価・デバッグ用)

    @property
    def ambiguous(self):
        # 入力の綴りに写した形で比べる (手作りの辞書の juvenī と Wiktionary の iuvenī は同じ)
        return len({transfer_macrons(c.macronized, self.word) for c in self.candidates}) > 1


def _prior(candidate):
    """文脈を見ない場合の候補の順位 (小さいほど優先)
    手作りの辞書にある形 > 日本語の訳語がある (= よく使われる) 語 > その他 (Wiktionary, Morpheus)"""
    if candidate.source == 'hand':
        return 0
    if any(item.get('gloss_lang') == 'ja' for item in candidate.items):
        return 1
    return 2


#
# 文脈
#
import glob
import math
import os
import collections

TEXTS_DIR = os.path.join(paths.LATIN_DIR, 'texts')
PAST_TENSES = {'perfect', 'imperfect', 'past-perfect'}


def _key(form):
    return form.lower().replace('j', 'i')


class Frequency:
    """マクロン付きのテキストでの形の出現回数 (ファイルごとに数え、評価時は対象ファイルを除ける)"""

    def __init__(self, paths=None):
        if paths is None:
            # 目録 (latin/texts/catalog.json) でマクロンが信頼できるとされたテキストだけを使う
            paths = catalog.default().knowledge_files()
        self.by_file = {}
        for path in paths:
            with open(path) as fp:
                self.by_file[os.path.abspath(path)] = collections.Counter(
                    _key(w) for w in WORD.findall(fp.read()))
        self.total = sum(self.by_file.values(), collections.Counter())

    def count(self, form, exclude=()):
        """exclude: 数えないファイルの集合 (評価用)"""
        n = self.total[_key(form)]
        for path in exclude or ():
            n -= self.by_file.get(os.path.abspath(path), {}).get(_key(form), 0)
        return n


def excluded_files(context):
    """評価するファイルと同じ系統 (目録の family) のファイル。知識から除く"""
    if not context or not context.exclude:
        return set()
    return catalog.default().family_of(context.exclude)


_hidden_quantities = None


def default_hidden_quantities():
    """隠れた長音の「印を付ける」流儀の知識: 目録でその流儀とされたテキスト (ファイルごと)。
    手作りの辞書も、目録でその流儀とされていれば加える"""
    global _hidden_quantities
    if _hidden_quantities is None:
        hq = hidden_quantity.HiddenQuantities()
        cat = catalog.default()
        for path in cat.hidden_mark_files():
            with open(path) as fp:
                hq.add_words(os.path.abspath(path), WORD.findall(fp.read()))
        if cat.dictionary.get('hidden') == 'mark':
            hq.add_words('hand', [s for s in latindic.LatinDic.dic if ' ' not in s])
        _hidden_quantities = hq
    return _hidden_quantities


HIDDEN_MODES = ('keep', 'strip', 'mark')


def apply_hidden_convention(word, mode, context=None):
    if mode == 'strip':
        return hidden_quantity.strip(word)
    if mode == 'mark':
        hq = (context and context.hidden_quantities) or default_hidden_quantities()
        return hq.mark(word, excluded_files(context))
    return word


_frequency = None


def default_frequency():
    global _frequency
    if _frequency is None:
        _frequency = Frequency()
    return _frequency


@dataclass
class Context:
    frequency: Frequency = None
    exclude: str = None         # 評価するファイル。同じ系統 (目録の family) のファイルを知識から除く
    past_ratio: float = 0.5     # 文書中の (曖昧でない) 動詞のうち過去時制の割合
    tags: list = None           # 語ごとの品詞タグ (RFTagger)
    hidden: str = 'keep'        # 隠れた長音の流儀: keep (辞書のまま) / strip (付けない) / mark (分かる範囲で付ける)
    hidden_quantities: object = None  # mark で使う知識 (省略時は latin/texts/ と手作りの辞書から)

TAG_WEIGHT = 1.5


def _distinct_forms(cands):
    """候補の形の種類 (i/j・u/v の綴りの違いは同じとみなす。マクロンの違いは区別する)"""
    return {orthography.uv(orthography.ij(c.macronized.lower())) for c in cands}


def _cases(candidate):
    return {cng for item in candidate.items for cng in (item.get('_') or [])}


def _tenses(candidate):
    return {item.get('tense') for item in candidate.items if item.get('pos') == 'verb'}


def _dominated(cands):
    """前置詞としてしか読めない語の支配格。cum (前置詞/接続詞) のように他の読みもある語は使わない"""
    items = [item for c in cands for item in c.items]
    if not items or any(item.get('pos') != 'preposition' for item in items):
        return set()
    return {item.get('dominates') for item in items}


def _is_modifier(cands):
    """形容詞・代名詞・分詞としてしか読めない語 (前置詞と名詞の間に入りうる)"""
    items = [item for c in cands for item in c.items]
    return bool(items) and all(item.get('pos') in ('adj', 'pronoun', 'participle') for item in items)


def _verb_slots(candidate, tenses):
    return {(item.get('person'), item.get('number'), item.get('mood'))
            for item in candidate.items if item.get('pos') == 'verb' and item.get('tense') in tenses}


def _score(candidate, i, slots, context, rivals=()):
    """候補のスコア (大きいほど優先) と、効いた手がかり"""
    score = 0.0
    reasons = []
    # 頻度
    if context.frequency:
        n = context.frequency.count(candidate.macronized, excluded_files(context))
        if n:
            score += math.log(1 + n)
            reasons.append('freq')
    # 辞書の種類による順位
    score -= 0.5 * _prior(candidate)
    cases = _cases(candidate)
    # 呼格だけの形は地の文ではまれ
    if cases and all(case == 'Voc' for case, _, _ in cases):
        score -= 2
        reasons.append('voc')
    # 前置詞の支配格: 直後の語か、間に修飾語を1つ挟んだ語 (in hōc locō, in magnā silvā)
    for j in (i - 1, i - 2):
        if j < 0 or slots[j] is None:
            break
        dominated = _dominated(slots[j])
        if dominated:
            if any(case in dominated for case, _, _ in cases):
                score += 1.5
                reasons.append('prep')
            elif cases:
                score -= 0.5
            break
        if not _is_modifier(slots[j]):
            break
    # 隣の語 (候補が1つに決まっていて格が分かるもの) との一致
    for j in (i - 1, i + 1):
        if 0 <= j < len(slots) and slots[j] and len(_distinct_forms(slots[j])) == 1:
            neighbour = _cases(slots[j][0])
            if neighbour and cases & neighbour:
                score += 1.0
                reasons.append('agree')
    # 時制: 過去時制の多い文書 (物語) では、人称・数・法が同じで時制だけ違う候補 (venit/vēnit) のうち過去を優先
    past_slots = _verb_slots(candidate, PAST_TENSES)
    if past_slots and any(past_slots & _verb_slots(r, {'present'}) for r in rivals):
        score += 2 * (context.past_ratio - 0.5)
        reasons.append('tense')
    # 品詞タガーの判定 (格・数・時制など) と矛盾しない候補を優先
    if context.tags and i < len(context.tags) and context.tags[i]:
        features = ldt.parse(context.tags[i])
        if any(ldt.item_matches(item, features) for item in candidate.items):
            score += TAG_WEIGHT
            reasons.append('tag')
    # 同点ならマクロンの少ない方 (短母音を既定とする)
    score -= 0.01 * macron_count(candidate.macronized)
    return score, reasons


def choose(word, cands, i=0, slots=None, context=None):
    if not cands:
        return Choice(word, word, cands, 'unknown')
    forms = {transfer_macrons(c.macronized, word) for c in cands}
    if len(forms) == 1:
        return Choice(word, transfer_macrons(cands[0].macronized, word), cands, 'unique')
    context = context or Context()
    scored = [(_score(c, i, slots or [cands], context, [r for r in cands if r is not c]), c) for c in cands]
    (score, reasons), best = max(scored, key=lambda sc: (sc[0][0], -len(sc[1].macronized)))
    return Choice(word, transfer_macrons(best.macronized, word), cands, '+'.join(reasons) or 'prior')


WORD = re.compile(r"[A-Za-zĀĒĪŌŪȲāēīōūȳ]+")
BOUNDARY = re.compile(r'^[.;:?!,"()]+$')


def _past_ratio(slots):
    past = present = 0
    for cands in slots:
        if cands and len(_distinct_forms(cands)) == 1:
            tenses = _tenses(cands[0])
            if tenses:
                if tenses <= PAST_TENSES:
                    past += 1
                elif 'present' in tenses and not tenses & PAST_TENSES:
                    present += 1
    return (past + 1) / (past + present + 2)


SENTENCE_END = {'.', ';', ':', '?', '!'}


def _tag_words(words):
    """語の列を文に分けて品詞タグを付け、語の位置に合わせたタグのリストを返す"""
    sentences, positions, current, current_pos = [], [], [], []
    for i, word in enumerate(words):
        current.append(word)
        current_pos.append(i)
        if word in SENTENCE_END:
            sentences.append(current); positions.append(current_pos)
            current, current_pos = [], []
    if current:
        sentences.append(current); positions.append(current_pos)
    tags = [None] * len(words)
    for sentence_tags, sentence_pos in zip(rftagger.tag_sentences(sentences), positions):
        for tag, i in zip(sentence_tags, sentence_pos):
            tags[i] = tag
    return tags


def macronize_words(words, context=None):
    """語の列 (句読点を含んでよい) のマクロンを推定する。すでにマクロンを含む語はそのまま"""
    # slots[i]: 語 i の候補のリスト。句読点は None (文脈の区切り)
    slots = []
    for word in words:
        if BOUNDARY.match(word):
            slots.append(None)
        elif not WORD.fullmatch(word) or has_macron(word):
            slots.append([])
        else:
            slots.append(candidates(word))
    if context is None:
        context = Context(frequency=default_frequency())
    if context.past_ratio is None or context.past_ratio == 0.5:
        context.past_ratio = _past_ratio(slots)
    if USE_TAGGER and context.tags is None and rftagger.available():
        context.tags = _tag_words(words)
    choices = []
    for i, (word, cands) in enumerate(zip(words, slots)):
        if cands is None or (not cands and (not WORD.fullmatch(word) or has_macron(word))):
            choices.append(Choice(word, word, [], 'given'))
        else:
            choice = choose(word, cands, i, slots, context)
            choice.macronized = apply_hidden_convention(choice.macronized, context.hidden, context)
            choices.append(choice)
    return choices


TOKEN = re.compile(r"[A-Za-zĀĒĪŌŪȲāēīōūȳ]+|[.;:?!,\"()]")


def macronize_text(text, context=None, hidden=None):
    """テキストのマクロンを推定する (空白や記号はそのまま残す)。hidden で隠れた長音の流儀を指定"""
    if hidden:
        context = context or Context(frequency=default_frequency())
        context.hidden = hidden
    tokens = TOKEN.findall(text)
    choices = iter(macronize_words(tokens, context))
    return TOKEN.sub(lambda m: next(choices).macronized, text)
