#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語の語のカタカナ表記 (latin.katakana) と、固有名詞の訳語 (latin.wiktionary._proper_noun_gloss)
#
import unittest

from latin.katakana import katakana
from latin.wiktionary import _proper_noun_gloss


class KatakanaTestCase(unittest.TestCase):
    def test_names(self):
        for latin, kana in [('Caesar', 'カエサル'), ('Mārcus', 'マールクス'), ('Iūlia', 'ユーリア'),
                            ('Cicerō', 'キケロー'), ('Vergilius', 'ウェルギリウス'), ('Quīntus', 'クィーントゥス'),
                            ('Polyphēmus', 'ポリュペームス'), ('Alexander', 'アレクサンデル')]:
            self.assertEqual(katakana(latin), kana)

    def test_geminates(self):
        self.assertEqual(katakana('Iuppiter'), 'ユッピテル')   # 閉鎖音は ッ
        self.assertEqual(katakana('Hannibal'), 'ハンニバル')   # n は ン
        self.assertEqual(katakana('Gallia'), 'ガリア')         # l, r は1つ
        self.assertEqual(katakana('Pompēius')[:3], 'ポンペ')   # p, b の前の m は ン


class ProperNounGlossTestCase(unittest.TestCase):
    def test_english_description(self):
        item = _proper_noun_gloss({'pos': 'noun', 'base': 'Caesar', 'ja': 'Roman cognomen of the gens Iulia',
                                   'gloss_lang': 'en'})
        self.assertEqual((item['ja'], item['gloss_lang']), ('カエサル', 'ja'))

    def test_japanese_description(self):
        item = _proper_noun_gloss({'pos': 'noun', 'base': 'Mārcus', 'gloss_lang': 'ja',
                                   'ja': 'マールクス,マルクス,古代ローマに見られる男性名（プラエノーメン）,頭文字M.'})
        self.assertEqual(item['ja'], 'マールクス,マルクス')

    def test_common_noun_unchanged(self):
        item = _proper_noun_gloss({'pos': 'noun', 'base': 'rosa', 'ja': 'rose', 'gloss_lang': 'en'})
        self.assertEqual(item['ja'], 'rose')


if __name__ == '__main__':
    unittest.main()
