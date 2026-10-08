#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Morpheus 由来の補助辞書 (tools/build_morpheus_dic.py で作る SQLite) の検索
#   マクロン推定の候補の供給元として使う (訳語は無い)
#
# 辞書ファイルが無ければ何も返さない
#
import os
import sqlite3
import unicodedata

from dragoman.core import paths
from . import ldt

DATA_DIR = paths.DATA_DIR
MACRONIZER_DIR = os.path.join(DATA_DIR, 'latin-macronizer', 'latin_macronizer')
DB_PATH = os.path.join(DATA_DIR, 'morpheus.sqlite')

_db = None


def key(text):
    """照合用のキー: マクロン除去・小文字化・j→i・v→u (Morpheus の語形は u/v, i/j を区別しない)"""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    return text.lower().replace('j', 'i').replace('v', 'u')


def available():
    return _connect() is not None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def lookup_flat(word):
    """マクロンを除いた形が一致する形を {マクロン付きの形: 項目のリスト} で返す"""
    db = _connect()
    if db is None:
        return {}
    result = {}
    for surface, lemma, tag in db.execute('SELECT surface, lemma, tag FROM forms WHERE key = ?', (key(word),)):
        result.setdefault(surface, []).append(ldt.to_item(tag, lemma, surface))
    return result
