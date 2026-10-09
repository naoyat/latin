#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 関係節: 先行詞の名詞に付く節。関係代名詞そのものは節から外し、その格を「空所の役割」(gap) として持つ
#
#   puerum quem puella vīdit     {少女が 見た}少年を       (空所: 対格 = 目的語)
#   puella quae cantat           {歌う}少女                (空所: 主格 = 主語)
#   locus in quō habitābat       {住んでいた}場所          (空所: 前置詞句 in + 奪格)
#
# 関係詞の無い日本語の連体修飾節と同じ形 (節と空所の役割) なので、言語をまたいで使える。
# 関係代名詞の形 (ラテン語の quī、ロシア語の который …) は、作る言語で先行詞の性・数と空所の役割から決める
#
from .LatinObject import LatinObject


def is_relative(word):
    items = getattr(word, 'items', None) or []
    return any(item.pos == 'pronoun' and item.attrib('desc') == '関係代名詞' for item in items)


class RelativeClause(LatinObject):
    def __init__(self, predicate, antecedent, pronoun, gap):
        self.predicate = predicate      # 関係節の述語 (Predicate)
        self.antecedent = antecedent    # 先行詞 (Word)
        self.pronoun = pronoun          # 関係代名詞 (Word。節の格の枠からは外してある)
        self.gap = gap                  # 空所の役割: 'Nom' / 'Acc' / 'Dat' / 'Abl' / 'Gen' / ('prep', 'in') …
        self.surface = pronoun.surface + ' … ' + predicate.surface
        self.surface_len = len(self.surface)
        self.case_slot = predicate.case_slot

    def translate(self):
        inner, _ = self.predicate.translate()
        return (inner.replace(' / ', ' '), False)
