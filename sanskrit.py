#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの解析と逐語訳 (作りかけ)。デーヴァナーガリーでも IAST でも入力できる
#
#   echo "रामो वनं गच्छति ।" | python3 sanskrit.py
#   python3 sanskrit.py -w -D -E FILE...
#
#   -w, --no-word-detail   語ごとの辞書引きの結果を表示しない
#   -D, --descendants      パーリ語・ヒンディー語・英語・日本語などに残った語 (子孫語) も表示する
#   -E, --etymology        語源 (祖語の系統・同源語・説明文) も表示する
#   -s, --speech           音読する (MBROLA のヒンディー語音声 in1。使えなければ espeak-ng のヒンディー語音声)
#   -t, --tts=BACKEND      音読の方式 (mbrola / espeak)
#   -v, --voice=NAME       MBROLA の音声 (in1 男声 / in2 女声)
#   --compound-labels=sa|ja|en
#                          複合語の種類の名称: sa は tatpuruṣa, bahuvrīhi… (既定)、ja は依主釈, 有財釈… (六合釈)、
#                          en は determinative, possessive…
#
import getopt
import sys

from sanskrit import analyzer, compound, dictionary, morphology, script
from latin import ansi_color, descendants, etymology, render

DESCENDANT_LANGS = ('pi', 'hi', 'en', 'ja')
FALLBACK_LANGS = ('bn', 'mr')


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


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'wDEst:v:h', ['no-word-detail', 'descendants', 'etymology', 'help',
                                                            'compound-labels=', 'speech', 'tts=', 'voice='])
    show_word_detail, show_descendants, show_etymology = True, False, False
    speech_mode, tts, voice = False, None, None
    for option, arg in opts:
        if option == '--compound-labels':
            if arg not in compound.LABEL_STYLES:
                sys.exit('--compound-labels: %s のどれか' % '|'.join(compound.LABEL_STYLES))
            compound.set_label_style(arg)
        elif option in ('-s', '--speech'):
            speech_mode = True
        elif option in ('-t', '--tts'):
            speech_mode, tts = True, arg
        elif option in ('-v', '--voice'):
            speech_mode, voice = True, arg
        elif option in ('-w', '--no-word-detail'):
            show_word_detail = False
        elif option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option in ('-h', '--help'):
            print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
            return
    if not (dictionary.available() and morphology.available()):
        sys.exit('no Sanskrit data (vidyut data and python3 tools/build_sanskrit_dic.py)')
    notes = word_notes(show_descendants, show_etymology)
    if speech_mode:
        from latin import speech
        speech.set_language('sa')
        speech_mode = speech.init_synth(tts, voice) is not None
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    texts = ['\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('#')) for t in texts]
    for text in texts:
        for analysis in analyzer.analyze_text(text):
            original = ' '.join(analysis.surfaces)
            render.render_sentence_header('%s  (%s)' % (original, script.devanagari(script.to_slp1(original))))
            if speech_mode:
                speech.say_latin(original)
            render.render_analysis(analysis, show_word_detail=show_word_detail, word_notes=notes)
            if speech_mode:
                speech.pause_while_speaking()


if __name__ == '__main__':
    main()
