#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の辞書 ($DRAGOMAN_DATA/bo/tibetan.sqlite。tools/build_tibetan_dic.py で作る) を引く
#
import functools
import os
import re
import sqlite3

from dragoman.core import en_ja, paths

DB_PATH = paths.data('bo', 'tibetan.sqlite')
SOURCES = ('wiktionary', 'hopkins', 'rangjung_yeshe')
_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None


def lookup(word, langs=None):
    """core/cli の子孫語・語源の表示用 (チベット語の辞書には無いので空)"""
    return []


@functools.lru_cache(maxsize=None)
def known():
    """見出し語 (ワイリー式) の集合。転写の読みの分かれる音節を決めるのに使う"""
    db = _connect()
    if db is None:
        return frozenset()
    words = set()
    for (w,) in db.execute('SELECT DISTINCT wylie FROM words UNION SELECT DISTINCT wylie FROM tags'):
        words.update(w.split())
    return frozenset(words)


def _variants(wylie):
    """引く形: そのまま、動名詞 (+ pa / ba)、語末の pa / ba / po / bo を除いた形"""
    out = [wylie]
    stem = re.sub(r' (pa|ba|po|bo|mo)$', '', wylie)
    if stem != wylie:
        out.append(stem)
    else:
        out += [wylie + ' pa', wylie + ' ba']
    return out


@functools.lru_cache(maxsize=100000)
def entries(wylie):
    """語 → [(品詞, 英語の訳語 (カンマ区切り), 出典)] (出典の順)"""
    db = _connect()
    if db is None:
        return []
    for w in _variants(wylie):
        rows = db.execute('SELECT pos, en, source FROM words WHERE wylie = ? ORDER BY rank', (w,)).fetchall()
        if rows:
            return rows
    return []


@functools.lru_cache(maxsize=100000)
def gloss(wylie, pos=None):
    """語 → (英語の訳語, 日本語の訳語)。品詞が合う訳語を先に"""
    rows = entries(wylie)
    if pos:
        rows = sorted(rows, key=lambda r: r[0] != pos)
    if not rows:
        return None, None
    en = rows[0][1]
    ja_pos = {'verbal_noun': 'noun', 'name': 'noun', 'pronoun': 'noun'}.get(pos or rows[0][0], pos or rows[0][0]) \
        or 'noun'
    for p, english, _ in rows:
        ja = en_ja.translate(english, ja_pos if ja_pos in ('noun', 'verb', 'adj', 'adv') else 'noun')
        if ja:
            return english, ja
    return en, None


@functools.lru_cache(maxsize=100000)
def is_word(wylie):
    """語として区切ってよい見出しか (Hill & Garrett の語彙・Wiktionary・Hopkins にある。Rangjung Yeshe の句は除く)"""
    return bool(tags(wylie)) or _exact(wylie)


def _exact(wylie):
    db = _connect()
    return db is not None and db.execute("SELECT 1 FROM words WHERE wylie = ? AND source != 'rangjung_yeshe'",
                                         (wylie,)).fetchone() is not None


@functools.lru_cache(maxsize=100000)
def pos(wylie):
    """大まかな品詞 (辞書の最初の品詞)"""
    rows = entries(wylie)
    return next((r[0] for r in rows if r[0]), None)


@functools.lru_cache(maxsize=100000)
def tags(wylie):
    """Hill & Garrett の品詞の印 (v.past, n.count …) の集合"""
    db = _connect()
    if db is None:
        return frozenset()
    row = db.execute('SELECT tags FROM tags WHERE wylie = ?', (wylie,)).fetchone()
    return frozenset(row[0].split()) if row else frozenset()


@functools.lru_cache(maxsize=100000)
def stems(wylie):
    """動詞の語形 → [(現在の語幹 (見出し), 時制 pres / past / fut / imp)]"""
    db = _connect()
    if db is None:
        return []
    rows = db.execute('SELECT DISTINCT lemma, tense FROM stems WHERE form = ?', (wylie,)).fetchall()
    return rows


@functools.lru_cache(maxsize=100000)
def sanskrit_all(wylie, limit=2):
    """サンスクリットの原語 (Mahāvyutpatti、Hopkins の順に、違うものを limit 個まで)"""
    db = _connect()
    if db is None:
        return ()
    for w in _variants(wylie):
        rows = db.execute("SELECT skt FROM sanskrit WHERE wylie = ? ORDER BY source = 'hopkins', rowid", (w,)).fetchall()
        out = []
        for (skt,) in rows:
            key = skt.rstrip('ḥmṃ').replace('-', '')
            if all(o.rstrip('ḥmṃ').replace('-', '') != key for o in out):
                out.append(skt)
        if out:
            return tuple(out[:limit])
    return ()


@functools.lru_cache(maxsize=100000)
def sanskrit(wylie):
    """サンスクリットの原語 (Mahāvyutpatti、なければ Hopkins)"""
    db = _connect()
    if db is None:
        return None
    for w in _variants(wylie):
        row = db.execute("SELECT skt FROM sanskrit WHERE wylie = ? ORDER BY source = 'hopkins'", (w,)).fetchone()
        if row:
            return row[0]
    return None
