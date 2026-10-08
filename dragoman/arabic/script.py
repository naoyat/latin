#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア文字: 母音記号 (ḥarakāt) を除いた形、ラテン文字への転写 (DIN 31635 に近い形)、
# 右から左に書く文字列の表示 (Unicode の隔離記号で囲む)
#
#   bare('ذَهَبَ الوَلَدُ') → 'ذهب الولد'
#   translit('ذَهَبَ') → 'ḏahaba'    translit('الشَّمْسُ') → 'aš-šamsu'    translit('مَدْرَسَةٌ') → 'madrasatun'
#
# 母音記号の無い語は子音だけを転写する (解析器の選んだ読み (母音記号付き) を渡すのが普通)
#
import re
import unicodedata

FATHA, DAMMA, KASRA, SUKUN, SHADDA = 'َ', 'ُ', 'ِ', 'ْ', 'ّ'
FATHATAN, DAMMATAN, KASRATAN = 'ً', 'ٌ', 'ٍ'
DAGGER_ALEF, TATWEEL = 'ٰ', 'ـ'
DIACRITICS = re.compile('[ً-ٰٟۖ-ۭـ]')
LETTERS = re.compile('[ء-غف-يٱ]')
RLI, PDI = '⁧', '⁩'

CONSONANTS = {'ء': 'ʾ', 'أ': 'ʾ', 'إ': 'ʾ', 'ؤ': 'ʾ', 'ئ': 'ʾ', 'ب': 'b', 'ت': 't', 'ث': 'ṯ', 'ج': 'ǧ', 'ح': 'ḥ',
              'خ': 'ḫ', 'د': 'd', 'ذ': 'ḏ', 'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'š', 'ص': 'ṣ', 'ض': 'ḍ', 'ط': 'ṭ',
              'ظ': 'ẓ', 'ع': 'ʿ', 'غ': 'ġ', 'ف': 'f', 'ق': 'q', 'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n', 'ه': 'h',
              'و': 'w', 'ي': 'y', 'ة': 't', 'ى': 'ā', 'ا': 'ā', 'آ': 'ʾā', 'ٱ': ''}
VOWELS = {FATHA: 'a', DAMMA: 'u', KASRA: 'i', FATHATAN: 'an', DAMMATAN: 'un', KASRATAN: 'in'}
# 太陽文字: 定冠詞 al- の l がこれに同化する (aš-šams)
SUN_LETTERS = set('تثدذرزسشصضطظلن')
HAMZA_SEATS = set('أإؤئء')


def bare(text):
    """母音記号・タトウィールを除く"""
    return DIACRITICS.sub('', unicodedata.normalize('NFC', text))


def normalize(text):
    """辞書引きのキー: 母音記号を除き、アリフの異体 (أ إ آ ٱ) を ا に"""
    return re.sub('[أإآٱ]', 'ا', bare(text))


def has_diacritics(text):
    return bool(DIACRITICS.search(text))


def is_arabic(text):
    return bool(LETTERS.search(text))


def isolate(text):
    """右から左に書く文字列を Unicode の隔離記号で囲む (左から右の行の中で語順が崩れないように)"""
    return RLI + text + PDI if is_arabic(text) else text


def sun_shadda(form):
    """定冠詞 al- の後ろの太陽文字にシャッダを補う (السُوق → السُّوق)。母音記号の無い語はそのまま"""
    if not has_diacritics(form):
        return form
    m = re.match('^(ال)([%s])(?![\u064b-\u0652]*\u0651)' % ''.join(SUN_LETTERS), form)
    if not m:
        return form
    return unicodedata.normalize('NFC', form[:3] + SHADDA + form[3:])


def _clusters(word):
    """[(字, 記号の集合)]"""
    out = []
    for c in unicodedata.normalize('NFC', word):
        if DIACRITICS.match(c) and out:
            out[-1][1].add(c)
        elif not DIACRITICS.match(c):
            out.append((c, set()))
    return out


def translit(word):
    """母音記号付きの語 → ラテン文字 (DIN 31635 に近い形)。語頭のハムザは書かない (ʾilā でなく ilā)"""
    if not is_arabic(word):
        return word
    clusters = _clusters(word)
    out = []
    i = 0
    assimilated = False
    # 定冠詞 al- (語頭の ال、または前置詞・接続詞の後ろの ال は呼び出し側で分けて渡す)
    if len(clusters) >= 3 and clusters[0][0] in 'اٱ' and clusters[1][0] == 'ل' and not clusters[0][1] - {FATHA}:
        nxt, marks = clusters[2]
        if nxt in SUN_LETTERS and SUKUN not in clusters[1][1]:
            out.append('a' + CONSONANTS[nxt] + '-')  # aš-šams (同化。重ねた字の片方は al- の側に書く)
            assimilated = True
        else:
            out.append('al-')
        i = 2
    while i < len(clusters):
        c, marks = clusters[i]
        nxt = clusters[i + 1] if i + 1 < len(clusters) else None
        if c == 'ا' and FATHATAN in marks:
            out[-1:] = [out[-1] + 'an'] if out else ['an']  # 支えのアリフに書いた -an (غَداً)
            i += 1
            continue
        if c == 'ا' and nxt is None and out and out[-1].endswith('ū'):
            i += 1
            continue  # 複数の -ū の後ろの書くだけのアリフ (ذَهَبُوا ḏahabū)
        if c == 'ا':
            if i == 0:
                # 語頭のアリフ (つなぎのハムザ): 母音だけ
                out.append(next((VOWELS[m] for m in marks if m in VOWELS), 'a' if not marks else ''))
            elif out and out[-1].endswith('a') and FATHATAN not in ''.join(clusters[i - 1][1]):
                out[-1] = out[-1][:-1] + 'ā'  # fatha + alif = ā
            elif FATHATAN in clusters[i - 1][1] or FATHATAN in marks:
                pass  # -an の支えのアリフ
            else:
                out.append('ā')
            i += 1
            continue
        if c == 'ى':
            if out and out[-1].endswith('a'):
                out[-1] = out[-1][:-1] + 'ā'
            elif not (out and out[-1].endswith('an')):
                out.append('ā')
            i += 1
            continue
        if c in 'وي' and not (marks & set(VOWELS)) and SHADDA not in marks and out:
            # 長母音 ū / ī (前の字の damma / kasra と組む)
            prev = out[-1]
            if c == 'و' and prev.endswith('u'):
                out[-1] = prev[:-1] + 'ū'
                i += 1
                continue
            if c == 'ي' and prev.endswith('i'):
                out[-1] = prev[:-1] + 'ī'
                i += 1
                continue
            if not marks and nxt is None and i > 0 and not clusters[i - 1][1]:
                pass
        if c == DAGGER_ALEF:
            out.append('ā')
            i += 1
            continue
        if c == 'ة':
            vowel = next((VOWELS[m] for m in marks if m in VOWELS), None)
            out.append('t' + vowel if vowel else '')
            if not vowel and out[-2:-1] and not out[-2].endswith('a'):
                out[-1] = 'a'
            i += 1
            continue
        if c == 'آ':
            out.append('ʾā' if i else 'ā')
            i += 1
            continue
        cons = CONSONANTS.get(c)
        if cons is None:
            out.append(c)
            i += 1
            continue
        if i == 0 and c in HAMZA_SEATS:
            cons = ''  # 語頭のハムザは書かない
        if SHADDA in marks and not (assimilated and i == 2):
            cons = cons * 2
        vowel = next((VOWELS[m] for m in marks if m in VOWELS), '')
        if DAGGER_ALEF in marks:
            vowel = 'ā'
        out.append(cons + vowel)
        i += 1
    return ''.join(out)
