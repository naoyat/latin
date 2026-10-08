#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# D'Ooge, Latin for Beginners (Project Gutenberg #18251) の読み物を texts/dooge/ に取り込む
#
#   curl -L -o ~/.local/share/dragoman-data/dooge-pg18251.txt \
#        https://www.gutenberg.org/cache/epub/18251/pg18251.txt
#   python3 tools/import_dooge.py
#
# - 巻末の READING MATTER の2つの読み物 (ヘラクレスの功業、レントゥルスの物語) を取り込む
# - 英語の見出し・説明の段落、脚注、挿絵の注記、脚注の印 ([1])、強勢の記号 (´)、短音記号 (ĕ) を除く
# - 綴りは原文のまま
#
import os
import re
import sys
import unicodedata
from core import paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = paths.DATA_DIR
SOURCE = os.path.join(DATA_DIR, 'dooge-pg18251.txt')
OUT_DIR = os.path.join(ROOT, 'texts', 'dooge')

STORIES = [('THE LABORS OF HERCULES', 'hercules'),
           ('P. CORNELIUS LENTULUS: THE STORY OF A ROMAN BOY', 'lentulus')]
END = 'APPENDIX I'
ENGLISH_WORDS = {'the', 'and', 'of', 'to', 'is', 'in', 'a', 'was', 'he', 'his', 'with', 'for', 'that',
                 'as', 'on', 'by', 'it', 'be', 'this', 'which', 'are', 'from', 'an', 'at', 'or'}


def is_latin(paragraph):
    words = re.findall(r"[A-Za-z]+", paragraph)
    if len(words) < 3:
        return False
    english = sum(1 for w in words if w.lower() in ENGLISH_WORDS)
    return english / len(words) < 0.08


def clean(paragraph):
    text = ' '.join(line.strip() for line in paragraph.split('\n'))
    text = re.sub(r'\[\d+\]', '', text)                    # 脚注の印
    text = text.replace('´', '').replace('́', '')      # 強勢の記号
    text = text.replace('·', ' ').replace('_', '')        # 中黒、斜体の印
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    # 短音記号 (ĕ, ă ...) を外す。マクロンは残す
    nfd = unicodedata.normalize('NFD', text)
    text = unicodedata.normalize('NFC', nfd.replace('̆', ''))
    return re.sub(r'\s+', ' ', text).strip()


def stories(lines):
    reading = max(i for i, line in enumerate(lines) if line.strip() == 'READING MATTER')
    end = next(i for i in range(reading, len(lines)) if lines[i].strip() == END)
    heads = []
    for title, name in STORIES:
        # 本文の見出しには脚注の印が付いていることがある ('...ROMAN BOY[1]')
        heads.append((next(i for i in range(reading, end)
                            if re.sub(r'\[\d+\]', '', lines[i]).strip() == title), name))
    heads.append((end, None))
    for (begin, name), (stop, _) in zip(heads, heads[1:]):
        yield name, lines[begin + 1:stop]


def paragraphs(lines):
    """空行で区切った段落のうち、脚注・挿絵・見出し (大文字だけの行) を除いたもの"""
    block = []
    for line in lines + ['']:
        if line.strip():
            block.append(line)
            continue
        if block:
            text = '\n'.join(block)
            first = block[0].strip()
            if not (first.startswith('[Footnote') or first.startswith('[Illustration')
                    or block[0].startswith('    ') or text.upper() == text):
                yield text
            block = []


def main():
    if not os.path.exists(SOURCE):
        sys.exit('not found: %s' % SOURCE)
    with open(SOURCE, encoding='utf-8') as fp:
        lines = fp.read().replace('\r\n', '\n').split('\n')
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, body in stories(lines):
        texts = [clean(p) for p in paragraphs(body) if is_latin(p)]
        path = os.path.join(OUT_DIR, name + '.txt')
        with open(path, 'w', encoding='utf-8') as fp:
            fp.write('\n\n'.join(texts) + '\n')
        print('%-10s %3d paragraphs, %5d words -> %s' % (
            name, len(texts), sum(len(t.split()) for t in texts), os.path.relpath(path, ROOT)))


if __name__ == '__main__':
    main()
