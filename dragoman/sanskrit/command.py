#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットのコマンドの設定 (core/cli.py)
#
import sys

from dragoman.core.cli import Command
from . import analyzer, compound, dictionary, morphology, script

USAGE = '''
  echo "रामो वनं गच्छति ।" | python3 dragoman.py --lang=sa
  echo "rāmo vanaṃ gacchati" | python3 dragoman.py --lang=sa      (IAST でも)
'''
OPTION_HELP = '''
  --compound-labels=STYLE  複合語の種類の名前: sa (tatpuruṣa など。既定) / ja (依主釈など) / en (determinative など)
  -v, --voice=VOICE        音読の MBROLA の音声 (in1 / in2)
'''


def header(analysis, options):
    original = ' '.join(analysis.surfaces)
    return '%s  (%s)' % (original, script.devanagari(script.to_slp1(original)))


def handle_option(option, arg, options):
    if option == '--compound-labels':
        if arg not in compound.LABEL_STYLES:
            sys.exit('--compound-labels: %s のどれか' % '|'.join(compound.LABEL_STYLES))
        compound.set_label_style(arg)
        return True
    if option in ('-v', '--voice'):
        options.speech, options.voice = True, arg
        return True
    return False


def available():
    if dictionary.available() and morphology.available():
        return None
    return 'no Sanskrit data (vidyut data and python3 tools/build_sanskrit_dic.py)'


COMMAND = Command(lang='sa', name='サンスクリット', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, descendant_langs=('pi', 'hi', 'en', 'ja'), fallback_langs=('bn', 'mr'),
                  short_options='v:', long_options=('compound-labels=', 'voice='), option_help=OPTION_HELP,
                  handle_option=handle_option)
