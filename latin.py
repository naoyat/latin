#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import select
import getopt

import latin.textutil as textutil
import latin.latin_char as char
import latin.latindic as latindic
import latin.util as util
from latin import analyzer
from latin import render
from latin import macronizer

from latin import speech as speak_latin

def analyse_text(text, options):
    if options.auto_macron_mode:
        # マクロンの無い入力にマクロンを推定して付けてから解析する
        text = macronizer.macronize_text(text)
    for analysis in analyzer.analyze_text(text):
        if options.echo_on:
            render.render_sentence_header(analysis.text)
        if options.speech_mode:
            speak_latin.say_latin(analysis.text)

        render.render_analysis(analysis, show_word_detail=options.show_word_detail,
                               show_translation=options.show_translation,
                               show_descendants=options.show_descendants,
                               show_etymology=options.show_etymology)

        # 音読モードの場合、読み終わるまでウェイトを入れる
        if options.speech_mode:
            speak_latin.pause_while_speaking()


def do_command(line, options=None):
    fs = line.split(' ')
    cmd = fs[0]

    def surface_tr():
        surface = ' '.join(fs[1:])
        if options and options.capital_to_macron_mode:
            surface = char.trans(surface)
        return surface

    # マクロンの推定
    if cmd in ('m', 'macron'):
        print(macronizer.macronize_text(' '.join(fs[1:])))

    # 辞書検索
    elif cmd in ('l', 'lookup'):
        surface = surface_tr()
        print("lookup", surface, end=' ')

        items = latindic.lookup(surface) #.decode('utf-8'))
        util.pp(items)

    # 動詞の活用を見る
    elif cmd in ('c', 'conjug'):
        surface_uc = surface_tr() #.decode('utf-8')
        table = {}
        ja = None
        moods = set()
        voices = set()
        tenses = set()
        for word, items in list(latindic.LatinDic.dic.items()):
            for item in items:
                pres1sg = item.get('pres1sg', None)
                if pres1sg == surface_uc:
                    if not ja: ja = item['ja']
                    mood = item.get('mood', '-')
                    moods.add(mood)
                    voice = item.get('voice', '-')
                    voices.add(mood + voice)
                    tense = item.get('tense', '-')
                    tenses.add(mood + voice + tense)
                    person = item.get('person', None)
                    number = item.get('number', None)
                    key = (mood,voice,tense,person,number)
                    item_surface = item['surface']
                    if key in table:
                        table[key].append(item_surface)
                    else:
                        table[key] = [item_surface]

        def surfaces(key):
            if key in table:
                return ', '.join(table[key])
            else:
                return '-'

        print("%s, %s" % (surface_uc, ja))
        for mood in ['indicative', 'subjunctive', 'imperative']:
            if mood not in moods: continue
            print("  %s" % mood)
            for voice in ['active', 'passive']:
                if mood + voice not in voices: continue
                print("    %s" % voice)
                for tense in ['present', 'imperfect', 'future',
                              'perfect', 'past-perfect', 'future-perfect']:
                    if mood + voice + tense not in tenses: continue
                    print("      %s" % tense)
                    for number in ['sg','pl']:
                        print("        %s" % number)
                        for person in [1,2,3]:
                            key = (mood, voice, tense, person, number)
                            if key in table:
                                print("          %d: %s" % (person, surfaces(key)))
        print("  infinitive")
        print("    present: %s" % surfaces(('infinitive','active','present',None,None)))
        print("    perfect: %s" % surfaces(('infinitive','active','perfect',None,None)))
        print("    future: %s" % surfaces(('infinitive','active','future',None,None)))

    # 名詞の変化形を見る
    elif cmd in ('d', 'decl'):
        surface_uc = surface_tr() #.decode('utf-8')
        table = {}
        base = None
        ja = None
        pos = None
        gender = None
        for word, items in list(latindic.LatinDic.dic.items()):
            for item in items:
                item_base = item.get('base', None)
                if item_base == surface_uc:
                    for case, number, item_gender in item['_']:
                        key = (case, number, item_gender)
                        item_surface = item['surface']
                        if key in table:
                            table[key].append(item_surface)
                        else:
                            table[key] = [item_surface]
                        if not pos:
                            pos = item['pos']
                            gender = item['_'][0][2]
                            base = item['base']
                            ja = item['ja']
        def surfaces(key):
            if key in table:
                return ', '.join(table[key])
            else:
                return '-'

        if pos == 'noun':
            print("%s (%s, %s), %s" % (base, pos, gender, ja))
            for number in ['sg', 'pl']:
                print("  %s:" % number)
                for case in ['Nom', 'Voc', 'Acc', 'Gen', 'Dat', 'Abl', 'Loc']:
                    key = (case, number, gender)
                    if key in table:
                        print("    %s: %s" % (case, surfaces(key)))

    else:
        print("COMMAND NOT SUPPORTED: %s, with \"%s\"" % (cmd, surface_tr()))

# read-eval-print loop
def repl(options=None, show_prompt=False):
    while True:
        if show_prompt:
            sys.stdout.write("> ")
            sys.stdout.flush()

        line = sys.stdin.readline()
        if not line: break

        text = line.rstrip()
        if not text: continue
        if text[0] == '.':
            do_command(text[1:], options=options)
        else:
            if options and options.capital_to_macron_mode:
                text = char.trans(text)
            analyse_text(text, options)

    if show_prompt:
        print()



class Options:
    def __init__(self, args):
        try:
            opts, self.args = getopt.getopt(args,
                                            "wqmast:DEh",
                                            ["no-word-detail",
                                             "no-translation",
                                             "capital-to-macron",
                                             "auto-macron",
                                             "speech",
                                             "tts=",
                                             "accent=",
                                             "no-wiktionary",
                                             "descendants",
                                             "etymology",
                                             "help"])
        except getopt.GetoptError:
            self.usage()
            sys.exit()

        self.show_word_detail = True
        self.show_translation = True
        self.capital_to_macron_mode = False
        self.auto_macron_mode = False
        self.speech_mode = False
        self.tts_backend = None  # speak_latin の既定 (mbrola、使えなければ espeak)
        self.accent = 'pitch'
        self.echo_on = True
        self.show_descendants = False
        self.show_etymology = False

        for option, arg in opts:
            if option in ('-w', '--no-word-detail'):
                self.show_word_detail = False
            elif option in ('-q', '--no-translation'):
                self.show_translation = False
            elif option in ('-m', '--capital-to-macron'):
                self.capital_to_macron_mode = True
            elif option in ('-a', '--auto-macron'):
                self.auto_macron_mode = True
            elif option in ('-s', '--speech'):
                self.speech_mode = True
            elif option in ('-t', '--tts'):
                self.speech_mode = True
                self.tts_backend = arg
            elif option == '--no-wiktionary':
                latindic.LatinDic.use_wiktionary = False
            elif option == '--accent':
                self.speech_mode = True
                self.accent = arg
            elif option in ('-D', '--descendants'):
                self.show_descendants = True
            elif option in ('-E', '--etymology'):
                self.show_etymology = True
            elif option in ('-h', '--help'):
                self.usage()
                sys.exit()

    def usage(self):
        print("Usage: python %s [options] [FILENAME]" % sys.argv[0])
        print("Options:")
        print("  -w, --no-word-detail               Don't show word details.")
        print("  -q, --no-translation               Don't show the translation (Japanese).")
        print("  -m, --capital-to-macron            [REPL] read capitalized vowels as macrons.")
        print("  -a, --auto-macron                  Guess macrons for input without them.")
        print("  -s, --speech                       Speak latin.")
        print("  -t, --tts=BACKEND                  Speak latin with BACKEND (mbrola [default], espeak, piper)")
        print("      --accent=ACCENT                [mbrola] pitch (default) or stress")
        print("      --no-wiktionary                Use only the hand-made dictionary.")
        print("  -D, --descendants                  Show descendants (French, English, ...) of each word.")
        print("  -E, --etymology                    Show etymology (ancestors, cognates) of each word.")
        print("  -h, --help                         Print this message and exit.")


def main():
    options = Options(sys.argv[1:])
    if options.speech_mode:
        speak_latin.set_accent(options.accent)
        speak_latin.init_synth(options.tts_backend)

    latindic.load()

    if len(options.args) == 0:
        # repl mode
        if select.select([sys.stdin,],[],[],0.0)[0]:
            # have data from pipe. no prompt.
            repl(options=options)
        else:
            repl(options=options, show_prompt=True)
    else:
        # file mode
        for file in options.args:
            text = textutil.load_text_from_file(file)
            if options and options.capital_to_macron_mode:
                text = char.trans(text)

            analyse_text(text, options)

if __name__ == '__main__':
    main()
