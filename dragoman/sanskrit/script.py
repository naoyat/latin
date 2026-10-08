#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの文字: デーヴァナーガリー / IAST の入力を受け付け、中では SLP1 (ASCII の転写) で扱う。
# 表示は IAST とデーヴァナーガリーを併記する (vidyut.lipi で変換)
#
import re
import unicodedata

from vidyut import lipi

VEDIC_ACCENTS = re.compile('[॒॑᳐-᳿]')  # ॑ ॒ などのヴェーダのアクセント記号
DANDA = '।॥'


def is_devanagari(text):
    return any('ऀ' <= c <= 'ॿ' and c not in DANDA for c in text)


IAST_VOWELS = set('aeiouAEIOU')


def _strip_accents(text):
    """IAST の母音の上の á à (ヴェーダのアクセント) を除く。ś の ´ は子音の一部なので残す"""
    out, base, marks = [], '', ''
    for c in unicodedata.normalize('NFD', text):
        if unicodedata.combining(c):
            vowel = base in IAST_VOWELS or (base in 'rlRL' and '\u0323' in marks)
            if c in '\u0301\u0300' and vowel:
                continue
            marks += c
        else:
            base, marks = c, ''
        out.append(c)
    return unicodedata.normalize('NFC', ''.join(out))


def to_slp1(text):
    """デーヴァナーガリーか IAST の語を SLP1 に (ヴェーダのアクセント記号は除く。IAST なら á à の記号)"""
    text = VEDIC_ACCENTS.sub('', text)
    if not is_devanagari(text):
        text = _strip_accents(text)
    scheme = lipi.Scheme.Devanagari if is_devanagari(text) else lipi.Scheme.Iast
    return lipi.transliterate(text, scheme, lipi.Scheme.Slp1)


def iast(slp1):
    return lipi.transliterate(slp1, lipi.Scheme.Slp1, lipi.Scheme.Iast)


def devanagari(slp1):
    return lipi.transliterate(slp1, lipi.Scheme.Slp1, lipi.Scheme.Devanagari)


def display(slp1):
    """IAST (デーヴァナーガリー)"""
    return '%s (%s)' % (iast(slp1), devanagari(slp1))
