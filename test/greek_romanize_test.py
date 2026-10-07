#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の転写 (greek.romanize)
#
import unittest

from greek.romanize import romanize, romanize_word


class RomanizeTestCase(unittest.TestCase):
    def test_sentence(self):
        self.assertEqual(romanize('ἐν ἀρχῇ ἦν ὁ λόγος'), 'en archêi ên ho lógos')

    def test_breathing_on_diphthong(self):
        self.assertEqual(romanize_word('οἱ'), 'hoi')
        self.assertEqual(romanize_word('αἱ'), 'hai')
        self.assertEqual(romanize_word('υἱός'), 'hyiós')

    def test_consonants(self):
        self.assertEqual(romanize_word('ἄγγελος'), 'ángelos')   # γγ → ng
        self.assertEqual(romanize_word('ῥήτωρ'), 'rhḗtōr')      # 語頭の ῥ → rh
        self.assertEqual(romanize_word('εὐαγγέλιον'), 'euangélion')
        self.assertEqual(romanize_word('Σωκράτης'), 'Sōkrátēs')


if __name__ == '__main__':
    unittest.main()
