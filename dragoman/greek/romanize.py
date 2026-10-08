#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語のラテン文字への転写 (学術的な転写を簡略に)
#
#   ἐν ἀρχῇ ἦν ὁ λόγος → en archêi ên ho lógos
#
# η ω は ē ō (曲アクセントなら ê ô)、υ は y (二重母音の中では u)、χ θ φ ψ は ch th ph ps、γγ γκ γξ γχ の γ は n、
# 気息記号 (῾) は h、語頭の ῥ は rh、下書きのイオタは i。鋭アクセント・重アクセントは母音の上にそのまま
#
import unicodedata

LETTERS = {'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'ē', 'θ': 'th', 'ι': 'i', 'κ': 'k',
           'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
           'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'ō', 'ϝ': 'w'}
VOWELS = set('αεηιουω')
SMOOTH, ROUGH, ACUTE, GRAVE, CIRCUMFLEX, IOTA_SUB, DIAERESIS = ('̓', '̔', '́', '̀', '͂',
                                                               'ͅ', '̈')
MACRON, BREVE = '̄', '̆'
VELARS = set('γκξχ')
DIPHTHONG_SECOND = set('ιυ')


def _letters(word):
    """[(小文字の字, 大文字か, 記号の集合)]"""
    out = []
    for c in unicodedata.normalize('NFD', word):
        if unicodedata.combining(c):
            if out:
                out[-1][2].add(c)
        else:
            out.append([c.lower(), c != c.lower(), set()])
    return out


def _accented(latin, marks):
    if CIRCUMFLEX in marks:
        latin = latin.replace('ē', 'ê').replace('ō', 'ô').replace('a', 'â').replace('i', 'î').replace('y', 'ŷ').replace(
            'u', 'û').replace('e', 'ê').replace('o', 'ô')
        return latin
    for mark in (ACUTE, GRAVE):
        if mark in marks:
            return unicodedata.normalize('NFC', latin[0] + mark + latin[1:]) if latin else latin
    return latin


def romanize_word(word):
    letters = _letters(word)
    out = []
    rough_pending = False
    for i, (c, upper, marks) in enumerate(letters):
        if c not in LETTERS:
            out.append(c)
            continue
        nxt = letters[i + 1][0] if i + 1 < len(letters) else ''
        prev = letters[i - 1][0] if i > 0 else ''
        latin = LETTERS[c]
        if c == 'γ' and nxt in VELARS:
            latin = 'n'
        if c == 'υ' and prev in VOWELS and prev not in DIPHTHONG_SECOND and DIAERESIS not in marks:
            latin = 'u'  # αυ ευ ηυ ου
        if c == 'ρ' and (ROUGH in marks or i == 0):
            latin = 'rh'
        # 二重母音の気息記号・アクセントは2つ目の字にある (οἱ, αὐτός)
        diphthong_head = c in VOWELS and nxt in DIPHTHONG_SECOND and i + 1 < len(letters) and \
            DIAERESIS not in letters[i + 1][2] and not (c == 'ι') and not (c == 'υ' and nxt == 'υ')
        second_of_diphthong = c in DIPHTHONG_SECOND and prev in VOWELS and prev not in DIPHTHONG_SECOND - {'υ'} \
            and DIAERESIS not in marks and i > 0
        if ROUGH in marks and c != 'ρ' and not second_of_diphthong:
            latin = 'h' + latin  # 二重母音の2つ目の字の気息記号は1つ目の字の前に (下で)
        if diphthong_head and ROUGH in letters[i + 1][2]:
            latin = 'h' + latin
        latin = _accented(latin, marks)
        if IOTA_SUB in marks:
            latin += 'i'
        if upper:
            latin = latin[:1].upper() + latin[1:]
        out.append(latin)
    return unicodedata.normalize('NFC', ''.join(out))


def romanize(text):
    return ' '.join(romanize_word(w) for w in text.split())
