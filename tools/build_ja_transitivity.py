#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 現代語の動詞の自他 (他動詞・自動詞) の表を JMdict から作る
#
#   python3 tools/build_ja_transitivity.py
#
# 古文の現代語訳で、助詞の無い体言を主語「が」にするか目的語「を」にするかを決めるのに使う (歌よむ → 歌を詠む)。
#
# 入力: $DRAGOMAN_DATA/JMdict_e.gz (http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz、EDRDG、CC BY-SA 4.0)
# 出力: $DRAGOMAN_DATA/ja-transitivity.tsv (見出し語 TAB vt / vi / vt,vi。JMdict 由来 (CC BY-SA))
#
import os
import sys
import gzip
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths


def main():
    found = {}
    with gzip.open(paths.data('JMdict_e.gz')) as f:
        for _, entry in ET.iterparse(f):
            if entry.tag != 'entry':
                continue
            kinds = set()
            for sense in entry.findall('sense'):
                for p in sense.findall('pos'):
                    if p.text == 'transitive verb':
                        kinds.add('vt')
                    elif p.text == 'intransitive verb':
                        kinds.add('vi')
            if kinds:
                for word in [k.findtext('keb') for k in entry.findall('k_ele')] + \
                        [r.findtext('reb') for r in entry.findall('r_ele')]:
                    found.setdefault(word, set()).update(kinds)
            entry.clear()
    out = paths.data('ja-transitivity.tsv')
    with open(out, 'w') as f:
        for word in sorted(found):
            f.write('%s\t%s\n' % (word, ','.join(sorted(found[word]))))
    print('%d words → %s' % (len(found), out))


if __name__ == '__main__':
    main()
