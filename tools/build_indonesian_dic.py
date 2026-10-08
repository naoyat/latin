#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語・マレー語の辞書 (SQLite) を Wiktionary (kaikki.org の抽出データ) から作る
#
#   python3 tools/build_indonesian_dic.py
#
# 見出し語 (小文字) ごとの言語 (id / ms)・品詞・訳語 (英語の語義。日本語には実行時に core/en_ja.py で直す)・
# 「〜の能動形 / 受動形」(membaca = active of baca、ditulis = passive of menulis) などのつながり。
# 接辞の付いた形で辞書に無いものは、解析 (indonesian/morphology.py) で接辞を外して引く。
#
# 入力: $DRAGOMAN_DATA/id/kaikki.org-dictionary-Indonesian.jsonl, $DRAGOMAN_DATA/ms/kaikki.org-dictionary-Malay.jsonl
#       (https://kaikki.org/dictionary/Indonesian/, /Malay/。CC BY-SA)
# 出力: $DRAGOMAN_DATA/id/wiktionary.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import re
import sys
import json
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.core.wiktionary_import import english_glosses

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'det',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'prep': 'preposition',
       'intj': 'intj', 'classifier': 'classifier', 'root': 'root'}
# 語義の「〜の形」の説明 → つながりの種類
LINKS = re.compile(r'^(?:(?:first|second|third)-person |formal |informal |colloquial )?(active|passive|plural|reduplication|alternative form|alternative spelling|misspelling|'
                   r'nonstandard spelling|informal spelling|obsolete spelling|superseded spelling|'
                   r'clipping|abbreviation|apocopic form|aphetic form|apheretic form|syncopic form|'
                   r'agent noun|abstract noun|causative|imperative|superlative|nominalization|'
                   r'informal form|colloquial form|nonstandard form|dialectal form) of ([^,;:()]+)', re.I)


def entries(path, lang):
    with open(path, encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            pos = POS.get(entry.get('pos'))
            word = entry.get('word', '')
            if pos is None or not word:
                continue
            link = None
            for sense in entry.get('senses', []):
                for gloss in sense.get('glosses', [])[:1]:
                    m = LINKS.match(gloss)
                    if m:
                        link = (m.group(1).lower(), m.group(2).strip().strip('“”"').split()[0].lower()
                                if m.group(1).lower() not in ('alternative form', 'alternative spelling')
                                else m.group(2).strip().strip('“”"').lower())
                        break
                if link:
                    break
            senses = [s for s in entry.get('senses', []) if not any(LINKS.match(g) for g in s.get('glosses', [])[:1])]
            en = english_glosses(entry, senses=senses) if senses else ''
            yield (word.lower(), lang, pos, en, link[0] if link else None, link[1] if link else None,
                   len(senses), word)


def main():
    t0 = time.time()
    out = paths.data('id', 'wiktionary.sqlite')
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, lang TEXT, pos TEXT, en TEXT, link TEXT, target TEXT, senses INTEGER,
                             word TEXT);
    ''')
    count = 0
    for lang, path in (('id', paths.data('id', 'kaikki.org-dictionary-Indonesian.jsonl')),
                       ('ms', paths.data('ms', 'kaikki.org-dictionary-Malay.jsonl'))):
        if not os.path.exists(path):
            print('missing:', path)
            continue
        rows = list(entries(path, lang))
        db.executemany('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?, ?)', rows)
        count += len(rows)
    db.executescript('CREATE INDEX lemmas_key ON lemmas (key);')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d entries → %s (%.1fs)' % (count, out, time.time() - t0))


if __name__ == '__main__':
    main()
