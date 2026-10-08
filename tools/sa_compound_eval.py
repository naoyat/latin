#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの複合語の分解の評価: UD Sanskrit-UFAL の複数語トークン (3-6 श्रीशारदागणपतिगुरुभ्यः) のうち、
# 前の語に Compound=Yes の付いたもの (複合語) を正解として、sanskrit.compound.split の分け方を比べる
#
#   python3 tools/sa_compound_eval.py [-e N] [FILE.conllu...]
#
import os
import sys
import glob
import getopt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.sanskrit import compound, script

DATA_DIR = paths.DATA_DIR
DEFAULT_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'sa', 'ud', 'sa_ufal-ud-*.conllu')))


def gold_compounds(path):
    """[(複合語の表記, 前の語の (表記, 見出し語) (SLP1) のリスト, 最後の語の表記)]"""
    lines = [line.rstrip('\n').split('\t') for line in open(path, encoding='utf-8') if line[:1].isdigit()]
    for i, fields in enumerate(lines):
        if '-' not in fields[0]:
            continue
        start, end = map(int, fields[0].split('-'))
        parts = [f for f in lines[i + 1:i + 2 + end - start] if f[0].isdigit() and '-' not in f[0]]
        members = parts[:-1]
        if not members or not all('Compound=Yes' in f[5] for f in members):
            continue  # 連声で融合しただけの2語
        yield fields[1], [(script.to_slp1(f[1]), script.to_slp1(f[2])) for f in members], script.to_slp1(parts[-1][1])


def same_stem(got, gold):
    """正解の表記か見出し語と合えば正しいとする (正解は分詞を語根で見出し語にしている: mṛta → mṛ)"""
    strip = lambda s: s[:-1] if s.endswith(('n', 't', 'd')) and len(s) > 2 else s
    return any(strip(got) == strip(g) for g in gold)


def main():
    opts, files = getopt.getopt(sys.argv[1:], 'e:')
    show = int(dict(opts).get('-e', 0))
    total = boundary_ok = exact = found = 0
    errors = []
    for path in files or DEFAULT_FILES:
        for surface, members, final in gold_compounds(path):
            total += 1
            candidates = compound.split(script.to_slp1(surface))
            if not candidates:
                errors.append('%s: 分けられない (正解 %s + %s)' % (surface, '-'.join(m[0] for m in members), final))
                continue
            found += 1
            got, _ = candidates[0]
            if len(got) == len(members):
                boundary_ok += 1
                if all(same_stem(g, m) for g, m in zip(got, members)):
                    exact += 1
                    continue
            errors.append('%s: %s (正解 %s)' % (surface, '-'.join(got), '-'.join(m[0] for m in members)))
    pct = lambda n: '%5.1f%%' % (100.0 * n / total) if total else '-'
    print('複合語 %d' % total)
    print('  分けられた      %s' % pct(found))
    print('  語の数が合う    %s' % pct(boundary_ok))
    print('  語幹まで合う    %s' % pct(exact))
    for e in errors[:show]:
        print('  ' + e)


if __name__ == '__main__':
    main()
