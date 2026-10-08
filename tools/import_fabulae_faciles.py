#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Ritchie's Fabulae Faciles (Project Gutenberg #8997) を texts/fabulae_faciles/ に取り込む
#
#   curl -L -o ~/.local/share/dragoman-data/fabulae-faciles-pg8997.txt \
#        https://www.gutenberg.org/cache/epub/8997/pg8997.txt
#   python3 tools/import_fabulae_faciles.py
#
# - 長音はアキュート記号で表されているのでマクロンに置き換える (á → ā)
# - 物語ごとの英語の導入文、英語の章題、挿絵の注記は除く
# - 綴りは原文のまま (consonantal i は j に変えない: Iuppiter, iuvenis)
#
import os
import re
import sys
from core import paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = paths.DATA_DIR
SOURCE = os.path.join(DATA_DIR, 'fabulae-faciles-pg8997.txt')
OUT_DIR = os.path.join(ROOT, 'texts', 'fabulae_faciles')

STORIES = [('PERSEUS', 'perseus'), ('HERCULES', 'hercules'),
           ('THE ARGONAUTS', 'argonautae'), ('ULYSSES', 'ulixes')]
ACUTE_TO_MACRON = str.maketrans('áéíóúýÁÉÍÓÚÝ', 'āēīōūȳĀĒĪŌŪȲ')


def story_bodies(lines):
    """本文中の物語の見出し (2回目に現れるもの。1回目は目次) から NOTES までを物語ごとに分ける"""
    start = next(i for i, line in enumerate(lines) if line.startswith('*** START OF'))
    notes = next(i for i in range(start, len(lines)) if lines[i].strip() == 'NOTES' and i > start + 300)
    heads = []
    for title, name in STORIES:
        found = [i for i in range(start, notes) if lines[i].strip() == title]
        heads.append((found[-1], name))
    heads.append((notes, None))
    for (begin, name), (end, _) in zip(heads, heads[1:]):
        yield name, lines[begin + 1:end]


def chapters(body):
    """'1. _THE ARK_' で始まる章ごとに本文の段落を返す (英語の導入文は最初の章より前にある)"""
    current = None
    for line in body:
        if re.match(r'^(\d+|[IVXL]+)\. _.*_\s*$', line):  # 原文に 'II.' (11章) の誤記がある
            if current:
                yield current
            current = []
        elif current is not None and not line.startswith('[Illustration'):
            current.append(line.strip())
    if current:
        yield current


def convert(paragraph_lines):
    text = ' '.join(line for line in paragraph_lines if line)
    text = text.translate(ACUTE_TO_MACRON)
    return re.sub(r'\s+', ' ', text).strip()


def main():
    if not os.path.exists(SOURCE):
        sys.exit('not found: %s' % SOURCE)
    with open(SOURCE, encoding='utf-8') as fp:
        lines = fp.read().split('\n')
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, body in story_bodies(lines):
        texts = [convert(chapter) for chapter in chapters(body)]
        path = os.path.join(OUT_DIR, name + '.txt')
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write('\n\n'.join(texts) + '\n')
        print('%-12s %3d chapters, %5d words -> %s' % (
            name, len(texts), sum(len(t.split()) for t in texts), os.path.relpath(path, ROOT)))


if __name__ == '__main__':
    main()
