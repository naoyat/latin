#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from latin import hidden_quantity as hq


class PositionsTestCase(unittest.TestCase):
    def test_closed_syllable(self):
        self.assertEqual(hq.positions('māgnus'), {1})
        self.assertEqual(hq.positions('cōgnōvit'), {1})
        self.assertEqual(hq.positions('ārdēns'), {0, 3})

    def test_muta_cum_liquida_is_not_hidden(self):
        # 閉鎖音 + 流音は音節を閉じないので、母音の長さは普通に表記される
        self.assertEqual(hq.positions('patrem'), set())
        self.assertEqual(hq.positions('mātrem'), set())

    def test_digraphs_and_x(self):
        self.assertEqual(hq.positions('aquam'), set())   # qu は1つの子音
        self.assertEqual(hq.positions('rēx'), set())     # x は1文字として数える

    def test_consonantal_i(self):
        self.assertEqual(hq.positions('ēius'), {0})
        self.assertEqual(hq.positions('cuius'), {1})
        self.assertEqual(hq.positions('Trōia'), {2})
        self.assertEqual(hq.positions('fīlia'), set())   # 母音の i


class ConventionTestCase(unittest.TestCase):
    def test_strip(self):
        self.assertEqual(hq.strip('māgnōs cōgnōvit ēius'.split()[0]), 'magnōs')
        self.assertEqual(hq.strip('cōgnōvit'), 'cognōvit')
        self.assertEqual(hq.strip('mātrem'), 'mātrem')

    def test_mark_from_knowledge(self):
        knowledge = hq.HiddenQuantities()
        knowledge.add_words('a', ['māgnus', 'māgnum', 'iussus'])
        self.assertEqual(knowledge.mark('magnō'), 'māgnō')      # 語幹 magn- の知識を他の形に使う
        self.assertEqual(knowledge.mark('iūssit'), 'iussit')    # 印を付けない知識があれば外す
        self.assertEqual(knowledge.mark('cōnsul'), 'cōnsul')    # 知識が無ければそのまま

    def test_mark_excludes_source(self):
        knowledge = hq.HiddenQuantities()
        knowledge.add_words('a', ['māgnus'])
        self.assertEqual(knowledge.mark('magnō', exclude={'a'}), 'magnō')


if __name__ == '__main__':
    unittest.main()
