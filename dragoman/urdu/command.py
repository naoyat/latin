#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語のコマンドの設定 (core/cli.py)。解析はヒンディー語の解析器で行う
#
from dragoman.core.cli import Command
from dragoman.hindi import explain
from . import analyzer, dictionary, script

USAGE = '''
  echo "لڑکے نے کتاب پڑھی۔" | python3 dragoman.py --lang=ur
  ウルドゥー文字の語をヒンディー語の語形に引き当て、ヒンディー語の解析器で解析する。見出しの行の転写は、選んだ
  ヒンディー語の語形から (短母音を書かないウルドゥー文字からは作れない)。音読は espeak-ng のウルドゥー語音声
'''


def header(analysis, options):
    original, latin = analysis.forms_text
    return '%s  (%s)' % (script.isolate(original), latin)


def romanized(word):
    from dragoman.hindi import script as hindi_script
    candidates = dictionary.candidates(word)
    return hindi_script.translit(candidates[0]) if candidates else word


def available():
    if dictionary.available():
        return None
    return 'no Urdu data (python3 tools/build_hindi_dic.py, then python3 tools/build_urdu_dic.py)'


COMMAND = Command(lang='ur', name='ウルドゥー語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: a.forms_text[0], romanize=romanized,
                  explain=explain.notes, descendant_langs=('en', 'ja', 'hi', 'pa'))
