#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からロシア語の見出し語の辞書 (SQLite) を作る
#
#   python3 tools/build_russian_dic.py
#
# 語形の解析は pymorphy3 が行うので、ここでは見出し語ごとの品詞・訳語・アスペクト・語源・子孫語と、
# 変化形の強勢の位置 (кни́ги。pymorphy3 の辞書には強勢が無い) だけを持つ。
#
# 入力 ($DRAGOMAN_DATA/ru/):
#   kaikki-Russian.jsonl.gz   https://kaikki.org/dictionary/Russian/kaikki.org-dictionary-Russian.jsonl.gz
#   ../ja-extract.jsonl.gz    日本語の訳語 (任意)
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

from russian import dictionary, script
from core.wiktionary_import import english_glosses, japanese_gloss, descendants_summary, etymology_summary

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'pronoun',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'prep': 'preposition', 'intj': 'intj',
       'participle': 'participle', 'predicative': 'adv'}
# 子孫語として集める言語 (ロシア語からの借用) と、ロシア語から語を継承しうる言語 (無し)
DESCENDANT_LANGS = ('en', 'ja', 'fr', 'de', 'uk', 'be')
INHERITING = set()
SKIP_FORM_TAGS = {'romanization', 'table-tags', 'inflection-template', 'class'}
ASPECT = re.compile(r'\)\s+(impf|pf|both)\b')
CYRILLIC = re.compile(r'^[а-яёА-ЯЁ́̀-]+$')


def load_japanese_glosses(path):
    glosses = {}
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "ru"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss:
                    glosses.setdefault(script.key(entry['word']), gloss)
    return glosses


def aspect_of(entry):
    """動詞のアスペクト ('pf' 完了体 / 'impf' 不完了体 / 'both' 両体)"""
    for t in entry.get('head_templates', []):
        m = ASPECT.search(t.get('expansion', ''))
        if m:
            return m.group(1)
    return None


def canonical(entry):
    return next((f['form'] for f in entry.get('forms', []) if 'canonical' in f.get('tags', [])), entry['word'])


def main():
    t0 = time.time()
    ja = load_japanese_glosses(os.path.join(os.path.dirname(dictionary.DATA_DIR), 'ja-extract.jsonl.gz'))
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, word TEXT, aspect TEXT, senses INTEGER);
        CREATE TABLE forms (key TEXT, stressed TEXT, UNIQUE (key, stressed));
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n = n_ja = n_forms = 0
    with gzip.open(os.path.join(dictionary.DATA_DIR, 'kaikki-Russian.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'ru' or entry.get('pos') not in POS:
                continue
            key = script.key(entry['word'])
            stressed = canonical(entry)
            # 変化形の強勢 (形の項目 «form of» も含めて全部入れる)
            forms = {stressed} | {f['form'] for f in entry.get('forms', [])
                                  if not SKIP_FORM_TAGS & set(f.get('tags', [])) and CYRILLIC.match(f['form'])}
            for form in forms:
                if script.stress_index(form) is not None:
                    db.execute('INSERT OR IGNORE INTO forms VALUES (?, ?)', (script.key(form), form))
                    n_forms += 1
            senses = entry.get('senses', [])
            if senses and all('form_of' in s or 'alt_of' in s for s in senses):
                continue
            gloss = ja.get(key)
            if gloss:  # 長い日本語の訳語は説明文 (ほかに訳語があれば落とす)
                short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                gloss = ','.join(short) if short else None
            gloss_lang = 'ja' if gloss else 'en'
            gloss = gloss or english_glosses(entry)
            if not gloss:
                continue
            n_ja += gloss_lang == 'ja'
            pos = POS[entry['pos']]
            db.execute('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (key, pos, gloss, gloss_lang, stressed, aspect_of(entry) if pos == 'verb' else None,
                        len(senses)))
            n += 1
            if entry.get('descendants'):
                summary = descendants_summary(entry, DESCENDANT_LANGS, INHERITING)
                if summary:
                    db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                               (key, entry['pos'], json.dumps(summary, ensure_ascii=False)))
            if entry.get('etymology_text') or entry.get('etymology_templates'):
                summary = etymology_summary(entry)
                if summary:
                    db.execute('INSERT INTO etymology VALUES (?, ?, ?)',
                               (key, entry['pos'], json.dumps(summary, ensure_ascii=False)))
    db.executescript('''
        CREATE INDEX lemmas_key ON lemmas (key);
        CREATE INDEX forms_key ON forms (key);
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d lemmas (Japanese glosses: %d), %d stressed forms -> %s (%.1fMB, %.0fs)' % (
        n, n_ja, n_forms, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
