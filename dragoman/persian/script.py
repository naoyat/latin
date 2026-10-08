#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア文字: 表記のゆれの正規化 (アラビア文字の ي ك → ی ک)、ZWNJ (半スペース)、右から左に書く文字列の表示、
# 辞書に転写の無い語のための大まかな転写
#
#   normalize('كتاب‌هاي') → 'کتاب‌های'    key('می‌روم') → 'میروم'
#
# 短母音は文字に書かれないので、正しい転写は辞書 (Wiktionary のイラン式の転写: ketâb, raftan) から付ける
#
import re
import unicodedata

ZWNJ = '‌'
DIACRITICS = re.compile('[ً-ٰٟـ]')
LETTERS = re.compile('[ء-غف-يپچژکگیآ]')
RLI, PDI = '⁧', '⁩'
VARIANTS = {'ي': 'ی', 'ى': 'ی', 'ك': 'ک', 'ۀ': 'ه' + ZWNJ + 'ی', 'ة': 'ه', 'ؤ': 'و', 'إ': 'ا', 'أ': 'ا', 'ٱ': 'ا'}
DIGITS = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
# 母音記号の無い語の大まかな転写 (子音と長母音だけ)
ROUGH = {'ا': 'â', 'آ': 'â', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ث': 's', 'ج': 'j', 'چ': 'č', 'ح': 'h', 'خ': 'x', 'د': 'd',
         'ذ': 'z', 'ر': 'r', 'ز': 'z', 'ژ': 'ž', 'س': 's', 'ش': 'š', 'ص': 's', 'ض': 'z', 'ط': 't', 'ظ': 'z', 'ع': "'",
         'غ': 'q', 'ف': 'f', 'ق': 'q', 'ک': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'و': 'v', 'ه': 'h', 'ی': 'y',
         'ء': "'", 'ئ': "'"}


def normalize(text):
    """アラビア文字の異体をペルシア文字に、母音記号・タトウィールを除く (ZWNJ は残す)"""
    text = unicodedata.normalize('NFC', text).translate(DIGITS)
    text = ''.join(VARIANTS.get(c, c) for c in text)
    return DIACRITICS.sub('', text)


def key(text):
    """辞書引きのキー: 正規化して ZWNJ を除く (می‌روم と میروم を同じに)"""
    return normalize(text).replace(ZWNJ, '')


def is_persian(text):
    return bool(LETTERS.search(text))


def isolate(text):
    """右から左に書く文字列を Unicode の隔離記号で囲む"""
    return RLI + text + PDI if is_persian(text) else text


def rough_translit(word):
    """辞書に無い語の大まかな転写 (短母音は補えない): کتاب → ktâb"""
    out = []
    word = key(word)
    for i, c in enumerate(word):
        if c in 'وی' and 0 < i:
            after_vowel = word[i - 1] in 'اآو'
            if c == 'ی':
                out.append('y' if after_vowel else 'i')
            else:
                out.append('u' if i == len(word) - 1 and not after_vowel else 'v')
        elif c == 'ه' and i == len(word) - 1 and i > 0:
            out.append('e')
        elif c == 'ا' and i == 0:
            out.append('a')
        else:
            out.append(ROUGH.get(c, c))
    return ''.join(out)
