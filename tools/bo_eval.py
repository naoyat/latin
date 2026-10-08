#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の解析を、Hill & Garrett の手で品詞を付けたコーパス (doi:10.5281/zenodo.574878、CC BY 4.0) で測る
#
#   python3 tools/bo_eval.py [--source=mdzangsblun,buston,mila,marpa] [--limit=N] [-v]
#
# 正解の語 (チベット文字の綴り|品詞の印) と解析の語を、文字の位置 (ツェク・空白・区切り記号を除く) で突き合わせて:
#   * 語の区切り: 適合率・再現率・F1 (位置が完全に一致した語)
#   * 品詞: 区切りの合った語のうち、大まかな品詞 (名詞・動詞・格助詞 …) が合う割合
#   * 格助詞: 正解の case.* (能格・具格 agn、属格 gen、la don の term / all、処格 loc、奪格 ela / abl、共格 ass) を、
#     同じ働きの助詞として取れた割合
#   * 時制: 正解の時制が1つの動詞 (v.past, v.pres, v.fut, v.imp) で、選んだ時制が合う割合
#
import os
import re
import sys
import getopt
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.tibetan import analyzer

DIR = paths.data('bo', 'hill', 'texts', 'Texts')
SOURCES = ('mdzangsblun', 'buston', 'mila', 'marpa')
SKIP = re.compile('[་\\s།༎༏༐༑༔༄༅]')
CASES = {'case.agn': 'gis', 'case.gen': 'gi', 'case.term': 'la', 'case.all': 'la', 'case.loc': 'na',
         'case.ela': 'nas', 'case.abl': 'las', 'case.ass': 'dang'}
TENSES = {'v.past': 'past', 'v.pres': 'pres', 'v.fut': 'fut', 'v.imp': 'imp'}


def coarse_gold(tag):
    tag = tag.split('~')[0]
    if tag.startswith('case.') or tag.startswith('cv.') or tag.startswith('cl.') or tag == 'd.indef':
        return 'part'
    if tag.startswith(('n.v.', 'v.')):
        return 'cop' if tag in ('v.cop', 'n.v.cop') else 'verb'
    if tag.startswith('n.'):
        return 'noun'
    if tag.startswith('p.'):
        return 'pron'
    if tag == 'adj':
        return 'adj'
    if tag.startswith('num'):
        return 'num'
    if tag in ('d.dem', 'd.det', 'd.emph'):
        return 'det'
    if tag == 'd.plural':
        return 'det'  # 複数・数量 (rnams, dag, thams cad, kun) は名詞の後ろの限定詞としてまとめる
    if tag == 'neg':
        return 'neg'
    if tag.startswith('adv'):
        return 'adv'
    return 'other'


def coarse_ours(word):
    return {'exist': 'verb', 'plural': 'det'}.get(word.kind, word.kind)


def spans(pieces):
    """[(綴り, 値)] → {(始め, 終わり): 値} (ツェク・空白・区切り記号を除いた文字の位置)"""
    out, pos = {}, 0
    for text, value in pieces:
        n = len(SKIP.sub('', text))
        if n:
            out[(pos, pos + n)] = value
        pos += n
    return out


def read_gold(source):
    path = os.path.join(DIR, '%s-horizontal.txt' % source)
    for line in open(path, encoding='utf-8'):
        tokens = [t.rsplit('|', 1) for t in line.split() if '|' in t]
        if tokens:
            yield ''.join(form for form, _ in tokens), tokens


def main():
    opts, _ = getopt.getopt(sys.argv[1:], 'v', ['source=', 'limit='])
    opts = dict(opts)
    sources = opts.get('--source', ','.join(SOURCES)).split(',')
    limit = int(opts.get('--limit', 0)) or None
    verbose = '-v' in opts
    c = collections.Counter()
    confusion = collections.Counter()
    for source in sources:
        for n, (text, tokens) in enumerate(read_gold(source)):
            if limit and n >= limit:
                break
            gold = spans([(form, tag) for form, tag in tokens if tag != 'punc'])
            words = []
            for sentence in analyzer.sentences(text):
                words += analyzer.analyze_sentence(sentence).words
            ours = spans([(w.text, w) for w in words if w.kind != 'punct'])
            c['gold'] += len(gold)
            c['ours'] += len(ours)
            for span, tag in gold.items():
                g = coarse_gold(tag)
                case = CASES.get(tag.split('~')[0])
                w = ours.get(span)
                if case:
                    c['case'] += 1
                if w is None:
                    continue
                c['match'] += 1
                o = coarse_ours(w)
                c['pos'] += g == o
                if g != o:
                    confusion[(g, o)] += 1
                if case:
                    c['case_ok'] += w.kind == 'part' and w.lemma == case
                if tag in TENSES and w.kind == 'verb' and w.tense:
                    c['tense'] += 1
                    c['tense_ok'] += w.tense == TENSES[tag]
                    if verbose and w.tense != TENSES[tag]:
                        print('tense', w.wylie, TENSES[tag], w.tense)
    p = c['match'] / max(c['ours'], 1)
    r = c['match'] / max(c['gold'], 1)
    print('語の区切り: 適合率 %.1f%%  再現率 %.1f%%  F1 %.1f%%  (正解 %d 語)' % (
        100 * p, 100 * r, 200 * p * r / max(p + r, 1e-9), c['gold']))
    print('品詞 (区切りの合った語): %.1f%%' % (100 * c['pos'] / max(c['match'], 1)))
    print('格助詞: %.1f%%  (%d 個)' % (100 * c['case_ok'] / max(c['case'], 1), c['case']))
    print('時制 (時制が1つの動詞): %.1f%%  (%d 語)' % (100 * c['tense_ok'] / max(c['tense'], 1), c['tense']))
    print('品詞の取り違え (正解 → 解析):', ', '.join('%s→%s %d' % (g, o, k) for (g, o), k in confusion.most_common(10)))


if __name__ == '__main__':
    main()
