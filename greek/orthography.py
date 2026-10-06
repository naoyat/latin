#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の表記の正規化
#
#   照合用の形 (key):   重アクセントを鋭アクセントに (τὸν → τόν)、長短の印 (ᾰ ῑ) を除く、
#                       前接語で付いた2つ目のアクセントを除く (ἄνθρωπός τις → ἄνθρωπος)、
#                       アポストロフィの統一 (δ' δʼ δ᾽ → δ’)
#   さらに緩い形 (flat): 小文字にし、アクセント・気息記号・下書きのイオータなど、記号をすべて除く
#                       (語末の ς も σ に)。アクセントの無い入力や、綴りの揺れの受け皿
#
import unicodedata

ACUTE, GRAVE, CIRCUMFLEX = '́', '̀', '͂'
MACRON, BREVE = '̄', '̆'
APOSTROPHES = "'ʼ᾽’᾿"


def _nfd(text):
    return unicodedata.normalize('NFD', text)


def _nfc(text):
    return unicodedata.normalize('NFC', text)


def key(word):
    """辞書と照合する形"""
    for a in APOSTROPHES:
        word = word.replace(a, '’')
    chars = [c for c in _nfd(word) if c not in (MACRON, BREVE)]
    chars = [ACUTE if c == GRAVE else c for c in chars]
    # 前接語のアクセント: 鋭アクセントが2つあれば後ろのものを除く
    if chars.count(ACUTE) + chars.count(CIRCUMFLEX) >= 2 and chars.count(ACUTE) >= 1:
        last = len(chars) - 1 - chars[::-1].index(ACUTE)
        del chars[last]
    return _nfc(''.join(chars))


def flat(word):
    """記号をすべて除いた緩い形 (小文字、語末の ς も σ)"""
    base = ''.join(c for c in _nfd(key(word)) if unicodedata.category(c) != 'Mn')
    return _nfc(base).lower().replace('ς', 'σ').replace('’', '')


def is_greek(text):
    return any('Ͱ' <= c <= 'Ͽ' or 'ἀ' <= c <= '῿' for c in text)
