#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) からアラビア語の見出し語の辞書 (SQLite) を作る
#
#   python3 tools/build_arabic_dic.py
#
# 語形の解析は CAMeL Tools (形態素辞書 calima-msa-r13) が行うので、ここでは見出し語ごとの品詞・訳語・
# 動詞の型 (I〜X)・語根・語源・子孫語だけを持つ。
#
# 入力 ($LATIN_DATA/ar/):
#   kaikki-Arabic.jsonl.gz   https://kaikki.org/dictionary/Arabic/kaikki.org-dictionary-Arabic.jsonl.gz
#   ../ja-extract.jsonl.gz   日本語の訳語 (任意。アラビア語の項目と、日本語の項目の訳語の表のアラビア語)
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

from arabic import dictionary, script
from core.wiktionary_import import (english_glosses, japanese_gloss, descendants_summary, etymology_summary,
                                   japanese_translation_pairs)

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'pronoun',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'prep': 'preposition', 'intj': 'intj'}
# 子孫語として集める言語 (アラビア語からの借用) と、アラビア語から語を継承しうる言語 (マルタ語など。ここでは無し)
DESCENDANT_LANGS = ('en', 'ja', 'fa', 'tr', 'es', 'pt', 'sw', 'ur', 'hi', 'ms', 'id', 'fr', 'de', 'it')
INHERITING = set()
VERB_FORM = re.compile(r'^(I{1,3}|IV|V|VI{1,3}|IX|X|XI{1,3}|XIV|XV|Iq|IIq|IIIq|IVq)\b')


def load_japanese_glosses(path):
    glosses = {}
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "ar"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss and entry.get('pos') in POS:
                    glosses.setdefault((script.normalize(entry['word']), POS[entry['pos']]), gloss)
    return glosses


def translation_gloss(pairs, vocalized):
    """訳語の表の日本語のうち、母音記号が見出し語と合うもの (母音記号の無いものはどれとも合う)"""
    from arabic.morphology import lex_key
    found = [ja for word, ja in pairs if not script.has_diacritics(word) or lex_key(word) == lex_key(vocalized)]
    return ','.join(found[:4]) or None


def verb_form(entry):
    """動詞の型 ('I' 〜 'X'。四語根は 'Iq' など)"""
    for t in entry.get('head_templates', []):
        if t.get('name') == 'ar-verb':
            m = VERB_FORM.match(t.get('args', {}).get('1', ''))
            if m:
                return m.group(1)
    for f in entry.get('forms', []):
        for tag in f.get('tags', []):
            if tag.startswith('form-'):
                return tag[5:].upper().replace('Q', 'q')
    return None


def root_of(entry):
    """語根 (ك ت ب → كتب)"""
    for t in entry.get('etymology_templates') or []:
        args = t.get('args', {})
        if t['name'] in ('ar-rootbox', 'ar-root') and args.get('1'):
            return args['1'].replace(' ', '')
        if t['name'] == 'ety' and args.get('2') == ':root' and args.get('3'):
            return args['3'].replace(' ', '')
    return None


def canonical(entry):
    return next((f['form'] for f in entry.get('forms', []) if 'canonical' in f.get('tags', [])), entry['word'])


def main():
    t0 = time.time()
    ja_path = os.path.join(os.path.dirname(dictionary.DATA_DIR), 'ja-extract.jsonl.gz')
    ja = load_japanese_glosses(ja_path)
    translations = japanese_translation_pairs(ja_path, 'ar', script.normalize, POS)
    used = set()
    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, word TEXT, form TEXT, root TEXT,
                             senses INTEGER);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    n = n_ja = 0
    with gzip.open(os.path.join(dictionary.DATA_DIR, 'kaikki-Arabic.jsonl.gz'), 'rt') as fp:
        for line in fp:
            entry = json.loads(line)
            if entry.get('lang_code') != 'ar' or entry.get('pos') not in POS:
                continue
            senses = entry.get('senses', [])
            if not senses or all('form_of' in s or 'alt_of' in s for s in senses):
                continue
            key = script.normalize(entry['word'])
            pos = POS[entry['pos']]
            # 日本語の訳語は綴りと品詞が同じ項目のうち最初のもの (動詞の I 型が II 型より先) にだけ付ける
            gloss = ja.pop((key, pos), None)
            if gloss:  # 長い日本語の訳語は説明文 (ほかに訳語があれば落とす)
                short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                gloss = ','.join(short) if short else None
            if not gloss and (key, pos) in translations and (key, pos) not in used:
                gloss = translation_gloss(translations[(key, pos)], canonical(entry))
                if gloss:
                    used.add((key, pos))  # 同じ綴り・品詞の項目のうち最初のもの (母音が合うもの) にだけ
            gloss_lang = 'ja' if gloss else 'en'
            gloss = gloss or english_glosses(entry)
            if not gloss:
                continue
            n_ja += gloss_lang == 'ja'
            db.execute('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (key, pos, gloss, gloss_lang, canonical(entry), verb_form(entry) if pos == 'verb' else None,
                        root_of(entry), len(senses)))
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
