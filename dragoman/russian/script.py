#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語の文字: 照合用のキー (強勢記号を除き、ё を е に、小文字)、強勢の表示、ラテン文字への転写
#
#   key('Кни́га') → 'книга'      key('ёлка') → 'елка'
#   translit('кни́га') → 'kníga' (Wiktionary と同じ学術転写。強勢は母音の上の ´)
#
import unicodedata

STRESS = '́'  # 結合アキュート (кни́га の и́)
GRAVE = '̀'   # 第二強勢 (複合語)

TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'jo', 'ж': 'ž', 'з': 'z', 'и': 'i', 'й': 'j',
    'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'x', 'ц': 'c', 'ч': 'č', 'ш': 'š', 'щ': 'šč', 'ъ': 'ʺ', 'ы': 'y', 'ь': 'ʹ', 'э': 'e', 'ю': 'ju', 'я': 'ja',
}


def strip_stress(text):
    nfd = unicodedata.normalize('NFD', text)
    return unicodedata.normalize('NFC', ''.join(c for c in nfd if c not in (STRESS, GRAVE)))


def key(word):
    """照合用のキー: 強勢記号を除き、小文字にし、ё を е に"""
    return strip_stress(word).lower().replace('ё', 'е')


def stress_index(word):
    """強勢のある母音の位置 (強勢記号の無い文字列での添字)。ё は常に強勢がある。分からなければ None"""
    plain = []
    for c in unicodedata.normalize('NFD', word):
        if c == STRESS:
            return len(plain) - 1
        if c != GRAVE:
            plain.append(c)
    text = unicodedata.normalize('NFC', word)
    for i, c in enumerate(strip_stress(text)):
        if c in 'ёЁ':
            return i
    return None


def translit(word):
    """学術転写 (強勢記号はそのまま母音の上に)"""
    out = []
    for c in unicodedata.normalize('NFD', word):
        if c in (STRESS, GRAVE):
            out.append(c)
            continue
        lower = c.lower()
        t = TRANSLIT.get(lower, TRANSLIT.get(unicodedata.normalize('NFC', lower), c))
        out.append(t.capitalize() if c != lower and t else t)
    return unicodedata.normalize('NFC', ''.join(out))
