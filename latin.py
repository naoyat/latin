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

from latin.LatinObject import LatinObject
from latin.Word import Word
from latin.Predicate import Predicate
from latin.AndOr import AndOr, non_genitive
from latin.PrepClause import PrepClause
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

    def same(word1, word2, pos_check=True):
        if not word1.items or not word2.items:
            return False
        item1 = word1.items[0]
        item2 = word2.items[0]
        if pos_check and item1.pos != item2.pos:
            return False
        if item1.pos == 'verb':
            return False
        cases1 = [x[0] for x in item1._]
        cases2 = [x[0] for x in item2._]
        cases = filter(lambda case:case in cases2, cases1)
        if cases:
            return True
        return False


#    print
    for i, word in enumerate(words):
        if i in visited: continue
        if not word.items: continue

        # A et B
        def bind_two_if_same():
            word1 = words[i-1]
            word2 = words[i+1]
            if same(word1, word2):
                print "// #%d ET #%d: %s == %s" % (i-1, i+1, word1.surface_utf8(), word2.surface_utf8())
                cl = AndOr(u'et')
                cl.add([word1])
                cl.add([word2])
                for j in range(i-1, i+2):
                    visited.add(j)
                words[i-1] = cl
                ao_loc.add(i-1)
                return True
            else:
                return False

        # A [adj] et B [adj]
        def bind_more_if_same():
            word1 = words[i-2]
            word1a = words[i-1]
            if not word1a.items or word1a.items[0].pos != 'adj':
                return False
            if not same(word1, word1a, pos_check=False):
                return False

            word2 = words[i+1]
            with_2a = False
            if i+2 < M:
                word2a = words[i+2]
                if word2a.items and word2a.items[0].pos == 'adj':
                    if same(word2, word2a, pos_check=False):
                        with_2a = True

            if same(word1, word2):
                print "// #%d #%d ET #%d (#%d): %s == %s" % (i-2, i-1, i+1, i+2, word1.surface_utf8(), word2.surface_utf8())
                cl = AndOr(u'et')
                word1.add_modifier(word1a)
                cl.add([word1])
                visited.add(i-2)
                visited.add(i-1)

                if with_2a:
                    word2.add_modifier(word2a)
                    visited.add(i+2)
                cl.add([word2])
                visited.add(i+1)

                words[i-2] = cl
                ao_loc.add(i-2)
                return True
            else:
                return False

        surface = word.surface
        if surface == u'et' and i+1 < len(words):
            # print "// %d ET %s" % (i, words[i+1].surface_utf8())
            if i >= 1:
                if not bind_two_if_same() and i >= 2:
                    bind_more_if_same()

        if surface[-3:] == u'que':
            if surface.lower() not in (u'neque', u'itaque', u'quoque'):
                # print "// %d %s-QUE" % (i, surface[:-3].encode('utf-8'))
                if i >= 1:
                    if not bind_two_if_same() and i >= 2:
                        bind_more_if_same()

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
            if word.pos == 'adj':
                # print "ADJ.", i, word._
                adjs.append((i, word._))
        elif isinstance(word, Word):
            if not word.items: continue
            if word.surface in (u'et', u'neque') or word.items[0].pos == 'preposition':
                blocks[i] = word
                continue

            first_item = word.items[0]
            if first_item.pos == 'verb':
                blocks[i] = word
                continue
            elif first_item.pos in ('adj', 'pp'):
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
        print "// ADJ#%d (%s)" % (adj_ix, words[adj_ix].surface_utf8()),
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
            if not non_genitive(word._) and word._[0][0] == 'Gen':
                gen.append(i)
        elif isinstance(word, Word):
            if not word.items:
                blocks[i] = word
                continue

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
            if not non_genitive(first_item._) and first_item._[0][0] == 'Gen':
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
        print "// GEN#%d (%s)" % (gen_ix, words[gen_ix].surface_utf8()),
        target_ix = find_target(gen_ix)
        if target_ix >= 0:
            print "-> TARGET#%d (%s)" % (target_ix, words[target_ix].surface_utf8())
            words[target_ix].add_genitive(words[gen_ix])
#            words[gen_ix] = None
        else:
            print "-> no target noun detected"
            non_gen.add(gen_ix)
            words[gen_ix].restrict_cases(('Nom','Voc','Acc','Dat','Abl','Loc'))

    return (words, filter(lambda ix:ix not in non_gen, gen))


def decolate(word):
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

        elif isinstance(obj, Word):
            if not obj.items: return

            text = decolate(obj)
            if obj.items[0].pos in ('conj', 'adv'):
                text = '(' + text + ')'
            print ' '*indent + text # word.surface.encode('utf-8')
            for gen in obj.genitives:
                render_with_indent(indent+2, gen)
            for mod in obj.modifiers:
                render_with_indent(indent+2, mod)
#                print '    ' + mod.surface.encode('utf-8')

        elif isinstance(obj, Predicate):
            text = obj.surface.encode('utf-8')
            text = ansi_color.underline(ansi_color.bold(text, ansi_color.RED))
            print ' '*indent + text, "(%s %s%s)" % (obj.mood(), str(obj.person()), obj.number())
            if obj.conjunction:
                render_with_indent(indent+2, obj.conjunction)
            for mod in obj.modifiers:
                render_with_indent(indent+2, mod)
            for case, objs in obj.case_slot.items():
                if isinstance(case, unicode):
                    print ' '*(indent+2) + "prep:"
                else:
                    print ' '*(indent+2) + case + ":"
                for obj in objs:
                    render_with_indent(indent+4, obj)

        elif isinstance(obj, list):
            for item in obj:
                render_with_indent(indent+2, item)
#        elif isinstance(obj, unicode):
#            print ' '*indent + obj.encode('utf-8')

        #        else:
#            print ' '*indent + str(obj)


def dump(obj, initial_indent=2):
#    print
    render_with_indent(initial_indent, obj)
#    print ' '*initial_indent + '--'


def translate(obj):
    if isinstance(obj, list):
        return ' // '.join([translate(item) for item in obj])
    elif isinstance(obj, LatinObject):
        return obj.translate()[0]
#    elif isinstance(obj, Predicate):
#        return obj.translate()
#    elif isinstance(obj, Word) or isinstance(obj, AndOr) or isinstance(obj, PrepClause):
#        return obj.translate()[0]
#        if not obj.items:
#            return ""
#        else:
#            return obj.translate() # obj.items[0].ja
    else:
        print "？？？"


def analyse_text(text, options=None):
    # テキストを（句点などで）センテンスに切り分ける
    for word_surfaces_in_a_sentence in textutil.sentence_stream(textutil.word_stream_from_text(text)):
        plain_text = ' '.join(word_surfaces_in_a_sentence)
        if options.echo_on:
            # print plain_text + "\n"
            print "\n" + ansi_color.underline(ansi_color.bold( plain_text )) + "\n"
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
        words, adj_ix = detect_adj_correspondances(words)
        words, gen_ix = detect_genitive_correspondances(words)
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
        verbs_ix = []
        verb_count = 0
        for i, word in enumerate(words):
            if isinstance(word, Predicate):
                verbs_ix.append(i)
                verb_count += 1

        verb_surfaces = ', '.join([ansi_color.bold(words[ix].surface_utf8()) for ix in verbs_ix])
        M = len(words)
        groups = []
        if verb_count == 0:
            print ansi_color.underline("NO VERB FOUND.")
            groups.append( range(M) )
        elif verb_count == 1:
            print ansi_color.underline("1 VERB FOUND:") + ' ' + verb_surfaces
            groups.append( range(M) )
        else:
            print ansi_color.underline("%d VERBS FOUND:" % verb_count) + ' ' + verb_surfaces
            groups.append( range(verbs_ix[0]+1) ) # [0..ix0]
            for i in range(1, verb_count-1):
                groups.append( [verbs_ix[i]] )
            groups.append( range(verbs_ix[verb_count-1], M) )
            for i in range(verb_count-1):
                fr = groups[i][-1] + 1
                to = groups[i+1][0] - 1
                if fr == to: continue

                well_divided_at = None
                for j in range(fr, to+1):
                    if words[j].surface == u',':
                        well_divided_at = j
                        break
                if well_divided_at is None:
                    for j in range(fr, to+1):
                        if words[j].surface == u'quod':
                            well_divided_at = j-1
                            break
                if well_divided_at is None:
                    for j in range(fr, to+1):
                        if words[j].surface == u'et':
                            well_divided_at = j-1
                            break
                if well_divided_at is not None:
                    groups[i] += range(fr, well_divided_at+1)
                    groups[i+1] = range(well_divided_at+1, to+1) + groups[i+1]
                else:
                    print "  NOT WELL: {%d..%d}" % (fr, to)
                    # うまく分けられない。とりあえず後の方に入れる
                    groups[i+1] = range(fr, to+1) + groups[i+1]

        print
        for i, group in enumerate(groups):
            if verb_count == 0:
                ws = []
                for word in words:
                    if isinstance(word, Word) and not word.items: continue
                    # ws.append(word)
                    dump(word)
                    print "  → ", translate(word)
                    print # "  --"
                # dump(ws)
                # print translate(ws)
            else:
                not_solved = []
                # words_in_group = [words[ix] for ix in group]
                verb_ix = verbs_ix[i]
                pred = words[verb_ix] # predicate
                for j, ix in enumerate(group):
                    if ix == verb_ix: continue
                    word = words[ix]
                    if isinstance(word, AndOr):
                        pred.add_nominal(word.cases[0], word)
                    elif isinstance(word, PrepClause):
                        pred.add_nominal(word.prep, word)
                    elif isinstance(word, Word):
                        if not word.items: continue
                        first_item = word.items[0]
                        if j == 0 and word.surface in (u'quod', u'ut'):
                            if word.items[1].pos == 'conj':
                                first_item = word.items[1]
                                word.items = word.items[1:]
                        if first_item.pos == 'conj':
                            if j < 2 and not pred.conjunction:
                                pred.conjunction = word
                            else:
                                not_solved.append(word)
                        elif first_item.pos == 'adv':
                            if j < 2 and not pred.conjunction:
                                pred.conjunction = word
                            elif word.surface in (u'ō', u'Ō'):
                                # 二重になってないかチェックする or conjunction を複数取る
                                pred.conjunction = word
                            else:
                                pred.add_modifier(word)
                        elif first_item._:
                            cases = [x[0] for x in first_item._]
                            case = None
                            if 'Voc' in cases and ix > 0 and words[ix-1].surface in (u'ō', u'Ō'):
                                case = 'Voc'
                                # 形的にVocしかありえないケースも拾いたい
                            else:
                                for x in first_item._:
                                    if x[0] == 'Nom':
                                        if x[2] == 'n':
                                            case = 'Nom/Acc'
                                        else:
                                            case = x[0]
                                        break
                                    elif x[0] == 'Acc':
                                        case = x[0]
                                        break
                                    else:
                                        if not case:
                                            case = x[0]

                            # if not case: case = case_n
                            pred.add_nominal(case, word)
                        else:
                            # print "not solved += ", word.surface_utf8()
                            not_solved.append(word) #(ix, word.surface_utf8()))

                if not_solved:
                    print "  NOT SOLVED:"
                    # dump(not_solved, initial_indent=2)
                    # print translate(not_solved)
                    for item in not_solved:
                        dump(item, 4)
                        print "    → ", translate(item)
                        print

                dump(pred)
                print
                print "  → ", translate(pred)
                print

        # 音読モードの場合、読み終わるまでウェイトを入れる
        # if options.speech_mode:
        #     speak_latin.pause_while_speaking()


def do_command(line, options=None):
    fs = line.split(' ')
    cmd = fs[0]

    def surface_tr():
        surface = ' '.join(fs[1:])
        if options and options.capital_to_macron_mode:
            surface = char.trans(surface)
        return surface

    # 辞書検索
    if cmd in ('l', 'lookup'):
        surface = surface_tr()
        print "lookup", surface,

        items = latindic.lookup(surface.decode('utf-8'))
        util.pp(items)

    # 動詞の活用を見る
    elif cmd in ('c', 'conjug'):
        surface_uc = surface_tr().decode('utf-8')
        table = {}
        ja = None
        moods = set()
        voices = set()
        tenses = set()
        for word, items in latindic.LatinDic.dic.items():
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
                    if table.has_key(key):
                        table[key].append(item_surface)
                    else:
                        table[key] = [item_surface]

        def surfaces(key):
            if table.has_key(key):
                return ', '.join([surface.encode('utf-8') for surface in table[key]])
            else:
                return '-'

        print "%s, %s" % (surface_uc.encode('utf-8'), ja)
        for mood in ['indicative', 'subjunctive', 'imperative']:
            if mood not in moods: continue
            print "  %s" % mood
            for voice in ['active', 'passive']:
                if mood + voice not in voices: continue
                print "    %s" % voice
                for tense in ['present', 'imperfect', 'future',
                              'perfect', 'past-perfect', 'future-perfect']:
                    if mood + voice + tense not in tenses: continue
                    print "      %s" % tense
                    for number in ['sg','pl']:
                        print "        %s" % number
                        for person in [1,2,3]:
                            key = (mood, voice, tense, person, number)
                            if table.has_key(key):
                                print "          %d: %s" % (person, surfaces(key))
        print "  infinitive"
        print "    present: %s" % surfaces(('infinitive','active','present',None,None))
        print "    perfect: %s" % surfaces(('infinitive','active','perfect',None,None))
        print "    future: %s" % surfaces(('infinitive','active','future',None,None))

    # 名詞の変化形を見る
    elif cmd in ('d', 'decl'):
        surface_uc = surface_tr().decode('utf-8')
        table = {}
        base = None
        ja = None
        pos = None
        gender = None
        for word, items in latindic.LatinDic.dic.items():
            for item in items:
                item_base = item.get('base', None)
                if item_base == surface_uc:
                    for case, number, gender in item['_']:
                        key = (case,number,gender)
                        item_surface = item['surface']
                        if table.has_key(item_surface):
                            table[key].append(item_surface)
                        else:
                            table[key] = [item_surface]
                        if not pos:
                            pos = item['pos']
                            gender = item['_'][0][2]
                            base = item['base']
                            ja = item['ja']
        def surfaces(key):
            if table.has_key(key):
                return ', '.join([surface.encode('utf-8') for surface in table[key]])
            else:
                return '-'

        if pos == 'noun':
            print "%s (%s, %s), %s" % (base.encode('utf-8'), pos, gender, ja)
            for number in ['sg', 'pl']:
                print "  %s:" % number
                for case in ['Nom', 'Voc', 'Acc', 'Gen', 'Dat', 'Abl', 'Loc']:
                    key = (case, number, gender)
                    if table.has_key(key):
                        print "    %s: %s" % (case, surfaces(key))

    else:
        print "COMMAND NOT SUPPORTED: %s, with \"%s\"" % (cmd, surface_tr())

# read-eval-print loop
def repl(options=None, show_prompt=False):
    while True:
        if show_prompt:
            sys.stdout.write("> ")
            sys.stdout.flush()

        line = sys.stdin.readline()
        if not line: break

        text = line.rstrip()
        if text[0] == '.':
            do_command(text[1:], options=options)
        else:
            if options and options.capital_to_macron_mode:
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
                                             "capital-to-macron",
                                             "auto-macron",
                                             "speech",
                                             "help"])
        except getopt.GetoptError:
            self.usage()
            sys.exit()

        self.show_word_detail = True
        self.show_translation = True
        self.capital_to_macron_mode = False
        self.auto_macron_mode = False
        self.speech_mode = False
        self.echo_on = True

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
            elif option in ('-h', '--help'):
                self.usage()
                sys.exit()

    def usage(self):
        print "Usage: python %s [options] [FILENAME]" % sys.argv[0]
        print "Options:"
        print "  -w, --no-word-detail               Don't show word details."
        print "  -q, --no-translation               Don't show the translation (Japanese)."
        print "  -m, --capital-to-macron            [REPL] read capitalized vowels as macrons."
        print "  -a, --auto-macron                  Automatically add macrons."
        print "  -s, --speech                       Speak latin. (MacOS only)"
        print "  -h, --help                         Print this message and exit."


def main():
    options = Options(sys.argv[1:])
    #if options.speech_mode:
    #    speak_latin.init_synth('Alex')

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
            if options and options.capital_to_macron_mode:
                text = char.trans(text)

            analyse_text(text, options)

if __name__ == '__main__':
    main()
