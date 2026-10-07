#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヘブライ文字: 朗唱記号 (טְעָמִים) を除いた形 (母音記号 ニクード は残す)、子音だけのキー、ラテン文字への転写、
# 右から左に書く文字列の表示 (Unicode の隔離記号で囲む)
#
#   pointed('בְּרֵאשִׁ֖ית') → 'בְּרֵאשִׁית'     consonants('בְּרֵאשִׁ֖ית') → 'בראשית'
#   translit('בְּרֵאשִׁית') → 'bərēʾšît'
#
import re
import unicodedata

CANTILLATION = re.compile('[\u0591-\u05af\u05bd\u05c4\u05c5\u034f\u200c\u200d]')  # 朗唱記号、メテグ、上下の点、CGJ
POINTS = re.compile('[\u05b0-\u05bc\u05bf\u05c1\u05c2\u05c7]')
LETTERS = re.compile('[\u05d0-\u05ea]')
MAQAF = '\u05be'
SOF_PASUQ = '\u05c3'
RLI, PDI = '\u2067', '\u2069'

SHEVA, HATAF_SEGOL, HATAF_PATAH, HATAF_QAMATS = '\u05b0', '\u05b1', '\u05b2', '\u05b3'
HIRIQ, TSERE, SEGOL, PATAH, QAMATS, HOLAM, HOLAM_HASER, QUBUTS = ('\u05b4', '\u05b5', '\u05b6', '\u05b7', '\u05b8',
                                                                   '\u05b9', '\u05ba', '\u05bb')
DAGESH, SHIN_DOT, SIN_DOT, QAMATS_QATAN = '\u05bc', '\u05c1', '\u05c2', '\u05c7'
VOWELS = {SHEVA: 'ə', HATAF_SEGOL: 'ĕ', HATAF_PATAH: 'ă', HATAF_QAMATS: 'ŏ', HIRIQ: 'i', TSERE: 'ē', SEGOL: 'e',
          PATAH: 'a', QAMATS: 'ā', HOLAM: 'ō', HOLAM_HASER: 'ō', QUBUTS: 'u', QAMATS_QATAN: 'o'}
CONSONANTS = {'א': 'ʾ', 'ב': 'b', 'ג': 'g', 'ד': 'd', 'ה': 'h', 'ו': 'w', 'ז': 'z', 'ח': 'ḥ', 'ט': 'ṭ', 'י': 'y',
              'כ': 'k', 'ך': 'k', 'ל': 'l', 'מ': 'm', 'ם': 'm', 'נ': 'n', 'ן': 'n', 'ס': 's', 'ע': 'ʿ', 'פ': 'p',
              'ף': 'p', 'צ': 'ṣ', 'ץ': 'ṣ', 'ק': 'q', 'ר': 'r', 'ש': 'š', 'ת': 't'}
SPIRANT = {'ב': 'v', 'כ': 'ḵ', 'ך': 'ḵ', 'פ': 'f', 'ף': 'f'}  # 弱いダゲシュの無い begadkefat (b k p だけ書き分ける)
FINALS = {'ך': 'כ', 'ם': 'מ', 'ן': 'נ', 'ף': 'פ', 'ץ': 'צ'}


FINAL_FORMS = {v: k for k, v in FINALS.items()}


def with_final(letters):
    """子音の列の最後の字を語末形に (קומ → קום)"""
    letters = ''.join(FINALS.get(c, c) for c in letters)
    return letters[:-1] + FINAL_FORMS.get(letters[-1], letters[-1]) if letters else letters


def pointed(text):
    """朗唱記号を除き、母音記号は残す"""
    return unicodedata.normalize('NFC', CANTILLATION.sub('', unicodedata.normalize('NFD', text)))


def consonants(text):
    """子音だけ (母音記号・朗唱記号を除く)"""
    return ''.join(LETTERS.findall(unicodedata.normalize('NFD', text)))


def is_hebrew(text):
    return bool(LETTERS.search(text))


def _clusters(word):
    """[(子音, 記号の集合)]"""
    out = []
    for c in unicodedata.normalize('NFD', pointed(word)):
        if LETTERS.match(c):
            out.append([c, set()])
        elif out and POINTS.match(c):
            out[-1][1].add(c)
    return out


def translit(word):
    """簡略な学術転写 (母音の長短、ʾ ʿ ḥ ṭ ṣ q š ś、母音の読みの文字 (matres lectionis) は長母音に)。
    マカフ (־) でつながった語はハイフンで"""
    if MAQAF in word:
        return '-'.join(translit(part) for part in word.split(MAQAF))
    clusters = _clusters(word)
    out = []
    prev_sheva = True  # 語頭のシェヴァは有声
    n = len(clusters)
    if n == 1:
        # 1字だけの切れ目 (接続詞 וְ・前置詞 בְּ・冠詞 הַ): シェヴァは有声、וּ は û、盗まれたパタハは無い
        c, marks = clusters[0]
        if c == 'ו' and DAGESH in marks and not (marks - {DAGESH}):
            return 'û'
        cons = 'ś' if c == 'ש' and SIN_DOT in marks else (SPIRANT[c] if c in SPIRANT and DAGESH not in marks
                                                         else CONSONANTS.get(c, c))
        vowel = next((VOWELS[v] for v in (HATAF_SEGOL, HATAF_PATAH, HATAF_QAMATS, HIRIQ, TSERE, SEGOL, PATAH, QAMATS,
                                         HOLAM, HOLAM_HASER, QUBUTS, QAMATS_QATAN, SHEVA) if v in marks), '')
        return cons + vowel
    for i, (c, marks) in enumerate(clusters):
        nxt = clusters[i + 1] if i + 1 < n else None
        # 母音の読みの文字: וּ (ū), וֹ (ō), ִי (ī), ֵי (ê), ָה 語末 (â)
        if c == 'ו' and DAGESH in marks and not (marks - {DAGESH}) and out and out[-1][-1] not in 'aāeēiouəăĕŏ' \
                and i > 0:
            out.append('û')
            prev_sheva = False
            continue
        if c == 'ו' and HOLAM in marks and not (marks - {HOLAM}) and i > 0:
            out.append('ô')
            prev_sheva = False
            continue
        if c == 'י' and not marks and out and out[-1].endswith(('i', 'ē')) and (nxt is None or nxt[1] or True):
            out[-1] = out[-1][:-1] + ('î' if out[-1].endswith('i') else 'ê')
            continue
        if c == 'ה' and not marks and i == n - 1 and out and out[-1].endswith(('ā', 'e', 'ē')):
            out[-1] = out[-1][:-1] + {'ā': 'â', 'e': 'ê', 'ē': 'ê'}[out[-1][-1]]
            continue
        if c == 'א' and not marks and i == n - 1:
            continue  # 語末の黙字の א
        if c == 'ש':
            cons = 'ś' if SIN_DOT in marks else 'š'
        elif c in SPIRANT and DAGESH not in marks:
            cons = SPIRANT[c]
        else:
            cons = CONSONANTS.get(c, c)
        if c == 'ו' and HOLAM in marks:
            out.append('ō' if i == 0 else 'wō')
            prev_sheva = False
            continue
        vowel = ''
        for v in (HATAF_SEGOL, HATAF_PATAH, HATAF_QAMATS, HIRIQ, TSERE, SEGOL, PATAH, QAMATS, HOLAM, HOLAM_HASER,
                  QUBUTS, QAMATS_QATAN):
            if v in marks:
                vowel = VOWELS[v]
        if SHEVA in marks:
            # 有声のシェヴァ: 語頭、シェヴァの後、強いダゲシュの子音 (簡略に: 前の音節が開いていれば)
            vowel = 'ə' if (prev_sheva or DAGESH in marks and i > 0) and nxt is not None else ''
        doubled = DAGESH in marks and i > 0 and out and out[-1][-1:] in 'aāeēiouûôîê' and c not in 'אהחער'
        out.append((cons + cons if doubled else cons) + vowel)
        prev_sheva = SHEVA in marks and vowel == ''
        if PATAH in marks and i == n - 1 and len(out) > 1 and (c in 'חע' or c == 'ה' and DAGESH in marks) and \
                out[-2][-1:] in 'aāăeēĕiîoōŏuûêô':
            out[-1] = 'a' + cons  # 盗まれたパタハ (rûaḥ): 母音の後ろの語末の ח・ע・הּ のパタハは子音の前で読む
    return ''.join(out)


ADONAI = 'אֲדֹנָי'
ELOHIM = 'אֱלֹהִים'


def qere(text):
    """音読のための読み替え (qere perpetuum): 神の名 יְהוָה は母音記号のとおり אֲדֹנָי「アドナイ」と読む。
    ヒリクの付いた形 (יֱהֹוִה。אֲדֹנָי יְהוִה と並ぶとき) は אֱלֹהִים「エロヒム」と読む (アドナイが重ならないように)。
    前に付いた接頭辞 (וַיהוָה, לַיהוָה) はそのまま残す"""
    out = []
    for word in text.split():
        letters = consonants(word)
        base = letters.lstrip('ובלכמה') if letters.endswith('יהוה') else letters
        if base == 'יהוה':
            nfd = unicodedata.normalize('NFD', pointed(word))
            prefix_len = len(letters) - 4
            # 接頭辞の字 (と記号) を取り出す
            head, count = '', 0
            for c in nfd:
                if LETTERS.match(c):
                    if count == prefix_len:
                        break
                    count += 1
                head += c
            reading = ELOHIM if HIRIQ in nfd[len(head):] else ADONAI
            out.append(unicodedata.normalize('NFC', head) + reading)
        else:
            out.append(word)
    return ' '.join(out)


def isolate(text):
    """右から左に書く文字列を隔離記号で囲む (左から右の文と混ぜても崩れないように)"""
    return RLI + text + PDI if is_hebrew(text) else text
