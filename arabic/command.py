#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア語 (現代標準アラビア語) のコマンドの設定 (core/cli.py)
#
from core.cli import Command
from . import analyzer, dictionary, explain, morphology, script

USAGE = '''
  echo "ذهب الولد إلى المدرسة." | python3 dragoman.py --lang=ar
  母音記号は無くてもよい (あればそれに合う読みだけを使う)。見出しの行には、解析で選んだ格・法の語尾を補った
  母音記号付きの形と転写を並べる
'''


def header(analysis, options):
    vocalized, latin = analyzer.sentence_text(analysis.forms)
    return '%s  (%s)' % (script.isolate(vocalized), latin)


def available():
    if dictionary.available() and morphology.available():
        return None
    return ('no Arabic data (pip install camel-tools; camel_data -i morphology-db-msa-r13 '
            'disambig-mle-calima-msa-r13 (CAMELTOOLS_DATA=$DRAGOMAN_DATA/ar/camel); python3 tools/build_arabic_dic.py)')


COMMAND = Command(lang='ar', name='アラビア語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, speech_text=lambda a, o: analyzer.sentence_text(a.forms)[0],
                  romanize=script.translit, explain=explain.notes,
                  descendant_langs=('en', 'ja', 'fa', 'tr', 'es', 'pt', 'sw', 'ur', 'ms'))
