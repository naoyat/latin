#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヘブライ語の態の型の表 (hebrew/binyan.py) で作る形の評価 (leave-one-out)
#
#   python3 tools/hebrew_binyan_eval.py [-e N]
#
# 聖書 (OSHB) によく出る語根 (上位 400) の、表の欄 (完了・未完了・命令・分詞・不定詞) に現れた形を、その語根自身の形を
# 使わずに作り (弱い語根は同じ分類の別の語根からの類推、強い語根は強い語根の型)、実際の形と比べる。
# 語頭の begadkefat の弱いダゲシュの有無は見ない (前の語が母音で終わると落ちる)
#
import os
import sys
import getopt
import collections
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.hebrew import binyan, dictionary


def normalized(form):
    t = unicodedata.normalize('NFD', form)
    if t and t[0] in 'בגדכפת':
        t = t[0] + t[1:4].replace('ּ', '', 1) + t[4:]
    return unicodedata.normalize('NFC', t)


def main():
    opts, _ = getopt.getopt(sys.argv[1:], 'e:')
    show = int(dict(opts).get('-e', 0))
    rows = dictionary.bare_verb_forms()
    columns = {(c[2][0], c[2][1]): c[1] for c in binyan.COLUMNS}
    stems = {v: k for k, v in binyan.STEM_CODES.items()}
    frequency = collections.Counter()
    for root, stem, vtype, pgn, form, count in rows:
        frequency[binyan._plain(root)] += count
    top = {r for r, _ in frequency.most_common(400)}
    best = {}
    for root, stem, vtype, pgn, form, count in rows:
        root = binyan._plain(root)
        column = columns.get((vtype, pgn))
        if root not in top or column is None or stem not in stems or len(root) != 3 or root in binyan.IRREGULAR:
            continue
        key = (root, stems[stem], column)
        if key not in best or count > best[key][1]:
            best[key] = (form, count)
    total, ok, misses = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    for (root, stem, column), (form, _) in best.items():
        kind = 'weak' if binyan.signature(root) != ('', '', '') else 'strong'
        guess = binyan.analogize(root, stem, column) if kind == 'weak' else None
        made = guess[0] if guess else binyan.generate(root, stem, column)
        total[kind] += 1
        if made and normalized(made) == normalized(form):
            ok[kind] += 1
        else:
            misses[kind].append('%s %s %s: %s (正解 %s%s)' % (root, stem, column, made, form,
                                                            ', %s から' % guess[1] if guess else ''))
    for kind in ('strong', 'weak'):
        print('%-7s %5.1f%% (%d / %d)' % (kind, 100.0 * ok[kind] / max(1, total[kind]), ok[kind], total[kind]))
        for line in misses[kind][:show]:
            print('    ' + line)


if __name__ == '__main__':
    main()
