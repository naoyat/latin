#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import io
import glob
import contextlib
import unittest

from latin import latindic, macronizer, wiktionary
from latin.macronizer import (transfer_macrons, strip_macrons, has_macron, macronize_text,
                              macronize_words, Context, Frequency, _anceps_variants)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def setUpModule():
    latindic.load()


class HandDictionaryOnly:
    """データの版に左右されないよう、手作りの辞書だけで推定する"""

    def setUp(self):
        self.saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = False

    def tearDown(self):
        latindic.LatinDic.use_wiktionary = self.saved


class UtilityTestCase(unittest.TestCase):
    def test_strip_and_detect(self):
        self.assertEqual(strip_macrons('Rōmā'), 'Roma')
        self.assertTrue(has_macron('rēx'))
        self.assertFalse(has_macron('rex'))

    def test_transfer_keeps_original_spelling(self):
        # j/i や大文字・小文字は入力のまま、マクロンの位置だけを写す
        self.assertEqual(transfer_macrons('iuvenī', 'juveni'), 'juvenī')
        self.assertEqual(transfer_macrons('rōma', 'Roma'), 'Rōma')
        self.assertEqual(transfer_macrons('afficī', 'adfici'), 'adficī')

    def test_anceps(self):
        # 長短どちらもありうる母音 (ī̆) は短い形と長い形の両方を候補にする
        self.assertEqual(_anceps_variants('sibī̆'), ['sibi', 'sibī'])
        self.assertEqual(_anceps_variants('sibī'), ['sibī'])


class MacronizeTestCase(HandDictionaryOnly, unittest.TestCase):
    def test_unique_candidates(self):
        self.assertEqual(macronize_text('Puella rosam amat.'), 'Puella rosam amat.')
        self.assertEqual(macronize_text('Romani regem habent.'), 'Rōmānī rēgem habent.')

    def test_text_layout_is_kept(self):
        self.assertEqual(macronize_text('  Rex, "Roma!"\n'), '  Rēx, "Rōma!"\n')

    def test_given_macrons_are_kept(self):
        self.assertEqual(macronize_text('rēx et regina'), 'rēx et rēgīna')

    def test_unknown_word_is_unchanged(self):
        self.assertEqual(macronize_text('Xyzzy rex'), 'Xyzzy rēx')

    def test_preposition_context(self):
        # 頻度を使わず、前置詞の支配格だけで選ぶ: in + 奪格
        choices = macronize_words(['Puella', 'in', 'silva', 'ambulat'], Context(frequency=None))
        self.assertEqual(choices[2].macronized, 'silvā')
        self.assertIn('prep', choices[2].reason)

    def test_enclitic(self):
        self.assertEqual(macronize_text('regemque'), 'rēgemque')

    def test_hidden_conventions(self):
        text = 'Rex magnus'
        self.assertEqual(macronize_text(text, hidden='strip'), 'Rēx magnus')
        knowledge = macronizer.hidden_quantity.HiddenQuantities()
        knowledge.add_words('x', ['māgnus'])
        context = Context(frequency=None, hidden='mark', hidden_quantities=knowledge)
        self.assertEqual(macronize_text(text, context), 'Rēx māgnus')

    def test_frequency_excludes_file(self):
        path = os.path.join(ROOT, 'texts', 'fabulae_faciles', 'perseus.txt')
        frequency = Frequency([path])
        self.assertGreater(frequency.count('Polydectēs'), 0)
        self.assertEqual(frequency.count('Polydectēs', exclude={path}), 0)


@unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
class AccuracyTestCase(unittest.TestCase):
    """Fabulae Faciles でのマクロン推定の正解率が下がっていないこと (回帰テスト)"""

    def setUp(self):
        self.saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = True

    def tearDown(self):
        latindic.LatinDic.use_wiktionary = self.saved

    def test_fabulae_faciles(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import macron_eval
        files = sorted(glob.glob(os.path.join(ROOT, 'texts', 'fabulae_faciles', '*.txt')))
        with contextlib.redirect_stdout(io.StringIO()):
            stats = macron_eval.evaluate(files, 0, Frequency())
        self.assertGreaterEqual(stats['words_ok'] / stats['words'], 0.95)
        self.assertGreaterEqual(stats['vowels_ok'] / stats['vowels'], 0.98)


if __name__ == '__main__':
    unittest.main()
