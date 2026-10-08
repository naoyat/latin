#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 子孫語の表示 (latin.descendants)。辞書の代わりに手で作った子孫語を使う
#
import unittest

from dragoman.core import descendants
from dragoman.latin import wiktionary

FAKE = {
    'acutus': [{'lang': 'fr', 'word': 'aigu', 'kind': 'inherited', 'via': [['fro', 'agu'], ['frm', 'aigu']]},
               {'lang': 'en', 'word': 'acute', 'kind': 'borrowed', 'via': [['enm', 'acute']]}],
    'canto': [{'lang': 'it', 'word': 'cantare', 'kind': 'inherited', 'via': []}],
}


class DescribeTestCase(unittest.TestCase):
    def setUp(self):
        self.saved = wiktionary.descendants
        wiktionary.descendants = lambda lemma: FAKE.get(lemma.replace('ū', 'u').replace('ō', 'o'), [])

    def tearDown(self):
        wiktionary.descendants = self.saved

    def test_french_and_english(self):
        self.assertEqual(descendants.describe('acūtus'),
                         '仏 aigu (継承: 古仏 agu → 中仏 aigu) / 英 acute (借用: 中英 acute)')

    def test_fallback_languages(self):
        # 仏・英が無ければ伊・西
        self.assertEqual(descendants.describe('cantō'), '伊 cantare (継承)')

    def test_none(self):
        self.assertIsNone(descendants.describe('xyz'))


if __name__ == '__main__':
    unittest.main()
