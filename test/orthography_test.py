#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from latin import orthography, latindic, wiktionary, macronizer


class OrthographyTestCase(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(orthography.variants('Iovis'), ['Iovis'])          # v があるので u/v は同一視しない
        self.assertEqual(orthography.variants('juvenī'), ['juvenī', 'iuvenī'])
        self.assertEqual(orthography.variants('uirum'), ['uirum'])          # 変換しても同じ
        self.assertEqual(orthography.variants('Iam'), ['Iam'])

    def test_may_merge_uv(self):
        self.assertTrue(orthography.may_merge_uv('uoluit'))
        self.assertFalse(orthography.may_merge_uv('volvit'))

    def test_flat(self):
        self.assertEqual(orthography.flat('Juvenī'), 'iuveni')
        self.assertEqual(orthography.flat('Juvenī', merge_uv=True), 'iuueni')


class HandDictionaryTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        latindic.load()

    def surfaces(self, word):
        items = latindic.lookup_hand(word) or []
        return sorted({item['surface'] for item in items})

    def test_ij(self):
        # 手作りの辞書は j で書いている
        self.assertEqual(self.surfaces('Iovis'), ['Jovis'])
        self.assertEqual(self.surfaces('iuvenem'), ['juvenem'])

    def test_uv_only_without_v(self):
        self.assertEqual(self.surfaces('uirum'), ['virum'])

    def test_macrons_must_match(self):
        self.assertEqual(self.surfaces('Troiae'), [])   # 辞書は Trōjae


@unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
class WiktionaryTestCase(unittest.TestCase):
    def surfaces(self, word):
        return sorted({item['surface'] for item in wiktionary.lookup(word) or []})

    def test_u_only_spelling_is_ambiguous(self):
        # u だけの綴りでは voluit (望んだ) と volvit (転がす) を区別できない
        self.assertEqual(self.surfaces('uoluit'), ['voluit', 'volvit'])

    def test_v_spelling_is_not_merged(self):
        self.assertEqual(self.surfaces('volvit'), ['volvit'])


class MacronizerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        latindic.load()
        cls.saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = False

    @classmethod
    def tearDownClass(cls):
        latindic.LatinDic.use_wiktionary = cls.saved

    def test_spelling_is_kept(self):
        # 手作りの辞書の juvenī を使いつつ、入力の i の綴りを保つ
        self.assertEqual(macronizer.macronize_text('iuveni', macronizer.Context()), 'iuvenī')
        # u の綴りは v に変えない (virum / vīrum のどちらになるかは文脈次第なので、綴りだけを見る)
        self.assertEqual(macronizer.strip_macrons(macronizer.macronize_text('uirum', macronizer.Context())), 'uirum')


if __name__ == '__main__':
    unittest.main()
