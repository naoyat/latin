#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary

USAGE = '''
  ./dragoman.py id -e "Anak itu membaca buku di sekolah."
  語を接辞 (meN-, di-, ber-, ter-, -kan, -i, ke-…-an, pe(N)- …) と接語 (-nya, -ku, -mu) に分けて辞書 (Wiktionary) を引き、
  語順 (主語-動詞-目的語、修飾語は名詞の後ろ) から格の枠を決めて日本語に訳す。辞書は tools/build_indonesian_dic.py
'''


def explain(word):
    item = word.items[0] if word.items else None
    if item is None:
        return []
    out = []
    derivation = item.attrib('derivation')
    if derivation:
        out.append('接辞: %s' % derivation)
    if item.attrib('relative'):
        out.append('関係節: %s (連体節にして名詞に掛ける)' % item.attrib('relative'))
    if item.pos == 'verb' and item.attrib('voice') == 'passive':
        out.append('受動 (di-): 前の名詞が受け手、oleh が動作主')
    return out


def original(analysis):
    """元の文 (関係節・所有でまとめた語を含む)"""
    words = getattr(analysis, 'original', None) or analysis.surfaces
    text = ''
    for w in words:
        text += w if w in analyzer.PUNCTUATION and w not in '(“"' else (' ' if text else '') + w
    return text


def available():
    return None if dictionary.available() else 'no Indonesian data (python3 tools/build_indonesian_dic.py)'


COMMAND = Command(lang='id', name='インドネシア語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=lambda a, o: original(a), speech_text=lambda a, o: original(a), explain=explain,
                  descendant_langs=('en', 'ja', 'ms'), speech_lang='id')
