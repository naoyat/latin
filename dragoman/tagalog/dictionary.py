#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語の辞書 ($DRAGOMAN_DATA/tl/wiktionary.sqlite。tools/build_tagalog_dic.py で作る) を引く
#
import functools
import os
import sqlite3

from dragoman.core import paths
from . import script

DB_PATH = paths.data('tl', 'wiktionary.sqlite')
FIELDS = ('key', 'pos', 'en', 'voice', 'target', 'senses', 'word')
_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


@functools.lru_cache(maxsize=100000)
def lemmas(key):
    """見出し → [{key, pos, en, voice, target, senses, word}] (語義の多い順)"""
    db = _connect()
    if db is None or not key:
        return ()
    rows = [dict(zip(FIELDS, r)) for r in
            db.execute('SELECT %s FROM lemmas WHERE key = ?' % ', '.join(FIELDS), (script.key(key),)).fetchall()]
    return tuple(sorted(rows, key=lambda r: -(r['senses'] or 0)))


@functools.lru_cache(maxsize=100000)
def forms(key):
    """語形 → [(見出し, アスペクト)]"""
    db = _connect()
    if db is None:
        return ()
    return tuple(db.execute('SELECT lemma, aspect FROM forms WHERE form = ?', (script.key(key),)).fetchall())


def lookup(word, langs=None):
    return []


def descendants(lemma):
    return []


def etymology(lemma):
    return []
