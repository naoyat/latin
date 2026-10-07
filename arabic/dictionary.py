#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア語の見出し語の辞書 (tools/build_arabic_dic.py で Wiktionary から作る SQLite) の検索。
# キーは母音記号を除き、アリフの異体を ا にそろえた形 (arabic.script.normalize)
#
import os
import json
import sqlite3

from . import script

DATA_DIR = os.path.join(os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data')), 'ar')
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
    """[{pos, ja, gloss_lang, word (母音記号付きの見出し語), form (動詞の型 I〜X), root, senses}]"""
    db = _connect()
    if db is None or not word:
        return []
    return [{'pos': pos, 'ja': ja, 'gloss_lang': lang, 'word': vocalized, 'form': form, 'root': root,
             'senses': senses or 0}
            for pos, ja, lang, vocalized, form, root, senses in db.execute(
                'SELECT pos, ja, gloss_lang, word, form, root, senses FROM lemmas WHERE key = ?',
                (script.normalize(word),)).fetchall()]


def _rows(table, key):
    db = _connect()
    if db is None or not key:
        return []
    return [json.loads(d) for d, in db.execute('SELECT data FROM %s WHERE lemma = ?' % table,
                                                 (script.normalize(key),)).fetchall()]


def descendants(lemma):
    return _rows('descendants', lemma)


def etymology(lemma):
    return _rows('etymology', lemma)
