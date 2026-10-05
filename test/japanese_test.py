#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 繋辞 (sum) の述語の形 (latin.japanese.copula_predicate)
#
import unittest

from latin.japanese import copula_predicate, copula_conjunctive


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

    def test_conjunctive(self):
        self.assertEqual(copula_conjunctive('長い'), '長くて')
        self.assertEqual(copula_conjunctive('幸福な'), '幸福で')
        self.assertEqual(copula_conjunctive('満ちた'), '満ちていて')


if __name__ == '__main__':
    unittest.main()
