#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary 由来の補助辞書 (tools/build_wiktionary_dic.py で作る SQLite) の検索
#
# 辞書ファイルが無ければ何も返さない (手作りの辞書だけで動く)
#
import os
import re
import json
import sqlite3

from core.wiktionary_import import make_item, flatten
from .katakana import katakana
from . import orthography

DATA_DIR = os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data'))
DB_PATH = os.path.join(DATA_DIR, 'wiktionary.sqlite')

_db = None
_lemma_cache = {}


def available():
    return _connect() is not None


_has_flat_uv = False


def _connect():
    global _db, _has_flat_uv
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
        # u/v を同一視した照合用の列 (古い辞書ファイルには無い)
        _has_flat_uv = any(row[1] == 'flat_uv' for row in _db.execute('PRAGMA table_info(forms)'))
    return _db


def _rows_uv(surface):
    """u/v を同一視して、マクロンを除いた形が一致する行 (入力に v が無いときだけ)"""
    if not _has_flat_uv or not orthography.may_merge_uv(surface):
        return []
    return _db.execute('SELECT surface, lemma_id, features FROM forms WHERE flat_uv = ?',
                       (orthography.flat(surface, merge_uv=True),)).fetchall()


KATAKANA_NAME = re.compile(r'[ァ-ヴー・]+')


def _proper_noun_gloss(item):
    """固有名詞の訳語を名前だけにする。英語の説明 (Roman cognomen of the gens Iulia) なら綴りからカタカナを作り、
    日本語の説明付き (マールクス,マルクス,古代ローマに見られる男性名…) ならカタカナの名前だけを残す"""
    base = item.get('base') or ''
    if item.get('pos') != 'noun' or not base[:1].isupper():
        return item
    if item.get('gloss_lang') == 'ja':
        # 先頭から続くカタカナの名前だけ (説明の中の括弧書き (プラエノーメン) は拾わない)
        names = []
        for part in re.split(r'[,、（）()]', item.get('ja') or ''):
            if not part:
                continue
            if not KATAKANA_NAME.fullmatch(part):
                break
            names.append(part)
        if names:
            item['ja'] = ','.join(dict.fromkeys(names))
    else:
        item['ja'] = katakana(base)
        item['gloss_lang'] = 'ja'
    return item


def _items(rows):
    items = []
    for surface, lemma_id, features in rows:
        if lemma_id not in _lemma_cache:
            info, = _db.execute('SELECT info FROM lemmas WHERE id = ?', (lemma_id,)).fetchone()
            _lemma_cache[lemma_id] = json.loads(info)
        items.append(_proper_noun_gloss(make_item(surface, _lemma_cache[lemma_id], json.loads(features))))
    # 大文字で始まる語は固有名詞の読みを先に (Iūlia: 「ユーリア」と、形容詞 Iūlius「七月の」)
    if rows and rows[0][0][:1].isupper():
        items.sort(key=lambda item: not (item.get('pos') == 'noun' and (item.get('base') or '')[:1].isupper()))
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
    variants = [surface, orthography.ij(surface)]
    for word in list(variants):
        lower = word.lower()
        for plain, assimilated in ASSIMILATIONS:
            if lower.startswith(plain) and len(lower) > len(plain) + 1:
                # 先頭の文字は元のまま (大文字・小文字を保つ)
                variants.append(word[0] + assimilated[1:] + word[len(plain):])
    return list(dict.fromkeys(variants))


def lookup(surface):
    """表記どおり → j を i に読み替え → 接頭辞を同化 → u/v を同一視 (入力に v が無ければ) → マクロンを無視、の順に探す"""
    db = _connect()
    if db is None:
        return None
    for key in _variants(surface):
        rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE surface = ?', (key,)).fetchall()
        if rows:
            return _items(rows)
    # u/v も同一視して、マクロンまで一致するもの (uirum → virum)
    key = orthography.uv(orthography.ij(surface))
    rows = [row for row in _rows_uv(surface) if orthography.uv(orthography.ij(row[0])) == key]
    if rows:
        return _items(rows)
    rows = db.execute('SELECT surface, lemma_id, features FROM forms WHERE flat = ?', (flatten(surface),)).fetchall()
    rows = rows or _rows_uv(surface)
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
        if not rows:
            rows = _rows_uv(variant)
        for row in rows:
            if ' ' in row[0]:
                continue
            result.setdefault(row[0], []).extend(_items([row]))
    return result


def descendants(lemma):
    """見出し語 (マクロンの有無は問わない) の子孫語。[{lang, word, kind, via}]。辞書が古くて表が無ければ []"""
    db = _connect()
    if db is None or not lemma:
        return []
    try:
        rows = db.execute('SELECT data FROM descendants WHERE lemma = ?',
                          (orthography.flat(lemma, merge_uv=True),)).fetchall()
    except sqlite3.OperationalError:
        return []
    result, seen = [], set()
    for data, in rows:
        for d in json.loads(data):
            key = (d['lang'], d['word'])
            if key not in seen:
                seen.add(key)
                result.append(d)
    return result


def etymology(lemma):
    """見出し語の語源。[{ancestors, cognates, text}] (同じ綴りの別語なら複数)。表が無ければ []"""
    db = _connect()
    if db is None or not lemma:
        return []
    try:
        rows = db.execute('SELECT data FROM etymology WHERE lemma = ?',
                          (orthography.flat(lemma, merge_uv=True),)).fetchall()
    except sqlite3.OperationalError:
        return []
    result = []
    for data, in rows:
        d = json.loads(data)
        if d not in result:
            result.append(d)
    return result
