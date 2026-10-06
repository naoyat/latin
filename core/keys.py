#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 照合用のキー: 長短の印 (マクロンなど、結合文字) を除いて小文字にし、子音の i/u の書き方の違い (j→i, v→u) を吸収する。
# Wiktionary の取り込み (core/wiktionary_import.py) とラテン語の表記の正規化 (latin/orthography.py) で使う
#
import unicodedata


def ij(text):
    """j を i に (子音の i を i で書く形に)"""
    return text.replace('j', 'i').replace('J', 'I')


def uv(text):
    """v を u に (子音の u を u で書く形に)。マクロン付きの ū は母音なのでそのまま"""
    return text.replace('v', 'u').replace('V', 'U')


def strip_macrons(text):
    nfd = unicodedata.normalize('NFD', text)
    return unicodedata.normalize('NFC', ''.join(c for c in nfd if unicodedata.category(c) != 'Mn'))


def flat(text, merge_uv=False):
    """マクロンを除いた照合用のキー (小文字、j→i。merge_uv なら v→u も)"""
    key = ij(strip_macrons(text).lower())
    return uv(key) if merge_uv else key
