#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from dragoman.latin.latin_phonology import analyze_word, phonemize_word, to_target_ipa


def syllables(word):
    return '.'.join(map(repr, analyze_word(word)))


class PhonemizeTestCase(unittest.TestCase):
    def test_digraphs(self):
        self.assertEqual(phonemize_word('Thēseus'), ['t_h', 'e:', 's', 'E', 'U', 's'])
        self.assertEqual(phonemize_word('aquam'), ['a', 'k', 'w', 'a', 'm'])
        self.assertEqual(phonemize_word('lingua'), ['l', 'I', 'N', 'g', 'w', 'a'])
        self.assertEqual(phonemize_word('magnum'), ['m', 'a', 'N', 'n', 'U', 'm'])
        self.assertEqual(phonemize_word('exīre'), ['E', 'k', 's', 'i:', 'r', 'E'])

    def test_diphthongs(self):
        self.assertEqual(phonemize_word('Caesar'), ['k', 'aE', 's', 'a', 'r'])
        self.assertEqual(phonemize_word('coepit'), ['k', 'OE', 'p', 'I', 't'])

    def test_consonantal_i_u(self):
        self.assertEqual(phonemize_word('Trōjae'), ['t', 'r', 'o:', 'j:', 'aE'])
        self.assertEqual(phonemize_word('iam'), ['j', 'a', 'm'])
        self.assertEqual(phonemize_word('virum'), ['w', 'I', 'r', 'U', 'm'])

    def test_assimilation(self):
        self.assertEqual(phonemize_word('urbs'), ['U', 'r', 'p', 's'])
        self.assertEqual(phonemize_word('mittō'), ['m', 'I', 't:', 'o:'])


class SyllableTestCase(unittest.TestCase):
    def test_accent_on_heavy_penult(self):
        self.assertEqual(syllables('aedificāvit'), 'aE.dI.fI.ˈka:.wIt')
        self.assertEqual(syllables('misericordiae'), 'mI.sE.rI.ˈkOr.dI.aE')

    def test_accent_on_antepenult(self):
        self.assertEqual(syllables('gladium'), 'ˈgla.dI.Um')
        self.assertEqual(syllables('aquam'), 'ˈa.kwam')
        self.assertEqual(syllables('itaque'), 'ˈI.ta.kwE')

    def test_two_syllables(self):
        self.assertEqual(syllables('canō'), 'ˈka.no:')
        self.assertEqual(syllables('Trōjae'), 'ˈtro:j.jaE')

    def test_enclitic(self):
        self.assertEqual(syllables('virumque'), 'wI.ˈrUm.kwE')

    def test_muta_cum_liquida(self):
        self.assertEqual(syllables('patrem'), 'ˈpa.trEm')


class TargetIpaTestCase(unittest.TestCase):
    def test_italian(self):
        self.assertEqual(to_target_ipa('Arma virumque canō.', 'it'),
                         ['ˈaɾma wɪɾˈumkwɛ kˈanoː.'])

    def test_spanish(self):
        self.assertEqual(to_target_ipa('Arma virumque canō.', 'es'),
                         ['ˈaɾma wiɾˈumkwe kˈano.'])


if __name__ == '__main__':
    unittest.main()
