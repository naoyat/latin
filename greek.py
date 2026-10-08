#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語 の解析と逐語訳 (python3 dragoman.py --lang=grc と同じ。オプションは --help で)
#
from core import cli
from greek.command import COMMAND

if __name__ == '__main__':
    cli.main(COMMAND)
