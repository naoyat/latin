#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析の結果 (格の枠) から文を作り直す試み: ラテン語 → 文の枠 → 英語・ラテン語
#
#   python3 tools/generate.py "Puella rosam pulchram in hortō videt."
#   python3 tools/generate.py samples/samples.txt
#   python3 tools/generate.py --to=en,ru,sa "…"     作る言語 (既定: en,la と、語の置き換えの表があれば ru,sa)
#   python3 tools/generate.py --from=grc "ἡ κόρη τὸ καλὸν ῥόδον βλέπει."   ロシア語 (ru)・サンスクリット (sa)・古典ギリシア語から
#   python3 tools/generate.py --from=ja "少女が庭で美しい薔薇を見た。"   日本語の文から (MeCab と規則で文の枠に)
#
# ラテン語に戻した文が元の文と同じ語 (順序は問わない) になれば ✓。違えば、違う語を出す。
# ファイルは1行1文 (# で始まる行は飛ばす。samples/samples.txt の形)
#
import os
import sys
import re
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.latin import analyzer, latindic
from dragoman.generate import frame, english, latin, russian, sanskrit, greek, japanese


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
OTHERS = [('ru', 'ロシア語:', russian), ('sa', '梵語:    ', sanskrit), ('grc', 'ギリシア語:', greek),
          ('ja', '日本語:  ', japanese)]


def run_japanese(text):
    """日本語の文 → 文の枠 → 各言語 (ラテン語との往復の比べは無し)"""
    from dragoman.generate import from_japanese
    for sentence in re.split(r'(?<=[。！？])', text.strip()):
        if not sentence.strip():
            continue
        print(sentence.strip())
        clauses = from_japanese.parse(sentence)
        if not clauses:
            print('  (述語が見つからない)\n')
            continue
        for clause in clauses:
            print(frame.describe(clause))
        for lang, label, module in [('ja', '日本語:  ', japanese), ('la', 'ラテン語:', latin),
                                    ('en', '英語:    ', english)] + [o for o in OTHERS if o[0] != 'ja']:
            if lang in TARGETS:
                try:
                    print('  %s ' % label + module.sentence(clauses))
                except Exception as e:
                    print('  %s (作れない: %s: %s)' % (label, type(e).__name__, e))
        print()


def run_other(text, source):
    """ロシア語・サンスクリット・古典ギリシア語の文 → 文の枠 → 各言語。元の言語に戻した文と元の文を比べる"""
    import importlib
    analyzer_module = importlib.import_module('dragoman.%s.analyzer' % {'ru': 'russian', 'sa': 'sanskrit', 'grc': 'greek'}[source])
    modules = {'la': ('ラテン語:', latin), 'en': ('英語:    ', english), 'ru': ('ロシア語:', russian),
               'sa': ('梵語:    ', sanskrit), 'grc': ('ギリシア語:', greek), 'ja': ('日本語:  ', japanese)}
    for analysis in analyzer_module.analyze_text(text):
        print(analysis.text)
        clauses = frame.frames(analysis)
        if not clauses:
            print('  (述語が見つからない)\n')
            continue
        for clause in clauses:
            print(frame.describe(clause))
        for lang in ['ja', 'la', 'en', 'ru', 'sa', 'grc']:
            if lang not in TARGETS and lang != source:
                continue
            label, module = modules[lang]
            try:
                out = module.sentence(clauses)
            except Exception as e:
                out = '(作れない: %s: %s)' % (type(e).__name__, e)
            mark = ''
            if lang == source:
                first = out.split('\n')[0]
                original = _source_words(analysis.text, source)
                mark = '   ✓ 同じ語' if original == _source_words(first, source) else '   ✗'
            first, _, rest = out.partition('\n')
            print('  %s %s%s%s' % (label, first, mark, ('\n' + rest) if rest else ''))
        print()


def _source_words(text, lang):
    """元の言語の文の語 (比べる用。サンスクリットは SLP1 に、ロシア語は小文字・ё → е)"""
    words = [w.strip('.,;:!?।"“”()·;') for w in text.split()]
    words = [w for w in words if w]
    if lang == 'sa':
        from dragoman.sanskrit import script
        return Counter(re.sub('[sr]$', 'H', script.to_slp1(w)) for w in words)   # rāmas = rāmaḥ (語末の連声)
    if lang == 'grc':   # 重アクセント = 鋭アクセント、前接語の前の2つめのアクセントは除く、語末の ν (ἔδωκεν = ἔδωκε)
        words = [unicodedata.normalize('NFD', w.lower()).replace('\u0300', '\u0301') for w in words]
        words = [w[:w.rfind('\u0301')] + w[w.rfind('\u0301') + 1:] if w.count('\u0301') + w.count('\u0342') > 1 else w
                 for w in words]   # 前接語の前で足したアクセント (ταῦτά ἐστιν)
        words = [unicodedata.normalize('NFC', w) for w in words]
        words = [{'ἐστί': 'ἐστι', 'ἐστίν': 'ἐστιν', 'εἰσί': 'εἰσι', 'εἰσίν': 'εἰσιν'}.get(w, w) for w in words]   # 前接語
        return Counter(unicodedata.normalize('NFC', re.sub('(?<=[ει])([\u0300-\u036f]*)ν$', r'\1',
                                                           unicodedata.normalize('NFD', w))) for w in words)
    return Counter(w.lower().replace('ё', 'е') for w in words)


def main():
    import getopt
    latindic.load()
    opts, args = getopt.gnu_getopt(sys.argv[1:], '', ['to=', 'from='])
    TARGETS[:] = ['en', 'la'] + [lang for lang, _, module in OTHERS if module.available()]
    source = 'la'
    for opt, value in opts:
        if opt == '--to':
            TARGETS[:] = value.split(',')
        elif opt == '--from':
            source = value
    global run
    if source in ('ru', 'sa', 'grc'):
        def run(text, source=source):
            run_other(text, source)
    if source == 'ja':
        run = run_japanese
        if 'ja' not in TARGETS:
            TARGETS.insert(0, 'ja')   # 日本語からなら訳し戻しも
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
