#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary 由来の補助辞書 (tools/build_wiktionary_dic.py で作る SQLite) の検索
#
# 辞書ファイルが無ければ何も返さない (手作りの辞書だけで動く)
#
import os
import json
import sqlite3

from .wiktionary_import import make_item, flatten

DATA_DIR = os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data'))
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')

_db = None
_lemma_cache = {}


def available():
    return _connect() is not None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def _items(rows):
    items = []
    for surface, lemma_id, features in rows:
        if lemma_id not in _lemma_cache:
            info, = _db.execute('SELECT info FROM lemmas WHERE id = ?', (lemma_id,)).fetchone()
            _lemma_cache[lemma_id] = json.loads(info)
        items.append(make_item(surface, _lemma_cache[lemma_id], json.loads(features)))
    return items


# 接頭辞の同化: テキストは同化しない綴り (adficiō)、Wiktionary の見出しは同化した綴り (afficiō) のことがある
ASSIMILATIONS = [('adf', 'aff'), ('adc', 'acc'), ('adp', 'app'), ('adl', 'all'), ('adr', 'arr'),
                 ('ads', 'ass'), ('adg', 'agg'), ('adt', 'att'), ('inr', 'irr'), ('inl', 'ill'),
                 ('inm', 'imm'), ('inp', 'imp'), ('inb', 'imb'), ('conl', 'coll'), ('conr', 'corr'),
                 ('conm', 'comm'), ('conp', 'comp'), ('conb', 'comb'), ('subf', 'suff'),
                 ('subc', 'succ'), ('subp', 'supp'), ('subg', 'sugg'), ('obp', 'opp'), ('obf', 'off'),
                 ('obc', 'occ')]


def _variants(surface):
    """表記どおり → j を i に読み替え → 接頭辞を同化、の順の候補"""
    variants = [surface, surface.replace('j', 'i').replace('J', 'I')]
    for word in list(variants):
        lower = word.lower()
        for plain, assimilated in ASSIMILATIONS:
            if lower.startswith(plain) and len(lower) > len(plain) + 1:
                # 先頭の文字は元のまま (大文字・小文字を保つ)
                variants.append(word[0] + assimilated[1:] + word[len(plain):])
    return list(dict.fromkeys(variants))


def lookup(surface):
    """表記どおり → j を i に読み替え → 接頭辞を同化 → マクロンを無視、の順に探す"""
    db = _connect()
    if db is None:
        return None
    for key in _variants(surface):
        rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE surface = ?', (key,)).fetchall()
        if rows:
            return _items(rows)
    rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE flat = ?', (flatten(surface),)).fetchall()
    # マクロンを無視した照合では大文字・小文字は区別する (固有名詞と普通名詞を混ぜない)
    rows = [row for row in rows if row[0][:1].isupper() == surface[:1].isupper()]
    return _items(rows) if rows else None


def lookup_flat(surface):
    """マクロンを除いた形が一致する形を {辞書の形: 項目のリスト} で返す (j/i、接頭辞の同化も考慮)"""
    db = _connect()
    if db is None:
        return {}
    result = {}
    for variant in _variants(surface):
        rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE flat = ?',
                          (flatten(variant),)).fetchall()
        for row in rows:
            if ' ' in row[0]:
                continue
            result.setdefault(row[0], []).extend(_items([row]))
    return result
