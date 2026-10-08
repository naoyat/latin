#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語の表記: 照合用の形 (現代の標準的なローマ字表記に寄せる) とカタカナ
#
# 知里幸惠『アイヌ神謡集』(1923) などの古いローマ字表記を、現代の表記 (中川裕・田村すず子などの辞典で使うもの) に寄せる:
#   sh → s (shirokanipe → sirokanipe、sapash → sapas)、ch → c (chikap → cikap)
#   母音の後ろの i / u (二重母音の後半) → y / w (kamui → kamuy、yaieyukar → yayeyukar、pauchi → pawci)
#   人称の接辞の = は照合では除く (ku=kor → kukor) ので、分けて書いても続けて書いてもよい
#
import re
import unicodedata

VOWELS = 'aeiou'
ACCENTS = {'́', '̀', '̂', '̄'}  # アクセント記号 (á) は照合では除く


def key(word):
    """照合用の形 (小文字、アクセント・= ・‘’ を除き、古い表記を現代の表記に)"""
    w = unicodedata.normalize('NFD', word.lower())
    w = ''.join(c for c in w if c not in ACCENTS)
    w = unicodedata.normalize('NFC', w)
    w = w.replace('=', '').replace('’', "'").replace('‘', "'").strip(".,;:!?“”\"()'")
    w = w.replace('sh', 's').replace('ch', 'c')
    w = re.sub(r'(?<=[aeiou])i', 'y', w)   # kamui → kamuy、yaieyukar → yayeyukar (母音の後ろの i)
    w = re.sub(r'(?<=[aeiou])u', 'w', w)   # pauci → pawci、kamuiutar → kamuywtar (母音の後ろの u)
    w = re.sub(r'(?<=n)g', 'k', w)          # 知里の表記の ng = nk (ingaras → inkaras)
    return w


def is_ainu_latin(text):
    return bool(re.search('[a-z]', text.lower()))


try:
    from ainu_utils import to_kana as _to_kana
except ImportError:  # ainu-utils (MIT) が無ければカタカナは出さない
    _to_kana = None


def kana(text):
    """ローマ字 → カタカナ (ainu-utils があれば)"""
    if _to_kana is None:
        return ''
    try:
        return _to_kana(key(text))
    except Exception:
        return ''
