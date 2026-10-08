#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dragoman の入口 (python3 -m dragoman と同じ。説明は python3 dragoman.py --help)
#
#   echo "Agricola in silvā magnam casam aedificat." | python3 dragoman.py
#   python3 dragoman.py --lang=grc FILE...
#   python3 dragoman.py --lang=la                       ラテン語の対話モード (変化表・マクロンの推定)
#
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dragoman.main import main  # noqa: E402

if __name__ == '__main__':
    main()
