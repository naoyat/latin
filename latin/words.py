#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 辞書ファイル (words/*.def) の場所
#
import os

WORDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'words')


def words_path(name):
    return os.path.join(WORDS_DIR, name)
