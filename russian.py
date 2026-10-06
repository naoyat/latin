#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語の解析と逐語訳 (作りかけ)
#
#   echo "Мальчик читает книгу." | python3 russian.py
#   python3 russian.py -w -D -E FILE...
#
#   -w, --no-word-detail   語ごとの辞書引きの結果を表示しない
#   -D, --descendants      英語・日本語などに借用された語 (子孫語) も表示する
#   -E, --etymology        語源 (祖語の系統・同源語・説明文) も表示する
#   -s, --speech           音読する (espeak-ng のロシア語音声。強勢の位置は Wiktionary の変化表から)
#
import getopt
import sys

from russian import analyzer, dictionary, morphology, script
from core import ansi_color, descendants, etymology, render

DESCENDANT_LANGS = ('en', 'ja', 'fr', 'de')
FALLBACK_LANGS = ('uk', 'be')


def word_notes(show_descendants, show_etymology):
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


def stressed_text(surfaces):
    """強勢記号を付けた文 (句読点の前の空白を詰める)"""
    out = ''
    for s in surfaces:
        if s.startswith('('):
            continue  # 補った繋辞
        if s in analyzer.PUNCTUATION and s not in ('—', '–', '(', '«', '„', '“'):
            out += s
        else:
            out += (' ' if out else '') + (s if s in analyzer.PUNCTUATION else morphology.stressed(s))
    return out


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'wDEsh', ['no-word-detail', 'descendants', 'etymology', 'speech',
                                                       'help'])
    show_word_detail, show_descendants, show_etymology, speech_mode = True, False, False, False
    for option, _ in opts:
        if option in ('-w', '--no-word-detail'):
            show_word_detail = False
        elif option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option in ('-s', '--speech'):
            speech_mode = True
        elif option in ('-h', '--help'):
            print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
            return
    if not (dictionary.available() and morphology.available()):
        sys.exit('no Russian data (pip install pymorphy3 pymorphy3-dicts-ru, and python3 tools/build_russian_dic.py)')
    notes = word_notes(show_descendants, show_etymology)
    if speech_mode:
        from core import speech
        speech.set_language('ru')
        speech_mode = speech.init_synth('espeak') is not None
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    texts = ['\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('#')) for t in texts]
    for text in texts:
        for analysis in analyzer.analyze_text(text):
            stressed = stressed_text(analysis.surfaces)
            render.render_sentence_header('%s  (%s)' % (stressed, script.translit(stressed)))
            if speech_mode:
                speech.say_latin(stressed)
            render.render_analysis(analysis, show_word_detail=show_word_detail, word_notes=notes)
            if speech_mode:
                speech.pause_while_speaking()


if __name__ == '__main__':
    main()
