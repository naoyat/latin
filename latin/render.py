#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析結果 (latin.analyzer.SentenceAnalysis) の端末表示
#
from . import ansi_color
from .LatinObject import LatinObject
from .Word import Word
from .Predicate import Predicate
from .AndOr import AndOr
from .PrepClause import PrepClause
from .Absolute import AblativeAbsolute
from . import descendants
from .Participle import ParticiplePhrase
from .Infinitive import InfinitiveClause


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
    text = word.surface
    if color is not None:
        return ansi_color.bold(text, color)
    else:
        return text


def render_with_indent(indent, obj):
        if isinstance(obj, AndOr):
            print(' '*indent + '[' + obj.and_or_word + '] ') # + str(obj._)
            for words in obj.words_slots:
                render_with_indent(indent+2, words[0])

        elif isinstance(obj, AblativeAbsolute):
            text = ansi_color.underline(obj.verb.surface)
            print(' '*indent + '[abl.abs] ' + text, '(%s)' % obj.kind())
            render_with_indent(indent+2, obj.subject)
            for c in obj.complements:
                render_with_indent(indent+2, c)

        elif isinstance(obj, InfinitiveClause):
            print(' '*indent + '[infinitive%s]' % (' ' + obj.kind if obj.kind else ''))
            render_with_indent(indent+2, obj.predicate)

        elif isinstance(obj, ParticiplePhrase):
            text = ansi_color.underline(obj.verb.surface)
            label = 'participle' if obj.adverbial else 'participle.attr'
            print(' '*indent + '[%s] ' % label + text, '(%s)' % obj.kind())
            for c in obj.complements:
                render_with_indent(indent+2, c)

        elif isinstance(obj, PrepClause):
            # print ' '*indent + obj.item.surface.encode('utf-8') + ' ' + obj.item.ja + ' <'+ obj.dominated_case + '>'
            print(' '*indent + obj.item.surface + ' <'+ obj.dominated_case + '>')
            for word in obj.words:
                render_with_indent(indent+2, word)

        elif isinstance(obj, Word):
            if not obj.items: return

            text = decolate(obj)
            if obj.items[0].pos in ('conj', 'adv'):
                text = '(' + text + ')'
            print(' '*indent + text) # word.surface.encode('utf-8')
            for gen in obj.genitives:
                render_with_indent(indent+2, gen)
            for mod in obj.modifiers:
                render_with_indent(indent+2, mod)
#                print '    ' + mod.surface.encode('utf-8')

        elif isinstance(obj, Predicate):
            text = obj.surface
            text = ansi_color.underline(ansi_color.bold(text, ansi_color.RED))
            print(' '*indent + text, "(%s %s%s)" % (obj.mood(), str(obj.person()), obj.number()))
            if obj.conjunction:
                render_with_indent(indent+2, obj.conjunction)
            for mod in obj.modifiers:
                render_with_indent(indent+2, mod)
            for clause in obj.subordinates:
                render_with_indent(indent+2, clause)
            for case, objs in list(obj.case_slot.items()):
                if isinstance(case, tuple):
                    print(' '*(indent+2) + "prep:")
                else:
                    print(' '*(indent+2) + case + ":")
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
        print("？？？")


def render_sentence_header(text):
    print("\n" + ansi_color.underline(ansi_color.bold(text)) + "\n")


def render_analysis(analysis, show_word_detail=True, show_translation=True, show_descendants=False):
    # 辞書引きの結果 (show_descendants なら、語ごとに英語・フランス語などに残った語も)
    if show_word_detail:
        print("  --- ")
        maxlen_uc = max([0] + [word.surface_len for word in analysis.words])
        for i, (word, detail) in enumerate(zip(analysis.words, analysis.word_details)):
            print('  %2d  ' % (i,) + word.surface + ' '*(maxlen_uc - word.surface_len + 1), detail)
            if show_descendants and word.items:
                for lemma, text in descendants.describe_word(word):
                    print(' ' * (maxlen_uc + 7) + ansi_color.fgcolor(ansi_color.CYAN, '%s: %s' % (lemma, text)))
        print("  --- ")
        print()

    # 構造化の途中経過
    for line in analysis.trace:
        print(line)
    print()

    verb_count = len(analysis.verbs)
    verb_surfaces = ', '.join([ansi_color.bold(verb.surface_utf8()) for verb in analysis.verbs])
    if verb_count == 0:
        print(ansi_color.underline("NO VERB FOUND."))
    elif verb_count == 1:
        print(ansi_color.underline("1 VERB FOUND:") + ' ' + verb_surfaces)
    else:
        print(ansi_color.underline("%d VERBS FOUND:" % verb_count) + ' ' + verb_surfaces)
    for line in analysis.grouping_trace:
        print(line)
    print()

    if verb_count == 0:
        for node in analysis.nodes:
            if isinstance(node, Word) and not node.items: continue
            dump(node)
            if show_translation:
                print("  → ", translate(node))
            print()
        return

    for clause in analysis.clauses:
        if clause.not_solved:
            print("  NOT SOLVED:")
            for item in clause.not_solved:
                dump(item, 4)
                if show_translation:
                    print("    → ", translate(item))
                print()

        dump(clause.predicate)
        print()
        if show_translation:
            print("  → ", translate(clause.predicate))
            print()
