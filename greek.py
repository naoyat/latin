#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の解析と逐語訳 (作りかけ)
#
#   python3 greek.py [オプション] [FILE...]      ファイル (なければ標準入力) の文を解析する
#   echo "ὁ ἄνθρωπος τὸν ἵππον βλέπει." | python3 greek.py
#
#   -w, --no-word-detail   語ごとの辞書引きの結果を表示しない
#   -D, --descendants      ラテン語・英語・フランス語などに残った語 (子孫語) も表示する
#   -E, --etymology        語源 (祖語の系統・同源語・説明文) も表示する
#
import getopt
import sys

from greek import analyzer, dictionary
from latin import ansi_color, descendants, etymology, render

DESCENDANT_LANGS = ('la', 'en', 'fr')
FALLBACK_LANGS = ('it', 'es')


def word_notes(show_descendants, show_etymology):
    """語ごとに添える行 (ギリシア語の辞書から引いた子孫語・語源)"""
    def notes(word):
        lines = []
        if show_descendants:
            for lemma, line in descendants.describe_word(word, DESCENDANT_LANGS, dictionary, FALLBACK_LANGS):
                lines.append(ansi_color.fgcolor(ansi_color.CYAN, '%s: %s' % (lemma, line)))
        if show_etymology:
            for lemma, ety in etymology.describe_word(word, dictionary):
                lines.append(ansi_color.fgcolor(ansi_color.MAGENTA, '%s の語源:' % lemma))
                lines.extend('  ' + line for line in ety)
        return lines
    return notes if (show_descendants or show_etymology) else None


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'wDEh', ['no-word-detail', 'descendants', 'etymology', 'help'])
    show_word_detail, show_descendants, show_etymology = True, False, False
    for option, _ in opts:
        if option in ('-w', '--no-word-detail'):
            show_word_detail = False
        elif option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option in ('-h', '--help'):
            print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
            return
    if not dictionary.available():
        sys.exit('no Greek dictionary (python3 tools/build_greek_dic.py)')
    notes = word_notes(show_descendants, show_etymology)
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    texts = ['\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#')) for text in texts]
    for text in texts:
        for analysis in analyzer.analyze_text(text):
            render.render_sentence_header(' '.join(analysis.surfaces))
            render.render_analysis(analysis, show_word_detail=show_word_detail, word_notes=notes)


if __name__ == '__main__':
    main()
