#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヘブライ語の辞書 (tools/build_hebrew_dic.py で OSHB・Strong・BDB の索引・Wiktionary から作る SQLite) の検索
#
#   forms(語形)     → OSHB に現れた解析 [(切れ目, 見出し語の番号, 語形の符号, 回数)]
#   lexicon(番号)   → 見出し語 (母音記号付き)、転写、品詞、語義 (英語)、日本語訳
#
import os
import json
import sqlite3

from . import script

DATA_DIR = os.path.join(os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data')), 'he')
DB_PATH = os.path.join(DATA_DIR, 'hebrew.sqlite')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def forms(word):
    """語形 → [{segments, lemmas, morph, count}] (多いものから)。母音記号付きで引き、無ければ子音だけで"""
    db = _connect()
    if db is None:
        return []
    rows = db.execute('SELECT segments, lemmas, morph, count FROM forms WHERE key = ? ORDER BY count DESC',
                      (script.pointed(word),)).fetchall()
    if not rows:
        rows = db.execute('SELECT segments, lemmas, morph, count FROM forms WHERE cons = ? ORDER BY count DESC',
                          (script.consonants(word),)).fetchall()
    return [{'segments': json.loads(s), 'lemmas': json.loads(l), 'morph': m, 'count': n} for s, l, m, n in rows]


def lexicon(aug):
    """見出し語の番号 (1254a, 430) → {word, xlit, pos, ja, gloss_lang, strong, root}"""
    db = _connect()
    if db is None:
        return None
    row = db.execute('SELECT word, xlit, pos, ja, gloss_lang, strong, root FROM lexicon WHERE aug = ?',
                     (aug,)).fetchone()
    if row is None:
        return None
    return dict(zip(('word', 'xlit', 'pos', 'ja', 'gloss_lang', 'strong', 'root'), row))


def verb_forms(root):
    """語根 (子音だけ) の動詞の形 [{lemma, stem, type, pgn, form, lang, count, bare}] (OSHB に現れたもの)。
    bare は接頭辞も人称接尾辞も付いていない語"""
    db = _connect()
    if db is None:
        return []
    keys = ('lemma', 'stem', 'type', 'pgn', 'form', 'lang', 'count', 'bare')
    return [dict(zip(keys, row)) for row in db.execute(
        'SELECT lemma, stem, type, pgn, form, lang, count, bare FROM verbs WHERE root = ? ORDER BY count DESC',
        (script.consonants(root),)).fetchall()]


def _rows(table, key):
    db = _connect()
    if db is None or not key:
        return []
    return [json.loads(d) for d, in db.execute('SELECT data FROM %s WHERE lemma = ?' % table,
                                                 (script.consonants(key),)).fetchall()]


def descendants(lemma):
    return _rows('descendants', lemma)


def etymology(lemma):
    return _rows('etymology', lemma)
