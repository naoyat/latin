#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 言語を選んで解析・訳する (各言語のコマンド latin.py / greek.py / sanskrit.py / russian.py / hebrew.py を呼ぶ)
#
#   python3 read.py --lang=la [latin.py のオプション] [FILE]       ラテン語 (既定)
#   python3 read.py --lang=grc [greek.py のオプション] [FILE]      古典ギリシア語
#   python3 read.py --lang=sa [sanskrit.py のオプション] [FILE]    サンスクリット
#   python3 read.py --lang=ru [russian.py のオプション] [FILE]     ロシア語
#   python3 read.py --lang=he [hebrew.py のオプション] [FILE]      聖書ヘブライ語
#
#   echo "रामो वनं गच्छति ।" | python3 read.py --lang=sa -w
#
import os
import runpy
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
COMMANDS = {'la': 'latin.py', 'grc': 'greek.py', 'sa': 'sanskrit.py', 'ru': 'russian.py', 'he': 'hebrew.py'}


def main():
    args, lang = [], 'la'
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('--lang='):
            lang = arg.split('=', 1)[1]
        elif arg == '--lang' and i + 1 < len(argv):
            lang = argv[i + 1]
            i += 1
        else:
            args.append(arg)
        i += 1
    if lang not in COMMANDS:
        sys.exit('--lang: %s のどれか' % '|'.join(COMMANDS))
    path = os.path.join(ROOT, COMMANDS[lang])
    sys.argv = [path] + args
    runpy.run_path(path, run_name='__main__')


if __name__ == '__main__':
    main()
