#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語・マレー語の辞書 ($DRAGOMAN_DATA/id/wiktionary.sqlite。tools/build_indonesian_dic.py で作る) を引く
#
import functools
import os
import sqlite3

from dragoman.core import paths

DB_PATH = paths.data('id', 'wiktionary.sqlite')
FIELDS = ('key', 'lang', 'pos', 'en', 'link', 'target', 'senses', 'word')
_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


@functools.lru_cache(maxsize=100000)
def _rows(key):
    db = _connect()
    if db is None or not key:
        return ()
    return tuple(dict(zip(FIELDS, row)) for row in
                 db.execute('SELECT %s FROM lemmas WHERE key = ?' % ', '.join(FIELDS), (key,)).fetchall())


def lemmas(key, lang='id'):
    """見出し (小文字) → [{key, lang, pos, en, link, target, senses, word}]。指定の言語の項目を先に、語義の多い順"""
    rows = list(_rows(key.lower()))
    return sorted(rows, key=lambda r: (r['lang'] != lang, -(r['senses'] or 0)))


def lookup(word, langs=None):
    return []


def descendants(lemma):
    return []


def etymology(lemma):
    return []
