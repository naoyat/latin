#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin.util as util # render

from latin.LatinObject import LatinObject
from latin.Item import Item

class Word (LatinObject):
    # has surface
    # has items
    def __init__(self, surface, items=None, extra_info={}):
        self.surface = surface
        self.surface_len = len(surface)
        if items is not None:
            self.items = map(Item, items) # へぇーこれで行けるんだ
        else:
            self.items = None
        self.extra_info = extra_info
        self._is_verb = None
        self._is_subj_verb = None
#        self.negated = False
        self.index = None
        self.modifiers = []
        self.genitives = []

    def add_modifier(self, word):
        self.modifiers.append(word)

    def add_genitive(self, word):
        self.genitives.append(word)

    def has_subst_case(self, case):
        # subst = ['noun','pronoun','adj','participle']
        subst = ['noun','pronoun']

        if not self.items: return False
        elif any([item.match_case(subst,case) for item in self.items]): return True
        elif any([item.pos == 'preposition' and item.dominates == case for item in self.items]): return True
        else: return False

    # 活用動詞ならtrue
    def is_verb(self):
        if self._is_verb is None: # memoize
            if self.items is None:
                self._is_verb = False
            else:
                self._is_verb = len(self.items) > 0 and all([item.pos == 'verb' and item.attrib('mood') == 'indicative' for item in self.items])
        return self._is_verb

    # 接続法動詞ならtrue
    def is_subj_verb(self):
        if self._is_subj_verb is None: # memoize
            if self.items is None:
                self._is_subj_verb = False
            else:
                self._is_subj_verb = len(self.items) > 0 and all([item.pos == 'verb' and item.attrib('mood') == 'subjunctive' for item in self.items])
        return self._is_subj_verb

    def description(self):
        if not self.items: return ''
        return util.render(self.surface) +":"+ util.render([item.description() for item in self.items])

    def detail(self):
        if self.items is None:
            return ''
        elif self.items == []:
            return '(?)'
        else:
            return ' | '.join([item.description() for item in self.items])

    def restrict_cases(self, possible_cases):
        # print "Word %s: RESTRICT CASES:" % self.surface_utf8(), possible_cases
        if not self.items: return
        for item in self.items:
            item._ = filter(lambda x:x[0] in possible_cases, item._)

    def translate(self):
        if self.items is None:
            return ('', False)
        else:
            tr = []
            for gen in self.genitives:
                tr.append(gen.translate()[0] + 'の')
            for mod in self.modifiers:
                tr.append(mod.translate()[0])
            # tr.append(  )
            if self.items:
                s = self.items[0].ja
                if tr:
                    s = '{' + ' & '.join(tr) + '}' + s
                return (s, False)
            else:
                return ('(?)', False)
