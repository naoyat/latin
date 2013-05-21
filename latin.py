#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import select
import getopt

from sentence import Word, Sentence

import latin.ansi_color as ansi_color
import latin.textutil as textutil
import latin.latin_char as char
import latin.latindic as latindic

import speak_latin

def lookup_all(surfaces_uc):
    def lookup(surface):
        items = latindic.lookup(surface)
        if items: return Word(surface, items)
        if char.isupper(surface[0]):
            surface_lower = char.tolower(surface)
            items = latindic.lookup(surface_lower)
            if items: return Word(surface, items)
        if surface[-3:] == u'que':
            items = latindic.lookup(surface[:-3])
            if items:
                return Word(surface[:-3], items, {'enclitic':'que'})
        return None

    words = []

    l = len(surfaces_uc)
    i = 0
    while i < l:
        surface = surfaces_uc[i]
        if ord(surface[0]) <= 64: # 辞書引き（記号のみから成る語を除く）
            words.append(Word(surface, None))
            i += 1
            continue
        if i < l-1:
            surface2 = surface + u' ' + surfaces_uc[i+1]
            word2 = lookup(surface2)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if word2 is not None: # len(word2.items) > 0: #is not None: and len(lu2) > 0:
                words.append(word2)
                i += 2
                continue
        word = lookup(surface)
        if word is not None:
            words.append(word)
        else:
            words.append(Word(surface, []))
        i += 1

    return words


# １文に活用動詞が１つ（あるいは0）になるように分断する
def split_sentence_by_verb(words):
    verbs_indices = []

    for i, word in enumerate(words):
        if word.is_verb():
            verbs_indices.append(i)
    # verbs = filter(is_verb, res)
    num_verbs = len(verbs_indices)

    sentences = []

    if num_verbs <= 1:
        sentences.append(Sentence(words))
    else:
        head = 0
        tail = len(words) - 1
        next_idx = tail + 1
        for i, idx in enumerate(verbs_indices):
            if i == num_verbs-1: # last one
                # print words[idx].surface.encode('utf-8')
                sentences.append(Sentence(words[head:]))
            else:
                next_idx = verbs_indices[i+1]
                # （次の動詞の手前までで）今の動詞の守備範囲を探る
                tail = idx + 1
                while tail < next_idx:
                    if words[tail].items is None: # 句読点系
                        sentences.append(Sentence(words[head:tail+1]))
                        break
                    elif words[tail].surface == u'et':
                        tail -= 1
                        sentences.append(Sentence(words[head:tail+1]))
                        break
                    tail += 1
                if tail == next_idx:
                    # 区切り（句読点）がない場合。とりあえず、次の動詞の直前まで取ってしまう
                    # （あとで検討）
                    sentences.append(Sentence(words[head:next_idx]))
                head = tail + 1

    return sentences


def analyse_sentence(surfaces, options=None):
    # words: string(utf-8)
    text = ' '.join(surfaces)

    if options.echo_on:
        print ansi_color.ANSI_UNDERLINE_ON + ansi_color.ANSI_BOLD_ON + \
            text + \
            ansi_color.ANSI_BOLD_OFF + ansi_color.ANSI_UNDERLINE_OFF
        print

    if options.speech_mode:
        speak_latin.say_latin(text.decode('utf-8'))


    surfaces_uc = [surface.decode('utf-8') for surface in surfaces]
    # words = [Word(surface, items) for surface, items in lookup_all_words(words_uc)]
    words = lookup_all(surfaces_uc)
    # dump_res(res)
    # util.pp(map(lambda r:r[0], res))

    for i, sentence in enumerate(split_sentence_by_verb(words)):
        # sentence.count_patterns()
        # 前置詞の格支配を利用して絞り込む
        sentence.prep_constraint()

        # sentence.dot('_'.join([word.surface.encode('utf-8') for word in sentence.words]))
        # 属格支配する形容詞
        sentence.genitive_domination()
        # 形容詞などの性・数・格一致を利用して絞り込む
        sentence.modifier_constraint()
#        sentence.count_patterns()
        # 属格がどこにかかるか
        sentence.genitive_constraint()

        if options and options.show_translation:
            sentence.translate()

        if options and options.show_word_detail:
            if options.show_translation:
                print "  ---"
            sentence.dump()

        print

# read-eval-print loop
def repl(options=None, show_prompt=False):
    while True:
        if show_prompt:
            sys.stdout.write("> ")
            sys.stdout.flush()

        line = sys.stdin.readline()
        if not line: break

        text = line.rstrip()
        if options and not options.strict_macron_mode:
            text = char.trans(text)

        # textutil.analyse_text(text, analyse_sentence)
        for sentence in textutil.sentence_stream(textutil.word_stream_from_text(text)):
            analyse_sentence(sentence, options=options)

    if show_prompt:
        print



class Options:
    def __init__(self, args):
        try:
            opts, self.args = getopt.getopt(args,
                                            "wqmash",
                                            ["no-word-detail",
                                             "no-translation",
                                             "strict-macron",
                                             "auto-macron",
                                             "speech",
                                             "help"])
        except getopt.GetoptError:
            self.usage()
            sys.exit()

        self.show_word_detail = True
        self.show_translation = True
        self.strict_macron_mode = False
        self.auto_macron_mode = False
        self.speech_mode = False
        self.echo_on = True

        for option, arg in opts:
            if option in ('-w', '--no-word-detail'):
                self.show_word_detail = False
            elif option in ('-q', '--no-translation'):
                self.show_translation = False
            elif option in ('-m', '--strict-macron'):
                self.strict_macron_mode = True
            elif option in ('-a', '--auto-macron'):
                self.auto_macron_mode = True
            elif option in ('-s', '--speech'):
                self.speech_mode = True
            elif option in ('-h', '--help'):
                self.usage()
                sys.exit()

    def usage(self):
        print "Usage: python %s [options] [FILENAME]" % sys.argv[0]
        print "Options:"
        print "  -w, --no-word-detail               Don't show word details."
        print "  -q, --no-translation               Don't show the translation (Japanese)."
        print "  -m, --strict-macron                [REPL] Ignore capitalized transcriptions."
        print "  -a, --auto-macron                  Automatically add macrons."
        print "  -s, --speech                       Speak latin."
        print "  -h, --help                         Print this message and exit."


def main():
    options = Options(sys.argv[1:])
    if options.speech_mode:
        speak_latin.init_synth('Alex')

    latindic.load(auto_macron_mode=options.auto_macron_mode)

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
            if options.strict_macron_mode:
                text = char.trans(text)

            # textutil.analyse_text(text, analyse_sentence, options=options)
            for sentence in textutil.sentence_stream(textutil.word_stream_from_text(text)):
                analyse_sentence(sentence, options=options)


if __name__ == '__main__':
    main()
