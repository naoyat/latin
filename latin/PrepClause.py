#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject

# 前置詞支配された名詞節
class PrepClause (LatinObject):
    def __init__(self, prep_word, dominated_case, words):
        # self.prep_surface = prep_word.surface
        self.prep = prep_word.surface
        self.dominated_case = dominated_case
        self.words = words

        for item in prep_word.items:
            if item.dominates == dominated_case:
                self.item = item
                break

        self.surface = self.item.surface + ' ' + ' '.join([word.surface for word in words])
        self.surface_len = len(self.surface)

    def translate(self):
        s = ' '.join([word.translate()[0] for word in self.words])
        s = '{' + s + '}' + self.item.ja
        return (s, False)
