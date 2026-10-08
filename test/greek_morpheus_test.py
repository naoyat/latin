#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Morpheus による語形の解析 (greek.morpheus)。ベータコードの変換は Morpheus が無くても試す
#
import unittest

from dragoman.greek import morpheus, dictionary


class BetacodeTestCase(unittest.TestCase):
    def test_round_trip(self):
        for word, beta in [('ἑτάροισι', 'e(ta/roisi'), ('Ἀχιλῆος', '*)axilh=os'), ('ῥῆμα', 'r(h=ma'),
                           ('ἀρχῇ', 'a)rxh=|')]:
            self.assertEqual(morpheus.to_betacode(word), beta)
            self.assertEqual(morpheus.from_betacode(beta), word)

    def test_final_sigma_and_homonym_number(self):
        self.assertEqual(morpheus.from_betacode('lo/gos1'), 'λόγος')


@unittest.skipUnless(morpheus.available() and dictionary.available(), 'Morpheus またはギリシア語の辞書が無い')
class AnalyzeTestCase(unittest.TestCase):
    def test_epic_forms(self):
        item, = morpheus.analyze('ἑτάροισι')
        self.assertEqual((item['pos'], item['base'], item['_']), ('noun', 'ἑταῖρος', [('Dat', 'pl', 'm')]))
        self.assertTrue(any(i.get('pres1sg') == 'βαίνω' and i['tense'] == 'aorist' for i in morpheus.analyze('βῆ')))
