#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの発音 (sanskrit.phonology) と MBROLA の .pho (sanskrit.prosody)。vidyut が無ければ飛ばす
#
import unittest

try:
    from dragoman.sanskrit import phonology, prosody
    HAVE_VIDYUT = True
except ImportError:
    HAVE_VIDYUT = False


@unittest.skipUnless(HAVE_VIDYUT, 'vidyut が無い')
class PhonologyTestCase(unittest.TestCase):
    def test_ipa(self):
        self.assertEqual(phonology.to_ipa('रामो वनं गच्छति ।'), 'ˈrɑː.moː ˈʋɐ.nɐŋ ˈgɐtʃ.tʃʰɐ.t̪i ‖')

    def test_visarga_echo_and_retroflex(self):
        ipa = phonology.to_ipa('कृष्णः')
        self.assertTrue(ipa.endswith('ɳɐ.hɐ'), ipa)   # kṛṣṇaḥ → kṛṣṇaha
        self.assertIn('r̩ʂ', ipa)

    def test_anusvara_takes_place_of_following_consonant(self):
        self.assertIn('ɐm', phonology.to_ipa('vanaṃ'))            # 語末 (後ろに語が無い)
        self.assertIn('ɐŋ', phonology.to_ipa('vanaṃ gacchati'))   # 次の語の g の前
        self.assertIn('ɐn', phonology.to_ipa('saṃtoṣa'))          # t の前

    def test_stress(self):
        sylls = phonology.syllabify(phonology.segments('kurukzetre'))
        self.assertEqual(phonology.stress_index(sylls), 2)  # 次末音節 kṣet が重い


@unittest.skipUnless(HAVE_VIDYUT, 'vidyut が無い')
class ProsodyTestCase(unittest.TestCase):
    def phones(self, text):
        return [line.split()[0] for line in prosody.to_pho(text).splitlines() if line and line[0] != ';']

    def test_in1_phones(self):
        phones = self.phones('धर्मक्षेत्रे')
        self.assertEqual([p for p in phones if p != '_'], ['dh', 'a', 'r', 'm', 'a', 'ks', 'e', 't', 'r', 'e'])
        self.assertIn('_', phones[phones.index('r') + 1:phones.index('m')])  # 子音の間の短い無音

    def test_long_vowel_is_twice(self):
        lines = [l.split() for l in prosody.to_pho('rāma').splitlines()]
        aa = next(int(l[1]) for l in lines if l[0] == 'aa')
        a = next(int(l[1]) for l in lines if l[0] == 'a')
        self.assertEqual(aa, 2 * a)


if __name__ == '__main__':
    unittest.main()
