#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語: 綴りの骨組み (urdu.script)、ヒンディー語の語形への引き当て (urdu.dictionary)、文の解析 (urdu.analyzer)。
# 対応表 (tools/build_urdu_dic.py) が無ければ、それを使う試験を飛ばす
#
import unittest

from dragoman.urdu import script, dictionary

HAVE_DATA = dictionary.available()


class ScriptTestCase(unittest.TestCase):
    def test_skeletons_match_devanagari(self):
        pairs = [('لڑکا', 'लड़का'), ('کتاب', 'किताब'), ('کتا', 'कुत्ता'), ('شانتی', 'शांति'), ('کریں', 'करें'),
                 ('کے', 'के'), ('کی', 'की')]
        for urdu, deva in pairs:
            self.assertIn(script.skeleton_deva(deva), script.skeletons(urdu), (urdu, deva))

    def test_final_ye_distinguished(self):
        # 語末の ے (e) と ی (ī) は書き分ける (کے ke と کی kī)
        self.assertNotIn(script.skeleton_deva('के'), script.skeletons('کی'))


@unittest.skipUnless(HAVE_DATA, 'no Urdu data (tools/build_hindi_dic.py, tools/build_urdu_dic.py)')
class AnalyzerTestCase(unittest.TestCase):
    def run_text(self, text):
        from dragoman.urdu import analyzer
        from dragoman.core import render
        a = next(analyzer.analyze_text(text))
        return [render.translate(c.predicate) for c in a.clauses], a.forms_text

    def test_candidates(self):
        self.assertEqual(dictionary.candidates('میں'), ['मैं', 'में'])  # 「私」と「〜で」の両方

    def test_ergative(self):
        trs, (text, latin) = self.run_text('لڑکے نے کتاب پڑھی۔')
        self.assertEqual(latin, 'laṛke ne kitāb paṛhī.')  # 転写は選んだヒンディー語の語形から
        self.assertIn('本を', trs[0])
        self.assertIn('読んだ', trs[0])

    def test_context_chooses_candidate(self):
        trs, (_, latin) = self.run_text('میں اسکول جاتا ہوں۔')
        self.assertTrue(latin.startswith('ma͠i '))       # 文頭の میں は「私」
        self.assertTrue(trs[0].startswith('私が'))
        trs, (_, latin) = self.run_text('وہ گھر میں ہے۔')
        self.assertIn(' mẽ ', latin)                     # 名詞の後ろの میں は「〜で」

    def test_negation_and_possession(self):
        self.assertTrue(self.run_text('میں اردو نہیں بول سکتا۔')[0][0].endswith('話すことができない'))
        self.assertTrue(self.run_text('میرے پاس ایک نئی کتاب ہے۔')[0][0].endswith('本が / ある'))


if __name__ == '__main__':
    unittest.main()
