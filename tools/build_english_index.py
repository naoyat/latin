#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 英語 → 見出し語の逆引きの表を Wiktionary (kaikki.org の抽出データ) から作る (文の生成 dragoman/generate で、
# ラテン語などの語をロシア語・サンスクリットの語に置き換えるのに使う)
#
#   python3 tools/build_english_index.py --lang=ru
#   python3 tools/build_english_index.py --lang=sa
#
# 各行: 見出し語、品詞、英語の訳語 (語義の頭の語句を先に。読点区切り、多くて12)、性 (名詞)、語根の類 (サンスクリットの動詞)、
#       語義の数 (よく使う語ほど多い)
#   ロシア語: 見出し語はアクセント記号を除いた形 (девочка)
#   サンスクリット: 見出し語は SLP1 (kanyA)。動詞は現在3人称単数の見出し (ददाति: class 3, root दा) から語根 (dA) と類 (3) を
#
# 入力: $DRAGOMAN_DATA/ru/kaikki-Russian.jsonl.gz、$DRAGOMAN_DATA/sa/kaikki-Sanskrit.jsonl.gz (CC BY-SA)
# 出力: $DRAGOMAN_DATA/<lang>/en-index.tsv (Wiktionary 由来 (CC BY-SA))
#
import os
import re
import sys
import gzip
import json
import getopt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.core.wiktionary_import import english_glosses

POS = {'noun': 'noun', 'adj': 'adj', 'verb': 'verb', 'adv': 'adv', 'pron': 'pronoun', 'det': 'pronoun',
       'prep': 'preposition', 'conj': 'conj', 'num': 'num'}
FILES = {'ru': 'kaikki-Russian.jsonl.gz', 'sa': 'kaikki-Sanskrit.jsonl.gz'}
GENDER = re.compile(r'\b(m|f|n)\b(?: inan| anim)?')
SA_VERB = re.compile(r'class (\d+).*root (\S+?)\)')


def glosses(entry, senses, limit=12):
    """語義ごとの頭の語句を先に、残りを後に"""
    per_sense = [english_glosses(entry, [sense], limit=limit).split(',') for sense in senses]
    out = []
    for rank in range(limit):
        for chunks in per_sense:
            if rank < len(chunks) and chunks[rank] and chunks[rank] not in out:
                out.append(chunks[rank])
    return ' '.join(','.join(out[:limit]).split())


def entries(lang):
    from dragoman.russian import script as ru_script
    from dragoman.sanskrit import script as sa_script
    with gzip.open(paths.data(lang, FILES[lang]), 'rt', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            pos = POS.get(entry.get('pos'))
            if pos is None:
                continue
            senses = [s for s in entry.get('senses', []) if 'form_of' not in s and 'form-of' not in s.get('tags', [])
                      and 'alt_of' not in s]
            en = glosses(entry, senses)
            if not en:
                continue
            head = ' '.join(h.get('expansion', '') for h in entry.get('head_templates', []))
            gender, gana = '', ''
            if lang == 'ru':
                lemma = ru_script.key(entry['word'])
                if pos == 'noun':
                    m = re.search(r'\b(m|f|n)(?: inan| anim|\b)', head.split('(')[0] + ' ' + head)
                    gender = m.group(1) if m else ''
            else:
                lemma = sa_script.to_slp1(entry['word'])
                if pos == 'verb':
                    m = SA_VERB.search(head)
                    if not m:
                        continue   # 語根の分からない動詞 (派生形の見出し) は入れない
                    gana, lemma = m.group(1), sa_script.to_slp1(m.group(2))
                elif pos in ('noun', 'adj'):
                    m = re.search(r'stem, (m|f|n)\b', head)
                    gender = m.group(1) if m else ''
            yield lemma, pos, en, gender, gana, len(senses)


def main():
    opts, _ = getopt.getopt(sys.argv[1:], '', ['lang='])
    lang = dict(opts).get('--lang', 'ru')
    out = paths.data(lang, 'en-index.tsv')
    seen = set()
    n = 0
    with open(out, 'w', encoding='utf-8') as f:
        for lemma, pos, en, gender, gana, senses in entries(lang):
            if (lemma, pos, gana, en) in seen:
                continue
            seen.add((lemma, pos, gana, en))
            f.write('\t'.join((lemma, pos, en, gender, gana, str(senses))) + '\n')
            n += 1
    print('%d entries → %s' % (n, out))


if __name__ == '__main__':
    main()
