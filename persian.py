#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語 の解析と逐語訳 (python3 dragoman.py --lang=fa と同じ。オプションは --help で)
#
from core import cli
from persian.command import COMMAND

if __name__ == '__main__':
    cli.main(COMMAND)
