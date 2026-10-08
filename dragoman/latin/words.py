#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 辞書ファイル (words/*.def) の場所
#
from dragoman.core import paths
import os

WORDS_DIR = os.path.join(paths.REPO_ROOT, 'words')


def words_path(name):
    return os.path.join(WORDS_DIR, name)
