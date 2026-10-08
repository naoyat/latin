#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語のコマンドの設定 (core/cli.py)。表示は語ごとの分解と日本語訳
#
from dragoman.core import ansi_color
from dragoman.core.cli import Command
from . import analyzer, dictionary, grammar, phonology, script, segment

USAGE = '''
  ./dragoman.py bo -e "རྒྱལ་པོས་བློན་པོ་ལ་གསེར་བྱིན་ནོ།"
  古典チベット語を語に分け (botok)、格助詞 (能格 gis・属格 gi・la don …)・動詞の語幹の時制・否定を示して、
  日本語に訳す。見出しはチベット文字とワイリー式、その下にラサ方言の発音 (IPA と声調)。
  音読 (-s) は espeak-ng の普通話の音声に音素で渡す。辞書は tools/build_tibetan_dic.py で作る (docs/tibetan.md)
'''
OPTION_HELP = '''
  --pron=PRON            発音: lhasa (ラサ方言。既定) / chant (読誦式: 語末の母音を変えず -l -n を読む)
'''


def pron(options):
    return options.extra.get('pron', 'lhasa')


def handle_option(option, arg, options):
    if option == '--pron':
        if arg not in ('lhasa', 'chant'):
            raise SystemExit('--pron は lhasa か chant')
        options.extra['pron'] = arg
        return True
    return False


def speech_text(analysis, options):
    return phonology.espeak_phonemes(analysis.text, pron(options), words=analysis.word_texts())

KINDS = {'noun': '名詞', 'pron': '代名詞', 'adj': '形容詞', 'num': '数詞', 'det': '指示詞', 'plural': '複数',
         'verb': '動詞', 'cop': '繋辞', 'exist': '存在動詞', 'neg': '否定', 'part': '助詞', 'adv': '副詞'}


def header(analysis, options):
    return '%s  (%s)' % (analysis.text, analysis.wylie)


def describe(w):
    if w.kind in ('part', 'plural', 'neg', 'cop', 'exist'):
        out = w.function
        if w.kind == 'part' and w.wylie != w.lemma:
            out += ' (%s の形)' % w.lemma
        return out + ('「%s」' % w.ja if w.ja else '')
    out = (w.ja or '').replace(',', '・') or (w.en or '')
    if w.kind == 'verb':
        if w.lemma and w.lemma != w.wylie:
            out += '  %s形 (見出し %s)' % (grammar.TENSE_NAMES.get(w.tense, ''), w.lemma)
        elif w.tense:
            out += '  %s形' % grammar.TENSE_NAMES.get(w.tense, '')
        if w.nominal:
            out += '  動名詞 (+pa/ba)'
    return out


def render(analysis, options):
    print('  [%s]' % analysis.pronunciation(pron(options)))
    if options.show_word_detail:
        print()
        width = max([len(w.wylie) for w in analysis.words if w.kind != 'punct'] + [4])
        for w in analysis.words:
            if w.kind == 'punct':
                continue
            line = '  %s  %s  %s  %s' % (w.text, w.wylie.ljust(width), KINDS.get(w.kind, w.kind), describe(w))
            note = w.note if options.explain else ''
            print(line + (ansi_color.fgcolor(ansi_color.GREEN, '  ' + note) if note else ''))
    print()
    print('  →  ' + analysis.japanese)
    for note in analysis.notes if options.explain else []:
        print('     ' + ansi_color.fgcolor(ansi_color.GREEN, note))
    print()


def available():
    if not dictionary.available():
        return 'no Tibetan dictionary (python3 tools/build_tibetan_dic.py; see docs/tibetan.md)'
    return None


COMMAND = Command(lang='bo', name='古典チベット語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=header, romanize=script.translit, render=render, speech_lang='bo',
                  speech_text=speech_text, speech_pron=pron, long_options=('pron=',), option_help=OPTION_HELP,
                  handle_option=handle_option)
