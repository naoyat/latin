#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析の結果 (格の枠) から文を作り直す試み: ラテン語 → 文の枠 → 英語・ラテン語
#
#   python3 tools/generate.py "Puella rosam pulchram in hortō videt."
#   python3 tools/generate.py samples/latin.txt
#
# ラテン語に戻した文が元の文と同じ語 (順序は問わない) になれば ✓。違えば、違う語を出す。
# ファイルは1行1文 (# で始まる行は飛ばす。samples/samples.txt の形)
#
import os
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.latin import analyzer, latindic
from dragoman.generate import frame, english, latin


def _word_list(text):
    text = unicodedata.normalize('NFC', text)
    return [w.strip('.,;:!?"“”()').lower() for w in text.split() if w.strip('.,;:!?"“”()')]


def _normal(text):
    """綴りの流儀をそろえる: マクロンを外し、j → i、v → u"""
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.replace('j', 'i').replace('J', 'I').replace('v', 'u').replace('V', 'U')


def _words(text):
    return Counter(_word_list(text))


def run(text):
    for analysis in analyzer.analyze_text(text):
        print(analysis.text)
        clauses = frame.frames(analysis)
        if not clauses:
            print('  (述語が見つからない)\n')
            continue
        for clause in clauses:
            print(frame.describe(clause))
        print('  英語:     ' + english.sentence(clauses))
        regenerated = latin.sentence(clauses)
        original, again = _words(analysis.text), _words(regenerated)
        if original != again and _words(_normal(analysis.text)) == _words(_normal(regenerated)):
            mark = '✓ 綴りの違いだけ (マクロン・i/j・u/v)'
        elif original == again:
            mark = '✓ 同じ語' + (' (語順も同じ)' if _word_list(regenerated) == _word_list(analysis.text) else '')
        else:
            mark = '✗ 元にだけある語: %s / 作った文にだけある語: %s' % (
                ' '.join(sorted((original - again).elements())) or '-',
                ' '.join(sorted((again - original).elements())) or '-')
        print('  ラテン語: ' + regenerated + '   ' + mark)
        print()


def main():
    latindic.load()
    args = sys.argv[1:]
    if not args:
        print(__doc__ if __doc__ else 'usage: generate.py TEXT|FILE')
        return
    for arg in args:
        if os.path.exists(arg):
            with open(arg, encoding='utf-8') as f:
                for line in f:   # 1行1文。# で始まる行 (見出し・注記) は飛ばす
                    if line.strip() and not line.startswith('#'):
                        run(line)
        else:
            run(arg)


if __name__ == '__main__':
    main()
