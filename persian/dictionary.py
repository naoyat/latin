#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語の見出し語の辞書 (tools/build_persian_dic.py で Wiktionary から作る SQLite) の検索。
# キーは正規化して ZWNJ を除いた形 (persian.script.key)
#
import os
import json
import sqlite3

from core import paths
from . import script

DATA_DIR = os.path.join(paths.DATA_DIR, 'fa')
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')
FIELDS = ('pos', 'ja', 'gloss_lang', 'word', 'roman', 'roman_classical', 'present', 'past', 'senses')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def _entry(row):
    entry = dict(zip(FIELDS, row))
    entry['present'] = json.loads(entry['present'] or '[]')  # [(現在語幹, 転写)]
    entry['past'] = json.loads(entry['past'] or 'null')       # (過去語幹, 転写)
    return entry


def lemmas(word):
    """[{pos, ja, gloss_lang, word, roman (イラン式の転写), roman_classical, present, past, senses}]"""
    db = _connect()
    if db is None or not word:
        return []
    return [_entry(row) for row in db.execute('SELECT %s FROM lemmas WHERE key = ?' % ', '.join(FIELDS),
                                              (script.key(word),)).fetchall()]


def verbs_by_stem(stem, kind):
    """語幹 (現在語幹 'present' / 過去語幹 'past') → その語幹を持つ動詞の項目のリスト"""
    db = _connect()
    if db is None:
        return []
    return [_entry(row) for row in db.execute(
        'SELECT %s FROM lemmas JOIN stems ON lemmas.rowid = stems.lemma WHERE stems.stem = ? AND stems.kind = ?'
        % ', '.join('lemmas.' + f for f in FIELDS), (script.key(stem), kind)).fetchall()]


def forms(word):
    """変化形 (複数形・比較級など) → [(見出し語のキー, タグ)]"""
    db = _connect()
    if db is None:
        return []
    return db.execute('SELECT lemma, tag FROM forms WHERE key = ?', (script.key(word),)).fetchall()


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
