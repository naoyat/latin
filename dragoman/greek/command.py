#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary
from . import romanize as greek_romanize

USAGE = '''
  echo "ἐν ἀρχῇ ἦν ὁ λόγος." | python3 dragoman.py --lang=grc
  python3 dragoman.py --lang=grc -w -D -E FILE...
'''
OPTION_HELP = '''
  --pron=PRON            音読の発音: attic (古典期アッティカ式。既定) / modern (現代ギリシア語式)
  -r, --romanize         見出しの行と語ごとの表示に転写を添える (ἐν ἀρχῇ → en archêi)
'''


def header(analysis, options):
    text = ' '.join(analysis.surfaces)
    return text + ('  (%s)' % greek_romanize.romanize(text) if options.romanize else '')


def handle_option(option, arg, options):
    if option == '--pron':
        options.extra['pron'] = arg
        return True
    return False


def available():
    return None if dictionary.available() else 'no Greek dictionary (python3 tools/build_greek_dic.py)'


COMMAND = Command(lang='grc', name='古典ギリシア語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, romanize=greek_romanize.romanize_word,
                  descendant_langs=('la', 'en', 'fr'), fallback_langs=('it', 'es'),
                  speech_pron=lambda options: options.extra.get('pron', 'attic'),
                  long_options=('pron=',), option_help=OPTION_HELP, handle_option=handle_option)
