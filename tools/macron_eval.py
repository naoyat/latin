#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# マクロン推定の評価
#   マクロン付きのテキストからマクロンを外して推定させ、元のテキストと比べる
#
#   python3 tools/macron_eval.py                    # texts/fabulae_faciles/*.txt で評価
#   python3 tools/macron_eval.py -e 20 FILE...      # 間違いの例を 20 件ずつ表示
#   python3 tools/macron_eval.py -p DIR FILE...     # 他のツールの出力 (DIR/<同名のファイル>) を採点する
#   python3 tools/macron_eval.py --hidden=mark      # 隠れた長音の流儀を指定して推定する
#
# 隠れた長音 (māgnus/magnus など。latin/hidden_quantity.py) は流儀が分かれるので、
# それを無視した正解率 (「隠れた長音を無視」) を主な指標とする
#
# 既定の評価データは目録 (texts/catalog.json) で評価に使えるとされたテキスト
# (手作りの辞書を作るのに使ったテキストは、精度が高く出すぎるので除く)。
# 頻度などの知識は、評価するテキストと同じ系統 (family) のテキストを除いて使う
#
import os
import sys
import glob
import getopt
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import latindic, analyzer
from latin.macronizer import macronize_words, strip_macrons, has_macron, transfer_macrons, Context, Frequency
from latin import hidden_quantity
from latin import catalog

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOWELS = set('aeiouyAEIOUYāēīōūȳĀĒĪŌŪȲ')


def compare(pred, gold, ignore_hidden=False):
    """(語が一致したか, 一致した母音の数, 母音の数)"""
    skip = hidden_quantity.positions(gold) if ignore_hidden else set()
    vowels = correct = 0
    for i, (p, g) in enumerate(zip(pred, gold)):
        if strip_macrons(g) in VOWELS and i not in skip:
            vowels += 1
            correct += has_macron(p) == has_macron(g)
    return correct == vowels, correct, vowels


def classify(choice, gold):
    if choice.candidates is None:  # 他のツールの出力 (候補の情報が無い)
        if compare(choice.macronized, gold, ignore_hidden=True)[0]:
            return '隠れた長音の流儀の違いだけ'
        return 'その他'
    if not choice.candidates:
        return '辞書に無い'
    if compare(choice.macronized, gold, ignore_hidden=True)[0]:
        return '隠れた長音の流儀の違いだけ'
    if gold not in {transfer_macrons(c.macronized, choice.word) for c in choice.candidates}:
        return '正解が候補に無い'
    return '候補の選び間違い'


class Predicted:
    """他のツールの出力を Choice と同じように扱うための入れ物"""
    def __init__(self, word, macronized):
        self.word = word
        self.macronized = macronized
        self.candidates = None
        self.ambiguous = False


def predicted_choices(gold_tokens, predicted_path):
    with open(predicted_path) as fp:
        predicted = [w for sentence in analyzer.sentences(fp.read()) for w in sentence]
    if [strip_macrons(w) for w in predicted] != [strip_macrons(w) for w in gold_tokens]:
        raise ValueError('%s: 語の並びが正解と一致しない (マクロン以外の変更がある)' % predicted_path)
    return [Predicted(strip_macrons(g), p) for g, p in zip(gold_tokens, predicted)]


def evaluate(files, show_errors=0, frequency=None, predicted_dir=None, hidden='keep'):
    stats = collections.Counter()
    errors = collections.defaultdict(collections.Counter)
    for path in files:
        with open(path) as fp:
            text = fp.read()
        # 文書単位で推定する (時制の傾向などを文書全体から求める)。頻度は評価するファイルを除いて数える
        gold_tokens = [w for sentence in analyzer.sentences(text) for w in sentence]
        if predicted_dir:
            choices = predicted_choices(gold_tokens, os.path.join(predicted_dir, os.path.basename(path)))
        else:
            context = Context(frequency=frequency, exclude=path) if frequency else Context(exclude=path)
            context.hidden = hidden
            choices = macronize_words([strip_macrons(w) for w in gold_tokens], context)
        for choice, gold in zip(choices, gold_tokens):
            if not gold[:1].isalpha():
                continue
            if True:
                ok, correct, vowels = compare(choice.macronized, gold)
                ok_h, correct_h, vowels_h = compare(choice.macronized, gold, ignore_hidden=True)
                stats['words'] += 1
                stats['words_ok'] += ok
                stats['words_ok_h'] += ok_h
                stats['vowels'] += vowels
                stats['vowels_ok'] += correct
                stats['vowels_h'] += vowels_h
                stats['vowels_ok_h'] += correct_h
                stats['ambiguous'] += choice.ambiguous
                stats['ambiguous_ok'] += choice.ambiguous and ok
                stats['baseline_ok'] += not has_macron(gold)
                if not ok:
                    errors[classify(choice, gold)]['%s→%s' % (gold, choice.macronized)] += 1

    n = stats['words']
    print('評価データ: %d ファイル, %d 語' % (len(files), n))
    print('  語単位の正解率      %5.1f%%   (隠れた長音を無視 %5.1f%%)' % (
        100 * stats['words_ok'] / n, 100 * stats['words_ok_h'] / n))
    print('  母音単位の正解率    %5.1f%%   (隠れた長音を無視 %5.1f%%)' % (
        100 * stats['vowels_ok'] / stats['vowels'], 100 * stats['vowels_ok_h'] / stats['vowels_h']))
    print('  候補が複数の語      %5.1f%%   (そのうち正解 %5.1f%%)' % (
        100 * stats['ambiguous'] / n, 100 * stats['ambiguous_ok'] / max(1, stats['ambiguous'])))
    print('  参考: マクロンを付けない場合の語単位の正解率 %5.1f%%' % (100 * stats['baseline_ok'] / n))
    total_errors = sum(sum(c.values()) for c in errors.values())
    print('間違い %d 語の内訳:' % total_errors)
    for kind, counter in sorted(errors.items(), key=lambda kv: -sum(kv[1].values())):
        count = sum(counter.values())
        print('  %-24s %4d (%2.0f%%)' % (kind, count, 100 * count / total_errors), end='')
        if show_errors:
            print('  ' + ', '.join('%s×%d' % (e, k) if k > 1 else e
                                   for e, k in counter.most_common(show_errors)), end='')
        print()
    return stats


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'e:p:h', ['errors=', 'predicted=', 'hidden=', 'help',
                                                         'no-wiktionary', 'no-frequency'])
    show_errors = 0
    hidden = 'keep'
    predicted_dir = None
    use_frequency = True
    for option, arg in opts:
        if option in ('-e', '--errors'):
            show_errors = int(arg)
        elif option == '--hidden':
            hidden = arg
        elif option in ('-p', '--predicted'):
            predicted_dir = arg
        elif option == '--no-frequency':
            use_frequency = False
        elif option == '--no-wiktionary':
            latindic.LatinDic.use_wiktionary = False
        elif option in ('-h', '--help'):
            print('Usage: python %s [-e N] [-p DIR] [--hidden=keep|strip|mark] [--no-wiktionary] [--no-frequency] [FILE...]'
                  % sys.argv[0])
            sys.exit()
    # 既定の評価データは目録 (texts/catalog.json) で評価に使えるとされたテキスト
    files = args or catalog.default().evaluation_files()
    latindic.load()
    # 頻度は texts/ 以下の全テキストから (評価するファイル自体は除く)
    evaluate(files, show_errors, Frequency() if use_frequency and not predicted_dir else None, predicted_dir, hidden)


if __name__ == '__main__':
    main()
