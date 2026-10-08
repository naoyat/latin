#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヒンディー語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary, explain, script

USAGE = '''
  echo "लड़के ने किताब पढ़ी।" | python3 dragoman.py --lang=hi
  見出しの行は、デーヴァナーガリーと転写 (辞書の語は Wiktionary の転写から、それ以外は内在の a の脱落を規則で) を並べる。
  音読は macOS の say のヒンディー語音声 Lekha
'''


def header(analysis, options):
    original, latin = analysis.forms_text
    return '%s  (%s)' % (original, latin)


def available():
    return None if dictionary.available() else 'no Hindi data (python3 tools/build_hindi_dic.py)'


COMMAND = Command(lang='hi', name='ヒンディー語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: a.forms_text[0], romanize=script.translit,
                  explain=explain.notes, descendant_langs=('en', 'ja', 'ur', 'pa', 'bn', 'ne'))
