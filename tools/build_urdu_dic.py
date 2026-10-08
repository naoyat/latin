#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語の語 → ヒンディー語の語形 (デーヴァナーガリー) の対応表 (SQLite) を作る
#
#   python3 tools/build_urdu_dic.py        (先に python3 tools/build_hindi_dic.py)
#
# ウルドゥー語はヒンディー語と文法が同じなので、ウルドゥー文字の語をヒンディー語の語形に引き当て、
# ヒンディー語の解析器 (hindi/) で解析する:
#   exact     Wiktionary のウルドゥー語の項目 (変化表の形) と、その「ヒンディー語の綴り」から (لڑکے → लड़के)
#   skeleton  ヒンディー語の全語形 (と機能語の表) の綴りの骨組み (urdu/script.py) から (短母音を書かない綴りを引き当てる)
#
# 入力: $DRAGOMAN_DATA/ur/kaikki-Urdu.jsonl.gz、$DRAGOMAN_DATA/hi/wiktionary.sqlite
# 出力: $DRAGOMAN_DATA/ur/urdu.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import sys
import gzip
import json
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import paths
from hindi import dictionary as hindi_dictionary, morphology as hindi_morphology, script as hindi_script
from urdu import dictionary, script

SKIP_TAGS = {'romanization', 'table-tags', 'inflection-template', 'class', 'Hindi', 'canonical'}


def hindi_spelling(entry):
    return next((f['form'] for f in entry.get('forms', []) if f.get('tags') == ['Hindi']), None)


def main():
    t0 = time.time()
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE exact (urdu TEXT, deva TEXT, roman TEXT, UNIQUE (urdu, deva));
        CREATE TABLE skeleton (skeleton TEXT, deva TEXT, UNIQUE (skeleton, deva));
    ''')
    hindi = sqlite3.connect(hindi_dictionary.DB_PATH)
    # ヒンディー語の語形を (見出し語, タグ) から引く表
    by_tags = {}
    for key, lemma, tags in hindi.execute('SELECT key, lemma, tags FROM forms'):
        by_tags.setdefault((lemma, tags), key)
    n_exact = 0
    with gzip.open(paths.data('ur', 'kaikki-Urdu.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'ur':
                continue
            deva = hindi_spelling(entry)
            if not deva or ' ' in deva:
                continue
            lemma = hindi_script.key(deva)
            roman = next((f['form'] for f in entry.get('forms', []) if 'romanization' in f.get('tags', [])), None)
            rows = [(script.normalize(entry['word']), lemma, roman)]
            for f in entry.get('forms', []):
                tags = [t for t in f.get('tags', []) if t not in ('romanization',)]
                if not tags or set(tags) & SKIP_TAGS or ' ' in f['form'] or not script.is_urdu(f['form']):
                    continue
                form = by_tags.get((lemma, json.dumps(sorted(tags))))
                if form:
                    rows.append((script.normalize(f['form']), form, None))
            for row in rows:
                n_exact += db.execute('INSERT OR IGNORE INTO exact VALUES (?, ?, ?)', row).rowcount
    # 骨組み: ヒンディー語の全語形と、機能語の表の語
    forms = {key for key, in hindi.execute('SELECT DISTINCT key FROM forms')}
    forms |= {hindi_script.key(w) for w in list(hindi_morphology.POSTPOSITIONS) + list(hindi_morphology.FUNCTION_WORDS)
              + list(hindi_morphology.PRONOUNS)}
    for stem in hindi_morphology.POSSESSIVES:
        forms |= {hindi_script.key(stem + e) for e in 'ाीे'}
    for words in hindi_morphology.COMPOUND_POSTPOSITIONS:
        forms |= {hindi_script.key(w) for w in words}
    n_skel = 0
    for form in forms:
        if ' ' in form:
            continue
        n_skel += db.execute('INSERT OR IGNORE INTO skeleton VALUES (?, ?)',
                             (script.skeleton_deva(form), form)).rowcount
    db.executescript('CREATE INDEX exact_urdu ON exact (urdu); CREATE INDEX skeleton_key ON skeleton (skeleton);')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('exact %d, skeleton %d -> %s (%.1fMB, %.0fs)' % (n_exact, n_skel, out, os.path.getsize(out) / 1e6,
                                                          time.time() - t0))


if __name__ == '__main__':
    main()
