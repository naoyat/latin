#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の辞書 (tools/build_greek_dic.py で作る SQLite) の検索
#
# 照合は「アクセントなどを保った形 (orthography.key)」→ 小文字 → 記号を除いた形 (orthography.flat) の順。
# 記号を除いた照合で見つかったものは、入力にアクセントがあればアクセントの位置まで一致するものを優先する
#
import os
import json
import sqlite3

from latin.wiktionary_import import make_item
from . import orthography

DATA_DIR = os.path.join(os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data')), 'grc')
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')

_db = None
_lemma_cache = {}


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def _signature(item):
    """方言の違いだけの同じ候補をまとめるための鍵"""
    return tuple((k, str(v)) for k, v in sorted(item.items()) if k not in ('dialect', 'source'))


def _items(rows):
    items, seen = [], set()
    for surface, lemma_id, features in rows:
        if lemma_id not in _lemma_cache:
            info, = _db.execute('SELECT info FROM lemmas WHERE id = ?', (lemma_id,)).fetchone()
            _lemma_cache[lemma_id] = json.loads(info)
        item = make_item(surface, _lemma_cache[lemma_id], json.loads(features))
        if _signature(item) not in seen:
            seen.add(_signature(item))
            items.append(item)
    return items


def lookup(surface):
    """表層形から辞書の項目 (dict) のリスト。見つからなければ []"""
    db = _connect()
    if db is None:
        return []
    key = orthography.key(surface)
    for k in dict.fromkeys([key, key.lower()]):
        rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE surface = ?', (k,)).fetchall()
        if rows:
            return _items(rows)
    rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE flat = ?',
                      (orthography.flat(surface),)).fetchall()
    return _items(rows)


def _rows(table, lemma):
    db = _connect()
    if db is None or not lemma:
        return []
    return [json.loads(data) for data, in
            db.execute('SELECT data FROM %s WHERE lemma = ?' % table, (orthography.key(lemma),)).fetchall()]


def descendants(lemma):
    result, seen = [], set()
    for data in _rows('descendants', lemma):
        for d in data:
            if (d['lang'], d['word']) not in seen:
                seen.add((d['lang'], d['word']))
                result.append(d)
    return result


def etymology(lemma):
    result = []
    for d in _rows('etymology', lemma):
        if d not in result:
            result.append(d)
    return result
