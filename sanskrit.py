#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリット の解析と逐語訳 (python3 dragoman.py --lang=sa と同じ。オプションは --help で)
#
from core import cli
from sanskrit.command import COMMAND

if __name__ == '__main__':
    cli.main(COMMAND)
