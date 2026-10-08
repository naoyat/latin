#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語 の解析と逐語訳 (python3 dragoman.py --lang=ur と同じ。オプションは --help で)
#
from core import cli
from urdu.command import COMMAND

if __name__ == '__main__':
    cli.main(COMMAND)
