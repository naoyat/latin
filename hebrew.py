#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語 の解析と逐語訳 (python3 dragoman.py --lang=he と同じ。オプションは --help で)
#
from core import cli
from hebrew.command import COMMAND

if __name__ == '__main__':
    cli.main(COMMAND)
