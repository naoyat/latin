#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dragoman: 文を辞書引き・構文解析して、日本語の逐語訳を付ける (ラテン語・古典ギリシア語・サンスクリット・ロシア語・
# 聖書ヘブライ語 (聖書アラム語)・アラビア語・ペルシア語・ヒンディー語・ウルドゥー語、古文 (現代語に組み立て直す))
#
#   ./dragoman.py [LANG] [オプション] [ファイル...]     (python3 dragoman.py / python3 -m dragoman でも)
#
#   echo "Agricola in silvā magnam casam aedificat." | ./dragoman.py
#   ./dragoman.py grc FILE...
#   ./dragoman.py hi -e "लड़के ने किताब पढ़ी।"
#   ./dragoman.py la                                   ラテン語の対話モード (変化表・マクロンの推定)
#   ./dragoman.py he --help                            言語ごとのオプション
#   ./dragoman.py --languages                          対応している言語の一覧
#
#   LANG          最初の引数が言語の符号なら言語の指定 (--lang=LANG でも)。省略するか auto なら文字から推定し、
#                 推定した言語を標準エラー出力に出す
#                 (ラテン文字 → la、ギリシア文字 → grc、キリル文字 → ru、ヘブライ文字 → he、
#                 ウルドゥー語の字 (ٹ ڈ ڑ ں ے ھ) のあるアラビア文字 → ur、ペルシア語の字 (پ چ ژ گ ک ی) の多いもの → fa、
#                 ほかのアラビア文字 → ar、デーヴァナーガリーはヒンディー語らしい語 (है, का, की, में …) があれば hi、無ければ sa、
#                 チベット文字 → bo、インドネシア語らしい語 (yang, dan, di, ini, itu …) が2つ以上あるラテン文字 → id
#                 (マレー語らしい語 kerana, sahaja, bahawa … があれば ms)、タガログ語らしい語 (ang, ng, mga, ay …) → tl、
#                 アイヌ語らしい語 (kamuy, kotan, wa, kor, ne …) → ain、かな交じりの日本語 → kobun)
#   -e, --text=TEXT       引数の文を入力にする (何度でも。ファイル・標準入力の代わりに)
#   -L, --languages       対応している言語の一覧を出す
#
# 共通のオプション (-w, -D, -E, -s, -t, -r, --no-explain, --english-glosses) は core/cli.py、
# 言語ごとのオプションは ./dragoman.py LANG --help で。
# ラテン語は dragoman/latin/main.py (対話モード・変化表・マクロンの推定などを含む) に渡す
#
import importlib
import os
import re
import sys
import tempfile

LANGUAGES = {'la': 'latin', 'grc': 'greek', 'sa': 'sanskrit', 'ru': 'russian', 'he': 'hebrew', 'ar': 'arabic',
             'fa': 'persian', 'hi': 'hindi', 'ur': 'urdu', 'bo': 'tibetan', 'id': 'indonesian', 'ms': 'malay',
             'tl': 'tagalog', 'ain': 'ainu', 'kobun': 'kobun'}
NAMES = {'la': 'ラテン語', 'grc': '古典ギリシア語', 'sa': 'サンスクリット', 'ru': 'ロシア語',
         'he': '聖書ヘブライ語 (聖書アラム語も)', 'ar': 'アラビア語 (現代標準アラビア語)', 'fa': 'ペルシア語',
         'hi': 'ヒンディー語', 'ur': 'ウルドゥー語', 'bo': '古典チベット語', 'id': 'インドネシア語', 'ms': 'マレー語', 'tl': 'タガログ語', 'ain': 'アイヌ語', 'kobun': '古文 (平安の和文。現代語に組み立て直す)'}
CODE = re.compile('^[a-z]{2,5}$')
INDONESIAN_WORDS = {'yang', 'dan', 'di', 'ini', 'itu', 'dengan', 'untuk', 'tidak', 'adalah', 'akan', 'dari', 'ke', 'pada',
                    'saya', 'mereka', 'ada', 'sudah', 'juga', 'dalam', 'oleh', 'bahwa', 'bahawa', 'kami', 'kita'}
AINU_WORDS = {'kamuy', 'kamui', 'aynu', 'ainu', 'kotan', 'ruwe', 'sekor', 'somo', 'anakne', 'orowa', 'cise', 'chise',
              'kor', 'wa', 'ne', 'an', 'oka', 'pirka', 'wen', 'nispa', 'nishpa', 'teeta', 'tane', 'ki', 'kane'}
TAGALOG_WORDS = {'ang', 'ng', 'mga', 'ay', 'si', 'hindi', 'ako', 'ko', 'siya', 'niya', 'ito', 'kay', 'po', 'naman',
                 'lang', 'pero', 'ikaw', 'mo', 'nila', 'sila', 'kami', 'tayo'}
MALAY_WORDS = {'kerana', 'sahaja', 'bahawa', 'wang', 'jepun', 'inggeris', 'kerajaan', 'boleh', 'hendak', 'awak'}
HINDI_WORDS = {'है', 'हैं', 'का', 'की', 'के', 'में', 'नहीं', 'को', 'से', 'ने', 'था', 'थी', 'और', 'पर', 'भी'}


def detect(text):
    """文字から言語を推定する (分からなければ None)"""
    counts = {
        'grc': len(re.findall('[Ͱ-Ͽἀ-῿]', text)),
        'ru': len(re.findall('[Ѐ-ӿ]', text)),
        'he': len(re.findall('[֐-׿]', text)),
        'arabic-script': len(re.findall('[؀-ۿ]', text)),
        'deva': len(re.findall('[ऀ-ॿ]', text)),
        'bo': len(re.findall('[\u0f00-\u0fff]', text)),
        'la': len(re.findall('[A-Za-zāēīōūȳĀĒĪŌŪ]', text)),
        'kobun': len(re.findall('[\u3040-\u30ff]', text)) * 2,  # かな (日本語の文は古文として)
    }
    best = max(counts, key=counts.get)
    if counts[best] == 0:
        return None
    if best == 'arabic-script':
        if re.search('[\u0679\u0688\u0691\u06ba\u06d2\u06d3\u06be]', text):
            return 'ur'  # ٹ ڈ ڑ ں ے ۓ ھ
        persian = len(re.findall('[پچژگکی‌]', text))
        return 'fa' if persian > len(re.findall('[كي]', text)) else 'ar'
    if best == 'la':
        words = set(re.findall('[a-z]+', text.lower()))
        if len(words & AINU_WORDS) >= 3 and len(words & AINU_WORDS) > len(words & TAGALOG_WORDS):
            return 'ain'  # ラテン文字のアイヌ語 (kamuy, kotan, wa, kor, ne …)
        if len(words & TAGALOG_WORDS) >= 2 and len(words & TAGALOG_WORDS) >= len(words & INDONESIAN_WORDS):
            return 'tl'  # ラテン文字のタガログ語 (ang, ng, mga, ay …)
        if len(words & INDONESIAN_WORDS) >= 2:
            return 'ms' if words & MALAY_WORDS else 'id'  # ラテン文字のインドネシア語・マレー語
    if best == 'deva':
        words = set(re.findall('[ऀ-ॣ०-ॿ]+', text))
        return 'hi' if words & HINDI_WORDS else 'sa'
    return best


def command_for(lang):
    return importlib.import_module('dragoman.%s.command' % LANGUAGES[lang]).COMMAND


def language_list():
    """対応している言語の一覧 (符号・名前・説明の文書)"""
    return '\n'.join(['  %-4s %s  (docs/%s.md)' % (code, NAMES[code], LANGUAGES[code]) for code in LANGUAGES] +
                     ['  auto 文字から推定する'])


def parse_args(argv):
    """(言語, 言語に渡す引数, -e の文のリスト)。言語は --lang=LANG か、最初の引数が言語の符号のとき"""
    lang, args, texts = None, [], []
    positional_seen = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith('--lang='):
            lang = arg.split('=', 1)[1]
        elif arg == '--lang' and i + 1 < len(argv):
            lang = argv[i + 1]
            i += 1
        elif arg.startswith('--text='):
            texts.append(arg.split('=', 1)[1])
        elif arg in ('-e', '--text') and i + 1 < len(argv):
            texts.append(argv[i + 1])
            i += 1
        elif arg.startswith('-e') and len(arg) > 2:
            texts.append(arg[2:])
        elif not arg.startswith('-') and not positional_seen and lang is None and not os.path.exists(arg) \
                and CODE.match(arg):
            lang = arg  # ./dragoman.py grc …
            positional_seen = True
        else:
            if not arg.startswith('-'):
                positional_seen = True
            args.append(arg)
        i += 1
    return lang, args, texts


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if '-L' in argv or '--languages' in argv:
        print('対応している言語:\n' + language_list())
        return
    lang, args, texts = parse_args(argv)
    if lang == 'auto':
        lang = None  # 文字から推定する
    if lang is not None and lang not in LANGUAGES:
        sys.exit('知らない言語: %s\n対応している言語:\n%s' % (lang, language_list()))
    if lang is None and ('-h' in args or '--help' in args):
        print(open(__file__, encoding='utf-8').read().split('\nimport')[0].replace('# ', '').replace('#', ''))
        print('対応している言語:\n' + language_list())
        return
    texts = texts or None
    if lang is None:
        # 言語を推定するためにテキストを先に読む (ファイルの指定はオプションでない引数)
        from dragoman.core import cli
        if texts is None:
            files = [a for a in args if not a.startswith('-') and os.path.exists(a)]
            texts = cli.read_texts(files)
            args = [a for a in args if a not in files]
        detected = detect('\n'.join(texts))
        lang = detected or 'la'
        # 推定した言語を標準エラー出力に (解析結果の出力は汚さない)
        print('推定した言語: %s (%s)%s' % (lang, NAMES[lang], '' if detected else '。文字から推定できないのでラテン語に'),
              file=sys.stderr)
    if lang == 'la':
        from dragoman.latin import main as latin_main
        if texts is not None:  # 文はラテン語のコマンドに一時ファイルで渡す
            with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8') as fp:
                fp.write('\n'.join(texts) + '\n')
            args.append(fp.name)
        latin_main.main(args)
        return
    from dragoman.core import cli
    cli.run(command_for(lang), args, texts)


if __name__ == '__main__':
    main()
