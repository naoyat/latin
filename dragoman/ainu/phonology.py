#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語の音読: 現代の表記に寄せたローマ字 → espeak-ng の音素 ([[...]])、または日本語の音声に読ませるカタカナ
#
# アイヌ語の音: 母音 a e i o u、子音 p t k c [tʃ] s h m n r [ɾ] w y、声門閉鎖 (')。アイヌ語の音声は無いので、
# espeak-ng のインドネシア語の音声 (母音・子音が近い) に音素で渡す (綴りで渡すと e を [ə] と読むことがある)
#
import re

from . import script

ESPEAK = {'c': 'tS', 'y': 'j', 'r': 'R2', "'": '?', 'p': 'p', 't': 't', 'k': 'k', 's': 's', 'h': 'h', 'm': 'm',
          'n': 'n', 'w': 'w', 'a': 'a', 'e': 'e', 'i': 'i', 'o': 'o', 'u': 'u'}
VOWELS = 'aeiou'
# 小書きのカタカナ (アイヌ語の音節末の子音) → 日本語の音声が読めるカナ
SMALL_KANA = {'ㇰ': 'ク', 'ㇱ': 'シ', 'ㇲ': 'ス', 'ㇳ': 'ト', 'ㇴ': 'ン', 'ㇵ': 'ハ', 'ㇶ': 'ヒ', 'ㇷ': 'フ', 'ㇸ': 'ヘ',
              'ㇹ': 'ホ', 'ㇺ': 'ム', 'ㇻ': 'ラ', 'ㇼ': 'リ', 'ㇽ': 'ル', 'ㇾ': 'レ', 'ㇿ': 'ロ', 'ㇷ゚': 'プ', '゚': ''}


def _word(word):
    w = script.key(word)
    out = ''
    stressed = False
    for c in w:
        if c in VOWELS and not stressed:
            out += "'"   # 最初の母音に強勢の印 (espeak-ng の音素入力で必要)
            stressed = True
        out += ESPEAK.get(c, '')
    return out


def espeak_phonemes(text):
    """文 → espeak-ng (-v id) の音素の列。句読点で間を置く"""
    out = []
    for token in re.findall(r"[A-Za-zÀ-ÿ'’=\-]+|[.,;:!?]", text):
        if token in '.,;:!?':
            out.append('_:' if token in '.!?' else '_')
            continue
        phonemes = _word(token)
        if phonemes:
            out.append(phonemes)
    return '[[' + ' '.join(out) + ']]'


def kana_for_speech(text):
    """日本語の音声 (say の Kyoko) に読ませるカタカナ (小書きのカナを普通のカナに)"""
    kana = script.kana(text)
    for small, full in SMALL_KANA.items():
        kana = kana.replace(small, full)
    return kana
