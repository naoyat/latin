#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Latin Macronizer (https://github.com/Alatius/latin-macronizer) に同梱の Morpheus の解析結果
# (macrons.txt) から、マクロン推定用の補助辞書 (SQLite) を作る
#
#   python3 tools/build_morpheus_dic.py
#
# 入力: $DRAGOMAN_DATA/latin-macronizer/latin_macronizer/macrons.txt
#       (語形 \t LDT タグ \t 見出し語 \t 長短付きの形)  長短の表記: 長母音の後に '_'、短母音の後に '^'
# 出力: $DRAGOMAN_DATA/morpheus.sqlite
#
# データは Latin Macronizer (GPL-3.0) 由来なのでリポジトリには入れない
#
import os
import sys
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import morpheus

LENGTHEN = {'a': 'ā', 'e': 'ē', 'i': 'ī', 'o': 'ō', 'u': 'ū', 'y': 'ȳ',
            'A': 'Ā', 'E': 'Ē', 'I': 'Ī', 'O': 'Ō', 'U': 'Ū', 'Y': 'Ȳ'}


def to_macrons(accented):
    """'pu^ella_' → 'puellā' ('+' は分音記号の印なので除く)"""
    out = []
    for ch in accented:
        if ch == '_' and out:
            out[-1] = LENGTHEN.get(out[-1], out[-1])
        elif ch not in '^+':
            out.append(ch)
    return ''.join(out)


def main():
    source = os.path.join(morpheus.MACRONIZER_DIR, 'macrons.txt')
    if not os.path.exists(source):
        sys.exit('not found: %s' % source)
    t0 = time.time()
    out = morpheus.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.execute('CREATE TABLE forms (surface TEXT, key TEXT, lemma TEXT, tag TEXT)')
    rows = {}  # 同じ (形, 見出し語, タグ) が重複して入っていることがあるので除く
    with open(source, encoding='utf-8') as fp:
        for line in fp:
            fields = line.rstrip('\n').split('\t')
            if len(fields) != 4:
                continue
            _wordform, tag, lemma, accented = fields
            surface = to_macrons(accented)
            rows[(surface, lemma, tag)] = (surface, morpheus.key(surface), lemma, tag)
    db.executemany('INSERT INTO forms VALUES (?, ?, ?, ?)', rows.values())
    db.execute('CREATE INDEX forms_key ON forms (key)')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d forms -> %s (%.0fMB, %.0fs)' % (len(rows), out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
