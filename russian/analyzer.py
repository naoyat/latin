#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語の文の解析
#
# 辞書引き (pymorphy3 の解析、russian/morphology.py) と動詞の読みの選択だけをここで行い、並列・係り先・前置詞句・
# 格の枠・日本語訳はラテン語と共通の解析器 (core/analyzer.py) を、ロシア語の設定 (RUSSIAN) で使う
#
import re

from core import analyzer as common
from core import language
from core.Word import Word
from . import dictionary, morphology

PUNCTUATION = {'.': 'period', '!': 'period', '?': 'question', '…': 'period', ',': 'comma', ';': 'comma',
               ':': 'comma', '—': 'comma', '–': 'comma', '(': 'comma', ')': 'comma', '«': None, '»': None,
               '"': None, '„': None, '“': None}
TOKEN = re.compile(r"[а-яёА-ЯЁ́̀]+(?:-[а-яёА-ЯЁ́̀]+)*|[A-Za-z]+|\d+|[.!?…,;:—–()«»\"„“]")


def _root_items(lemma):
    """見出し語 (動詞の不定形) の訳語 (分詞の元の動詞の訳語に使う)"""
    return [{'pos': 'verb', 'ja': l['ja'], 'gloss_lang': l['gloss_lang']}
            for l in dictionary.lemmas(lemma) if l['pos'] == 'verb']


RUSSIAN = language.Language(
    name='ru',
    and_words=('и',),
    nor_words=('ни',),
    or_words=('или',),
    copulas=frozenset({'быть'}),
    negations=frozenset({'не', 'нет'}),
    case_particles={'Nom': 'が', 'Gen': 'の', 'Dat': 'に', 'Acc': 'を', 'Ins': 'で', 'Loc': 'で', 'Voc': 'よ'},
    absolute_case=None,  # 独立格の構文は無い (古代ロシア語の独立与格を除く)
    lookup=_root_items,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_follows_head=True,
    objects_follow_verb=True,
)


def tokens(text):
    return TOKEN.findall(text)


def sentences(text):
    """テキストを文に分け、各文の語の列を返す"""
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


def _word(token):
    if token in PUNCTUATION:
        return Word(token, None)
    return Word(token, morphology.analyze(token))


FINITE_MOODS = ('indicative', 'imperative')


def _finite(item):
    return item.pos == 'verb' and item.attrib('mood') in FINITE_MOODS


def choose_verbs(words):
    """定動詞の読みが一番の語は動詞に絞る (стали: 動詞 стать の過去複数と、名詞 сталь「鋼」の属格)"""
    for word in words:
        if word.items and _finite(word.items[0]):
            word.items = [item for item in word.items if _finite(item)]


def prefer_governed_cases(words):
    """前置詞の後ろの語は、前置詞の支配する格の読みを先にする (из дома: 副詞 дома「家で」より名詞 дом の属格)"""
    for i, word in enumerate(words):
        cases = {item.attrib('dominates') for item in word.items or [] if item.pos == 'preposition'}
        if not cases:
            continue
        for following in words[i + 1:i + 4]:
            if not following.items:
                break
            governed = [item for item in following.items
                        if item._ and any(cng[0] in cases for cng in item._)]
            if not governed:
                break
            following.items = governed + [item for item in following.items if item not in governed]
            if governed[0].pos in ('noun', 'pronoun'):
                break  # 名詞まで (間の形容詞も同じように)


COPULA = {'pos': 'verb', 'pres1sg': 'быть', 'base': 'быть', 'ja': '在る,居る', 'gloss_lang': 'ja', 'aspect': 'impf',
          'voice': 'active', 'mood': 'indicative', 'tense': 'present', 'person': 3, 'number': 'sg',
          'desc': '省略された繋辞'}


def _nominative(word):
    return bool(word.items) and word.items[0].pos in ('noun', 'pronoun', 'adj') and \
        any(cng[0] == 'Nom' for cng in word.items[0]._ or [])


def supply_copula(words):
    """現在形の繋辞は書かない (Он студент「彼は学生だ」, Москва — столица「モスクワは首都だ」)。
    定動詞が無く、主格の名詞類が2つ以上 (か短語尾形容詞が) あれば、見えない繋辞 быть を補う。
    ダッシュ (—) があればそこに、無ければ最初の主格の名詞類の後ろに"""
    if any(w.items and w.items[0].pos == 'verb' and w.items[0].attrib('mood') in FINITE_MOODS for w in words):
        return words
    noms = [i for i, w in enumerate(words) if _nominative(w)]
    short = [i for i, w in enumerate(words) if w.items and w.items[0].attrib('desc') == '短語尾']
    if len(noms) < 2 and not (noms and short):
        return words
    dash = next((i for i, w in enumerate(words) if w.surface in ('—', '–') and noms[0] < i), None)
    copula = Word('(есть)', [dict(COPULA, surface='(есть)')])
    if dash is not None:
        return words[:dash] + [copula] + words[dash + 1:]
    at = noms[0] + 1
    while at < len(words) and words[at].items and words[at].items[0].pos == 'noun' and \
            any(cng[0] == 'Gen' for cng in words[at].items[0]._ or []):
        at += 1  # 主語に掛かる属格の後ろへ
    return words[:at] + [copula] + words[at:]


def merge_compound_verbs(words):
    """быть と組になる動詞の形を1語にまとめる:
    был напечатан (быть の過去 + 短語尾分詞)「印刷された」、будет читать (быть の未来 + 不定形)「読むだろう」"""
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        nxt = words[i + 1] if i + 1 < len(words) else None
        aux = word.items[0] if word.items and word.items[0].pos == 'verb' and \
            word.items[0].attrib('pres1sg') == 'быть' else None
        if aux is not None and nxt is not None and nxt.items:
            main = nxt.items[0]
            merged = None
            if main.pos == 'verb' and main.attrib('voice') == 'passive' and aux.attrib('tense') in ('imperfect', 'perfect', 'future'):
                tense = 'future' if aux.attrib('tense') == 'future' else 'perfect'
                merged = dict(main.item, tense=tense)
            elif main.pos == 'verb' and main.attrib('mood') == 'infinitive' and aux.attrib('tense') == 'future':
                merged = dict(main.item, mood='indicative', tense='future', person=aux.attrib('person'),
                              number=aux.attrib('number'))
            if merged:
                merged['surface'] = word.surface + ' ' + nxt.surface
                combined = Word(merged['surface'], [merged])
                combined.token_ix = getattr(nxt, 'token_ix', None)  # 本動詞の位置 (UD でも был は助動詞)
                out.append(combined)
                i += 2
                continue
        out.append(word)
        i += 1
    return out


def lookup_all(surfaces):
    words = [_word(s) for s in surfaces]
    for ix, word in enumerate(words):
        word.token_ix = ix  # 元の語の位置 (補った繋辞には無い)
    choose_verbs(words)
    words = merge_compound_verbs(words)
    prefer_governed_cases(words)
    words = supply_copula(words)
    for i, word in enumerate(words):
        word.index = i
    return words


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(RUSSIAN):
        return common.analyze_words([w.surface for w in words], words, word_details, [])


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
