#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語 (現代ペルシア語。イラン) の解析と逐語訳 (作りかけ)
#
#   echo "من به مدرسه می‌روم." | python3 persian.py
#   python3 persian.py -w -D -E FILE...
#
#   -w, --no-word-detail   語ごとの辞書引きの結果を表示しない
#   -D, --descendants      ほかの言語に入った語 (子孫語) も表示する
#   -E, --etymology        語源も表示する
#   -s, --speech           音読する (espeak-ng のペルシア語音声)
#   -r, --romanize         語ごとの辞書引きの結果に、語の転写を添える
#   --no-explain           動詞の語幹・時制の作り方、エザーフェなどの解説を出さない
#
# 見出しの行は、ペルシア文字 (右から左。Unicode の隔離記号で囲む) と転写 (Wiktionary のイラン式。文字に書かれない
# エザーフェ -e を補う) を並べる
#
import getopt
import sys

from persian import analyzer, dictionary, explain, script
from core import ansi_color, descendants, etymology, render

DESCENDANT_LANGS = ('en', 'ja', 'tr', 'ur', 'hi', 'ar', 'hy', 'ka')


def word_notes(show_descendants, show_etymology, show_explanation=True):
    def notes(word):
        lines = []
        if show_explanation:
            lines += [ansi_color.fgcolor(ansi_color.GREEN, line) for line in explain.notes(word)]
        if show_descendants:
            for lemma, line in descendants.describe_word(word, DESCENDANT_LANGS, dictionary):
                lines.append(ansi_color.fgcolor(ansi_color.CYAN, '%s: %s' % (lemma, line)))
        if show_etymology:
            for lemma, ety in etymology.describe_word(word, dictionary):
                lines.append(ansi_color.fgcolor(ansi_color.MAGENTA, '%s の語源:' % lemma))
                lines.extend('  ' + line for line in ety)
        return lines
    return notes if (show_descendants or show_etymology or show_explanation) else None


def romanized(word):
    return script.rough_translit(word)


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'wDEsrh', ['no-word-detail', 'descendants', 'etymology', 'speech',
                                                        'romanize', 'no-explain', 'help'])
    show_word_detail, show_descendants, show_etymology, speech_mode = True, False, False, False
    romanize, show_explanation = False, True
    for option, arg in opts:
        if option in ('-w', '--no-word-detail'):
            show_word_detail = False
        elif option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option in ('-s', '--speech'):
            speech_mode = True
        elif option in ('-r', '--romanize'):
            romanize = True
        elif option == '--no-explain':
            show_explanation = False
        elif option in ('-h', '--help'):
            print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
            return
    if not dictionary.available():
        sys.exit('no Persian data (python3 tools/build_persian_dic.py)')
    notes = word_notes(show_descendants, show_etymology, show_explanation)
    if speech_mode:
        from core import speech
        speech.set_language('fa')
        speech_mode = speech.init_synth(None) is not None
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    texts = ['\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('#')) for t in texts]
    for text in texts:
        for analysis in analyzer.analyze_text(text):
            original, latin = analyzer.sentence_text(analysis.forms)
            render.render_sentence_header('%s  (%s)' % (script.isolate(original), latin))
            if speech_mode:
                speech.say_latin(original)
            render.render_analysis(analysis, show_word_detail=show_word_detail, word_notes=notes,
                                   romanize=romanized if romanize else None)
            if speech_mode:
                speech.pause_while_speaking()


if __name__ == '__main__':
    main()
