#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# RFTagger による品詞タグ付け (Latin Dependency Treebank で学習したモデル)
#
#   tag_sentences([['Puella', 'in', 'silva', 'ambulat', '.']])
#     → [['n-s---fn-', 'r--------', 'n-s---fb-', 'v3spia---', 'u--------']]
#
# モデルは Latin Macronizer に同梱の rftagger-ldt.model を使う。
# RFTagger (https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/) は別途ビルドが必要
# (教育・研究・評価目的なら無償)。どちらかが無ければ available() が False になる
#
import os
import subprocess
import tempfile

DATA_DIR = os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data'))
RFTAGGER = os.environ.get('LATIN_RFTAGGER', os.path.join(DATA_DIR, 'RFTagger', 'src', 'rft-annotate'))
MODEL = os.environ.get('LATIN_RFTAGGER_MODEL',
                       os.path.join(DATA_DIR, 'latin-macronizer', 'latin_macronizer', 'rftagger-ldt.model'))


def available():
    return os.path.exists(RFTAGGER) and os.path.exists(MODEL)


def _tagger_tokens(word):
    """タガーに渡す形: マクロンを外し、全部大文字なら小文字にし、-que は前に切り出す (LDT の流儀)"""
    from .macronizer import strip_macrons, ENCLITIC_EXCEPTIONS  # macronizer がこのモジュールを使うので遅延 import
    word = strip_macrons(word)
    if word.isupper() and len(word) > 1:
        word = word.lower()
    lower = word.lower()
    if lower.endswith('que') and len(word) > 3 and lower not in ENCLITIC_EXCEPTIONS:
        return ['que', word[:-3]], 1  # タグは本体 (2番目) のものを使う
    return [word], 0


def tag_sentences(sentences):
    """文 (語のリスト) のリストに品詞タグを付ける。タグを付けられなかった語は None"""
    if not available():
        return [[None] * len(s) for s in sentences]
    lines = []
    picks = []  # 各語のタグが出力の何行目にあるか
    for sentence in sentences:
        sentence_picks = []
        for word in sentence:
            tokens, which = _tagger_tokens(word)
            sentence_picks.append(len(lines) + which)
            lines.extend(tokens)
        lines.append('')
        picks.append(sentence_picks)
    with tempfile.TemporaryDirectory() as tmp:
        inp, out = os.path.join(tmp, 'in.txt'), os.path.join(tmp, 'out.txt')
        with open(inp, 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(lines) + '\n')
        subprocess.run([RFTAGGER, '-s', '-q', MODEL, inp, out], check=True)
        with open(out, encoding='utf-8') as fp:
            output = fp.read().split('\n')
    tags = []
    for line in output:
        if '\t' in line:
            tags.append(line.split('\t')[1].replace('.', ''))
        else:
            tags.append(None)  # 文の区切り (入力の空行に対応)
    return [[tags[k] if k < len(tags) else None for k in sentence_picks] for sentence_picks in picks]
