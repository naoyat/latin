#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject

# 格つき名詞節
class CasedClause (LatinObject):
    def __init__(self, case, words):
        self.case = case
        self.words = words
        self.surface = case + u' ' + u' '.join([word.surface for word in words])
        self.surface_len = len(self.surface)

    def is_verb(self):
        return False

    def detail(self):
        return '**'

# 前置詞支配された名詞節
class PrepClause (CasedClause):
    def __init__(self, prep_word, dominated_case, words):
        # self.prep_surface = prep_word.surface
        self.dominated_case = dominated_case
        self.words = words

        for item in prep_word.items:
            if item.dominates == dominated_case:
                self.item = item
                break

        self.surface = self.item.surface + u' ' + u' '.join([word.surface for word in words])
        self.surface_len = len(self.surface)

