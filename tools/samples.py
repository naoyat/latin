#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 現行の解析器が例文をどう解析・翻訳するかを表示する
#
#   python3 tools/samples.py                 # 全サンプルの訳を1行ずつ
#   python3 tools/samples.py 独立 繋辞        # 見出しにその文字列を含む節だけ
#   python3 tools/samples.py -t              # 述語と格の枠の構造も表示
#   python3 tools/samples.py -d              # さらに語ごとの辞書引きの結果も表示
#   python3 tools/samples.py -d -D           # 語ごとに英語・フランス語などに残った語 (子孫語) も
#   python3 tools/samples.py -d -E           # 語ごとに語源 (祖語の系統・同源語) も
#   python3 tools/samples.py > before.txt    # パイプやファイルへは色なしで出す (版ごとの比較に)
#
#   -f, --file=FILE     例文のファイル (既定は samples/samples.txt)
#   -l, --list          節の見出しの一覧を表示する
#   --no-wiktionary     手作りの辞書だけを使う
#   --no-tagger         品詞タガーを使わない
#
import contextlib
import getopt
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from latin import latindic, analyzer, render, macronizer, ansi_color

DEFAULT_FILE = os.path.join(ROOT, 'samples', 'samples.txt')
AUTO_MACRON = '[auto-macron]'
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def read_sections(path):
    """[(見出し, [文, ...])]。# だけの行は注釈、## で始まる行が見出し"""
    sections = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('##'):
                sections.append((line.lstrip('#').strip(), []))
            elif line and not line.startswith('#'):
                if not sections:
                    sections.append(('', []))
                sections[-1][1].append(line)
    return sections


def brief(analysis):
    """訳だけを1文につき数行で"""
    if not analysis.clauses:
        nodes = [node for node in analysis.nodes if node.translate()[0]]
        print('  → ', ' / '.join(render.translate(node) for node in nodes))
        return
    for clause in analysis.clauses:
        print('  → ', render.translate(clause.predicate))
        for item in clause.not_solved:
            print('     (行き場の無い語句: %s → %s)' % (item.surface, render.translate(item)))


def show(sections, mode, show_descendants=False, show_etymology=False):
    for title, sentences in sections:
        print()
        print(ansi_color.underline(ansi_color.bold('■ ' + title)))
        for text in sentences:
            if AUTO_MACRON in title:
                macronized = macronizer.macronize_text(text)
                print()
                print(text)
                text = macronized
                print('  (マクロン推定) ' + text)
            else:
                print()
                print(text)
            for analysis in analyzer.analyze_text(text):
                if mode == 'brief':
                    brief(analysis)
                else:
                    render.render_analysis(analysis, show_word_detail=(mode == 'detail'),
                                           show_descendants=show_descendants,
                                           show_etymology=show_etymology)


def usage():
    print(__doc__ if __doc__ else open(__file__, encoding='utf-8').read().split('\nimport')[0])


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'tdDEf:lh',
                                   ['tree', 'detail', 'descendants', 'etymology', 'file=', 'list', 'no-wiktionary', 'no-tagger',
                                    'help'])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)

    mode, path, list_only = 'brief', DEFAULT_FILE, False
    show_descendants = show_etymology = False
    for option, arg in opts:
        if option in ('-t', '--tree'):
            mode = 'tree'
        elif option in ('-d', '--detail'):
            mode = 'detail'
        elif option in ('-f', '--file'):
            path = arg
        elif option in ('-l', '--list'):
            list_only = True
        elif option in ('-D', '--descendants'):
            show_descendants = True
        elif option in ('-E', '--etymology'):
            show_etymology = True
        elif option == '--no-wiktionary':
            latindic.LatinDic.use_wiktionary = False
        elif option == '--no-tagger':
            analyzer.USE_TAGGER = False
        elif option in ('-h', '--help'):
            usage()
            return

    sections = read_sections(path)
    if list_only:
        for title, sentences in sections:
            print('%s (%d)' % (title, len(sentences)))
        return
    if args:
        sections = [s for s in sections if any(arg in s[0] for arg in args)]
        if not sections:
            print('該当する節がありません (-l で見出しの一覧)')
            sys.exit(1)

    latindic.load()
    if sys.stdout.isatty():
        show(sections, mode, show_descendants, show_etymology)
    else:
        # パイプやファイルへは色を落として出す
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            show(sections, mode, show_descendants, show_etymology)
        sys.stdout.write(ANSI.sub('', buf.getvalue()))


if __name__ == '__main__':
    main()
