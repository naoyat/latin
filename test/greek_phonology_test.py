#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の音韻処理 (greek.phonology) と韻律付け (greek.prosody)
#
import unittest

from dragoman.greek import phonology, prosody, dictionary, length


def ipa(text, pron='attic'):
    return phonology.to_ipa(text, pron, lengths=False)  # 辞書に頼らない (長短どちらもある母音は短い)


class PhonologyTestCase(unittest.TestCase):
    def test_attic(self):
        self.assertEqual(ipa('ἐν ἀρχῇ ἦν ὁ λόγος'), 'en arkʰɛ̂ː ɛ̂ːn ho lógos')
        self.assertEqual(ipa('ζῷον'), 'zdɔ̂ːon')        # ζ = [zd]、下書きのイオータで長い
        self.assertEqual(ipa('εἰρήνη'), 'eːrɛ́ːnɛː')    # ει = [eː], η = [ɛː]
        self.assertEqual(ipa('οὐρανός'), 'oːranós')     # ου = [oː]
        self.assertEqual(ipa('ἄγγελος'), 'áŋgelos')     # γγ = [ŋg]
        self.assertEqual(ipa('κόσμος'), 'kózmos')       # 有声子音の前の σ

    def test_diaeresis_breaks_diphthong(self):
        self.assertEqual(ipa('Πηληϊάδεω'), 'pɛːlɛːiádeɔː')

    def test_accent_on_first_vowel_breaks_diphthong(self):
        self.assertEqual(ipa('ἄειδε'), 'áeːde')  # ἄ-ει-δε

    def test_koine(self):
        self.assertEqual(ipa('εἰρήνη', 'koine'), 'irˈene')
        self.assertEqual(ipa('ὁ λόγος', 'koine'), 'o lˈogos')  # 気息が消える

    def test_erasmian(self):
        self.assertEqual(ipa('ζῷον', 'erasmian'), 'dzˈɔːon')


    def test_modern(self):
        self.assertEqual(ipa('ἐν ἀρχῇ ἦν ὁ λόγος', 'modern'), 'en arçˈi ˈin o lˈoɣos')
        self.assertEqual(ipa('εὐχαριστῶ', 'modern'), 'efxaristˈo')   # ευ は無声音の前で [ef]
        self.assertEqual(ipa('Εὐαγγέλιον', 'modern'), 'evanɟˈelion')  # 母音の前で [ev]、γγ [ŋɟ]
        self.assertEqual(ipa('πέντε', 'modern'), 'pˈende')            # 語中の ντ [nd]


@unittest.skipUnless(dictionary.available(), 'ギリシア語の辞書 (tools/build_greek_dic.py) が無い')
class LengthTestCase(unittest.TestCase):
    def test_long_vowels_from_dictionary(self):
        self.assertEqual(phonology.to_ipa('θεὰ'), 'tʰeàː')    # θεᾱ́
        self.assertEqual(phonology.to_ipa('ἔλυσα'), 'élyːsa')  # ἔλῡσᾰ

    def test_short_stays_short(self):
        self.assertEqual(length.mark('ἵππον'), 'ἵππον')  # ῐ̔́ππον


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


    def test_gr2_symbols(self):
        # gr2 は独自の記号: ψ → Y, ξ → X, 子音の後の r → R, γγ の [ŋ] → V
        phones = [l.split()[0] for l in prosody.to_pho('ψυχή ξένος πρός ἄγγελος.', 'modern', phone_set='gr2').splitlines()]
        for p in ('Y', 'X', 'R', 'V', 'q'):
            self.assertIn(p, phones)


if __name__ == '__main__':
    unittest.main()
