#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヒンディー語の辞書 (tools/build_hindi_dic.py で Wiktionary から作る SQLite) の検索。
# Wiktionary の変化表 (名詞の直格・斜格、形容詞の性・数、動詞の完了分詞・未完了分詞・未来・接続法・命令など) を
# 語形の辞書にしたもの。キーは NFD にそろえた形 (hindi.script.key)
#
import os
import json
import sqlite3

from core import paths
from . import script

DATA_DIR = os.path.join(paths.DATA_DIR, 'hi')
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')
FIELDS = ('pos', 'ja', 'gloss_lang', 'word', 'roman', 'gender', 'urdu', 'senses', 'transitivity')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def lemmas(word):
    """[{pos, ja, gloss_lang, word, roman, gender ('m' / 'f' / None), urdu (ウルドゥー文字の綴り), senses,
      transitivity ('transitive' / 'intransitive' / 'ambitransitive' / None)}]"""
    db = _connect()
    if db is None or not word:
        return []
    return [dict(zip(FIELDS, row)) for row in db.execute(
        'SELECT %s FROM lemmas WHERE key = ?' % ', '.join(FIELDS), (script.key(word),)).fetchall()]


def forms(word):
    """語形 → [(見出し語, 品詞, タグの集合)]"""
    db = _connect()
    if db is None or not word:
        return []
    return [(lemma, pos, set(json.loads(tags))) for lemma, pos, tags in db.execute(
        'SELECT lemma, pos, tags FROM forms WHERE key = ?', (script.key(word),)).fetchall()]


def by_urdu(word):
    """ウルドゥー文字の綴り → ヒンディー語の見出し語のリスト"""
    db = _connect()
    if db is None or not word:
        return []
    return [w for w, in db.execute('SELECT word FROM lemmas WHERE urdu = ?', (word,)).fetchall()]


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
