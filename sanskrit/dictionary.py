#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの見出し語の辞書 (tools/build_sanskrit_dic.py で Wiktionary から作る SQLite) の検索。
# キーは SLP1 の語幹・語根 (vana, gam)
#
import os
import json
import sqlite3

DATA_DIR = os.path.join(os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data')), 'sa')
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')
VIDYUT_DATA = os.path.join(DATA_DIR, 'vidyut-data')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def lemmas(key):
    """[{pos, ja, gloss_lang, word, gana, causative}] (gana, causative は動詞の見出しから引いた語根のみ)"""
    db = _connect()
    if db is None or not key:
        return []
    return [{'pos': pos, 'ja': ja, 'gloss_lang': lang, 'word': word, 'gana': gana, 'causative': bool(causative)}
            for pos, ja, lang, word, gana, causative in db.execute(
                'SELECT pos, ja, gloss_lang, word, gana, causative FROM lemmas WHERE key = ?', (key,)).fetchall()]


def _rows(table, key):
    db = _connect()
    if db is None or not key:
        return []
    return [json.loads(d) for d, in db.execute('SELECT data FROM %s WHERE lemma = ?' % table, (key,)).fetchall()]


def descendants(key):
    from . import script
    result, seen = [], set()
    for data in _rows('descendants', script.to_slp1(key) if not key.isascii() else key):
        for d in data:
            if (d['lang'], d['word']) not in seen:
                seen.add((d['lang'], d['word']))
                result.append(d)
    return result


def etymology(key):
    from . import script
    result = []
    for d in _rows('etymology', script.to_slp1(key) if not key.isascii() else key):
        if d not in result:
            result.append(d)
    return result
