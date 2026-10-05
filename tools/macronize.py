#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語テキストにマクロン (長音記号) を推定して付ける
#
#   python3 tools/macronize.py FILE...      # 結果を標準出力へ
#   echo "Gallia est omnis divisa" | python3 tools/macronize.py
#
#   -v, --verbose   候補が複数あった語に印を付ける ([候補1|候補2] の形で全候補を表示)
#   --hidden=MODE   隠れた長音 (māgnus/magnus など) の流儀
#                   keep: 辞書のまま (既定) / strip: 付けない / mark: 分かる範囲で付ける
#
import os
import sys
import getopt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import latindic, macronizer


def verbose_text(text, hidden='keep'):
    tokens = macronizer.TOKEN.findall(text)
    context = macronizer.Context(frequency=macronizer.default_frequency(), hidden=hidden)
    choices = iter(macronizer.macronize_words(tokens, context))

    def render(_match):
        choice = next(choices)
        if not choice.ambiguous:
            return choice.macronized
        forms = [choice.macronized] + sorted(
            {macronizer.transfer_macrons(c.macronized, choice.word) for c in choice.candidates} - {choice.macronized})
        return '[%s]' % '|'.join(forms)
    return macronizer.TOKEN.sub(render, text)


def main():
    opts, files = getopt.getopt(sys.argv[1:], 'vh', ['verbose', 'help', 'no-wiktionary', 'hidden='])
    verbose = False
    hidden = 'keep'
    for option, arg in opts:
        if option in ('-v', '--verbose'):
            verbose = True
        elif option == '--hidden':
            if arg not in macronizer.HIDDEN_MODES:
                sys.exit('--hidden must be one of: %s' % ', '.join(macronizer.HIDDEN_MODES))
            hidden = arg
        elif option == '--no-wiktionary':
            latindic.LatinDic.use_wiktionary = False
        elif option in ('-h', '--help'):
            print('Usage: python %s [-v] [--hidden=keep|strip|mark] [--no-wiktionary] [FILE...]' % sys.argv[0])
            sys.exit()
    latindic.load()
    texts = [open(f).read() for f in files] if files else [sys.stdin.read()]
    for text in texts:
        sys.stdout.write(verbose_text(text, hidden) if verbose else macronizer.macronize_text(text, hidden=hidden))


if __name__ == '__main__':
    main()
