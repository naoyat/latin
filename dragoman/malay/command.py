#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# マレー語のコマンドの設定 (core/cli.py)。解析はインドネシア語と共通 (マレー語の辞書の項目を先に引く)
#
from dragoman.core.cli import Command
from dragoman.indonesian import command as indonesian_command
from dragoman.indonesian import dictionary
from . import analyzer

USAGE = '''
  ./dragoman.py ms -e "Saya pergi ke sekolah kerana hendak belajar."
  解析はインドネシア語と共通 (docs/indonesian.md)。辞書はマレー語の項目を先に引く
'''

COMMAND = Command(lang='ms', name='マレー語', analyzer=analyzer, dictionary=dictionary,
                  available=indonesian_command.available, usage=USAGE, header=lambda a, o: ' '.join(a.surfaces),
                  explain=indonesian_command.explain, descendant_langs=('en', 'ja', 'id'), speech_lang='ms')
