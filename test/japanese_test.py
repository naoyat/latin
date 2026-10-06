#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 日本語の述語の形: 繋辞 (sum) の述語 (copula_predicate) と動詞の否定形 (JaVerb.form(negated=True))
#
import unittest

from core import japanese
from core.japanese import JaVerb, copula_predicate, copula_conjunctive
from core import verb_flags as Verb


class CopulaTestCase(unittest.TestCase):
    def test_i_adjective(self):
        self.assertEqual(copula_predicate('美しい'), '美しい')
        self.assertEqual(copula_predicate('美しい', tense='past'), '美しかった')
        self.assertEqual(copula_predicate('美しい', negated=True), '美しくない')
        self.assertEqual(copula_predicate('いい', tense='past'), 'よかった')

    def test_rentaishi(self):
        self.assertEqual(copula_predicate('大きな'), '大きい')
        self.assertEqual(copula_predicate('この,これ'), 'これである')

    def test_na_adjective(self):
        self.assertEqual(copula_predicate('幸福な'), '幸福である')
        self.assertEqual(copula_predicate('幸福な', tense='future', negated=True), '幸福ではないだろう')

    def test_participle(self):
        self.assertEqual(copula_predicate('満ちた', tense='past'), '満ちていた')
        self.assertEqual(copula_predicate('凍った', negated=True), '凍っていない')

    def test_noun(self):
        # 名詞の訳語はまとめて結ぶ
        self.assertEqual(copula_predicate('王,指導者', adjective=False, tense='past'), '王,指導者であった')
        self.assertEqual(copula_predicate('美しい', adjective=False), '美しいである')

    def test_mixed(self):
        self.assertEqual(copula_predicate('うれしい,愉快な', tense='past'), 'うれしかった,愉快であった')
        self.assertEqual(copula_predicate('金製の,金色の'), '金製のもの,金色のものである')

    def test_negated_coordination(self):
        # 長くも 広くもなかった
        self.assertEqual(copula_conjunctive('長い', negated=True) +
                         copula_predicate('広い', tense='past', negated=True, also=True), '長くも広くもなかった')
        self.assertEqual(copula_conjunctive('幸福な', negated=True) +
                         copula_predicate('農夫', adjective=False, negated=True, also=True), '幸福でも農夫でもない')

    def test_conjunctive(self):
        self.assertEqual(copula_conjunctive('長い'), '長くて')
        self.assertEqual(copula_conjunctive('幸福な'), '幸福で')
        self.assertEqual(copula_conjunctive('満ちた'), '満ちていて')



@unittest.skipUnless(japanese.is_mecab_available, 'MeCab が無い')
class NegativeTestCase(unittest.TestCase):
    def negative(self, verb, flag):
        return JaVerb(verb).form(flag, negated=True)

    def test_tenses(self):
        self.assertEqual(self.negative('恐れる', Verb.INDICATIVE_ACTIVE_PRESENT), '恐れない')
        self.assertEqual(self.negative('恐れる', Verb.INDICATIVE_ACTIVE_IMPERFECT), '恐れていなかった')
        self.assertEqual(self.negative('恐れる', Verb.INDICATIVE_ACTIVE_FUTURE), '恐れないだろう')
        self.assertEqual(self.negative('恐れる', Verb.INDICATIVE_ACTIVE_PERFECT), '恐れなかった')

    def test_conjugation_types(self):
        self.assertEqual(self.negative('書く', Verb.INDICATIVE_ACTIVE_PRESENT), '書かない')
        self.assertEqual(self.negative('言う', Verb.INDICATIVE_ACTIVE_PRESENT), '言わない')
        self.assertEqual(self.negative('する', Verb.INDICATIVE_ACTIVE_PRESENT), 'しない')
        self.assertEqual(self.negative('ある', Verb.INDICATIVE_ACTIVE_PRESENT), 'ない')
        self.assertEqual(self.negative('愛する', Verb.INDICATIVE_ACTIVE_PRESENT), '愛さない')

    def test_passive_and_imperative(self):
        self.assertEqual(self.negative('ほめる', Verb.INDICATIVE_PASSIVE_PERFECT), 'ほめられなかった')
        self.assertEqual(self.negative('恐れる', Verb.IMPERATIVE_ACTIVE_PRESENT), '恐れるな')

    def test_affirmative_unchanged(self):
        self.assertEqual(JaVerb('恐れる').form(Verb.INDICATIVE_ACTIVE_PERFECT), '恐れた')


if __name__ == '__main__':
    unittest.main()
