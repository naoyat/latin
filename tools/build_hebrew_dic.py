#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語の辞書 (SQLite) を作る
#
#   python3 tools/build_hebrew_dic.py
#
# 入力 ($LATIN_DATA/he/):
#   oshb/*.xml        Open Scriptures Hebrew Bible (https://github.com/openscriptures/morphhb の wlc/)。
#                     本文は Westminster Leningrad Codex (パブリックドメイン)、語形の解析は CC BY 4.0
#   lexicon/          https://github.com/openscriptures/HebrewLexicon の AugIndex.xml, LexicalIndex.xml, HebrewStrong.xml
#                     (Strong の辞書・BDB の索引)
#   kaikki-Hebrew.jsonl.gz, ../ja-extract.jsonl.gz   Wiktionary (日本語訳・語源。任意)
# 出力:
#   hebrew.sqlite
#     forms   (key: 朗唱記号を除いた語形, cons: 子音だけ, segments, lemmas, morph, count)
#     lexicon (aug: 見出し語の番号 → 語・転写・品詞・語義・日本語訳・語根)
#     verbs   (語根・態・時制の型・人称性数 → 動詞の形と回数。態の型の表 hebrew/binyan.py に使う)
#
import os
import re
import sys
import glob
import gzip
import json
import sqlite3
import time
import collections
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hebrew import dictionary, script
from core.wiktionary_import import japanese_gloss, descendants_summary, etymology_summary

OSIS = '{http://www.bibletechnologies.net/2003/OSIS/namespace}'
LEMMA_PREFIXES = set('cdlbmkis')  # 接頭辞の見出し: 接続詞 ו、冠詞 ה、前置詞 ל ב מ כ、疑問の ה、関係詞 ש
DESCENDANT_LANGS = ('en', 'ja', 'el', 'la', 'ar')
WIKTIONARY_POS = {'N': ('noun', 'name'), 'Np': ('name', 'noun'), 'V': ('verb',), 'A': ('adj',), 'D': ('adv',),
                  'P': ('pron',), 'R': ('prep',), 'C': ('conj',)}


def text_of(element):
    return ''.join(element.itertext())


def load_lexical_index(path):
    """id → {word, xlit, pos, def, strong, root}。語根 (root) は項目の etym の root、無ければ派生元 (type="sub") を
    たどる (אָב → אבה)"""
    out, parents = {}, {}
    for entry in ET.parse(path).getroot().iter():
        if not entry.tag.endswith('entry'):
            continue
        get = lambda name: next((c for c in entry if c.tag.endswith(name)), None)
        w, pos, d, xref, etym = get('w'), get('pos'), get('def'), get('xref'), get('etym')
        out[entry.get('id')] = {'word': text_of(w) if w is not None else '', 'xlit': w.get('xlit') if w is not None else '',
                                'pos': text_of(pos) if pos is not None else '', 'def': text_of(d) if d is not None else '',
                                'strong': xref.get('strong') if xref is not None else None,
                                'root': etym.get('root') if etym is not None else None}
        if etym is not None and etym.get('type') == 'sub' and etym.text:
            parents[entry.get('id')] = etym.text.split(',')[0].strip()
    for id_, entry in out.items():
        seen = set()
        parent = parents.get(id_)
        while not entry['root'] and parent and parent not in seen:
            seen.add(parent)
            entry['root'] = out.get(parent, {}).get('root')
            parent = parents.get(parent)
    return out


def load_strong(path):
    """番号 (1254) → [定義の語]"""
    out = {}
    for entry in ET.parse(path).getroot().iter():
        if not entry.tag.endswith('entry'):
            continue
        defs = [text_of(d).strip() for d in entry.iter() if d.tag.endswith('def')]
        out[entry.get('id', '').lstrip('H')] = [d for d in defs if d]
    return out


def load_japanese(path):
    """子音だけの見出し語 → [(品詞, 日本語訳)]"""
    out = collections.defaultdict(list)
    if os.path.exists(path):
        with gzip.open(path, 'rt') as fp:
            for line in fp:
                if '"lang_code": "he"' not in line:
                    continue
                entry = json.loads(line)
                gloss = japanese_gloss(entry)
                if gloss:
                    short = [g for g in gloss.split(',') if len(g) <= 12 and ':w:' not in g and '→' not in g]
                    if short:
                        out[script.consonants(entry['word'])].append((entry.get('pos'), ','.join(short)))
    return out


def lemma_ids(lemma):
    """OSHB の lemma ("c/d/776", "1254 a") → 切れ目ごとの番号 (接頭辞は文字のまま)"""
    out = []
    for part in lemma.split('/'):
        part = part.strip()
        if part in LEMMA_PREFIXES:
            out.append(part)
        else:
            out.append(re.sub(r'[\s+]', '', part))
    return out


def main():
    t0 = time.time()
    base = dictionary.DATA_DIR
    aug_index = {w.get('aug'): w.text for w in ET.parse(os.path.join(base, 'lexicon', 'AugIndex.xml')).getroot().iter()
                 if w.get('aug')}
    lexical = load_lexical_index(os.path.join(base, 'lexicon', 'LexicalIndex.xml'))
    strong = load_strong(os.path.join(base, 'lexicon', 'HebrewStrong.xml'))
    ja = load_japanese(os.path.join(os.path.dirname(base), 'ja-extract.jsonl.gz'))

    forms = collections.Counter()
    used = set()
    for path in sorted(glob.glob(os.path.join(base, 'oshb', '*.xml'))):
        for w in ET.parse(path).getroot().iter(OSIS + 'w'):
            text, lemma, morph = text_of(w), w.get('lemma'), w.get('morph')
            if not text or not lemma or not morph:
                continue
            segments = [script.pointed(s) for s in text.split('/')]
            ids = lemma_ids(lemma)
            used.update(i for i in ids if i not in LEMMA_PREFIXES)
            forms[(script.pointed(text.replace('/', '')), tuple(segments), tuple(ids), morph)] += 1

    out = dictionary.DB_PATH
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE forms (key TEXT, cons TEXT, segments TEXT, lemmas TEXT, morph TEXT, count INTEGER);
        CREATE TABLE lexicon (aug TEXT PRIMARY KEY, word TEXT, xlit TEXT, pos TEXT, ja TEXT, gloss_lang TEXT, strong TEXT,
                              root TEXT);
        CREATE TABLE verbs (root TEXT, lemma TEXT, stem TEXT, type TEXT, pgn TEXT, form TEXT, lang TEXT, count INTEGER,
                            bare INTEGER);
        CREATE TABLE descendants (lemma TEXT, pos TEXT, data TEXT);
        CREATE TABLE etymology (lemma TEXT, pos TEXT, data TEXT);
    ''')
    for (key, segments, ids, morph), n in forms.items():
        db.execute('INSERT INTO forms VALUES (?, ?, ?, ?, ?, ?)',
                   (key, script.consonants(key), json.dumps(segments, ensure_ascii=False),
                    json.dumps(ids), morph, n))
    # 動詞の形 (語根ごと)
    verbs = collections.Counter()
    for (key, segments, ids, morph), n in forms.items():
        codes = morph[1:].split('/')
        for k, code in enumerate(codes):
            if not code.startswith('V') or k >= len(segments) or k >= len(ids):
                continue
            entry = lexical.get(aug_index.get(ids[k], ''), {})
            root = script.consonants(entry.get('root') or entry.get('word') or '')
            if not root:
                continue
            stem, vtype, rest = code[1:2], code[2:3], code[3:]
            bare = k == 0 and k == len(codes) - 1  # 接頭辞 (ו など) も人称接尾辞も付いていない語
            verbs[(root, ids[k], stem, vtype, rest, segments[k], morph[:1], bare)] += n
    for (root, lemma, stem, vtype, pgn, form, lang, bare), n in verbs.items():
        db.execute('INSERT INTO verbs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (root, lemma, stem, vtype, pgn, form, lang, n, int(bare)))
    n_ja = 0
    for aug in sorted(used):
        entry = lexical.get(aug_index.get(aug, ''), None)
        number = re.sub(r'[a-z]$', '', aug)
        if entry is None:
            continue
        defs = [entry['def']] if entry['def'] else []
        defs += [d for d in strong.get(number, []) if d not in defs][:3]
        gloss, gloss_lang = ','.join(defs[:4]) or entry['word'], 'en'
        kinds = WIKTIONARY_POS.get(entry['pos'][:2], WIKTIONARY_POS.get(entry['pos'][:1], ()))
        for pos, j in ja.get(script.consonants(entry['word']), []):
            if not kinds or pos in kinds:
                gloss, gloss_lang = j, 'ja'
                n_ja += 1
                break
        db.execute('INSERT OR REPLACE INTO lexicon VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                   (aug, script.pointed(entry['word']), entry['xlit'], entry['pos'], gloss, gloss_lang, number,
                    entry['root']))
    kaikki = os.path.join(base, 'kaikki-Hebrew.jsonl.gz')
    if os.path.exists(kaikki):
        with gzip.open(kaikki, 'rt') as fp:
            for line in fp:
                entry = json.loads(line)
                if entry.get('lang_code') != 'he':
                    continue
                key = script.consonants(entry['word'])
                if entry.get('descendants'):
                    summary = descendants_summary(entry, DESCENDANT_LANGS, set())
                    if summary:
                        db.execute('INSERT INTO descendants VALUES (?, ?, ?)',
                                   (key, entry.get('pos'), json.dumps(summary, ensure_ascii=False)))
                if entry.get('etymology_text') or entry.get('etymology_templates'):
                    summary = etymology_summary(entry)
                    if summary:
                        db.execute('INSERT INTO etymology VALUES (?, ?, ?)',
                                   (key, entry.get('pos'), json.dumps(summary, ensure_ascii=False)))
    db.executescript('''
        CREATE INDEX forms_key ON forms (key);
        CREATE INDEX forms_cons ON forms (cons);
        CREATE INDEX verbs_root ON verbs (root);
        CREATE INDEX descendants_lemma ON descendants (lemma);
        CREATE INDEX etymology_lemma ON etymology (lemma);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d forms, %d lemmas (Japanese glosses: %d) -> %s (%.1fMB, %.0fs)' % (
        len(forms), len(used), n_ja, out, os.path.getsize(out) / 1e6, time.time() - t0))


if __name__ == '__main__':
    main()
