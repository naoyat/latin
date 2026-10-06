#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の辞書引き (いまは語ごとの辞書引きまで。文の解析はこれから)
#
#   python3 greek.py [-D] [-E] [FILE...]       ファイル (なければ標準入力) の文を語ごとに引く
#   echo "ὁ ἄνθρωπος τὸν ἵππον βλέπει." | python3 greek.py -E
#
#   -D, --descendants   ラテン語・英語・フランス語などに残った語 (子孫語) も表示する
#   -E, --etymology     語源 (祖語の系統・同源語・説明文) も表示する
#
import getopt
import re
import sys

from greek import dictionary, orthography
from latin import ansi_color, descendants, etymology
from latin.Word import Word

# 語 (ギリシア文字と結合文字、語中・語末のアポストロフィ) と句読点 (· は上の点、; は疑問符)
TOKEN = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+(?:[’'ʼ᾽][Ͱ-Ͽἀ-῿̀-ͯ]*)?"
                   r"|[.,·;·;:!]")
PUNCTUATION = set('.,·;·;:!')
DESCENDANT_LANGS = ('la', 'en', 'fr')
FALLBACK_LANGS = ('it', 'es')


def words_of(text):
    for surface in TOKEN.findall(text):
        if surface in PUNCTUATION:
            yield Word(surface, None)
        else:
            yield Word(surface, dictionary.lookup(surface))


def show(text, show_descendants=False, show_etymology=False):
    words = list(words_of(text))
    if not words:
        return
    print(ansi_color.underline(ansi_color.bold(' '.join(w.surface for w in words))))
    print()
    width = max(len(w.surface) for w in words)
    indent = ' ' * (width + 7)
    for i, word in enumerate(words):
        print('  %2d  %s %s' % (i, word.surface + ' ' * (width - len(word.surface)), word.detail()))
        if not word.items:
            continue
        if show_descendants:
            for lemma, line in descendants.describe_word(word, DESCENDANT_LANGS, dictionary, FALLBACK_LANGS):
                print(indent + ansi_color.fgcolor(ansi_color.CYAN, '%s: %s' % (lemma, line)))
        if show_etymology:
            for lemma, lines in etymology.describe_word(word, dictionary):
                print(indent + ansi_color.fgcolor(ansi_color.MAGENTA, '%s の語源:' % lemma))
                for line in lines:
                    print(indent + '  ' + line)
    print()


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'DEh', ['descendants', 'etymology', 'help'])
    show_descendants = show_etymology = False
    for option, _ in opts:
        if option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option in ('-h', '--help'):
            print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
            return
    if not dictionary.available():
        sys.exit('no Greek dictionary (python3 tools/build_greek_dic.py)')
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    for text in texts:
        # 文に分ける (句点・疑問符・上の点で)
        for sentence in re.split(r'(?<=[.;;··])\s+', text.strip()):
            if orthography.is_greek(sentence):
                show(sentence, show_descendants, show_etymology)


if __name__ == '__main__':
    main()
