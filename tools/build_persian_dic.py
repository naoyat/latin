#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からペルシア語の見出し語の辞書 (SQLite) を作る
#
#   python3 tools/build_persian_dic.py
#
# 見出し語ごとの品詞・訳語・転写 (イラン式と古典式)・動詞の現在語幹と過去語幹 (転写付き)・変化形 (複数形・比較級)・
# 語源・子孫語を持つ。語形の解析 (接頭辞・人称語尾・複数・接語) は persian/morphology.py が規則で行う。
#
# 入力 ($DRAGOMAN_DATA/fa/):
#   kaikki-Persian.jsonl.gz   https://kaikki.org/dictionary/Persian/kaikki.org-dictionary-Persian.jsonl.gz
#   ../ja-extract.jsonl.gz    日本語の訳語 (任意。ペルシア語の項目と、日本語の項目の訳語の表のペルシア語)
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

from persian import dictionary, script
from core.wiktionary_import import (english_glosses, japanese_gloss, descendants_summary, etymology_summary,
                                   japanese_translation_pairs)

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'det',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'prep': 'preposition',
       'postp': 'postposition', 'intj': 'intj'}
DESCENDANT_LANGS = ('en', 'ja', 'tr', 'ur', 'hi', 'ar', 'hy', 'ka', 'az', 'uz', 'fr', 'de', 'ru')
INHERITING = set()
PAREN = re.compile(r'(\S+) \(([^()]*)\)')
FORM_TAGS = {'plural', 'comparative', 'superlative'}


def load_japanese_glosses(path):
    glosses = {}
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "fa"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss and entry.get('lang_code') == 'fa' and entry.get('pos') in POS:
                    glosses.setdefault((script.key(entry['word']), POS[entry['pos']]), gloss)
    return glosses


def iranian(roman):
    """'pisar, pusar / pesar, posar' → 'pesar' (/ の後ろがイラン式。無ければそのまま)"""
    part = roman.split('/')[-1]
    return part.split(',')[0].strip()


def classical(roman):
    return roman.split('/')[0].split(',')[0].strip()


def head_expansion(entry):
    return next((t.get('expansion', '') for t in entry.get('head_templates', []) if t.get('expansion')), '')


def romanization(entry):
    """(イラン式, 古典式)。見出しの展開 'کتاب • (kitāb / ketâb) (...)' から"""
    expansion = head_expansion(entry)
    m = re.search(r'•\s*\(([^()]*)\)', expansion)
    if m:
        return iranian(m.group(1)), classical(m.group(1))
    roman = [f['form'] for f in entry.get('forms', []) if 'romanization' in f.get('tags', [])]
    return (roman[-1], roman[0]) if roman else (None, None)


def stems(entry, roman):
    """動詞の (現在語幹のリスト [(語幹, 転写)], 過去語幹 (語幹, 転写))"""
    expansion = head_expansion(entry)
    present = []
    m = re.search(r'present stem (.*?)(?:, past stem|, Tajik|\)\s*$|$)', expansion)
    if m:
        for stem, rom in PAREN.findall(m.group(1)):
            present.append((script.normalize(stem), iranian(rom)))
        if not present:  # 転写の無い語幹 (کار کن)
            for f in entry.get('forms', []):
                if f.get('tags') == ['present', 'stem']:
                    present.append((script.normalize(f['form']), None))
                    break
    past = None
    m = re.search(r'past stem (\S+) \(([^()]*)\)', expansion)
    word = script.normalize(entry['word'])
    if m:
        past = (script.normalize(m.group(1)), iranian(m.group(2)))
    elif word.endswith('ن'):
        past = (word[:-1], roman[:-2] if roman and roman.endswith('an') else None)
    # 転写の無い現在語幹は、同じ綴りの語幹の転写を借りる
    seen = {}
    for stem, rom in present:
        if rom:
            seen[script.key(stem)] = rom
    present = [(s, r or seen.get(script.key(s))) for s, r in present]
    out = []
    for p in present:
        if p not in out:
            out.append(p)
    return out, past


def main():
    t0 = time.time()
    ja_path = os.path.join(os.path.dirname(dictionary.DATA_DIR), 'ja-extract.jsonl.gz')
    ja = load_japanese_glosses(ja_path)
    translations = japanese_translation_pairs(ja_path, 'fa', script.key, POS)
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, word TEXT, roman TEXT, roman_classical TEXT,
                             present TEXT, past TEXT, senses INTEGER);
        CREATE TABLE stems (stem TEXT, kind TEXT, lemma INTEGER);
        CREATE TABLE forms (key TEXT, lemma TEXT, tag TEXT);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n = n_ja = 0
    used = set()
    with gzip.open(os.path.join(dictionary.DATA_DIR, 'kaikki-Persian.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'fa' or entry.get('pos') not in POS:
                continue
            senses = entry.get('senses', [])
            if not senses or all('form_of' in s or 'alt_of' in s for s in senses):
                continue
            key = script.key(entry['word'])
            pos = POS[entry['pos']]
            gloss = ja.pop((key, pos), None)
            if gloss:
                short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                gloss = ','.join(short) if short else None
            if not gloss and (key, pos) in translations and (key, pos) not in used:
                gloss = ','.join(j for _, j in translations[(key, pos)][:4])
                used.add((key, pos))
            gloss_lang = 'ja' if gloss else 'en'
            gloss = gloss or english_glosses(entry)
            if not gloss:
                continue
            n_ja += gloss_lang == 'ja'
            roman, roman_classical = romanization(entry)
            present, past = stems(entry, roman) if pos == 'verb' else ([], None)
            cur = db.execute('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                             (key, pos, gloss, gloss_lang, script.normalize(entry['word']), roman, roman_classical,
                              json.dumps(present, ensure_ascii=False) if present else None,
                              json.dumps(past, ensure_ascii=False) if past else None, len(senses)))
            rowid = cur.lastrowid
            if ' ' in entry['word'].strip():
                present, past = [], None  # 複合動詞 (کار کردن) の語幹は軽動詞のもの。文の解析で名詞と軽動詞をまとめる
            for stem, _ in present:
                db.execute('INSERT INTO stems VALUES (?, ?, ?)', (script.key(stem), 'present', rowid))
            if past:
                db.execute('INSERT INTO stems VALUES (?, ?, ?)', (script.key(past[0]), 'past', rowid))
            for f in entry.get('forms', []):
                tags = set(f.get('tags', [])) & FORM_TAGS
                if tags and script.is_persian(f['form']) and ' ' not in f['form'].split('،')[0].strip():
                    form = f['form'].split('،')[0].strip()
                    db.execute('INSERT INTO forms VALUES (?, ?, ?)', (script.key(form), key, sorted(tags)[0]))
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
        CREATE INDEX stems_stem ON stems (stem, kind);
        CREATE INDEX forms_key ON forms (key);
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d lemmas (Japanese glosses: %d) -> %s (%.1fMB, %.0fs)' % (
        n, n_ja, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
