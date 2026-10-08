#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語のコマンドの設定 (core/cli.py)。表示は語ごとの分解と日本語訳
#
from dragoman.core import ansi_color
from dragoman.core.cli import Command
from . import analyzer, morphology, script

USAGE = '''
  ./dragoman.py ain -e "teeta wenkur tane nishpa ne"
  アイヌ語 (北海道方言。ローマ字) の語を人称の接辞 (ku= / e= / ci= / a= / en= / un= …) と語幹に分け、後置詞・助詞から
  語順のまま日本語に訳す。知里幸惠『アイヌ神謡集』の古いローマ字表記 (sh, ch, kamui) も現代の表記に寄せて読む。
  語彙は手作りの表 (dragoman/ainu/grammar.py) と Wiktionary。詳しくは docs/ainu.md
'''

KINDS = {'noun': '名詞', 'pron': '代名詞', 'verb': '動詞', 'adj': '形容詞', 'attr': '形容詞 (修飾)', 'adv': '副詞',
         'det': '連体詞', 'num': '数詞', 'postp': '後置詞', 'particle': '助詞', 'neg': '否定', 'aux': '助動詞',
         'copula': '繋辞', 'unknown': '(辞書に無い)'}


def header(analysis, options):
    kana = analysis.kana
    return analysis.text + ('\n  [%s]' % kana if kana else '')


def render(analysis, options):
    if options.show_word_detail:
        print()
        width = max([len(t.surface) for t in analysis.tokens if t.kind != 'punct'] + [4])
        for t in analysis.tokens:
            if t.kind == 'punct':
                continue
            parts = ' + '.join(t.morph.parts) if t.morph is not None and len(t.morph.parts) > 1 else ''
            notes = []
            if t.morph is not None and t.morph.subject:
                notes.append('主語「%s」(人称の接辞)' % t.morph.subject)
            if t.morph is not None and t.morph.object:
                notes.append('目的語「%s」(人称の接辞)' % t.morph.object)
            if t.morph is not None and t.morph.source and t.morph.source != '表':
                notes.append('訳語: %s' % t.morph.source)
            if t.case:
                notes.append('→「%s」' % t.case)
            line = '  %s  %s  %s%s' % (t.surface.ljust(width), KINDS.get(t.kind, t.kind), t.gloss,
                                       ('  (%s)' % parts) if parts else '')
            note = '  '.join(notes) if options.explain else ''
            print(line + (ansi_color.fgcolor(ansi_color.GREEN, '  ' + note) if note else ''))
    print()
    print('  →  ' + analysis.japanese)
    print()


def available():
    return None


COMMAND = Command(lang='ain', name='アイヌ語', analyzer=analyzer, dictionary=None, available=available,
                  usage=USAGE, header=header, render=render)
