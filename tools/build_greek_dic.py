#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) から古典ギリシア語の辞書 (SQLite) を作る
#
#   python3 tools/build_greek_dic.py
#
# 入力 ($DRAGOMAN_DATA/grc/, 既定 ~/.local/share/dragoman-data/grc/):
#   kaikki-AncientGreek.jsonl.gz  https://kaikki.org/dictionary/Ancient%20Greek/kaikki.org-dictionary-AncientGreek.jsonl.gz
#   ../ja-extract.jsonl.gz        日本語の訳語 (任意。ラテン語の辞書と共用)
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

from dragoman.greek import dictionary, orthography
from dragoman.greek.wiktionary_import import DESCENDANT_LANGS, INHERITING
from dragoman.greek.wiktionary_import import convert_entry, japanese_gloss, ja_key, descendants_summary, \
    etymology_summary, lemma_key


def load_japanese_glosses(path):
    glosses = {}
    if not os.path.exists(path):
        print('(no Japanese glosses: %s)' % path)
        return glosses
    with gzip.open(path, 'rt') as fp:
        for line in fp:
            if '"lang_code": "grc"' not in line:
                continue
            entry = json.loads(line)
            if entry.get('lang_code') != 'grc':
                continue
            if any('form_of' in s or 'alt_of' in s for s in entry.get('senses', [])):
                continue
            gloss = japanese_gloss(entry)
            if gloss and ja_key(entry) not in glosses:
                glosses[ja_key(entry)] = gloss
    return glosses


def main():
    data_dir = dictionary.DATA_DIR
    t0 = time.time()
    ja_glosses = load_japanese_glosses(os.path.join(os.path.dirname(data_dir), 'ja-extract.jsonl.gz'))
    print('Japanese glosses: %d (%.0fs)' % (len(ja_glosses), time.time() - t0), flush=True)

    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (id INTEGER PRIMARY KEY, info TEXT);
        CREATE TABLE forms (surface TEXT, flat TEXT, lemma_id INTEGER, features TEXT);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n_lemmas = n_forms = n_ja = n_desc = n_ety = 0
    with gzip.open(os.path.join(data_dir, 'kaikki-AncientGreek.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'grc':
                continue
            if entry.get('descendants'):
                summary = descendants_summary(entry, DESCENDANT_LANGS, INHERITING)
                if summary:
                    db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                               (lemma_key(entry), entry.get('pos'), json.dumps(summary, ensure_ascii=False)))
                    n_desc += 1
            if entry.get('etymology_text') or entry.get('etymology_templates'):
                summary = etymology_summary(entry)
                if summary:
                    db.execute('INSERT INTO etymology VALUES (?, ?, ?)',
                               (lemma_key(entry), entry.get('pos'), json.dumps(summary, ensure_ascii=False)))
                    n_ety += 1
            for info, forms in convert_entry(entry, ja_glosses):
                n_lemmas += 1
                n_ja += info.get('gloss_lang') == 'ja'
                cur = db.execute('INSERT INTO lemmas (info) VALUES (?)', (json.dumps(info, ensure_ascii=False),))
                db.executemany('INSERT INTO forms VALUES (?, ?, ?, ?)',
                               [(surface, orthography.flat(surface), cur.lastrowid,
                                 json.dumps(features, ensure_ascii=False)) for surface, features in forms])
                n_forms += len(forms)
                if n_lemmas % 10000 == 0:
                    print('  %d lemmas, %d forms (%.0fs)' % (n_lemmas, n_forms, time.time() - t0), flush=True)
    db.executescript('''
        CREATE INDEX forms_surface ON forms (surface);
        CREATE INDEX forms_flat ON forms (flat);
        CREATE INDEX forms_lemma ON forms (lemma_id);   -- 見出し語の語形をすべて (文の生成の逆引き)
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d lemmas (Japanese glosses: %d, descendants: %d, etymology: %d), %d forms -> %s (%.0fMB, %.0fs)' % (
        n_lemmas, n_ja, n_desc, n_ety, n_forms, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
