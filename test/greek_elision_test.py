#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 母音の省略の復元 (greek.elision)
#
import unittest

from greek import elision, dictionary, phonology


class FunctionWordTestCase(unittest.TestCase):
    """表で戻すもの (辞書が無くても戻る)"""

    def test_function_words(self):
        self.assertEqual(elision.restore('ἀλλ’', 'ἐγώ'), 'ἀλλά')
        self.assertEqual(elision.restore("δ'", 'ἄν'), 'δέ')        # アポストロフィの書き方は問わない
        self.assertEqual(elision.restore('ἐφ’', 'ἡμῖν'), 'ἐπί')     # 気息の前の有気音
        self.assertEqual(elision.restore('καθ’', 'ἡμέραν'), 'κατά')

    def test_not_elided(self):
        self.assertIsNone(elision.restore('λόγος'))


class CrasisTestCase(unittest.TestCase):
    def test_split(self):
        self.assertEqual(elision.split_crasis('κἀγὼ'), ('καί', 'ἐγώ'))  # 重アクセントの書き方でも
        self.assertEqual(elision.split_crasis('τοὐναντίον'), ('τό', 'ἐναντίον'))
        self.assertIsNone(elision.split_crasis('καί'))


class ElisionMarkTestCase(unittest.TestCase):
    def test_smooth_breathing_as_apostrophe(self):
        # Perseus のテキストは省略を語末の気息記号 (U+0313) や ῤ で書く
        self.assertEqual(elision.restore('δ̓'), 'δέ')
        self.assertEqual(elision.restore('ῥ̓'), 'ἄρα')
        self.assertEqual(elision.restore('ὄφῤ'), 'ὄφρα')
        self.assertIsNone(elision.restore('ὁ'))  # 母音の気息記号はそのまま


@unittest.skipUnless(dictionary.available(), 'ギリシア語の辞書 (tools/build_greek_dic.py) が無い')
class DictionaryTestCase(unittest.TestCase):
    def test_restore_by_dictionary(self):
        self.assertEqual(elision.restore('μυρί’', 'Ἀχαιοῖς'), 'μυρία')
        self.assertEqual(elision.restore('βούλομ’', 'ἐγώ'), 'βούλομαι')  # 叙事詩の -αι
        self.assertEqual(elision.restore('ἔθηκ’', 'ἐμοί'), 'ἔθηκα')

    def test_epic_and_ionic_forms(self):
        from greek import dialect
        self.assertEqual(dialect.attic('ἀγορήν'), 'αγοραν')    # イオニア方言の η
        self.assertEqual(dialect.attic('κονίῃσι'), 'κονιαισ')  # 叙事詩の複数与格
        self.assertEqual(dialect.attic('μέσσον'), 'μεσον')     # 重子音の揺れ
        self.assertEqual(dialect.attic('νηυσίν'), 'ναυσιν')

    def test_length_of_elided_word(self):
        self.assertIn('myːrí', phonology.to_ipa('μυρί’ Ἀχαιοῖς'))  # μῡρία の ῡ
