#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の音韻処理 (greek.phonology) と韻律付け (greek.prosody)
#
import unittest

from greek import phonology, prosody


class PhonologyTestCase(unittest.TestCase):
    def test_attic(self):
        self.assertEqual(phonology.to_ipa('ἐν ἀρχῇ ἦν ὁ λόγος'), 'en arkʰɛ̂ː ɛ̂ːn ho lógos')
        self.assertEqual(phonology.to_ipa('ζῷον'), 'zdɔ̂ːon')        # ζ = [zd]、下書きのイオータで長い
        self.assertEqual(phonology.to_ipa('εἰρήνη'), 'eːrɛ́ːnɛː')    # ει = [eː], η = [ɛː]
        self.assertEqual(phonology.to_ipa('οὐρανός'), 'oːranós')     # ου = [oː]
        self.assertEqual(phonology.to_ipa('ἄγγελος'), 'áŋgelos')     # γγ = [ŋg]
        self.assertEqual(phonology.to_ipa('κόσμος'), 'kózmos')       # 有声子音の前の σ

    def test_diaeresis_breaks_diphthong(self):
        self.assertEqual(phonology.to_ipa('Πηληϊάδεω'), 'pɛːlɛːiádeɔː')

    def test_accent_on_first_vowel_breaks_diphthong(self):
        self.assertEqual(phonology.to_ipa('ἄειδε'), 'áeːde')  # ἄ-ει-δε

    def test_koine(self):
        self.assertEqual(phonology.to_ipa('εἰρήνη', 'koine'), 'irˈene')
        self.assertEqual(phonology.to_ipa('ὁ λόγος', 'koine'), 'o lˈogos')  # 気息が消える

    def test_erasmian(self):
        self.assertEqual(phonology.to_ipa('ζῷον', 'erasmian'), 'dzˈɔːon')


class ProsodyTestCase(unittest.TestCase):
    def vowel_lines(self, text, pron='attic'):
        lines = [l.split() for l in prosody.to_pho(text, pron).splitlines()]
        return [l for l in lines if l[0] in ('E', 'O', 'a', 'e:', 'o:', 'I', 'i:', 'y', 'aE', 'OE')]

    def test_circumflex_rises_then_falls(self):
        # μῆνιν: η の中で上がって下がる
        line = self.vowel_lines('μῆνιν.')[0]
        hz = [int(x) for x in line[3::2]]
        self.assertEqual(line[0], 'E')
        self.assertTrue(hz[1] > hz[0] and hz[1] > hz[-1], hz)

    def test_acute_on_long_vowel_rises_late(self):
        # εἰρήνη: ή は後半で上がる (最後の目標がいちばん高い)
        line = self.vowel_lines('εἰρήνη.')[1]
        hz = [int(x) for x in line[3::2]]
        self.assertEqual(max(hz), hz[-1], hz)

    def test_stress_lengthens(self):
        attic = self.vowel_lines('λόγος.', 'koine')
        self.assertGreater(int(attic[0][1]), int(attic[1][1]))  # アクセントのある ό が長い


if __name__ == '__main__':
    unittest.main()
