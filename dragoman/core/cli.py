#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 言語ごとのコマンド (dragoman.py --lang=xx) の共通の骨組み
#
# 各言語は <言語>/command.py に Command を置き、言語ごとに違うところ (見出しの行・語の転写・解説・データの確認・
# 音読の言語・固有のオプション) だけを書く。オプションの解析、テキストの読み込み、音読、表示はここで行う。
#
#   共通のオプション:
#   -w, --no-word-detail   語ごとの辞書引きの結果を表示しない
#   -D, --descendants      ほかの言語に入った語 (子孫語) も表示する
#   -E, --etymology        語源も表示する
#   -s, --speech           音読する
#   -t, --tts=BACKEND      音読の方式 (mbrola / espeak / piper / say)
#   -r, --romanize         語ごとの辞書引きの結果に、語の転写を添える
#   --no-explain           初学者向けの解説 (動詞の型・語根など) を出さない
#   --english-glosses      英語の訳語 (Wiktionary などの語義) を日本語に置き換えない
#   --sentence-per-line    改行も文の区切りにする (歌詞・詩など、行末に句点の無い行。行末がカンマなら次の行に続ける)
#   -h, --help             説明を表示する
#
import getopt
import sys
from dataclasses import dataclass, field

from dragoman.core import ansi_color, descendants, etymology, render

COMMON_SHORT = 'wDEst:rh'
COMMON_LONG = ['no-word-detail', 'descendants', 'etymology', 'speech', 'tts=', 'romanize', 'no-explain',
               'english-glosses', 'sentence-per-line', 'help']


@dataclass
class Options:
    show_word_detail: bool = True
    show_descendants: bool = False
    show_etymology: bool = False
    speech: bool = False
    tts: str = None
    voice: str = None
    romanize: bool = False
    explain: bool = True
    sentence_per_line: bool = False
    extra: dict = field(default_factory=dict)  # 言語固有のオプションの値


@dataclass
class Command:
    lang: str                       # 言語の符号 (grc, sa, ru, he, ar, fa, hi)
    name: str                       # 言語の名前 (日本語)
    analyzer: object                # analyze_text(text) を持つモジュール
    dictionary: object              # 子孫語・語源を引く辞書のモジュール
    available: object               # () → データが無いときの案内 (str) / None
    usage: str = ''                 # 説明の先頭 (使い方の例)
    header: object = None           # (analysis, options) → 見出しの行。無ければ語を並べるだけ
    speech_text: object = None      # (analysis, options) → 音読に渡す文
    romanize: object = None         # 語の転写の関数 (-r)
    explain: object = None          # (word) → 解説の行
    descendant_langs: tuple = ('en', 'ja')
    fallback_langs: tuple = ()
    speech_lang: str = None         # core.speech の言語の符号
    speech_pron: object = None      # (options) → 発音の流儀 (ギリシア語の --pron)
    speech_setup: object = None     # (options, speech) → 音読の前の設定 (ヘブライ語の神の名の読み方)
    short_options: str = ''         # 固有のオプション (getopt の書式)
    long_options: tuple = ()
    option_help: str = ''           # 固有のオプションの説明 (説明の表示に添える)
    handle_option: object = None    # (option, arg, options) → 処理したら True。'exit' で終了
    texts_hook: object = None       # (options) → 解析の前に行うこと (表の表示など)。True を返したら終わる
    render: object = None           # (analysis, options) → 解析結果の表示 (既定は core.render。古文は品詞分解と現代語訳)


def help_text(command):
    common = open(__file__, encoding='utf-8').read().split('共通のオプション:\n')[1].split('\nimport')[0]
    common = '\n'.join(line[1:] for line in common.splitlines() if line.startswith('#   '))
    out = '%s の解析と逐語訳\n\n%s\n\n共通のオプション:\n%s' % (command.name, command.usage.strip('\n'), common)
    if command.option_help:
        out += '\n\n%s のオプション:\n%s' % (command.name, command.option_help.strip('\n'))
    return out


def word_notes(command, options):
    def notes(word):
        lines = []
        if options.explain and command.explain:
            lines += [ansi_color.fgcolor(ansi_color.GREEN, line) for line in command.explain(word)]
        if options.show_descendants:
            for lemma, line in descendants.describe_word(word, command.descendant_langs, command.dictionary,
                                                          command.fallback_langs):
                lines.append(ansi_color.fgcolor(ansi_color.CYAN, '%s: %s' % (lemma, line)))
        if options.show_etymology:
            for lemma, ety in etymology.describe_word(word, command.dictionary):
                lines.append(ansi_color.fgcolor(ansi_color.MAGENTA, '%s の語源:' % lemma))
                lines.extend('  ' + line for line in ety)
        return lines
    wanted = options.show_descendants or options.show_etymology or (options.explain and command.explain)
    return notes if wanted else None


def parse(command, argv):
    opts, args = getopt.gnu_getopt(argv, COMMON_SHORT + command.short_options,
                               COMMON_LONG + list(command.long_options))
    options = Options()
    for option, arg in opts:
        if command.handle_option:
            handled = command.handle_option(option, arg, options)
            if handled == 'exit':
                return None, None
            if handled:
                continue
        if option in ('-w', '--no-word-detail'):
            options.show_word_detail = False
        elif option in ('-D', '--descendants'):
            options.show_descendants = True
        elif option in ('-E', '--etymology'):
            options.show_etymology = True
        elif option in ('-s', '--speech'):
            options.speech = True
        elif option in ('-t', '--tts'):
            options.speech, options.tts = True, arg
        elif option in ('-r', '--romanize'):
            options.romanize = True
        elif option == '--no-explain':
            options.explain = False
        elif option == '--sentence-per-line':
            options.sentence_per_line = True
        elif option == '--english-glosses':
            from dragoman.core import en_ja
            en_ja.ENABLED = False
        elif option in ('-h', '--help'):
            print(help_text(command))
            return None, None
    return options, args


def split_lines(text):
    """1行1文: 行ごとに分ける。行末がカンマ・セミコロン・コロン (、，) なら次の行に続ける"""
    chunks, current = [], []
    for line in text.splitlines():
        if not line.strip():
            if current:
                chunks.append(' '.join(current))
                current = []
            continue
        current.append(line.strip())
        if not line.rstrip().endswith((',', ';', ':', '、', '，', '،', '؛')):
            chunks.append(' '.join(current))
            current = []
    if current:
        chunks.append(' '.join(current))
    return chunks


def read_texts(args):
    """ファイル (無ければ標準入力) のテキスト。# で始まる行は注釈として除く"""
    texts = [open(path, encoding='utf-8').read() for path in args] if args else [sys.stdin.read()]
    return ['\n'.join(l for l in t.splitlines() if not l.lstrip().startswith('#')) for t in texts]


def run(command, argv=None, texts=None):
    options, args = parse(command, sys.argv[1:] if argv is None else argv)
    if options is None:
        return
    if command.texts_hook and command.texts_hook(options):
        return
    missing = command.available()
    if missing:
        sys.exit(missing)
    notes = word_notes(command, options)
    speech = None
    if options.speech:
        from dragoman.core import speech
        speech.set_language(command.speech_lang or command.lang,
                            command.speech_pron(options) if command.speech_pron else None)
        if command.speech_setup:
            command.speech_setup(options, speech)
        if speech.init_synth(options.tts, options.voice) is None:
            speech = None
    texts = texts if texts is not None else read_texts(args)
    if options.sentence_per_line:
        texts = [chunk for text in texts for chunk in split_lines(text)]
    for text in texts:
        for analysis in command.analyzer.analyze_text(text):
            line = command.header(analysis, options) if command.header else ' '.join(analysis.surfaces)
            render.render_sentence_header(line)
            if speech:
                speech.say_latin(command.speech_text(analysis, options) if command.speech_text
                                 else ' '.join(analysis.surfaces))
            if command.render:
                command.render(analysis, options)
            else:
                render.render_analysis(analysis, show_word_detail=options.show_word_detail, word_notes=notes,
                                       romanize=command.romanize if options.romanize else None)
            if speech:
                speech.pause_while_speaking()


def main(command):
    run(command)
