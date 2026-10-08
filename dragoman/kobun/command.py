#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文のコマンドの設定 (core/cli.py)。表示は品詞分解と現代語訳
#
from dragoman.core import ansi_color
from dragoman.core.cli import Command
from . import analyzer, grammar, mecab

USAGE = '''
  ./dragoman.py kobun -e "今は昔、竹取の翁といふものありけり。"
  平安の和文 (学校の古文) を品詞分解し、助動詞の意味・活用の種類と活用形・係り結びを示して、現代語に組み立て直す。
  形態素解析は MeCab + 中古和文UniDic (国立国語研究所、CC BY-NC-SA 4.0。$DRAGOMAN_DATA/ojp/unidic-chuko)。
  音読は macOS の say の日本語音声 (現代仮名遣いの読みを渡す)
'''


def explain(token):
    if token.pos == '助動詞':
        meaning = grammar.auxiliary(token)[0]
        return meaning + ('  → ここでは%s' % token.chosen if token.chosen else '')
    if token.pos == '助詞' and token.pos2 == '係助詞' and token.lemma in grammar.KAKARI:
        form, meaning = grammar.KAKARI[token.lemma]
        return '係り結び (%s。結びは%s)' % (meaning, form)
    honor = grammar.honorific(token)
    if honor is not None:
        return '%s語 (%s)' % (honor[0], grammar.HONORIFIC_NOTES[honor[0]])
    from .modernize import vocabulary
    word = vocabulary(token)
    if word:
        return '重要古語「%s」' % word
    if token.obsolete == 'table':
        return '現代語に無い語「%s」' % grammar.OBSOLETE.get(token.lemma, grammar.OBSOLETE.get(token.base_orth, ''))
    if token.obsolete == 'unknown':
        return '現代語に無い語 (表に無い)'
    return ''


def render(analysis, options):
    if options.show_word_detail:
        print()
        width = max([len(t.surface) for t in analysis.tokens] + [2])
        for t in analysis.tokens:
            if t.pos == '補助記号':
                continue
            conj = ' '.join(x for x in (t.ctype.replace('文語', ''), t.form) if x and x != '*')
            base = t.base_orth if t.base_orth not in ('*', t.surface) else ''
            line = '  %s  %s%s%s' % (t.surface.ljust(width, '　'), t.pos + ('・' + t.pos2 if t.pos2 not in ('*', '一般') else ''),
                                     ('  ' + conj) if conj else '', ('  (基本形 %s)' % base) if base else '')
            note = explain(t) if options.explain else ''
            print(line + (ansi_color.fgcolor(ansi_color.GREEN, '  ' + note) if note else ''))
    print()
    print('  →  ' + analysis.modern)
    for note in analysis.notes if options.explain else []:
        print('     ' + ansi_color.fgcolor(ansi_color.GREEN, note))
    print()


def available():
    return None if mecab.available() else (
        'no classical Japanese dictionary (unidic-chuko from https://clrd.ninjal.ac.jp/unidic/ '
        'unzipped into $DRAGOMAN_DATA/ojp/unidic-chuko)')


COMMAND = Command(lang='kobun', name='古文 (平安の和文)', analyzer=analyzer, dictionary=None, available=available,
                  usage=USAGE, header=lambda a, o: a.text, speech_text=lambda a, o: a.reading,
                  speech_lang='ja', render=render)
