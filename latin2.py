#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import select
import getopt

import latin.ansi_color as ansi_color
import latin.textutil as textutil
import latin.latin_char as char
import latin.latindic as latindic
import latin.util as util

from latin.Word import Word
from latin.Predicate import Predicate
from latin.AndOr import AndOr, non_genitive
from latin.CasedClause import CasedClause, PrepClause
from latin.Sentence import Sentence

import speak_latin

def identity(x): return x

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
#                return Word(surface[:-3], items, {'enclitic':'que'})
                return Word(surface, items, {'enclitic':'que'})
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

    # words の中での添字情報をWordインスタンスに保存
    for i, word in enumerate(words):
        word.index = i

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
                    if isinstance(words[tail], AndOr):
                        pass
                    elif isinstance(words[tail], CasedClause):
                        pass
                    elif words[tail].items is None: # 句読点系
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


# 前置詞に支配される部分を切り出す
def detect_prep_domination(words):
    M = len(words)
    visited = [False] * M

    i = 0
    while i < M-1:
#        print " WHILE-i : %d/%d" % (i, M-1)
        word = words[i]

        # 前置詞だけ見たいので、Word以外はスキップ
        if not isinstance(word, Word):
            i += 1
            continue # while-i-loop

        # 句読点をスキップ
        if word.items is None:
            i += 1
            continue # while-i-loop

        preps = []
        for item in word.items:
            if item.pos == 'preposition':
                preps.append(item)

        if not preps:
            i += 1
            continue # while-i-loop

        dominates = [x for x in set([item.dominates for item in preps])]
        # print "PREP (%s) DETECTED AT %d :" % (word.surface.encode('utf-8'), i), dominates

        j = i + 1
        while j < M:
            w = words[j]
            if isinstance(w, Word):
                if w.items is None:
                    j += 1
                    continue # while-j-loop
                stop = False
                for k, item in enumerate(w.items):
                    if item.pos in ['verb', 'preposition', 'conj', 'adv']:
                        stop = True
                        break # for-k-loop
                    if item._: # subst
                        if item.pos == 'adj':
                            continue # for-k-loop
                        can_skip = False
                        yes = False
                        for case, number, gender in item._:
                            if case == 'Gen':
                                can_skip = True
                            elif case in dominates:
                                dominates = [case] # 絞り込み
                                yes = True
                                break # for-cng-loop
                            else:
                                pass
                        if not yes and not can_skip:
                            stop = True
                            break # for-k-loop
                if stop:
                    break # while-j-loop
            elif isinstance(w, AndOr):
                pass
            elif isinstance(w, Predicate):
                break # while-j-loop
            else:
                break # while-j-loop
            j += 1

        cl = PrepClause(word, dominates[0], words[i+1:j])
        for ix in range(i, j):
            words[ix] = None
            visited[ix] = True
        words[i] = cl

#        print " [%d..%d]" % (i, j-1),
#        for w in words[i:j]:
#            try:
#                print w.surface.encode('utf-8'),
#            except:
#                pass
##        print u' '.join([w.surface for w in words[i:j]]).encode('utf-8')
#        print
        i = j

    return words


def detect_and_or(words):
    M = len(words)

    surfaces = [word.surface for word in words]
    # カンマや活用動詞で分断しグルーピングする
    groups = []
    curr = []
    for i, surface in enumerate(surfaces):
        if surface in (u',', u'.', u';', u'"', u'!', u'?'):
            groups.append(curr)
            curr = []
        elif words[i].is_verb():
            groups.append(curr)
            curr = []
        else:
            curr.append(i)
    if curr: groups.append(curr)

    # groups: [[0, 1, 2], [4, 5, 6, 7]]

    visited = set() #[False] * M
    ao_loc = set()

    # ある単語 word がグループ group 内で生起する位置（複数）を配列で返す
    #   eg. word_indices_in_group(neque, [0, 1, 2, 3, 4, 5, 6, 7]) -> [2, 4]
    def word_indices_in_group(word, group):
        return filter(lambda x:x>=0, [i if surfaces[i].lower() == word else -1 for i in group])

    # et-et- / neque-neque- の検出
    def detect(and_or_word):
        ao_indices = [word_indices_in_group(and_or_word, group) for group in groups]
        for i, aos in enumerate(ao_indices):
            num_of_ao = len(aos)
            if num_of_ao >= 2:
                upper = and_or_word.upper()
                # print "  %s-%s- found in #%d" % (upper, upper, i), aos
                cl = AndOr(and_or_word)
                # 区間が確定しているもの（＝最後の１つ以外）をまず追加
                for j in range(num_of_ao-1):
                    this_et_idx = aos[j]
                    next_et_idx = aos[j+1]
                    cl.add(words[this_et_idx+1:next_et_idx])
                # 最後の１つは、どこで終わるか確かめながら追加
                last_et_idx = aos[num_of_ao-1]
                end_idx = groups[i][-1] + 1
                ws = []
                for idx in range(last_et_idx+1, end_idx):
                    word = words[idx]
                    first_item = word.items[0]
                    if cl.pos == 'noun':
                        # 格変化のある語に限る
                        if first_item._ is None: break
                        if non_genitive(first_item._):
                            cases = [x[0] for x in first_item._]
                            # これまでの物と格が一致する可能性がなければ排除
                            cases_x = filter(lambda case:case in cases, cl.cases)
                            if not cases_x: break
                    ws.append(word)
                    idx += 1
                if ws:
                    cl.add(ws)
                else:
                    pass # ERROR: type mismatch

                # print "CL: [%d..%d)" % (aos[0], idx)
                # cl.dump()
                for j in range(aos[0], idx):
                    # words[j] = None
                    # visited[j] = True
                    visited.add(j)

                cl.restrict()

                words[aos[0]] = cl
                ao_loc.add(aos[0])
                # aos.append(aos[0])

    detect(u'et')
    detect(u'neque')

    detect(u'aut')


    for i, word in enumerate(words):
        if i in visited: continue
        if not word.items: continue

        surface = word.surface
        if surface == u'et' and i+1 < len(words):
            print "  // %d ET %s" % (i, words[i+1].surface_utf8())

        if surface[-3:] == u'que':
            if surface.lower() not in (u'neque', u'itaque', u'quoque'):
                print "  // %d %s-QUE" % (i, surface[:-3].encode('utf-8'))
    print

    visited_ix = filter(lambda ix:ix not in ao_loc, visited)#[ix for ix in visited])
    return (words, visited_ix)


def detect_verbs(words):
    verb_ix = []

    for i, word in enumerate(words):
        if isinstance(word, AndOr): continue
        if not word.items: continue

        verb_items = filter(lambda item:item.pos == 'verb', word.items)
#        print "\t%d) %s" % (i, word.surface_utf8()), verb_items
        if verb_items and len(verb_items) == len(word.items):
            verb = Predicate(word)
            words[i] = verb
            verb_ix.append(i)
#            print " [%d] %s (verb %d%s)" % (i, verb.surface.encode('utf-8'), verb.person(), verb.number())
            # この動詞に関わるものを拾って繋げたい
#            verbs_at.append(i)
#            verbs[i] = verb

    return (words, verb_ix)


def detect_adj_correspondances(words):
    M = len(words)
    nouns = {}
    adjs = []
    blocks = {}

    for i in range(M):
        word = words[i]
        if isinstance(word, Predicate):
            blocks[i] = word
        elif isinstance(word, AndOr):
            # nouns[i] = word._
            pass
        elif isinstance(word, Word):
            if not word.items: continue
            if word.surface in (u'et', u'neque') or word.items[0].pos == 'preposition':
                blocks[i] = word
                continue

            first_item = word.items[0]
            if first_item.pos in ('adj', 'pp'):
                adjs.append((i, first_item._))
            elif first_item.pos == 'noun':
                nouns[i] = first_item._
            else:
                pass
        else:
            # blocks[i] = word
            pass

    if not adjs: return (words, [])

    def matches(_a, _b):
        return any([b in _a for b in _b])

    def find_target(adj_ix, a_):
        def sub(fr, to, step):
            for i in range(fr, to, step):
                if blocks.has_key(i):
                    return -1
                if not nouns.has_key(i):
                    continue
                n_ = nouns[i]
                if matches(n_, a_):
                    return i
            return -1

        pre = sub(adj_ix-1, -1, -1)
        if pre >= 0: return pre

        post = sub(adj_ix+1, M, 1)
        if post >= 0: return post

        return -1

    as_noun = set()

    for adj_ix, _ in adjs:
        print "ADJ#%d (%s)" % (adj_ix, words[adj_ix].surface_utf8()),
        noun_ix = find_target(adj_ix, _)
        if noun_ix >= 0:
            print "-> NOUN#%d (%s)" % (noun_ix, words[noun_ix].surface_utf8())
            words[noun_ix].add_modifier(words[adj_ix])
#            words[adj_ix] = None
        else:
            print "-> no target noun detected"
            as_noun.add(adj_ix)

    return (words, filter(lambda ix:ix not in as_noun, [adj_ix for adj_ix, _ in adjs]))


def detect_genitive_correspondances(words):
    M = len(words)
    targets = {}
    gen = []
    blocks = {}

    for i in range(M):
        word = words[i]
        if isinstance(word, Predicate):
            pass #blocks[i] = word
        elif isinstance(word, AndOr):
            # targets[i] = word
            if non_genitive(word._):
                pass
            else:
                gen.append(i)
        elif isinstance(word, Word):
            if not word.items: continue

            first_item = word.items[0]
            if word.surface in (u'et', u'neque') or first_item.pos == 'preposition':
                blocks[i] = word
                continue
            if first_item.pos == 'adj' and first_item.attrib('base') == u'plēnus':
                targets[i] = word
                continue

            if first_item.pos != 'noun':
                continue

            targets[i] = word
            if non_genitive(first_item._):
                pass
            else:
                gen.append(i)
        else:
            # blocks[i] = word
            pass

    if not gen: return (words, [])

#    print "non-Gen:", [(ix, word.surface_utf8()) for ix,word in targets.items()]
#    print "    Gen:", gen

    def find_target(gen_ix):
        def sub(fr, to, step):
            for i in range(fr, to, step):
                if blocks.has_key(i):
                    return -1
                if not targets.has_key(i):
                    continue
                return i
            return -1

        pre = sub(gen_ix-1, -1, -1)
        if pre >= 0: return pre

        post = sub(gen_ix+1, M, 1)
        if post >= 0: return post

        return -1

    gen.sort(reverse=True)

    non_gen = set()

    for gen_ix in gen:
        print "GEN#%d (%s)" % (gen_ix, words[gen_ix].surface_utf8()),
        target_ix = find_target(gen_ix)
        if target_ix >= 0:
            print "-> TARGET#%d (%s)" % (target_ix, words[target_ix].surface_utf8())
            words[target_ix].add_modifier(words[gen_ix])
#            words[gen_ix] = None
        else:
            print "-> no target noun detected"
            non_gen.add(gen_ix)
            words[gen_ix].restrict_cases(('Nom','Voc','Acc','Dat','Abl','Loc'))

    return (words, filter(lambda ix:ix not in non_gen, gen))


def dump_words(words):
#    words = sentence.words
    # （表示用に）単語の最大長を得ておく
    maxlen_uc = max([0] + [word.surface_len for word in words])

    def color_for_word(word):
        if word.has_subst_case('Nom'):
            color = ansi_color.BLUE
        elif word.has_subst_case('Acc'):
            color = ansi_color.BLACK
        elif word.has_subst_case('Gen'):
            color = ansi_color.GREEN
        elif word.has_subst_case('Abl'):
            color = ansi_color.YELLOW
        elif word.has_subst_case('Dat'):
            color = ansi_color.MAGENTA
        else:
            color = None # ansi_color.DEFAULT
        return color

    def decolate(word):
        color = color_for_word(word)
        text = word.surface.encode('utf-8')
        if color is not None:
            return ansi_color.bold(text, color)
        else:
            return text

    def render_with_indent(indent, obj):
        if isinstance(obj, Sentence):
            for word in obj.words:
                render_with_indent(indent+2, word)

        elif isinstance(obj, AndOr):
            print ' '*indent + '[' + obj.and_or_word.encode('utf-8') + '] ' # + str(obj._)
            for words in obj.words_slots:
                render_with_indent(indent+2, words[0])

        elif isinstance(obj, PrepClause):
            # print ' '*indent + obj.item.surface.encode('utf-8') + ' ' + obj.item.ja + ' <'+ obj.dominated_case + '>'
            print ' '*indent + obj.item.surface.encode('utf-8') + ' <'+ obj.dominated_case + '>'
            for word in obj.words:
                render_with_indent(indent+2, word)

#        elif isinstance(obj, CasedClause):
#            pass

        elif isinstance(obj, Word):
            if not obj.items: return

            text = decolate(obj)
            if obj.items[0].pos in ('conj', 'adv'):
                text = '(' + text + ')'
            print ' '*indent + text # word.surface.encode('utf-8')
            for mod in obj.modifiers:
                render_with_indent(indent+2, mod)
#                print '    ' + mod.surface.encode('utf-8')

        elif isinstance(obj, Predicate):
            text = obj.surface.encode('utf-8')
            text = ansi_color.underline(ansi_color.bold(text, ansi_color.RED))
            print ' '*indent + text, "(%s %s%s)" % (obj.mood(), str(obj.person()), obj.number())

        elif isinstance(obj, list):
            for item in obj:
                render_with_indent(indent+2, item)
#        elif isinstance(obj, unicode):
#            print ' '*indent + obj.encode('utf-8')

#        else:
#            print ' '*indent + str(obj)

    print
    render_with_indent(0, words)
    print


def analyse_text(text, options=None):
    # テキストを（句点などで）センテンスに切り分ける
    for word_surfaces_in_a_sentence in textutil.sentence_stream(textutil.word_stream_from_text(text)):
        plain_text = ' '.join(word_surfaces_in_a_sentence)
        if options.echo_on:
            # print plain_text + "\n"
            print ansi_color.underline(ansi_color.bold( plain_text )) + "\n"
        if options.speech_mode:
            speak_latin.say_latin(plain_text.decode('utf-8'))

        # unicodeに変換して
        word_surfaces_uc = [word_surface.decode('utf-8', 'strict') for word_surface in word_surfaces_in_a_sentence]
        # 辞書を引いてから
        words = lookup_all(word_surfaces_uc)

        # 先にlookup結果を表示してしまう
        if options and options.show_word_detail:
            print "  --- "
            maxlen_uc = max([0] + [word.surface_len for word in words])
            for i, word in enumerate(words):
                text = word.surface.encode('utf-8')
                print '  %2d  ' % (i) + text + ' '*(maxlen_uc - word.surface_len + 1), word.detail()
            print "  --- "
            print

        # 形容詞/属格の対応
        words, visited_ix = detect_and_or(words)
#        print "VX", visited_ix
        words, adj_ix = detect_adj_correspondances(words)
#        print "AX", adj_ix
        words, gen_ix = detect_genitive_correspondances(words)
#        print "GX", gen_ix
        for ix in visited_ix:
            words[ix] = None
        for ix in adj_ix:
            words[ix] = None
        for ix in gen_ix:
            words[ix] = None
        words = filter(identity, words)

        words, verb_ix = detect_verbs(words)

        words = detect_prep_domination(words)
        words = filter(identity, words)
#        print [word.surface_utf8() for word in words]

        print

        # 名詞句を述語動詞に結びつける
        verb_ix = []
        verb_count = 0
        for i, word in enumerate(words):
            if isinstance(word, Predicate):
                verb_ix.append(i)
                verb_count += 1

        M = len(words)
        groups = []
        if verb_count == 0:
            print "NO VERB FOUND."
        elif verb_count == 1:
            print "1 VERB FOUND:"
            groups.append( range(M) )
        else:
            print "%d VERBS FOUND:" % verb_count
            groups.append( range(verb_ix[0]+1) ) # [0..ix0]
            for i in range(1, verb_count-1):
                groups.append( [verb_ix[i]] )
            groups.append( range(verb_ix[verb_count-1], M) )
            for i in range(verb_count-1):
                fr = groups[i][-1] + 1
                to = groups[i+1][0] - 1
                well_divided_at = None
                for j in range(fr, to+1):
                    if words[j].surface == u',':
                        well_divided_at = j
                        break
                if well_divided_at is None:
                    for j in range(fr, to+1):
                        if words[j].surface == u'et':
                            well_divided_at = j
                            break
                if well_divided_at is not None:
                    groups[i] += range(fr, well_divided_at+1)
                    groups[i+1] = range(well_divided_at+1, to+1) + groups[i+1]
                else:
                    print "  NOT WELL: {%d..%d}" % (fr, to)
                    # うまく分けられない。とりあえず後の方に入れる
                    groups[i+1] = range(fr, to+1) + groups[i+1]

        print groups

        for group in groups:
            words_in_group = [words[ix] for ix in group]
            dump_words(words_in_group)
#            print

#        # 解析
#        # analyse(words, options)
#        sentences = split_sentence_by_verb(words)
#        for sentence in sentences:
#            if options and options.show_word_detail:
##                if options.show_translation:
##                    print "  ---"
#                dump_words(sentence.words)
##                sentence.dump()

#    if options and options.show_word_detail:
#        if options.show_translation:
#            print "  ---"
#        dump_words(sentence.words)
##        sentence.dump()

#        # 音読モードの場合、読み終わるまでウェイトを入れる
#        if options.speech_mode:
#            speak_latin.pause_while_speaking()


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

        analyse_text(text, options)

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
        print "  -s, --speech                       Speak latin. (MacOS only)"
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

            analyse_text(text, options)

if __name__ == '__main__':
    main()
