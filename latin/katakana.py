#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語の語 (主に固有名詞) をカタカナで書く
#
#   Caesar → カエサル, Mārcus → マールクス, Iūlia → ユーリア, Cicerō → キケロー,
#   Polyphēmus → ポリュペームス, Hannibal → ハンニバル, Iuppiter → ユッピテル
#
# 音素列 (latin_phonology.phonemize_word) から書く。長母音は「ー」、閉鎖音・s・f の重子音は「ッ」、
# n・m の重子音は「ン」、l・r の重子音は1つにする (Gallia → ガリア)。有気音は無気音と同じに書く。
#
from .latin_phonology import phonemize_word

# 母音の音素 → 段 (a i u e o) と長さ
VOWELS = {'a': ('a', False), 'a:': ('a', True), 'E': ('e', False), 'e:': ('e', True),
          'I': ('i', False), 'i:': ('i', True), 'O': ('o', False), 'o:': ('o', True),
          'U': ('u', False), 'u:': ('u', True), 'y': ('y', False), 'y:': ('y', True)}
DIPHTHONGS = {'aE': 'アエ', 'aU': 'アウ', 'OE': 'オエ'}

ROWS = {
    '':  {'a': 'ア', 'i': 'イ', 'u': 'ウ', 'e': 'エ', 'o': 'オ', 'y': 'ユ'},
    'k': {'a': 'カ', 'i': 'キ', 'u': 'ク', 'e': 'ケ', 'o': 'コ', 'y': 'キュ'},
    'g': {'a': 'ガ', 'i': 'ギ', 'u': 'グ', 'e': 'ゲ', 'o': 'ゴ', 'y': 'ギュ'},
    's': {'a': 'サ', 'i': 'シ', 'u': 'ス', 'e': 'セ', 'o': 'ソ', 'y': 'シュ'},
    'z': {'a': 'ザ', 'i': 'ジ', 'u': 'ズ', 'e': 'ゼ', 'o': 'ゾ', 'y': 'ジュ'},
    't': {'a': 'タ', 'i': 'ティ', 'u': 'トゥ', 'e': 'テ', 'o': 'ト', 'y': 'テュ'},
    'd': {'a': 'ダ', 'i': 'ディ', 'u': 'ドゥ', 'e': 'デ', 'o': 'ド', 'y': 'デュ'},
    'n': {'a': 'ナ', 'i': 'ニ', 'u': 'ヌ', 'e': 'ネ', 'o': 'ノ', 'y': 'ニュ'},
    'h': {'a': 'ハ', 'i': 'ヒ', 'u': 'フ', 'e': 'ヘ', 'o': 'ホ', 'y': 'ヒュ'},
    'f': {'a': 'ファ', 'i': 'フィ', 'u': 'フ', 'e': 'フェ', 'o': 'フォ', 'y': 'フュ'},
    'p': {'a': 'パ', 'i': 'ピ', 'u': 'プ', 'e': 'ペ', 'o': 'ポ', 'y': 'ピュ'},
    'b': {'a': 'バ', 'i': 'ビ', 'u': 'ブ', 'e': 'ベ', 'o': 'ボ', 'y': 'ビュ'},
    'm': {'a': 'マ', 'i': 'ミ', 'u': 'ム', 'e': 'メ', 'o': 'モ', 'y': 'ミュ'},
    'r': {'a': 'ラ', 'i': 'リ', 'u': 'ル', 'e': 'レ', 'o': 'ロ', 'y': 'リュ'},
    'l': {'a': 'ラ', 'i': 'リ', 'u': 'ル', 'e': 'レ', 'o': 'ロ', 'y': 'リュ'},
    'j': {'a': 'ヤ', 'i': 'イ', 'u': 'ユ', 'e': 'イェ', 'o': 'ヨ', 'y': 'ユ'},
    'w': {'a': 'ウァ', 'i': 'ウィ', 'u': 'ウ', 'e': 'ウェ', 'o': 'ウォ', 'y': 'ウュ'},
    'kw': {'a': 'クァ', 'i': 'クィ', 'u': 'ク', 'e': 'クェ', 'o': 'クォ', 'y': 'クュ'},
    'gw': {'a': 'グァ', 'i': 'グィ', 'u': 'グ', 'e': 'グェ', 'o': 'グォ', 'y': 'グュ'},
}
# 母音が続かない子音
CODA = {'k': 'ク', 'g': 'グ', 's': 'ス', 'z': 'ズ', 't': 'ト', 'd': 'ド', 'n': 'ン', 'N': 'ン', 'h': 'フ',
        'f': 'フ', 'p': 'プ', 'b': 'ブ', 'm': 'ム', 'r': 'ル', 'l': 'ル', 'j': 'イ', 'w': 'ウ'}
SOKUON = {'p', 'b', 't', 'd', 'k', 'g', 's', 'f', 'z'}


def _base(ph):
    """有気音・重子音の印を外した子音 (p_h → p, t: → t)。軟口蓋鼻音 N は n"""
    ph = ph.rstrip(':').replace('_h', '')
    return 'n' if ph == 'N' else ph


def katakana(word):
    phonemes = phonemize_word(word)
    out = []
    i = 0
    while i < len(phonemes):
        ph = phonemes[i]
        if ph in DIPHTHONGS:
            out.append(DIPHTHONGS[ph])
            i += 1
            continue
        if ph in VOWELS:
            vowel, long = VOWELS[ph]
            out.append(ROWS[''][vowel] + ('ー' if long else ''))
            i += 1
            continue
        geminate = ph.endswith(':')
        consonant = _base(ph)
        # kw, gw (qu, gu + 母音)
        if consonant in ('k', 'g') and i + 1 < len(phonemes) and phonemes[i + 1] == 'w' and \
                i + 2 < len(phonemes) and phonemes[i + 2] in VOWELS:
            consonant += 'w'
            i += 1
        if geminate:
            if consonant in SOKUON:
                out.append('ッ')
            elif consonant in ('n', 'm'):
                out.append('ン')
        nxt = phonemes[i + 1] if i + 1 < len(phonemes) else None
        if nxt in VOWELS and consonant in ROWS:
            vowel, long = VOWELS[nxt]
            out.append(ROWS[consonant][vowel] + ('ー' if long else ''))
            i += 2
        elif nxt in DIPHTHONGS and consonant in ROWS:
            first = {'aE': 'a', 'aU': 'a', 'OE': 'o'}[nxt]
            out.append(ROWS[consonant][first] + DIPHTHONGS[nxt][1:])
            i += 2
        elif consonant == 'm' and nxt is not None and _base(nxt) in ('p', 'b'):
            out.append('ン')  # Pompēius → ポンペーイウス
            i += 1
        else:
            out.append(CODA.get(consonant, ''))
            i += 1
    return ''.join(out)
