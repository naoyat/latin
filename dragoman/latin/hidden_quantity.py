#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 隠れた長音 (hidden quantity)
#
# 閉音節の母音 (後ろに子音が2つ続く) は、韻律上は母音の長短にかかわらず長いので、
# 母音そのものの長さが分かりにくく、マクロンを付けるかどうかが資料によって違う
#   māgnus / magnus, cōgnōvit / cognōvit, iūssus / iussus
# 子音の i の前の母音 (ēius / eius, hūius / huius) も同様に流儀が分かれる
#
# ここでいう「隠れた長音の位置」:
#   - 後ろに子音が2つ続く母音 (ただし「閉鎖音 + 流音」(patrem の tr) は音節を閉じないので除く)
#     ch, ph, th, rh, qu は1つの子音として数える。x, z は1文字として数える (rēx は対象外)
#   - 母音と母音の間の i の直前の母音 (eius, cuius, maior, Trōia)
#
import unicodedata

VOWELS = set('aeiouy')
MUTA = set('pbtdcgf')
LIQUIDA = set('lr')
DIGRAPHS = ('ch', 'ph', 'th', 'rh', 'qu')
LENGTHEN = {'a': 'ā', 'e': 'ē', 'i': 'ī', 'o': 'ō', 'u': 'ū', 'y': 'ȳ',
            'A': 'Ā', 'E': 'Ē', 'I': 'Ī', 'O': 'Ō', 'U': 'Ū', 'Y': 'Ȳ'}
MACRON = '̄'


def _plain(word):
    nfd = unicodedata.normalize('NFD', word)
    return unicodedata.normalize('NFC', ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')).lower()


def _consonant_units(plain, start):
    """start 以降、次の母音までの子音を (文字列, 長さ) の単位に分ける"""
    units = []
    k = start
    while k < len(plain) and plain[k] not in VOWELS:
        two = plain[k:k+2]
        if two in DIGRAPHS:
            units.append(two)
            k += 2
        else:
            units.append(plain[k])
            k += 1
    return units, k


def positions(word):
    """語の中の隠れた長音の位置 (文字の添字) の集合"""
    plain = _plain(word).replace('j', 'i')
    result = set()
    for i, ch in enumerate(plain):
        if ch not in VOWELS:
            continue
        # u は qu, gu, su の後では母音ではない (qu は子音の単位として数える)
        if ch == 'u' and i > 0 and plain[i-1] == 'q':
            continue
        nxt = plain[i+1:i+2]
        # 母音と母音の間の i (子音): eius, cuius, maior
        if nxt == 'i' and i + 2 < len(plain) and plain[i+2] in VOWELS and ch in 'aeouy':
            result.add(i)
            continue
        units, end = _consonant_units(plain, i + 1)
        if len(units) < 2:
            continue
        if len(units) == 2 and end < len(plain) and units[0] in MUTA and units[1] in LIQUIDA:
            continue  # 閉鎖音 + 流音 (patrem)
        result.add(i)
    return result


def strip(word):
    """隠れた長音の位置のマクロンを外す"""
    hidden = positions(word)
    nfc = unicodedata.normalize('NFC', word)
    out = []
    for i, ch in enumerate(nfc):
        if i in hidden:
            ch = unicodedata.normalize('NFC', ''.join(c for c in unicodedata.normalize('NFD', ch) if c != MACRON))
        out.append(ch)
    return ''.join(out)


def _key(plain, i):
    """隠れた長音の位置 i の知識を共有する単位: 語頭から、その母音の後ろの子音2つまで (magn-, cogn-, eiu-)"""
    units, end = _consonant_units(plain, i + 1)
    if plain[i+1:i+2] == 'i' and not units:
        return plain[:i+3]
    return plain[:i + 1 + sum(len(u) for u in units[:2])]


class HiddenQuantities:
    """マクロン付きの語から「どの語幹の隠れた長音に印が付くか」を集める (ファイルごと。評価時は対象を除ける)"""

    def __init__(self):
        self.by_source = {}

    def add_words(self, source, words):
        counts = self.by_source.setdefault(source, {})
        for word in words:
            nfc = unicodedata.normalize('NFC', word)
            plain = _plain(nfc).replace('j', 'i')
            if len(plain) != len(nfc):
                continue
            for i in positions(nfc):
                key = _key(plain, i)
                marked, unmarked = counts.get(key, (0, 0))
                if MACRON in unicodedata.normalize('NFD', nfc[i]):
                    counts[key] = (marked + 1, unmarked)
                else:
                    counts[key] = (marked, unmarked + 1)

    def is_marked(self, plain, i, exclude=()):
        """その語幹の隠れた長音に印が付くか。知識が無ければ None。exclude: 使わない知識の出どころの集合"""
        marked = unmarked = 0
        for source, counts in self.by_source.items():
            if source in exclude:
                continue
            m, u = counts.get(_key(plain, i), (0, 0))
            marked += m
            unmarked += u
        if marked == unmarked == 0:
            return None
        return marked > unmarked

    def mark(self, word, exclude=()):
        """隠れた長音の位置を、知識があればそれに従って付け外しする (知識の無い位置と、それ以外の位置は変えない)"""
        nfc = unicodedata.normalize('NFC', word)
        plain = _plain(nfc).replace('j', 'i')
        if len(plain) != len(nfc):
            return word
        out = list(nfc)
        for i in positions(nfc):
            marked = self.is_marked(plain, i, exclude)
            if marked is True:
                out[i] = LENGTHEN.get(plain[i] if out[i].islower() else plain[i].upper(), out[i])
            elif marked is False:
                out[i] = unicodedata.normalize('NFC', ''.join(
                    c for c in unicodedata.normalize('NFD', out[i]) if c != MACRON))
        return ''.join(out)
