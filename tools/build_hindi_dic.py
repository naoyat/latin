#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からヒンディー語の辞書 (SQLite) を作る
#
#   python3 tools/build_hindi_dic.py
#
# 見出し語ごとの品詞・訳語・転写・性・ウルドゥー文字の綴りと、変化表の1語の語形 (名詞の直格・斜格、形容詞の
# 性・数、動詞の分詞・未来・接続法・命令、代名詞の能格・与格・属格) を語形の辞書にする。助動詞と組む形
# (पढ़ता हूँ) は文の解析 (hindi/analyzer.py) で組み立てる。
#
# 入力 ($DRAGOMAN_DATA/hi/):
#   kaikki-Hindi.jsonl.gz   https://kaikki.org/dictionary/Hindi/kaikki.org-dictionary-Hindi.jsonl.gz
#   ../ja-extract.jsonl.gz  日本語の訳語 (任意。ヒンディー語の項目と、日本語の項目の訳語の表のヒンディー語)
# 出力:
#   wiktionary.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import re
import sys
import gzip
import json
import sqlite3
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.hindi import dictionary, script
from dragoman.core.wiktionary_import import (english_glosses, japanese_gloss, descendants_summary, etymology_summary,
                                   japanese_translation_pairs)

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'det',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'postp': 'postposition',
       'prep': 'preposition', 'intj': 'intj'}
DESCENDANT_LANGS = ('en', 'ja', 'ur', 'pa', 'bn', 'ne', 'mr', 'gu')
INHERITING = set()
SKIP_TAGS = {'romanization', 'table-tags', 'inflection-template', 'class', 'Urdu'}
EQUIVALENT = ({'feminine'}, {'masculine'})  # 名詞の「女性形・男性形」(लड़का の लड़की) は変化形ではない
GENDER = re.compile(r'\)\s+(m|f|m or f)\b')


def load_japanese_glosses(path):
    glosses = {}
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "hi"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss and entry.get('lang_code') == 'hi' and entry.get('pos') in POS:
                    glosses.setdefault((script.key(entry['word']), POS[entry['pos']]), gloss)
    return glosses


def head(entry):
    return next((t.get('expansion', '') for t in entry.get('head_templates', []) if t.get('expansion')), '')


def gender_of(entry):
    m = GENDER.search(head(entry))
    return {'m': 'm', 'f': 'f'}.get(m.group(1)) if m else None


def transitivity(entry):
    """動詞の他動性 ('transitive' / 'intransitive' / 'ambitransitive' / None)。見出しの展開の (transitive, …) から"""
    m = re.search(r'\((ambitransitive|intransitive|transitive)\b', head(entry))
    return m.group(1) if m else None


def main():
    t0 = time.time()
    ja_path = os.path.join(os.path.dirname(dictionary.DATA_DIR), 'ja-extract.jsonl.gz')
    ja = load_japanese_glosses(ja_path)
    translations = japanese_translation_pairs(ja_path, 'hi', script.key, POS)
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, word TEXT, roman TEXT, gender TEXT,
                             urdu TEXT, senses INTEGER, transitivity TEXT);
        CREATE TABLE forms (key TEXT, lemma TEXT, pos TEXT, tags TEXT, UNIQUE (key, lemma, pos, tags));
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n = n_ja = n_forms = 0
    used = set()
    with gzip.open(os.path.join(dictionary.DATA_DIR, 'kaikki-Hindi.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'hi' or entry.get('pos') not in POS:
                continue
            senses = entry.get('senses', [])
            if senses and all('form_of' in s or 'alt_of' in s for s in senses):
                # 変化形の項目 (गया: जाना の完了分詞、है: होना の現在) は語形の辞書にだけ入れる
                for sense in senses:
                    for target in sense.get('form_of', []):
                        tags = [t for t in sense.get('tags', []) if t != 'form-of']
                        if tags and script.is_devanagari(target.get('word', '')):
                            db.execute('INSERT OR IGNORE INTO forms VALUES (?, ?, ?, ?)',
                                       (script.key(entry['word']), script.key(target['word']), POS[entry['pos']],
                                        json.dumps(sorted(tags))))
                            n_forms += 1
                continue
            if not senses:
                continue
            word = script.key(entry['word'])
            pos = POS[entry['pos']]
            gloss = ja.pop((word, pos), None)
            if gloss:
                short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                gloss = ','.join(short) if short else None
            if not gloss and (word, pos) in translations and (word, pos) not in used:
                gloss = ','.join(j for _, j in translations[(word, pos)][:4])
                used.add((word, pos))
            gloss_lang = 'ja' if gloss else 'en'
            gloss = gloss or english_glosses(entry)
            if not gloss:
                continue
            n_ja += gloss_lang == 'ja'
            forms = entry.get('forms', [])
            roman = next((f['form'] for f in forms if 'romanization' in f.get('tags', [])), None)
            urdu = next((f['form'] for f in forms if f.get('tags') == ['Urdu']), None)
            db.execute('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (word, pos, gloss, gloss_lang, entry['word'], roman, gender_of(entry), urdu, len(senses),
                        transitivity(entry) if pos == 'verb' else None))
            n += 1
            # 語形 (1語のもの)。見出し語そのものも入れる
            rows = {(word, json.dumps(['lemma']))}
            for f in forms:
                tags = [t for t in f.get('tags', []) if t not in ('romanization',)]
                if not tags or set(tags) & SKIP_TAGS or set(tags) in EQUIVALENT or ' ' in f['form'].strip() or \
                        not script.is_devanagari(f['form']):
                    continue
                rows.add((script.key(f['form'].strip()), json.dumps(sorted(tags))))
            for key, tags in rows:
                db.execute('INSERT OR IGNORE INTO forms VALUES (?, ?, ?, ?)', (key, word, pos, tags))
                n_forms += 1
            if entry.get('descendants'):
                summary = descendants_summary(entry, DESCENDANT_LANGS, INHERITING)
                if summary:
                    db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                               (word, entry['pos'], json.dumps(summary, ensure_ascii=False)))
            if entry.get('etymology_text') or entry.get('etymology_templates'):
                summary = etymology_summary(entry)
                if summary:
                    db.execute('INSERT INTO etymology VALUES (?, ?, ?)',
                               (word, entry['pos'], json.dumps(summary, ensure_ascii=False)))
    db.executescript('''
        CREATE INDEX lemmas_key ON lemmas (key);
        CREATE INDEX lemmas_urdu ON lemmas (urdu);
        CREATE INDEX forms_key ON forms (key);
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d lemmas (Japanese glosses: %d), %d forms -> %s (%.1fMB, %.0fs)' % (
        n, n_ja, n_forms, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
