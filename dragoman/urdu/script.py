#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー文字 (ペルシア文字のナスタアリーク体): ヒンディー語のデーヴァナーガリーと引き合わせる「綴りの骨組み」
#
# ウルドゥー語とヒンディー語は文法と日常語が同じで、違いは文字と改まった語彙。ウルドゥー文字は短母音を書かず、
# ペルシア語・アラビア語の字を書き分ける (ز ذ ض ظ はどれも z)。そこで両方の文字を、短母音を落とし、
# 書き分けの違う字をまとめた骨組みにして比べる:
#   لڑکا → lRkA、लड़का → lRkA        میں → mYn (मैं ma͠i「私」と में mẽ「〜で」の両方)
#
import re
import unicodedata

DIACRITICS = re.compile('[ً-ٰٟـٕٖٔ-ٞ]')
RLI, PDI = '⁧', '⁩'
URDU = {'ا': 'A', 'آ': 'A', 'أ': 'A', 'ب': 'b', 'پ': 'p', 'ت': 't', 'ط': 't', 'ٹ': 'T', 'ث': 's', 'س': 's', 'ص': 's',
        'ج': 'j', 'چ': 'c', 'ح': 'h', 'ہ': 'h', 'ۂ': 'h', 'ه': 'h', 'ھ': 'H', 'خ': 'x', 'د': 'd', 'ڈ': 'D', 'ذ': 'z',
        'ز': 'z', 'ض': 'z', 'ظ': 'z', 'ر': 'r', 'ڑ': 'R', 'ژ': 'z', 'ش': 'S', 'غ': 'G', 'ف': 'f', 'ق': 'q',
        'ک': 'k', 'ك': 'k', 'گ': 'g', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ں': 'n', 'و': 'V', 'ؤ': 'V', 'ی': 'Y',
        'ي': 'Y', 'ے': 'Y', 'ئ': 'Y', 'ۓ': 'Y', 'ى': 'Y', 'ع': '', 'ء': ''}
DEVA_CONSONANTS = {'क': 'k', 'ख': 'kH', 'ग': 'g', 'घ': 'gH', 'च': 'c', 'छ': 'cH', 'ज': 'j', 'झ': 'jH', 'ट': 'T',
                   'ठ': 'TH', 'ड': 'D', 'ढ': 'DH', 'ण': 'n', 'त': 't', 'थ': 'tH', 'द': 'd', 'ध': 'dH', 'न': 'n',
                   'प': 'p', 'फ': 'pH', 'ब': 'b', 'भ': 'bH', 'म': 'm', 'य': 'Y', 'र': 'r', 'ल': 'l', 'व': 'V',
                   'श': 'S', 'ष': 'S', 'स': 's', 'ह': 'h', 'ङ': 'n', 'ञ': 'n', 'ळ': 'l'}
DEVA_NUKTA = {'क': 'q', 'ख': 'x', 'ग': 'G', 'ज': 'z', 'फ': 'f', 'ड': 'R', 'ढ': 'RH', 'झ': 'z'}
DEVA_SIGNS = {'ा': 'A', 'ि': '', 'ी': 'Y', 'ु': '', 'ू': 'V', 'ृ': 'r', 'े': 'Y', 'ै': 'Y', 'ो': 'V', 'ौ': 'V',
              'ॉ': 'V', 'ॅ': 'Y', 'ं': 'n', 'ँ': 'n', '्': '', 'ः': 'h'}
DEVA_VOWELS = {'अ': 'A', 'आ': 'A', 'इ': 'A', 'ई': 'AY', 'उ': 'A', 'ऊ': 'AV', 'ऋ': 'r', 'ए': 'AY', 'ऐ': 'AY',
               'ओ': 'AV', 'औ': 'AV', 'ऑ': 'AV'}


def normalize(text):
    """母音記号を除く (ZWNJ も)"""
    return DIACRITICS.sub('', unicodedata.normalize('NFC', text)).replace('‌', '')


def is_urdu(text):
    return bool(re.search('[؀-ۿ]', text))


def isolate(text):
    return RLI + text + PDI if is_urdu(text) else text


# 引き合わせで同じとみなす字 (ヌクタの無いヒンディー語の綴り: जबान zabān、फ / f、क / q、ख / x、ग / ġ)
MERGE = str.maketrans({'z': 'j', 'f': 'P', 'q': 'k', 'x': 'K', 'G': 'g'})


def _finish(key):
    """重ねた子音を1つに (कुत्ता / کتا)、書き分けの違う字をまとめる"""
    key = key.replace('pH', 'P').replace('kH', 'K').translate(MERGE)
    return re.sub(r'(.)\1+', r'\1', key)


def skeletons(word):
    """ウルドゥー文字の語 → 骨組みの候補 (語末の ہ は -ā (کمرہ kamrā) か h (شاہ śāh) の両方)"""
    word = normalize(word)
    out = ''
    for k, c in enumerate(word):
        if c == 'ع' and k == 0:
            out += 'A'  # 語頭の ع は母音の支え (علم ilm → इल्म)
        elif c in 'ےۓ' and k == len(word) - 1:
            out += 'E'  # 語末の ے (e / ai) は ی (ī) と書き分ける (کے ke / کی kī)
        else:
            out += URDU.get(c, '')
    keys = [out]
    if word.endswith(('ہ', 'ه')) and len(word) > 1:
        keys += [out[:-1] + 'A', out[:-1]]  # کمرہ kamrā、وشوہ viśva
    return list(dict.fromkeys(_finish(k) for k in keys))


def skeleton_deva(word):
    """デーヴァナーガリーの語 → 骨組み"""
    chars = unicodedata.normalize('NFD', word)
    out = ''
    for k, c in enumerate(chars):
        nukta = k + 1 < len(chars) and chars[k + 1] == '़'
        if c in DEVA_CONSONANTS:
            out += DEVA_NUKTA.get(c, DEVA_CONSONANTS[c]) if nukta else DEVA_CONSONANTS[c]
        elif c in DEVA_SIGNS:
            last = k == len(chars) - 1
            if last and c in 'ेै':  # (鼻音化した -ẽ は یں: करें / کریں)
                out += 'E'  # 語末の e / ai は ے
            else:
                out += {'ि': 'Y', 'ु': 'V'}.get(c, DEVA_SIGNS[c]) if last else DEVA_SIGNS[c]  # 語末の短い i・u は ی・و
        elif c in DEVA_VOWELS:
            out += DEVA_VOWELS[c] if k == 0 else DEVA_VOWELS[c].lstrip('A') or 'A'
    return _finish(out)
