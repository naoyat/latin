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
#   python3 tools/samples.py --lang=grc      # 古典ギリシア語 (samples/greek.txt)
#   python3 tools/samples.py --lang=sa       # サンスクリット (samples/sanskrit.txt)
#   python3 tools/samples.py --lang=ru       # ロシア語 (samples/russian.txt)
#   python3 tools/samples.py --lang=he       # 聖書ヘブライ語 (samples/hebrew.txt)
#   python3 tools/samples.py --lang=ar       # アラビア語 (samples/arabic.txt)
#   python3 tools/samples.py --lang=fa       # ペルシア語 (samples/persian.txt)
#   python3 tools/samples.py --lang=hi       # ヒンディー語 (samples/hindi.txt)
#   python3 tools/samples.py --lang=ur       # ウルドゥー語 (samples/urdu.txt)
#   python3 tools/samples.py --lang=bo       # 古典チベット語 (samples/tibetan.txt)。日本語訳を表示
#   python3 tools/samples.py --lang=kobun    # 古文 (samples/kobun.txt)。現代語訳を表示
#
#   --lang=la|grc|sa|ru|he|ar|fa|hi|ur|bo|kobun 言語 (既定は la。ラテン語)
#   -f, --file=FILE     例文のファイル (既定は言語ごとの samples/*.txt)
#   -r, --romanize      ラテン文字以外の文に転写を添える (-d なら語ごとにも)
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

from dragoman.core import render, ansi_color
from dragoman.latin import latindic, analyzer, macronizer

DEFAULT_FILE = os.path.join(ROOT, 'samples', 'samples.txt')
LANG_FILES = {'la': DEFAULT_FILE, 'grc': os.path.join(ROOT, 'samples', 'greek.txt'),
              'sa': os.path.join(ROOT, 'samples', 'sanskrit.txt'), 'ru': os.path.join(ROOT, 'samples', 'russian.txt'),
              'he': os.path.join(ROOT, 'samples', 'hebrew.txt'), 'ar': os.path.join(ROOT, 'samples', 'arabic.txt'),
              'fa': os.path.join(ROOT, 'samples', 'persian.txt'), 'hi': os.path.join(ROOT, 'samples', 'hindi.txt'),
              'ur': os.path.join(ROOT, 'samples', 'urdu.txt'), 'bo': os.path.join(ROOT, 'samples', 'tibetan.txt'),
              'kobun': os.path.join(ROOT, 'samples', 'kobun.txt')}


def analyzer_for(lang):
    """言語ごとの analyze_text"""
    if lang == 'grc':
        from dragoman.greek import analyzer as greek_analyzer
        return greek_analyzer.analyze_text
    if lang == 'sa':
        from dragoman.sanskrit import analyzer as sanskrit_analyzer
        return sanskrit_analyzer.analyze_text
    if lang == 'ru':
        from dragoman.russian import analyzer as russian_analyzer
        return russian_analyzer.analyze_text
    if lang == 'he':
        from dragoman.hebrew import analyzer as hebrew_analyzer
        return hebrew_analyzer.analyze_text
    if lang == 'ar':
        from dragoman.arabic import analyzer as arabic_analyzer
        return arabic_analyzer.analyze_text
    if lang == 'fa':
        from dragoman.persian import analyzer as persian_analyzer
        return persian_analyzer.analyze_text
    if lang == 'hi':
        from dragoman.hindi import analyzer as hindi_analyzer
        return hindi_analyzer.analyze_text
    if lang == 'ur':
        from dragoman.urdu import analyzer as urdu_analyzer
        return urdu_analyzer.analyze_text
    if lang == 'kobun':
        from dragoman.kobun import analyzer as kobun_analyzer
        return kobun_analyzer.analyze_text
    if lang == 'bo':
        from dragoman.tibetan import analyzer as tibetan_analyzer
        return tibetan_analyzer.analyze_text
    return analyzer.analyze_text
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


def romanizer(lang):
    """言語ごとの (文の転写, 語の転写)。ラテン文字の言語は None"""
    if lang == 'grc':
        from dragoman.greek import romanize as greek_romanize
        return greek_romanize.romanize, greek_romanize.romanize_word
    if lang == 'ru':
        import re
        from dragoman.russian import morphology as russian_morphology, script as russian_script
        word = lambda w: russian_script.translit(russian_morphology.stressed(w))
        cyrillic = re.compile('[а-яёА-ЯЁ\u0301-]+')
        return (lambda text: cyrillic.sub(lambda m: word(m.group(0)), text)), word
    if lang == 'he':
        from dragoman.hebrew import script as hebrew_script
        return (lambda text: ' '.join(hebrew_script.translit(w) for w in hebrew_script.pointed(text).split()
                                      if hebrew_script.is_hebrew(w))), hebrew_script.translit
    if lang == 'ar':
        from dragoman.arabic import script as arabic_script
        return None, arabic_script.translit  # 文の転写は解析の後で (選んだ読み・格の語尾から)
    if lang == 'fa':
        from dragoman.persian import script as persian_script
        return None, persian_script.rough_translit  # 文の転写は解析の後で (辞書の転写とエザーフェから)
    if lang == 'hi':
        from dragoman.hindi import script as hindi_script
        return hindi_script.translit, hindi_script.translit
    return None, None


def show(sections, mode, show_descendants=False, show_etymology=False, lang='la', romanize=False):
    analyze_text = analyzer_for(lang)
    romanize_text, romanize_word = romanizer(lang) if romanize else (None, None)
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
            if lang == 'sa':
                from dragoman.sanskrit import script
                print('  (%s)' % script.iast(script.to_slp1(text)))  # デーヴァナーガリーの文は IAST も
            elif lang == 'hi':
                from dragoman.hindi import script as hindi_script
                print('  (%s)' % hindi_script.translit(text))
            elif lang == 'bo':
                from dragoman.tibetan import script as tibetan_script, dictionary as tibetan_dictionary
                print('  (%s)' % tibetan_script.translit(text, tibetan_dictionary.known()))
            elif lang == 'he':
                from dragoman.hebrew import script as hebrew_script
                print('  (%s)' % ' '.join(hebrew_script.translit(w) for w in hebrew_script.pointed(text).split()
                                          if hebrew_script.is_hebrew(w)))
            elif romanize_text:
                print('  (%s)' % romanize_text(text))
            for analysis in analyze_text(text):
                if lang == 'kobun':
                    # 古文は現代語訳 (と係り結びの注) を表示する (-d なら品詞分解も)
                    from dragoman.core.cli import Options
                    from dragoman.kobun import command as kobun_command
                    if mode == 'brief':
                        print('  → ', analysis.modern)
                    else:
                        kobun_command.render(analysis, Options(show_word_detail=(mode == 'detail')))
                    continue
                if lang == 'bo':
                    from dragoman.core.cli import Options
                    from dragoman.tibetan import command as tibetan_command
                    if mode == 'brief':
                        print('  → ', analysis.japanese)
                    else:
                        tibetan_command.render(analysis, Options(show_word_detail=(mode == 'detail')))
                    continue
                if lang == 'ar':
                    # 母音記号を補った形 (選んだ読みと格の語尾) と転写
                    from dragoman.arabic import analyzer as arabic_analyzer, script as arabic_script
                    vocalized, latin = arabic_analyzer.sentence_text(analysis.forms)
                    print('  %s  (%s)' % (arabic_script.isolate(vocalized), latin))
                elif lang == 'ur':
                    print('  (%s)' % analysis.forms_text[1])  # 選んだヒンディー語の語形からの転写
                elif lang == 'fa':
                    from dragoman.persian import analyzer as persian_analyzer
                    print('  (%s)' % persian_analyzer.sentence_text(analysis.forms)[1])  # エザーフェを補った転写
                if mode == 'brief':
                    brief(analysis)
                else:
                    render.render_analysis(analysis, show_word_detail=(mode == 'detail'),
                                           show_descendants=show_descendants,
                                           show_etymology=show_etymology, romanize=romanize_word)


def usage():
    print(__doc__ if __doc__ else open(__file__, encoding='utf-8').read().split('\nimport')[0])


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'tdDEf:lrh',
                                   ['tree', 'detail', 'descendants', 'etymology', 'file=', 'list', 'no-wiktionary', 'no-tagger',
                                    'lang=', 'romanize', 'help'])
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)

    mode, path, list_only, lang, romanize = 'brief', None, False, 'la', False
    show_descendants = show_etymology = False
    for option, arg in opts:
        if option in ('-t', '--tree'):
            mode = 'tree'
        elif option in ('-d', '--detail'):
            mode = 'detail'
        elif option in ('-f', '--file'):
            path = arg
        elif option in ('-r', '--romanize'):
            romanize = True
        elif option == '--lang':
            if arg not in LANG_FILES:
                print('--lang: %s のどれか' % '|'.join(LANG_FILES))
                sys.exit(1)
            lang = arg
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

    sections = read_sections(path or LANG_FILES[lang])
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
        show(sections, mode, show_descendants, show_etymology, lang, romanize)
    else:
        # パイプやファイルへは色を落として出す
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            show(sections, mode, show_descendants, show_etymology, lang, romanize)
        sys.stdout.write(ANSI.sub('', buf.getvalue()))


if __name__ == '__main__':
    main()
