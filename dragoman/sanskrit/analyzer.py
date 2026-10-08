#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの文の解析
#
# 辞書引き (vidyut の kosha。語末の連声を戻して引き、引けなければ vidyut の cheda で連声・複合語を分解する) と、
# 後置の並列 (A B ca → ca を前に) の処理だけをここで行い、並列・係り先・格の枠・日本語訳はラテン語と共通の解析器
# (latin.analyzer.analyze_words) を、サンスクリットの設定 (SANSKRIT) で使う
#
import os
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.core.Word import Word
from . import compound, dictionary, morphology, script

PUNCTUATION = {'।': 'period', '॥': 'period', '.': 'period', ',': 'comma', ';': 'comma', '?': 'question', '!': 'period'}
TOKEN = re.compile(r"[ऀ-ॣ०-ॿ᳐-᳿'ऽ]+|[A-Za-zĀāĪīŪūṚṛṜṝḶḷṂṃḤḥṄṅÑñṬṭḌḍṆṇŚśṢṣ"
                   r"̀́'’]+|[।॥.,;?!]")


def _root_items(root):
    """語根 (IAST) の訳語 (分詞の元の動詞の訳語に使う)"""
    return [{'pos': 'verb', 'ja': l['ja'], 'gloss_lang': l['gloss_lang']}
            for l in dictionary.lemmas(script.to_slp1(root)) if l['pos'] in ('root', 'verb')]


SANSKRIT = language.Language(
    name='sa',
    and_words=('ca',),
    or_words=('vā',),
    copulas=frozenset({'as', 'bhū'}),
    negations=frozenset({'na', 'mā'}),
    vocative_particles=frozenset({'he', 'bho', 'bhoḥ', 'bhos'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Ins': 'で', 'Dat': 'に', 'Abl': 'から', 'Gen': 'の', 'Loc': 'で',
                    'Voc': 'よ'},
    absolute_case='Loc',  # 処格独立 (sati saptamī)
    pronoun_subject=True,
    possessor_cases=('Gen', 'Dat'),  # mama pustakam asti「私には本がある」
    lookup=_root_items,
)

POSTPOSITIVE = ('ca', 'vā')  # 後置の並列 (A B ca, A ca B ca)

_chedaka = None


def _cheda(slp1):
    """連声・複合語の分解 (vidyut の cheda)。分解した語 (SLP1) のリスト"""
    global _chedaka
    try:
        if _chedaka is None:
            from vidyut import cheda
            _chedaka = cheda.Chedaka(dictionary.VIDYUT_DATA)
        return [t.text for t in _chedaka.run(slp1)]
    except Exception:
        return [slp1]


def tokens(text):
    return TOKEN.findall(text)


def sentences(text):
    """テキストを文 (ダンダ・句点で区切る) に分け、各文の語の列を返す"""
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


# na + a… の連声 (nāsti = na asti「無い」)。辞書に1語として載っている形も2語に分けて読む
NA_FUSED = ('nAsti', 'nAsIt', 'nAsan', 'nAsmi', 'nAsi', 'nAham', 'nAyam', 'nAtra', 'nApi', 'nAnyaH', 'nAnyat')


def _words(token):
    """1語 (の表記) → Word のリスト (連声で融合していれば複数)"""
    if token in PUNCTUATION:
        return [Word(token, None)]
    slp1 = script.to_slp1(token)
    if slp1 in NA_FUSED:
        return _words('na') + _words(script.iast('a' + slp1[2:]))
    key, items = morphology.lookup(slp1)
    if items and any(item['ja'] != item.get('base') for item in items):
        return [Word(script.iast(key), compound.annotate(items))]
    if items:
        # kosha にあって訳語の無い語は、複合語として分けた訳語と成り立ちを借りる (読みは kosha のまま)
        # (最後の語の性から bahuvrīhi と分かれば、品詞も形容詞に: pītāmbaraḥ「黄色い衣を持つ (者)」)
        analyses = compound.analyze(key)
        for item in items:
            for c in analyses:
                if item['pos'] in ('noun', 'adj') and c['pos'] in ('noun', 'adj') and \
                        set(map(tuple, c.get('_', []))) & set(map(tuple, item.get('_', []))):
                    item.update(ja=c['ja'], pos=c['pos'], base='%s = %s' % (item.get('base'), c['base']))
                    break
        return [Word(script.iast(key), items)]
    # 辞書に無い語は、複合語として分ける (mahārājaḥ → mahat-rāja「偉大な王」)
    for candidate in morphology.unsandhi_candidates(slp1):
        compound_items = compound.analyze(candidate)
        if compound_items:
            return [Word(script.iast(candidate), compound_items)]
    parts = _cheda(slp1)
    if len(parts) > 1:
        words = []
        for part in parts:
            key, items = morphology.lookup(part)
            words.append(Word(script.iast(key), items))
        return words
    return [Word(script.iast(slp1), [])]


FINITE_MOODS = ('indicative', 'imperative', 'optative', 'subjunctive')


def _finite(item):
    return item.pos == 'verb' and item.attrib('mood') in FINITE_MOODS


def choose_verbs(words):
    """定動詞の読みを決める (タガーが無いので)。定動詞の読みが一番の語は動詞に絞る。
    それで述語が無ければ、定動詞の読みを持つ語のうち最後のもの (動詞は文末に来やすい) を動詞の読みに絞る"""
    # 呼びかけの間投詞 (he rāma) の後ろは呼格
    for prev, word in zip(words, words[1:]):
        if prev.surface in SANSKRIT.vocative_particles and word.items:
            vocatives = [i for i in word.items if any(cng[0] == 'Voc' for cng in i._ or [])]
            word.items = vocatives or word.items
    candidates = [w for w in words if w.items and any(_finite(i) for i in w.items)]
    # 定動詞の読みが一番の語 (varṣati: 動詞「雨が降る」と現在分詞の処格) は動詞に
    for word in candidates:
        if _finite(word.items[0]):
            word.items = [i for i in word.items if _finite(i)]
    if not candidates or any(all(_finite(i) for i in w.items) for w in candidates):
        return
    last = candidates[-1]
    last.items = [i for i in last.items if _finite(i)]


def _cngs(item):
    return set(map(tuple, item._ or []))


def choose_agreeing_nouns(words):
    """形容詞・指示代名詞の隣の名詞は、性・数・格の合う読みを先頭にする
    (sarve janāḥ: janāḥ は janas「種族」単数主格 より jana「人」複数主格)"""
    # 形容詞と名詞が性・数・格で合って隣り合えば、前を形容詞、後ろを名詞に読む (mahān devaḥ「偉大な神」。
    # deva にも形容詞「神の」の読みがあるが、形容詞は名詞の前に来やすい)。後ろに合う名詞が無ければ前の名詞と
    decided = set()
    for i, word in enumerate(words):
        adj = next((item for item in word.items or [] if item.pos == 'adj'), None)
        if adj is None or i in decided or word.items[0].pos == 'pronoun':
            continue
        for j in (i + 1, i - 1):
            if not 0 <= j < len(words) or not words[j].items:
                continue
            if words[max(i, j) + 1:max(i, j) + 2] and words[max(i, j) + 1].surface in POSTPOSITIVE:
                continue  # A B ca は並列 (rāmaḥ lakṣmaṇaḥ ca)
            noun = next((item for item in words[j].items if item.pos == 'noun' and _cngs(adj) & _cngs(item)), None)
            if noun is None or (j < i and j not in decided and words[j].items[0].pos == 'adj'):
                continue
            word.items = [adj] + [item for item in word.items if item is not adj]
            words[j].items = [noun] + [item for item in words[j].items if item is not noun]
            decided.update((i, j))
            break
    for i, word in enumerate(words):
        if not word.items or not (word.items[0].pos == 'adj' or word.items[0].attrib('desc') == '指示代名詞'):
            continue
        modifier = _cngs(word.items[0])
        for j in (i + 1, i - 1):
            if not 0 <= j < len(words) or not words[j].items or words[j].items[0].pos != 'noun':
                continue
            noun = words[j]
            if modifier & _cngs(noun.items[0]):
                break
            agreeing = [item for item in noun.items if item.pos == 'noun' and modifier & _cngs(item)]
            if agreeing:
                noun.items = agreeing + [item for item in noun.items if item not in agreeing]
                break


def lookup_all(surfaces):
    words = []
    for ix, surface in enumerate(surfaces):
        for word in _words(surface):
            word.token_ix = ix  # 元の語の位置 (連声の分解・後置の ca の移動の後も)
            words.append(word)
    choose_verbs(words)
    choose_agreeing_nouns(words)
    # 後置の並列 (A B ca) は ca を前の語の手前に移して、ラテン語と同じ形 (A et B / et A et B) にする
    for i in range(1, len(words)):
        if words[i].surface in POSTPOSITIVE and words[i].items and words[i].items[0].pos == 'conj':
            words[i - 1], words[i] = words[i], words[i - 1]
    for i, word in enumerate(words):
        word.index = i
    return words


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(SANSKRIT):
        return common.analyze_words([w.surface for w in words], words, word_details, [])


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
