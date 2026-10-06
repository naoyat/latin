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


SMOOTH = '\u0313'


def _elision_mark(word):
    """語末の子音に付いた気息記号 (δ̓) や ῤ (ὄφῤ) は、省略のアポストロフィの書き方 (Perseus のテキストなど)"""
    nfd = _nfd(word)
    if nfd.endswith(SMOOTH):
        base = [c for c in nfd[:-1] if not unicodedata.combining(c)]
        if base and base[-1].isalpha() and base[-1].lower() not in 'αεηιουω':
            return _nfc(nfd[:-1]) + '’'  # δ̓, ῥ̓ (ρ に気息記号が2つ)
    if word.endswith('ῤ'):
        return word[:-1] + 'ρ’'
    return word


def key(word, keep_length=False):
    """辞書と照合する形 (keep_length なら長短の印 ᾱ ᾰ を残す。音読で母音の長さを知るため)"""
    word = _elision_mark(word)
    for a in APOSTROPHES:
        word = word.replace(a, '’')
    chars = [c for c in _nfd(word) if keep_length or c not in (MACRON, BREVE)]
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
