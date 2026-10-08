#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語の見出し語の辞書 (tools/build_russian_dic.py で Wiktionary から作る SQLite) の検索。
# キーは強勢記号を除いた小文字 (ё は е。russian.script.key)
#
import os
import json
import sqlite3

from core import paths
from . import script

DATA_DIR = os.path.join(paths.DATA_DIR, 'ru')
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def lemmas(word):
    """[{pos, ja, gloss_lang, word (強勢付きの見出し語), aspect, senses}]"""
    db = _connect()
    if db is None or not word:
        return []
    return [{'pos': pos, 'ja': ja, 'gloss_lang': lang, 'word': stressed, 'aspect': aspect, 'senses': senses or 0}
            for pos, ja, lang, stressed, aspect, senses in db.execute(
                'SELECT pos, ja, gloss_lang, word, aspect, senses FROM lemmas WHERE key = ?',
                (script.key(word),)).fetchall()]


def stressed_forms(word):
    """語形 (強勢記号なし) → 強勢付きの形の候補 (Wiktionary の変化表から)"""
    db = _connect()
    if db is None or not word:
        return []
    return [s for s, in db.execute('SELECT stressed FROM forms WHERE key = ?', (script.key(word),)).fetchall()]


def _rows(table, key):
    db = _connect()
    if db is None or not key:
        return []
    return [json.loads(d) for d, in db.execute('SELECT data FROM %s WHERE lemma = ?' % table,
                                                 (script.key(key),)).fetchall()]


def descendants(lemma):
    return _rows('descendants', lemma)


def etymology(lemma):
    return _rows('etymology', lemma)
