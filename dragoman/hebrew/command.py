#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語 (と聖書アラム語) のコマンドの設定 (core/cli.py)
#
import sys

from dragoman.core.cli import Command
from . import analyzer, dictionary, explain, script

USAGE = '''
  echo "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ׃" | python3 dragoman.py --lang=he
  母音記号 (ニクード) 付きの本文を入れる (朗唱記号はあってもよい)。聖書アラム語の部分もそのまま読める
'''
OPTION_HELP = '''
  --divine-name=MODE     音読での神の名 יְהוָה の読み方: adonai (既定。ヒリクの形はエロヒム) / hashem「ハシェム」/
                         literal (字面のまま)
  --binyan=ROOT          語根 (כתב / ktb / 語形でも) の態の型の表を出す (聖書に現れた形と、規則から作った形 *)
'''


def original_text(analysis):
    return ' '.join(script.pointed(s) for s in getattr(analysis, 'tokens', analysis.surfaces)
                    if s not in analyzer.PUNCTUATION and not s.startswith('('))


def header(analysis, options):
    original = original_text(analysis)
    return '%s  (%s)' % (script.isolate(original), ' '.join(script.translit(w) for w in original.split()))


def handle_option(option, arg, options):
    if option == '--binyan':
        options.extra['binyan'] = arg
        return True
    if option == '--divine-name':
        if arg not in script.DIVINE_NAME_MODES:
            sys.exit('--divine-name: %s のどれか' % '|'.join(script.DIVINE_NAME_MODES))
        options.extra['divine_name'] = arg
        return True
    return False


def texts_hook(options):
    if 'binyan' in options.extra:
        from . import binyan
        print('\n'.join(binyan.table(options.extra['binyan'])))
        return True
    return False


def speech_setup(options, speech):
    speech.divine_name = options.extra.get('divine_name', 'adonai')


def available():
    return None if dictionary.available() else 'no Hebrew data (python3 tools/build_hebrew_dic.py)'


COMMAND = Command(lang='he', name='聖書ヘブライ語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: original_text(a), romanize=script.translit,
                  explain=explain.notes, descendant_langs=('en', 'ja', 'el', 'la', 'ar'),
                  long_options=('binyan=', 'divine-name='), option_help=OPTION_HELP, handle_option=handle_option,
                  texts_hook=texts_hook, speech_setup=speech_setup)
