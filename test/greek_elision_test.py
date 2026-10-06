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


@unittest.skipUnless(dictionary.available(), 'ギリシア語の辞書 (tools/build_greek_dic.py) が無い')
class DictionaryTestCase(unittest.TestCase):
    def test_restore_by_dictionary(self):
        self.assertEqual(elision.restore('μυρί’', 'Ἀχαιοῖς'), 'μυρία')
        self.assertEqual(elision.restore('βούλομ’', 'ἐγώ'), 'βούλομαι')  # 叙事詩の -αι
        self.assertEqual(elision.restore('ἔθηκ’', 'ἐμοί'), 'ἔθηκα')

    def test_length_of_elided_word(self):
        self.assertIn('myːrí', phonology.to_ipa('μυρί’ Ἀχαιοῖς'))  # μῡρία の ῡ
