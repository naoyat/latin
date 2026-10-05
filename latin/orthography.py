#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 綴りの流儀の違いの吸収
#
#   子音の i: j で書く流儀 (juvenis, Jovis) と i で書く流儀 (iuvenis, Iovis)
#   子音の u: v で書く流儀 (virum) と u で書く流儀 (uirum)
#
# 辞書を引くときは、表記どおり → i/j を同一視 → さらに u/v も同一視、の順に試す。
# u/v を最初から同一視しないのは、別の語がぶつかるため (volvit「転がす」と voluit「望んだ」は
# u に統一するとどちらも uoluit)。v と u を書き分けているテキストなら表記どおりで見つかる
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


def may_merge_uv(word):
    """u/v を同一視してよいか: 入力に v があればそのテキストは v と u を書き分けているので、しない"""
    return 'v' not in word and 'V' not in word


def variants(word):
    """辞書を引くときに試す綴りの順: 表記どおり → i/j を同一視 → u/v も同一視 (入力に v が無ければ)"""
    result = [word, ij(word)]
    if may_merge_uv(word):
        result.append(uv(ij(word)))
    return list(dict.fromkeys(result))


def flat(text, merge_uv=False):
    """マクロンを除いた照合用のキー (小文字、j→i。merge_uv なら v→u も)"""
    key = ij(strip_macrons(text).lower())
    return uv(key) if merge_uv else key
