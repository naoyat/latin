#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からサンスクリットの見出し語の辞書 (SQLite) を作る
#
#   python3 tools/build_sanskrit_dic.py
#
# 語形の解析は vidyut (kosha) が行うので、ここでは見出し語 (語幹・語根) ごとの品詞・訳語・語源・子孫語だけを持つ。
# 動詞は Wiktionary では現在3人称単数 (गच्छति) が見出しなので、語根 (गम् gam) のキーでも入れる。
#
# 入力 ($LATIN_DATA/sa/):
#   kaikki-Sanskrit.jsonl.gz  https://kaikki.org/dictionary/Sanskrit/kaikki.org-dictionary-Sanskrit.jsonl.gz
#   ../ja-extract.jsonl.gz    日本語の訳語 (任意)
# 出力:
#   wiktionary.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import sys
import gzip
import json
import re
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sanskrit import dictionary, script
from core.wiktionary_import import english_glosses, japanese_gloss, descendants_summary, etymology_summary

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'adj', 'pron': 'pronoun', 'det': 'pronoun',
       'verb': 'verb', 'root': 'root', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'postp': 'adv',
       'prep': 'adv', 'intj': 'adv'}
# 子孫語として集める言語 (インドの言語と、英語・日本語への借用) と、サンスクリットから語を継承しうる言語
DESCENDANT_LANGS = ('pi', 'hi', 'bn', 'mr', 'en', 'ja')
INHERITING = {'pi', 'pra', 'inc-pra', 'psu', 'pmh', 'hi', 'bn', 'mr', 'gu', 'pa', 'ne', 'si', 'or', 'as', 'ur',
              'inc-ohi', 'inc-obn', 'inc-oaw', 'inc-mgd', 'inc-apa'}


def lemma_keys(entry):
    """見出し語のキー (SLP1)。動詞は語根も"""
    keys = [script.to_slp1(entry['word'])]
    if entry.get('pos') == 'verb':
        keys += [script.to_slp1(f['form']) for f in entry.get('forms', []) if 'root' in f.get('tags', [])]
    return [k for k in dict.fromkeys(keys) if k]


def load_japanese_glosses(path):
    glosses = {}
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "sa"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss:
                    glosses.setdefault(script.to_slp1(entry['word']), gloss)
    return glosses


CLASS = re.compile(r'\(([^()]*)\broot\b[^()]*\)')


def verb_class(entry):
    """動詞の見出し (third-singular indicative (class 1, type P, root पा)) から、現在語幹の類と使役かどうか"""
    for t in entry.get('head_templates', []):
        m = CLASS.search(t.get('expansion', ''))
        if m:
            gana = re.search(r'class (\d+)', m.group(1))
            return (int(gana.group(1)) if gana else None), int('causative' in m.group(1))
    return None, 0


def main():
    t0 = time.time()
    ja = load_japanese_glosses(os.path.join(os.path.dirname(dictionary.DATA_DIR), 'ja-extract.jsonl.gz'))
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, word TEXT, gana INTEGER, causative INTEGER, senses INTEGER);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n = n_ja = 0
    with gzip.open(os.path.join(dictionary.DATA_DIR, 'kaikki-Sanskrit.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'sa' or entry.get('pos') not in POS:
                continue
            senses = entry.get('senses', [])
            if senses and all('form_of' in s or 'alt_of' in s for s in senses):
                continue
            keys = lemma_keys(entry)
            gloss = ja.get(keys[0]) if keys else None
            if gloss:  # 長い日本語の訳語は説明文 (ほかに訳語があれば落とす)
                short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                gloss = ','.join(short) if short else None
            gloss_lang = 'ja' if gloss else 'en'
            gloss = gloss or english_glosses(entry)
            if entry['pos'] == 'name' and gloss_lang == 'en':
                gloss = gloss.split(',')[0]  # 固有名詞は名前だけ (Rāma, son of Dasharatha… → Rāma)
            n_ja += gloss_lang == 'ja'
            gana, causative = verb_class(entry) if entry['pos'] == 'verb' else (None, 0)
            for i, key in enumerate(keys):
                pos = POS[entry['pos']] if i == 0 else 'root'
                db.execute('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                           (key, pos, gloss, gloss_lang, entry['word'], gana if i else None, causative if i else 0,
                            len(senses)))
                n += 1
            if entry.get('descendants'):
                summary = descendants_summary(entry, DESCENDANT_LANGS, INHERITING)
                if summary:
                    db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                               (keys[0], entry['pos'], json.dumps(summary, ensure_ascii=False)))
            if entry.get('etymology_text') or entry.get('etymology_templates'):
                summary = etymology_summary(entry)
                if summary:
                    for key in keys:
                        db.execute('INSERT INTO etymology VALUES (?, ?, ?)',
                                   (key, entry['pos'], json.dumps(summary, ensure_ascii=False)))
    db.executescript('''
        CREATE INDEX lemmas_key ON lemmas (key);
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d keys (Japanese glosses: %d) -> %s (%.1fMB, %.0fs)' % (n, n_ja, out, os.path.getsize(out) / 1e6,
                                                                  time.time() - t0))


if __name__ == '__main__':
    main()
