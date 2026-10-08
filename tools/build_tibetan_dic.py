#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の辞書 (SQLite) を作る
#
#   python3 tools/build_tibetan_dic.py
#
# 見出し語はワイリー式 (EWTS)。訳語 (英語) は Wiktionary → Hopkins → Rangjung Yeshe の順に使い、日本語には実行時に
# core/en_ja.py で直す。品詞は Hill & Garrett の品詞辞書 (チベット文字の見出し語をワイリー式に直す) と Wiktionary から、
# 動詞の語幹 (現在・過去・未来・命令) は Wiktionary の活用表と Rangjung Yeshe の「pf. of {sgrub pa}」などの項目から。
# サンスクリットの原語は Mahāvyutpatti (翻訳名義大集) と Hopkins の梵語の表から。
#
# 入力 ($DRAGOMAN_DATA/bo/):
#   kaikki/kaikki.org-dictionary-Tibetan.jsonl   https://kaikki.org/dictionary/Tibetan/ (CC BY-SA)
#   hill/lex/Lexicons/classical-lexicon.txt      Hill & Garrett 2017, doi:10.5281/zenodo.574876 (CC BY 4.0)
#   dict/01-Hopkins2015, 02-RangjungYeshe, 15-Hopkins-Skt2015, 21-Mahavyutpatti-Skt
#       https://github.com/christiansteinert/tibetan-dictionary (辞書の著作権はそれぞれの著者。手元だけで使う)
# 出力:
#   tibetan.sqlite (手元だけで使う。リポジトリにも公開の場所にも置かない)
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
from dragoman.tibetan import script

DIR = paths.data('bo')
KAIKKI_POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'det',
              'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'postp': 'postposition',
              'intj': 'intj'}
STEM_TAGS = {'present': 'pres', 'past': 'past', 'future': 'fut', 'imperative': 'imp'}
RY_STEM = re.compile(r"\b(pf|p|ft|f|imp)\.? of \{([^}]+)\}")
RY_TENSE = {'pf': 'past', 'p': 'past', 'ft': 'fut', 'f': 'fut', 'imp': 'imp'}


def verb_root(wylie):
    """動名詞の見出し (sgrub pa, 'gro ba) → 語幹 (sgrub, 'gro)"""
    return re.sub(r" (pa|ba|po|bo)$", '', wylie.strip())


def clean_glosses(text, limit=3):
    """Hopkins・Rangjung Yeshe の語義 → 短い英語の語句 (カンマ区切り)"""
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[[^]]*\]|\([^)]*\)', '', text)
    text = re.sub(r'\b(verb|noun|adj|adjective|adverb):', ';', text)
    text = re.sub(r'\b(Syn|Skt|Def|See|cf|abbr|epith|n|p|pf|f|ft|imp|Tantra)\b\.?.*?(;|$)', ';', text)
    out = []
    for chunk in re.split(r'[;,]|\d\)|\\n', text):
        chunk = re.sub(r'^(to|a|an|the) ', '', chunk.strip().strip('.:-= '), flags=re.I).strip()
        if not chunk or len(chunk.split()) > 3 or not re.fullmatch(r"[A-Za-z' -]+", chunk) or chunk in out:
            continue
        out.append(chunk.lower())
        if len(out) >= limit:
            break
    return ','.join(out)


def read_pipe(path):
    with open(path, encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                head, body = line.rstrip('\n').split('|', 1)
                yield head.strip(), body


def hill_pos(tags):
    """Hill & Garrett の品詞 → 大まかな品詞"""
    for t in tags:
        if t.startswith('v.') or t in ('v.cop', 'v.aux'):
            return 'verb'
    for t in tags:
        if t == 'adj':
            return 'adj'
        if t.startswith('n.v.'):
            return 'verbal_noun'
        if t.startswith('n.prop'):
            return 'name'
        if t.startswith(('n.', 'p.')):
            return 'noun' if t.startswith('n.') else 'pronoun'
        if t.startswith(('num', 'numeral')):
            return 'num'
        if t.startswith('adv'):
            return 'adv'
    return None


def main():
    t0 = time.time()
    out = os.path.join(DIR, 'tibetan.sqlite')
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE words (wylie TEXT, pos TEXT, en TEXT, source TEXT, rank INTEGER);
        CREATE TABLE stems (form TEXT, lemma TEXT, tense TEXT, source TEXT);
        CREATE TABLE sanskrit (wylie TEXT, skt TEXT, source TEXT);
        CREATE TABLE tags (wylie TEXT, tags TEXT);
    ''')
    words, stems, sanskrit = [], set(), []
    pos_of = {}

    # Hill & Garrett の品詞辞書
    hill = os.path.join(DIR, 'hill', 'lex', 'Lexicons', 'classical-lexicon.txt')
    tag_rows = {}
    for line in open(hill, encoding='utf-8'):
        cols = line.rstrip('\n').split('\t')
        if len(cols) < 2 or not script.is_tibetan(cols[0]):
            continue
        wylie = script.word_translit(cols[0])
        tags = [c.replace(' -', '').strip() for c in cols[1:] if c.strip()]
        tag_rows.setdefault(wylie, set()).update(tags)
    for wylie, tags in tag_rows.items():
        p = hill_pos(sorted(tags))
        if p:
            pos_of[wylie] = p
    db.executemany('INSERT INTO tags VALUES (?, ?)', [(w, ' '.join(sorted(t))) for w, t in tag_rows.items()])

    # Wiktionary
    kaikki = os.path.join(DIR, 'kaikki', 'kaikki.org-dictionary-Tibetan.jsonl')
    for line in open(kaikki, encoding='utf-8'):
        entry = json.loads(line)
        pos = KAIKKI_POS.get(entry.get('pos'))
        if pos is None or not script.is_tibetan(entry['word']):
            continue
        wylie = script.word_translit(entry['word'])
        en = english_glosses(entry)
        if en:
            words.append((wylie, pos, en, 'wiktionary', 0))
        pos_of.setdefault(wylie, pos)
        if pos == 'verb':
            for f in entry.get('forms', []):
                tense = next((STEM_TAGS[t] for t in f.get('tags', []) if t in STEM_TAGS), None)
                if tense and f.get('source') == 'conjugation' and script.is_tibetan(f['form']):
                    stems.add((script.word_translit(f['form']), wylie, tense, 'wiktionary'))

    # Hopkins・Rangjung Yeshe
    for name, source, rank in (('01-Hopkins2015', 'hopkins', 1), ('02-RangjungYeshe', 'rangjung_yeshe', 2)):
        path = os.path.join(DIR, 'dict', name)
        if not os.path.exists(path):
            continue
        for head, body in read_pipe(path):
            for m in RY_STEM.finditer(body):
                stems.add((verb_root(head), verb_root(m.group(2)), RY_TENSE[m.group(1)], source))
            en = clean_glosses(body)
            if en:
                words.append((head, pos_of.get(head, pos_of.get(verb_root(head), '')), en, source, rank))

    # サンスクリットの原語
    for name, source in (('21-Mahavyutpatti-Skt', 'mahavyutpatti'), ('15-Hopkins-Skt2015', 'hopkins')):
        path = os.path.join(DIR, 'dict', name)
        if not os.path.exists(path):
            continue
        for head, body in read_pipe(path):
            skt = re.sub(r'\[[^]]*\]', '', body).split(';')[0].strip()
            if skt:
                sanskrit.append((head, skt, source))

    db.executemany('INSERT INTO words VALUES (?, ?, ?, ?, ?)', words)
    db.executemany('INSERT INTO stems VALUES (?, ?, ?, ?)', sorted(stems))
    db.executemany('INSERT INTO sanskrit VALUES (?, ?, ?)', sanskrit)
    db.executescript('''
        CREATE INDEX words_wylie ON words (wylie);
        CREATE INDEX stems_form ON stems (form);
        CREATE INDEX sanskrit_wylie ON sanskrit (wylie);
        CREATE INDEX tags_wylie ON tags (wylie);
    ''')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d glosses, %d stems, %d Sanskrit, %d POS → %s (%.1fs)' % (
        len(words), len(stems), len(sanskrit), len(tag_rows), out, time.time() - t0))


if __name__ == '__main__':
    main()
