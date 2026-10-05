#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からラテン語の補助辞書 (SQLite) を作る
#
#   python3 tools/build_wiktionary_dic.py
#
# 入力 ($LATIN_DATA, 既定 ~/.local/share/latin-data):
#   kaikki-Latin.jsonl.gz  https://kaikki.org/dictionary/Latin/kaikki.org-dictionary-Latin.jsonl.gz
#   ja-extract.jsonl.gz    https://kaikki.org/dictionary/downloads/ja/ja-extract.jsonl.gz (任意。日本語の訳語)
# 出力:
#   wiktionary.sqlite
#
# データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う。
#
import os
import sys
import gzip
import json
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import wiktionary
from latin import orthography
from latin.wiktionary_import import convert_entry, japanese_gloss, ja_key, flatten, descendants_summary, canonical


def load_japanese_glosses(path):
    glosses = {}
    if not os.path.exists(path):
        print('(no Japanese glosses: %s)' % path)
        return glosses
    with gzip.open(path, 'rt') as fp:
        for line in fp:
            if '"lang_code": "la"' not in line:
                continue
            entry = json.loads(line)
            if entry.get('lang_code') != 'la':
                continue
            if any('form_of' in s or 'alt_of' in s for s in entry.get('senses', [])):
                continue
            gloss = japanese_gloss(entry)
            if gloss and ja_key(entry) not in glosses:
                glosses[ja_key(entry)] = gloss
    return glosses


def make_participle_gloss(ja_glosses):
    """動詞の日本語訳語から分詞の訳語を作る (手作り辞書の latin_verb_reg と同じ方法)"""
    from latin import verb_flags as Verb
    from latin.japanese import JaVerb, is_mecab_available
    if not is_mecab_available:
        return None
    flags = {'present': Verb.PARTICIPLE_PRESENT, 'past': Verb.PARTICIPLE_PERFECT,
             'future': Verb.PARTICIPLE_FUTURE}
    cache = {}

    def participle_gloss(verb, tense):
        ja = ja_glosses.get((flatten(verb), 'verb'))
        if not ja:
            return None
        key = (ja, tense)
        if key not in cache:
            try:
                cache[key] = ','.join(JaVerb(j).form(flags[tense]) for j in ja.split(',')[:2])
            except Exception:
                cache[key] = None
        return cache[key]
    return participle_gloss


def main():
    data_dir = wiktionary.DATA_DIR
    t0 = time.time()
    ja_glosses = load_japanese_glosses(os.path.join(data_dir, 'ja-extract.jsonl.gz'))
    print('Japanese glosses: %d (%.0fs)' % (len(ja_glosses), time.time() - t0), flush=True)
    participle_gloss = make_participle_gloss(ja_glosses)

    out = os.path.join(data_dir, 'wiktionary.sqlite')
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (id INTEGER PRIMARY KEY, info TEXT);
        CREATE TABLE forms (surface TEXT, flat TEXT, flat_uv TEXT, lemma_id INTEGER, features TEXT);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n_lemmas = n_forms = n_ja = n_desc = 0
    with gzip.open(os.path.join(data_dir, 'kaikki-Latin.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') == 'la' and entry.get('descendants'):
                summary = descendants_summary(entry)
                if summary:
                    db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                               (orthography.flat(canonical(entry), merge_uv=True), entry.get('pos'),
                                json.dumps(summary, ensure_ascii=False)))
                    n_desc += 1
            result = convert_entry(entry, ja_glosses, participle_gloss)
            if not result:
                continue
            info, forms = result
            n_lemmas += 1
            n_ja += info.get('gloss_lang') == 'ja'
            cur = db.execute('INSERT INTO lemmas (info) VALUES (?)', (json.dumps(info, ensure_ascii=False),))
            db.executemany('INSERT INTO forms VALUES (?, ?, ?, ?, ?)',
                           [(surface, flatten(surface), orthography.flat(surface, merge_uv=True),
                             cur.lastrowid, json.dumps(features, ensure_ascii=False))
                            for surface, features in forms])
            n_forms += len(forms)
            if n_lemmas % 10000 == 0:
                print('  %d lemmas, %d forms (%.0fs)' % (n_lemmas, n_forms, time.time() - t0), flush=True)
    db.executescript('''
        CREATE INDEX forms_surface ON forms (surface);
        CREATE INDEX forms_flat ON forms (flat);
        CREATE INDEX forms_flat_uv ON forms (flat_uv);
        CREATE INDEX descendants_lemma ON descendants (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d lemmas (Japanese glosses: %d, descendants: %d), %d forms -> %s (%.0fMB, %.0fs)' % (
        n_lemmas, n_ja, n_desc, n_forms, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
