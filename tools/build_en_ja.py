#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 英語 → 日本語の訳語の表 (SQLite) を、日本語版 Wiktionary の英語の項目 (ja-extract) から作る
#
#   python3 tools/build_en_ja.py
#
# 各言語の辞書で日本語の訳語が無く英語の語義 (Wiktionary・CAMeL Tools など) になっている語を、共通部分
# (core/en_ja.py) で日本語に置き換えるのに使う。品詞 (名詞・動詞・形容詞・副詞) ごとに、整えた訳語を最大4つ持つ。
#
# 入力: $DRAGOMAN_DATA/ja-extract.jsonl.gz (日本語版 Wiktionary の抽出)
# 出力: $DRAGOMAN_DATA/en-ja.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import sys
import gzip
import json
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import en_ja, paths
from core.wiktionary_import import japanese_gloss

POS = {'noun': 'noun', 'verb': 'verb', 'adj': 'adj', 'adv': 'adv', 'name': 'name', 'phrase': 'phrase'}


def main():
    t0 = time.time()
    out = en_ja.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.execute('CREATE TABLE en_ja (en TEXT, pos TEXT, ja TEXT, UNIQUE (en, pos))')
    n = 0
    with gzip.open(paths.data('ja-extract.jsonl.gz'), 'rt') as fp:
        for line in fp:
            if '"lang_code": "en"' not in line:
                continue
            entry = json.loads(line)
            if entry.get('lang_code') != 'en' or entry.get('pos') not in POS:
                continue
            pos = POS[entry['pos']]
            glosses = en_ja.clean(japanese_gloss(entry, limit=8), pos)
            if not glosses:
                continue
            db.execute('INSERT OR IGNORE INTO en_ja VALUES (?, ?, ?)',
                       (en_ja.key(entry['word']), pos, ','.join(glosses[:4])))
            n += 1
    db.execute('CREATE INDEX en_ja_en ON en_ja (en)')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d entries -> %s (%.1fMB, %.0fs)' % (n, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
