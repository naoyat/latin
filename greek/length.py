#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 長短どちらもある母音 (α ι υ) の長さを、辞書 (Wiktionary の変化表の形の長短の印 ᾱ ᾰ) から入力の語に移す
#
#   θεὰ → θεᾱ̀,  μυρία → μῡρία (ῐ は短いまま)
#
# 辞書の候補が同じ長さを示している母音だけに印を付ける (候補で食い違うもの、両方の印 ῡ̆ が付いたものは付けない)
#
import unicodedata

from . import dictionary

MACRON, BREVE = '̄', '̆'
DICHRONA = set('αιυ')


def _letters(word):
    """[(小文字の文字, 記号の集合)]"""
    units = []
    for c in unicodedata.normalize('NFD', word):
        if unicodedata.combining(c):
            if units:
                units[-1][1].add(c)
        elif c.isalpha():
            units.append((c.lower(), set()))
    return units


def _long_positions(marked):
    """長短の印の付いた形で、長い (ᾱ。ῡ̆ は除く) 母音の位置と、短い (ᾰ) 母音の位置"""
    long, short = set(), set()
    for i, (c, marks) in enumerate(_letters(marked)):
        if c in DICHRONA:
            if MACRON in marks and BREVE not in marks:
                long.add(i)
            elif BREVE in marks and MACRON not in marks:
                short.add(i)
    return long, short


def mark(word):
    """入力の語に、辞書から分かる長母音の印 (マクロン) を付けて返す (辞書が無い・分からなければそのまま)"""
    if not dictionary.available():
        return word
    letters = _letters(word)
    variants = []
    for item in dictionary.lookup(word):
        marked = item.get('length')
        if marked and [c for c, _ in _letters(marked)] == [c for c, _ in letters]:
            variants.append(_long_positions(marked))
    if not variants:
        return word
    # どの候補でも長く、どの候補でも短くないもの
    long = set.intersection(*(l for l, _ in variants)) - set.union(*(s for _, s in variants))
    if not long:
        return word
    out, i = [], -1
    for c in unicodedata.normalize('NFD', word):
        out.append(c)
        if not unicodedata.combining(c) and c.isalpha():
            i += 1
            if i in long:
                out.append(MACRON)
    return unicodedata.normalize('NFC', ''.join(out))
