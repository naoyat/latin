#!/usr/bin/env python
# -*- coding: utf-8 -*-
# A=ā E=ē I=ī O=ō U=ū Y=ȳ

from latin.latin_syllable import separate_syllaba, locate_accent
import unittest

class SyllabaTestCase(unittest.TestCase):
    def assertSep(self, word_utf8, expected_separation_utf8):
        syllables = separate_syllaba(word_utf8.decode('utf-8'))
        actual_separation_utf8 = ('-'.join(syllables)).encode('utf-8')
        self.assertEqual(actual_separation_utf8, expected_separation_utf8)

    def assertAccent(self, word_utf8, expected_accent_utf8):
        syllables = separate_syllaba(word_utf8.decode('utf-8'))
        acc_idx = locate_accent(syllables)
        if acc_idx is not None:
            syllables[acc_idx] = '[' + syllables[acc_idx] + ']'
        actual_accent_utf8 = ('-'.join(syllables)).encode('utf-8')
        self.assertEqual(actual_accent_utf8, expected_accent_utf8)

    def test_sep(self):
        # v | Cv
        self.assertSep("caesar", "cae-sar")
        self.assertSep("rubicōne", "ru-bi-cō-ne")

        # vC | Cv
        self.assertSep("superātō", "su-pe-rā-tō")
        self.assertSep("commīlitōnēs", "com-mī-li-tō-nēs")
        # v | [pbtdcg][lr]v
        self.assertSep("arīminēnsī", "a-rī-mi-nēn-sī")
        self.assertSep("adlocūtus", "a-dlo-cū-tus") # can be "ad-lo-cū-tus"
        self.assertSep("suggestum", "sug-ge-stum") # can be "sug-ges-tum"

        # C | CC
        self.assertSep("novembris", "no-vem-bris")

        #
        self.assertSep("lūx", "lūx")
        self.assertSep("mer", "mer")
        self.assertSep("vir", "vir")
        self.assertSep("ex", "ex")
        self.assertSep("in", "in")
        self.assertSep("et", "et")
        self.assertSep("sed", "sed")

        self.assertSep("bellō", "bel-lō")
        self.assertSep("dictātor", "dic-tā-tor")
        self.assertSep("cōnsulēs", "cōn-su-lēs")

        self.assertSep("deus", "de-us")
        self.assertSep("suōs", "su-ōs")
        self.assertSep("mēnsium", "mēn-si-um")

    def test_accent(self):
        # 単音節
        self.assertAccent("lūx", "lūx")
        self.assertAccent("mer", "mer")
        self.assertAccent("vir", "vir")
        self.assertAccent("ex", "ex")
        self.assertAccent("in", "in")
        self.assertAccent("et", "et")
        self.assertAccent("sed", "sed")

        # 2音節
        self.assertAccent("caesar", "[cae]-sar")
        self.assertAccent("bellō", "[bel]-lō")
        self.assertAccent("suōs", "[su]-ōs")
        self.assertAccent("forō", "[fo]-rō")

        self.assertAccent("deus", "[de]-us")

        # 3音節
        ## long paenultima
        self.assertAccent("dictātor", "dic-[tā]-tor")
        self.assertAccent("rubicōne", "ru-bi-[cō]-ne")
        self.assertAccent("commīlitōnēs", "com-mī-li-[tō]-nēs")

        ## short paenultima
        self.assertAccent("cōnsulēs", "[cōn]-su-lēs")
        self.assertAccent("mēnsium", "[mēn]-si-um")


if __name__ == '__main__':
    unittest.main()
