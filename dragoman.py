#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dragoman: 文を辞書引き・構文解析して、日本語の逐語訳を付ける (ラテン語・古典ギリシア語・サンスクリット・ロシア語・
# 聖書ヘブライ語 (聖書アラム語)・アラビア語・ペルシア語・ヒンディー語・ウルドゥー語)
#
#   echo "Agricola in silvā magnam casam aedificat." | python3 dragoman.py
#   python3 dragoman.py --lang=grc FILE...
#   python3 dragoman.py --lang=hi -s -w FILE...
#   python3 dragoman.py --lang=he --help              言語ごとのオプション
#
#   --lang=LANG   la (ラテン語) / grc (古典ギリシア語) / sa (サンスクリット) / ru (ロシア語) / he (聖書ヘブライ語) /
#                 ar (アラビア語) / fa (ペルシア語) / hi (ヒンディー語) / ur (ウルドゥー語)。
#                 省略すると文字から推定する (ラテン文字 → la、ギリシア文字 → grc、キリル文字 → ru、ヘブライ文字 → he、
#                 ウルドゥー語の字 (ٹ ڈ ڑ ں ے ھ) のあるアラビア文字 → ur、ペルシア語の字 (پ چ ژ گ ک ی) の多いもの → fa、
#                 ほかのアラビア文字 → ar、
#                 デーヴァナーガリーは ヒンディー語らしい語 (है, का, की, में …) があれば hi、無ければ sa)
#
# 共通のオプション (-w, -D, -E, -s, -t, -r, --no-explain) は core/cli.py、言語ごとのオプションは --lang=xx --help で。
# ラテン語は latin.py (対話モード・マクロンの推定などを含む) に渡す
#
import importlib
import os
import re
import runpy
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
LANGUAGES = {'la': None, 'grc': 'greek', 'sa': 'sanskrit', 'ru': 'russian', 'he': 'hebrew', 'ar': 'arabic',
             'fa': 'persian', 'hi': 'hindi', 'ur': 'urdu'}
HINDI_WORDS = {'है', 'हैं', 'का', 'की', 'के', 'में', 'नहीं', 'को', 'से', 'ने', 'था', 'थी', 'और', 'पर', 'भी'}


def detect(text):
    """文字から言語を推定する (分からなければ None)"""
    counts = {
        'grc': len(re.findall('[Ͱ-Ͽἀ-῿]', text)),
        'ru': len(re.findall('[Ѐ-ӿ]', text)),
        'he': len(re.findall('[֐-׿]', text)),
        'arabic-script': len(re.findall('[؀-ۿ]', text)),
        'deva': len(re.findall('[ऀ-ॿ]', text)),
        'la': len(re.findall('[A-Za-zāēīōūȳĀĒĪŌŪ]', text)),
    }
    best = max(counts, key=counts.get)
    if counts[best] == 0:
        return None
    if best == 'arabic-script':
        if re.search('[\u0679\u0688\u0691\u06ba\u06d2\u06d3\u06be]', text):
            return 'ur'  # ٹ ڈ ڑ ں ے ۓ ھ
        persian = len(re.findall('[پچژگکی‌]', text))
        return 'fa' if persian > len(re.findall('[كي]', text)) else 'ar'
    if best == 'deva':
        words = set(re.findall('[ऀ-ॣ०-ॿ]+', text))
        return 'hi' if words & HINDI_WORDS else 'sa'
    return best


def command_for(lang):
    return importlib.import_module(LANGUAGES[lang] + '.command').COMMAND


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    lang = None
    args = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('--lang='):
            lang = arg.split('=', 1)[1]
        elif arg == '--lang' and i + 1 < len(argv):
            lang = argv[i + 1]
            i += 1
        else:
            args.append(arg)
        i += 1
    if lang is not None and lang not in LANGUAGES:
        sys.exit('--lang: %s のどれか' % '|'.join(LANGUAGES))
    if lang is None and ('-h' in args or '--help' in args):
        print(open(__file__, encoding='utf-8').read().split('\nimport')[0])
        return
    texts = None
    if lang is None:
        # 言語を推定するためにテキストを先に読む (ファイルの指定はオプションでない引数)
        from core import cli
        files = [a for a in args if not a.startswith('-') and os.path.exists(a)]
        texts = cli.read_texts(files)
        lang = detect('\n'.join(texts)) or 'la'
        args = [a for a in args if a not in files]
    if lang == 'la':
        path = os.path.join(ROOT, 'latin.py')
        if texts is not None:  # 読んでしまったテキストは一時ファイルで渡す
            with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fp:
                fp.write('\n'.join(texts))
            args.append(fp.name)
        sys.argv = [path] + args
        runpy.run_path(path, run_name='__main__')
        return
    from core import cli
    cli.run(command_for(lang), args, texts)


if __name__ == '__main__':
    main()
