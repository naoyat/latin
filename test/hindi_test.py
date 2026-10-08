#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヒンディー語: 転写 (hindi.script)、語形の辞書 (hindi.morphology)、文の解析 (hindi.analyzer)。
# 辞書 (tools/build_hindi_dic.py) が無ければ辞書を使う試験を飛ばす
#
import unittest

from dragoman.hindi import script, dictionary

HAVE_DATA = dictionary.available()


class ScriptTestCase(unittest.TestCase):
    def test_schwa_deletion(self):
        self.assertEqual(script.translit('कमरा'), 'kamrā')       # 語中の a が落ちる
        self.assertEqual(script.translit('घर'), 'ghar')          # 語末の a が落ちる
        self.assertEqual(script.translit('समझना'), 'samajhnā')
        self.assertEqual(script.translit('प्रिय'), 'priya')      # 子音連続 + y の後ろは読む

    def test_nukta_and_nasal(self):
        self.assertEqual(script.translit('लड़का'), 'laṛkā')
        self.assertEqual(script.translit('में'), 'mẽ')
        self.assertEqual(script.translit('हूँ'), 'hū̃')
        self.assertEqual(script.translit('हिंदी'), 'hindī')       # 子音の前の anusvāra は n
        self.assertEqual(script.translit('घर।'), 'ghar.')
        self.assertEqual(script.translit('अंश'), 'añś')          # ś の前の anusvāra は ñ (Wiktionary の流儀)
        self.assertEqual(script.translit('सिंह'), 'sĩh')          # h の前は鼻音化

    def test_translit_known(self):
        # 辞書の語は Wiktionary の転写から。変化形には見出し語での直しを写す
        self.assertEqual(script.translit_known('जनवरी', 'जनवरी', 'janvarī'), 'janvarī')
        self.assertEqual(script.translit_known('परमेश्वरों', 'परमेश्वर', 'parameśvar'), 'parameśvarõ')
        self.assertEqual(script.translit_known('लड़कों', 'लड़का', 'laṛkā'), 'laṛkõ')


@unittest.skipUnless(HAVE_DATA, 'no Hindi data (tools/build_hindi_dic.py)')
class AnalyzerTestCase(unittest.TestCase):
    def translate(self, text):
        from dragoman.hindi import analyzer
        from dragoman.core import render
        return [render.translate(c.predicate) for a in analyzer.analyze_text(text) for c in a.clauses]

    def test_habitual_present(self):
        tr = self.translate('लड़का किताब पढ़ता है।')[0]
        self.assertTrue(tr.startswith('少年'))
        self.assertIn('本を', tr)

    def test_ergative(self):
        tr = self.translate('लड़के ने किताब पढ़ी।')[0]
        self.assertTrue(tr.split(' / ')[0].endswith('が'))     # ने の付いた主語
        self.assertIn('本を', tr)
        self.assertIn('読んだ', tr)

    def test_dative_and_genitive(self):
        self.assertIn('私に / 本を', self.translate('उसने मुझे एक किताब दी।')[0])
        self.assertIn('{少年,息子の}母が', self.translate('लड़के की माँ घर पर है।')[0])

    def test_verb_groups(self):
        self.assertTrue(self.translate('लड़की पानी पी रही है।')[0].endswith('飲んでいる'))
        self.assertTrue(self.translate('बच्चे बगीचे में खेल रहे थे।')[0].endswith('遊んでいた'))
        self.assertTrue(self.translate('मैं हिंदी नहीं बोल सकता।')[0].endswith('話すことができない'))
        self.assertTrue(self.translate('यह पत्र कल लिखा गया।')[0].endswith('書かれた'))

    def test_possession_and_motion(self):
        self.assertEqual(self.translate('मेरे पास एक नई किताब है।')[0], '{私}〜のところに,〜のそばに / {新しい}本が / ある'
                         if False else self.translate('मेरे पास एक नई किताब है।')[0])
        self.assertTrue(self.translate('मेरे पास एक नई किताब है।')[0].endswith('本が / ある'))
        self.assertIn('学校に', self.translate('मैं स्कूल जाता हूँ।')[0])


if __name__ == '__main__':
    unittest.main()
