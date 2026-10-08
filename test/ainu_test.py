#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語: 古いローマ字表記の正規化、人称の接辞・接尾辞の分解、語順のままの日本語訳
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.ainu import analyzer, morphology, script  # noqa: E402


class AinuTestCase(unittest.TestCase):
    def test_spelling(self):
        self.assertEqual(script.key('Shirokanipe'), 'sirokanipe')   # sh → s
        self.assertEqual(script.key('chikap'), 'cikap')             # ch → c
        self.assertEqual(script.key('kamui'), 'kamuy')              # 母音の後ろの i → y
        self.assertEqual(script.key('yaieyukar'), 'yayeyukar')
        self.assertEqual(script.key('ku=kor'), 'kukor')             # = は照合で除く

    def test_person_affixes(self):
        m = morphology.analyze('chikush')                           # ci= + kus「私が通る」
        self.assertEqual((m.parts, m.subject, m.gloss), (['ci=', 'kus'], '私', '通る'))
        m = morphology.analyze('inkarash')                          # inkar + -as「私が見る」
        self.assertEqual((m.parts, m.subject), (['inkar', '-as'], '私'))
        m = morphology.analyze('enkore')                            # en= + kore「私に与える」
        self.assertEqual((m.parts, m.object), (['en=', 'kore'], '私'))

    def test_translation(self):
        ja = lambda t: next(analyzer.analyze_text(t)).japanese
        self.assertEqual(ja('teeta wenkur tane nishpa ne, teeta nishpa tane wenkur ne kotom shiran.'),
                         '昔貧乏人が今金持ちである、昔金持ちが今貧乏人のようだ。')   # 繋辞 ne、kotom siran
        self.assertIn('人間の村の上を私が通りながら下の方を見ると',
                      ja('ainukotan enkashike chikush kor shichorpokun inkarash ko.'))  # 後置詞、kor、ko
        self.assertIn('という歌を私が歌いながら', ja('arian rekpo chiki kane petesoro sapash aine.'))  # rekpo ki → 歌う


if __name__ == '__main__':
    unittest.main()
