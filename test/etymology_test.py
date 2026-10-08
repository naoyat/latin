#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 語源の表示 (latin.etymology)。辞書の代わりに手で作った語源を使う
#
import unittest

from dragoman.core import etymology
from dragoman.latin import wiktionary

FAKE = {
    'pater': [{'ancestors': [['inh', 'itc-pro', '*patēr', ''], ['inh', 'ine-pro', '*ph₂tḗr', ''],
                             ['root', 'ine-pro', '*peh₂-', '']],
               'cognates': [['grc', 'πατήρ', '', ''], ['sa', 'पितृ', 'pitṛ́', '']],
               'text': 'From Proto-Italic *patēr.'}],
    'philosophia': [{'ancestors': [['bor', 'grc', 'φιλοσοφία', 'love of wisdom']], 'cognates': [], 'text': ''}],
}


class DescribeTestCase(unittest.TestCase):
    def setUp(self):
        self.saved = wiktionary.etymology
        wiktionary.etymology = lambda lemma: FAKE.get(lemma, [])

    def tearDown(self):
        wiktionary.etymology = self.saved

    def test_inherited(self):
        self.assertEqual(etymology.describe('pater'), [
            '系統: イタリック祖語 *patēr ← 印欧祖語 *ph₂tḗr (語根 印欧祖語 *peh₂-)',
            '同源: 古代ギリシア πατήρ, サンスクリット पितृ (pitṛ́)',
            'From Proto-Italic *patēr.'])

    def test_borrowed(self):
        self.assertEqual(etymology.describe('philosophia'), ['系統: 古代ギリシア φιλοσοφία “love of wisdom” [借用]'])

    def test_none(self):
        self.assertEqual(etymology.describe('xyz'), [])


if __name__ == '__main__':
    unittest.main()
