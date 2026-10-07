#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# デーヴァナーガリー (ヒンディー語): ラテン文字への転写 (Wiktionary の転写に近い形: laṛkā, mẽ, paṛhnā)。
# ヒンディー語は子音に含まれる母音 a を、語末と「母音 + 子音 _ 子音 + 母音」の位置で読まない (schwa の脱落):
#   कमरा kamrā (kamarā でない)、लड़का laṛkā、समझना samajhnā、घर ghar
#
#   translit('पढ़ता हूँ') → 'paṛhtā hū̃'    key('पढ़ता') → 'पढ़ता' (ヌクタの合成をそろえる)
#
import re
import unicodedata

VIRAMA, NUKTA, ANUSVARA, CANDRABINDU, VISARGA = '्', '़', 'ं', 'ँ', 'ः'
CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ṅ', 'च': 'c', 'छ': 'ch', 'ज': 'j', 'झ': 'jh', 'ञ': 'ñ',
    'ट': 'ṭ', 'ठ': 'ṭh', 'ड': 'ḍ', 'ढ': 'ḍh', 'ण': 'ṇ', 'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm', 'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'ś',
    'ष': 'ṣ', 'स': 's', 'ह': 'h', 'ळ': 'ḷ',
}
NUKTA_CONSONANTS = {'क': 'q', 'ख': 'x', 'ग': 'ġ', 'ज': 'z', 'फ': 'f', 'ड': 'ṛ', 'ढ': 'ṛh', 'य': 'y', 'र': 'r'}
VOWEL_SIGNS = {'ा': 'ā', 'ि': 'i', 'ी': 'ī', 'ु': 'u', 'ू': 'ū', 'ृ': 'ŕ',
               'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ॅ': 'ê', 'ॉ': 'ô'}
VOWELS = {'अ': 'a', 'आ': 'ā', 'इ': 'i', 'ई': 'ī', 'उ': 'u', 'ऊ': 'ū', 'ऋ': 'ŕ', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o',
          'औ': 'au', 'ऑ': 'ô', 'ऍ': 'ê'}
NASAL = {'a': 'ã', 'ā': 'ā̃', 'i': 'ĩ', 'ī': 'ī̃', 'u': 'ũ', 'ū': 'ū̃', 'e': 'ẽ', 'o': 'õ', 'ai': 'a͠i', 'au': 'a͠u'}
# 子音の前の anusvāra は同じ調音位置の鼻音 (हिंदी hindī、संबंध sambandh)
HOMORGANIC = {'k': 'ṅ', 'g': 'ṅ', 'c': 'ñ', 'j': 'ñ', 'ṭ': 'ṇ', 'ḍ': 'ṇ', 'p': 'm', 'b': 'm', 'm': 'm'}
DANDA = '।॥'
DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')
DEVANAGARI = re.compile('[ऀ-ॿ]')


def key(text):
    """辞書引きのキー: NFC にそろえ、ヌクタ付きの合成文字 (ड़ U+095C) を基本字 + ヌクタに分ける"""
    text = unicodedata.normalize('NFC', text).translate(DIGITS)
    return unicodedata.normalize('NFD', text).replace('‍', '').replace('‌', '')


def is_devanagari(text):
    return bool(DEVANAGARI.search(text))


def _syllables(word):
    """[(子音 (無ければ None), 母音 (None は内在の a、'' は virāma), 鼻音化)]"""
    out = []
    chars = list(key(word))
    i = 0
    while i < len(chars):
        c = chars[i]
        if c in CONSONANTS:
            cons = CONSONANTS[c]
            if i + 1 < len(chars) and chars[i + 1] == NUKTA:
                cons = NUKTA_CONSONANTS.get(c, cons)
                i += 1
            vowel = None
            if i + 1 < len(chars) and chars[i + 1] in VOWEL_SIGNS:
                vowel = VOWEL_SIGNS[chars[i + 1]]
                i += 1
            elif i + 1 < len(chars) and chars[i + 1] == VIRAMA:
                vowel = ''
                i += 1
            out.append([cons, vowel, False])
        elif c in VOWELS:
            out.append([None, VOWELS[c], False])
        elif c in (ANUSVARA, CANDRABINDU) and out:
            out[-1][2] = 'anusvara' if c == ANUSVARA else 'candrabindu'
        elif c == VISARGA and out:
            out.append(['ḥ', '', False])
        else:
            out.append([c, '', False])  # 句読点・数字など
        i += 1
    return out


def _schwa_deletion(sylls):
    """内在の a (vowel None) を読むかどうか: 語末は読まない。右から見て「母音 + 子音 _ 子音 + 母音」の a は読まない"""
    n = len(sylls)
    keep = [s[1] is not None for s in sylls]  # True: 書かれた母音 (または virāma)
    vowels = [s[1] if s[1] is not None else 'a' for s in sylls]
    # 語末の a (-ya / -ra / -śva などの子音連続の後ろは読む: विश्व viśva、प्रिय priya。बुद्ध buddh は読まない)
    if n > 1 and sylls[-1][1] is None and sylls[-1][0] is not None and not sylls[-1][2] and not (
            sylls[-2][1] == '' and (sylls[-1][0] in ('y', 'r') or sylls[-1][0] == 'v' and sylls[-2][0] in ('ś', 's', 't', 'd'))
            or sylls[-1][0] == 'y' and sylls[-2][1] in ('i', 'ī')):  # -iya (प्रिय priya)
        vowels[-1] = ''
    # 語中: i 番目の a は、前の音節に母音があり (i-1 の a は残る)、後ろの子音に母音が続けば落とす
    for i in range(n - 2, 0, -1):
        if sylls[i][1] is not None or sylls[i][0] is None or sylls[i][2]:
            continue
        prev_has_vowel = vowels[i - 1] != ''
        nxt = sylls[i + 1]
        next_has_vowel = nxt[0] is not None and vowels[i + 1] != ''
        if prev_has_vowel and next_has_vowel and i >= 1 and (i - 1 > 0 or sylls[i - 1][0] is None or True):
            vowels[i] = ''
            # 連続して落とさない (कमरा は kamrā、कमरों は kamrõ)
            if i - 1 >= 1 and sylls[i - 1][1] is None:
                pass
    del keep
    return vowels


def translit_word(word):
    sylls = _syllables(word)
    if not sylls:
        return word
    vowels = _schwa_deletion(sylls)
    out = []
    for k, ((cons, written, nasal), vowel) in enumerate(zip(sylls, vowels)):
        if cons is not None:
            out.append(cons)
        if nasal:
            nxt = sylls[k + 1][0] if k + 1 < len(sylls) else None
            if nasal == 'anusvara' and nxt and nxt[0] not in 'ḥ' and vowel not in ('', None) and \
                    nxt[0].isalpha():
                out.append(vowel + HOMORGANIC.get(nxt[0], 'n'))  # संस्कृत sanskŕt、अहिंसा ahinsā
                continue
            out.append(NASAL.get(vowel or 'a', (vowel or 'a') + '̃'))
            continue
        out.append(vowel)
    return ''.join(out)


def translit(text):
    """文・語のラテン文字への転写 (ダンダ । は .)"""
    text = re.sub('[।॥]', '.', text)
    return ' '.join(re.sub('[\u0900-\u0963\u0966-\u097f]+', lambda m: translit_word(m.group(0)), w)
                    for w in text.split())
