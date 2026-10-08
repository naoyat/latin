#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary, morphology, script

USAGE = '''
  echo "Мальчик читает книгу." | python3 dragoman.py --lang=ru
'''
OPTION_HELP = '''
  見出しの行には強勢記号を付けた文と転写を添える。音読は macOS の say のロシア語音声 Milena (無ければ espeak-ng)
'''


def stressed_text(surfaces):
    """強勢記号を付けた文 (句読点の前の空白を詰める)"""
    out = ''
    for s in surfaces:
        if s.startswith('('):
            continue  # 補った繋辞
        if s in analyzer.PUNCTUATION and s not in ('—', '–', '(', '«', '„', '“'):
            out += s
        else:
            out += (' ' if out else '') + (s if s in analyzer.PUNCTUATION else morphology.stressed(s))
    return out


def header(analysis, options):
    stressed = stressed_text(analysis.surfaces)
    return '%s  (%s)' % (stressed, script.translit(stressed))


def romanized(word):
    """強勢付きの転写 (Девочка → Dévočka)"""
    return script.translit(morphology.stressed(word))


def available():
    if dictionary.available() and morphology.available():
        return None
    return 'no Russian data (pip install pymorphy3 pymorphy3-dicts-ru, and python3 tools/build_russian_dic.py)'


COMMAND = Command(lang='ru', name='ロシア語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: stressed_text(a.surfaces), romanize=romanized,
                  descendant_langs=('en', 'ja', 'fr', 'de'), fallback_langs=('uk', 'be'), option_help=OPTION_HELP)
