#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 母音の省略 (エリジオン) の復元: 短い母音で終わる語は、次が母音で始まると語末の母音が落ち、アポストロフィで書かれる
#
#   ἀλλ’ ἐγώ → ἀλλά,  μυρί’ Ἀχαιοῖς → μυρία,  βούλομ’ ἐγώ → βούλομαι (叙事詩)
#   次の語が気息で始まると、落ちた後の無声閉鎖音は有気音になる: ἐφ’ ἡμῖν → ἐπί,  καθ’ ἡμέραν → κατά
#
# よく出る機能語は表で戻し、ほかは短い母音 (α ο ε ι、叙事詩の αι) を順に補って辞書で引ける形を選ぶ
#
import unicodedata

from . import dictionary, orthography

APOSTROPHE = '’'
DEASPIRATE = {'φ': 'π', 'θ': 'τ', 'χ': 'κ'}
VOWELS_TO_TRY = ('α', 'ο', 'ε', 'ι', 'αι')

# 省略された形 (アクセント・気息記号を除いた形) → 元の形
FUNCTION_WORDS = {
    'δ': 'δέ', 'τ': 'τε', 'γ': 'γε', 'ἀλλ': 'ἀλλά', 'οὐδ': 'οὐδέ', 'μηδ': 'μηδέ', 'οὔτ': 'οὔτε', 'μήτ': 'μήτε',
    'ἐπ': 'ἐπί', 'ἐφ': 'ἐπί', 'ἀπ': 'ἀπό', 'ἀφ': 'ἀπό', 'ὑπ': 'ὑπό', 'ὑφ': 'ὑπό', 'κατ': 'κατά', 'καθ': 'κατά',
    'μετ': 'μετά', 'μεθ': 'μετά', 'παρ': 'παρά', 'ἀντ': 'ἀντί', 'ἀνθ': 'ἀντί', 'δι': 'διά', 'ἀμφ': 'ἀμφί',
    'περ': 'περί', 'ἔτ': 'ἔτι', 'ἔπ': 'ἔπι', 'τοῦτ': 'τοῦτο', 'ταῦτ': 'ταῦτα', 'ἐστ': 'ἐστι', 'ἅμ': 'ἅμα',
    'ἆρ': 'ἆρα', 'ἄρ': 'ἄρα', 'ἵν': 'ἵνα', 'ὅτ': 'ὅτε', 'πότ': 'πότε', 'ποτ': 'ποτε', 'τότ': 'τότε',
}


def is_elided(word):
    return orthography.key(word).endswith(APOSTROPHE)


def _starts_with_rough(word):
    return word is not None and '̔' in unicodedata.normalize('NFD', word)[:3]


def _bare(word):
    """気息・アクセントを残したまま、語末のアポストロフィを除いた形"""
    return orthography.key(word).rstrip(APOSTROPHE)


def restore(word, next_word=None):
    """省略された語の元の形 (分からなければ None)。next_word は次の語 (気息で始まるかを見る)"""
    if not is_elided(word):
        return None
    base = _bare(word)
    if not base:
        return None
    for key in (base, base.lower()):
        if key in FUNCTION_WORDS:
            return FUNCTION_WORDS[key]
    stems = [base]
    if base[-1] in DEASPIRATE and _starts_with_rough(next_word):
        stems.insert(0, base[:-1] + DEASPIRATE[base[-1]])  # ἀφ’ ἵππων → ἀπ-
    for stem in stems:
        for vowel in VOWELS_TO_TRY:
            candidate = stem + vowel
            if dictionary.available() and dictionary.lookup(candidate):
                return candidate
    return None
