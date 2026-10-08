#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary, explain, script

USAGE = '''
  echo "من به مدرسه می‌روم." | python3 dragoman.py --lang=fa
  見出しの行は、ペルシア文字と転写 (Wiktionary のイラン式。文字に書かれないエザーフェ -e を補う) を並べる。
  音読は espeak-ng のペルシア語音声
'''


def header(analysis, options):
    original, latin = analyzer.sentence_text(analysis.forms)
    return '%s  (%s)' % (script.isolate(original), latin)


def available():
    return None if dictionary.available() else 'no Persian data (python3 tools/build_persian_dic.py)'


COMMAND = Command(lang='fa', name='ペルシア語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: analyzer.sentence_text(a.forms)[0],
                  romanize=script.rough_translit, explain=explain.notes,
                  descendant_langs=('en', 'ja', 'tr', 'ur', 'hi', 'ar', 'hy', 'ka'))
