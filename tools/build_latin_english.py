#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語の見出し語 → 英語の訳語の表を Wiktionary (kaikki.org の抽出データ) から作る (文の生成 dragoman/generate で使う)
#
#   python3 tools/build_latin_english.py
#
# 見出し語はマクロン付きの形 (videō, līber)。語義のうち変化形の説明 (first-person singular … of) は除く。
# 訳語は語義ごとの頭の語句を先に並べる (文の生成では、解析の日本語の訳語に合うものを選ぶ)。
#
# 入力: $DRAGOMAN_DATA/kaikki-Latin.jsonl.gz (https://kaikki.org/dictionary/Latin/。CC BY-SA)
# 出力: $DRAGOMAN_DATA/la-en.tsv (見出し語、品詞、英語の訳語 (読点区切り、多くて12)、動詞の基本形。同綴の語は別の行。
#       Wiktionary 由来 (CC BY-SA))
#
import os
import sys
import gzip
import json
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.core.wiktionary_import import english_glosses

POS = {'noun': 'noun', 'name': 'noun', 'adj': 'adj', 'verb': 'verb', 'adv': 'adv', 'prep': 'preposition',
       'pron': 'pronoun', 'det': 'pronoun', 'conj': 'conj', 'num': 'num', 'particle': 'adv'}


def _glosses(entry, senses, limit=12):
    """語義ごとの頭の語句を先に、残りを後に (magister: master, teacher, … 。2つめの語義の teacher も拾う)"""
    per_sense = [english_glosses(entry, [sense], limit=limit).split(',') for sense in senses]
    out = []
    for rank in range(limit):
        for chunks in per_sense:
            if rank < len(chunks) and chunks[rank] and chunks[rank] not in out:
                out.append(chunks[rank])
    return ' '.join(','.join(out[:limit]).split())   # 語義の中の改行・タブは空白に


PART = re.compile(r'(?:present infinitive|perfect active|supine) (\S+?)[,;)]')


def _principal_parts(entry):
    """動詞の基本形 (不定詞・完了・目的分詞): 'volāre volāvī volātum'。同綴の語を語形で見分けるのに使う"""
    head = ' '.join(h.get('expansion', '') for h in entry.get('head_templates', []))
    return ' '.join(PART.findall(head))


def main():
    src = paths.data('kaikki-Latin.jsonl.gz')
    out = paths.data('la-en.tsv')
    rows = {}
    with gzip.open(src, 'rt', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            pos = POS.get(entry.get('pos'))
            if pos is None:
                continue
            senses = [s for s in entry.get('senses', []) if 'form_of' not in s and 'form-of' not in s.get('tags', [])]
            en = _glosses(entry, senses)
            if not en:
                continue
            canonical = [f['form'] for f in entry.get('forms', []) if 'canonical' in f.get('tags', [])]
            lemma = canonical[0] if canonical and ' ' not in canonical[0] else entry['word']
            parts = _principal_parts(entry) if pos == 'verb' else ''
            if (en, parts) not in rows.setdefault((lemma, pos), []):
                rows[(lemma, pos)].append((en, parts))   # 同綴の語 (volō「望む」と volō「飛ぶ」) は別の行に
    with open(out, 'w', encoding='utf-8') as f:
        for (lemma, pos), entries in sorted(rows.items()):
            for en, parts in entries:
                f.write('%s\t%s\t%s\t%s\n' % (lemma, pos, en, parts))
    print('%d entries → %s' % (len(rows), out))


if __name__ == '__main__':
    main()
