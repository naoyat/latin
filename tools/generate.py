#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析の結果 (格の枠) から文を作り直す試み: ラテン語 → 文の枠 → 英語・ラテン語
#
#   python3 tools/generate.py "Puella rosam pulchram in hortō videt."
#   python3 tools/generate.py samples/samples.txt
#   python3 tools/generate.py --to=en,ru,sa "…"     作る言語 (既定: en,la と、語の置き換えの表があれば ru,sa)
#
# ラテン語に戻した文が元の文と同じ語 (順序は問わない) になれば ✓。違えば、違う語を出す。
# ファイルは1行1文 (# で始まる行は飛ばす。samples/samples.txt の形)
#
import os
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.latin import analyzer, latindic
from dragoman.generate import frame, english, latin, russian, sanskrit


def _word_list(text):
    text = unicodedata.normalize('NFC', text)
    return [w.strip('.,;:!?"“”()').lower() for w in text.split() if w.strip('.,;:!?"“”()')]


def _normal(text):
    """綴りの流儀をそろえる: マクロンを外し、j → i、v → u"""
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text.replace('j', 'i').replace('J', 'I').replace('v', 'u').replace('V', 'U')


def _spelling(word):
    """綴りの流儀をそろえた語 (比較用): マクロン・j/v・i 語幹の対格複数 -īs (omnīs = omnēs)・ad- の同化 (adfectus = affectus)"""
    word = _normal(word).lower()
    for plain, assimilated in (('adf', 'aff'), ('adc', 'acc'), ('adp', 'app'), ('adl', 'all'), ('inr', 'irr'),
                               ('conl', 'coll'), ('inl', 'ill'), ('adt', 'att')):
        if word.startswith(plain):
            word = assimilated + word[len(plain):]
    word = {'iis': 'eis', 'ii': 'ei', 'isdem': 'eisdem', 'iidem': 'eidem'}.get(word, word)   # is の複数 iīs = eīs
    return word[:-2] + 'es' if word.endswith('is') and len(word) > 4 else word


def _words(text):
    return Counter(_word_list(text))


def run(text):
    for analysis in analyzer.analyze_text(text):
        print(analysis.text)
        clauses = frame.frames(analysis)
        if not clauses:
            print('  (述語が見つからない)\n')
            continue
        for clause in clauses:
            print(frame.describe(clause))
        if 'en' in TARGETS:
            print('  英語:     ' + english.sentence(clauses))
        for lang, label, module in OTHERS:
            if lang in TARGETS:
                try:
                    print('  %s ' % label + module.sentence(clauses))
                except Exception as e:   # 1つの言語で作れなくても、ほかの言語は出す
                    print('  %s (作れない: %s: %s)' % (label, type(e).__name__, e))
        if 'la' not in TARGETS:
            print()
            continue
        regenerated = latin.sentence(clauses)
        original, again = _words(analysis.text), _words(regenerated)
        spelled = Counter(map(_spelling, _word_list(analysis.text))), Counter(map(_spelling, _word_list(regenerated)))
        if original != again and spelled[0] == spelled[1]:
            mark = '✓ 綴りの違いだけ (マクロン・i/j・u/v・-īs/-ēs・同化)'
        elif original == again:
            mark = '✓ 同じ語' + (' (語順も同じ)' if _word_list(regenerated) == _word_list(analysis.text) else '')
        else:
            # 違う語は綴りの違いを除いて出す
            only_original = [w for w in _word_list(analysis.text) if (spelled[0] - spelled[1])[_spelling(w)] > 0]
            only_again = [w for w in _word_list(regenerated) if (spelled[1] - spelled[0])[_spelling(w)] > 0]
            mark = '✗ 元にだけある語: %s / 作った文にだけある語: %s' % (
                ' '.join(sorted(set(only_original))) or '-', ' '.join(sorted(set(only_again))) or '-')
        print('  ラテン語: ' + regenerated + '   ' + mark)
        print()


TARGETS = ['en', 'la']
OTHERS = [('ru', 'ロシア語:', russian), ('sa', '梵語:    ', sanskrit)]


def main():
    import getopt
    latindic.load()
    opts, args = getopt.gnu_getopt(sys.argv[1:], '', ['to='])
    TARGETS[:] = ['en', 'la'] + [lang for lang, _, module in OTHERS if module.available()]
    for opt, value in opts:
        if opt == '--to':
            TARGETS[:] = value.split(',')
    if not args:
        print(__doc__ if __doc__ else 'usage: generate.py TEXT|FILE')
        return
    for arg in args:
        if os.path.exists(arg):
            with open(arg, encoding='utf-8') as f:
                for line in f:   # 1行1文。# で始まる行 (見出し・注記) は飛ばす
                    if line.strip() and not line.startswith('#'):
                        run(line)
        else:
            run(arg)


if __name__ == '__main__':
    main()
