#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語: ワイリー式の転写、語の区切り、格 (能格・具格・絶対格) と日本語訳。辞書・botok が無ければ飛ばす
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.tibetan import dictionary, phonology, script, segment  # noqa: E402

HAVE_DATA = dictionary.available()


class WylieTestCase(unittest.TestCase):
    def test_translit(self):
        self.assertEqual(script.translit('བསྒྲུབས'), 'bsgrubs')        # 前置字 + 上に乗る字 + 基字 + 下に付く字
        self.assertEqual(script.translit('དགའ'), "dga'")
        self.assertEqual(script.translit('གཡོ'), 'g.yo')               # གཡ (g + y) と གྱ (gy) を分ける
        self.assertEqual(script.translit('གྱི'), 'gyi')
        self.assertEqual(script.translit('མངས'), 'mangs')
        self.assertEqual(script.translit('དབང'), 'dbang')
        self.assertEqual(script.translit('པའི'), "pa'i")                # 語末の འི
        self.assertEqual(script.translit('སེངྒེ'), 'sengge')
        self.assertEqual(script.translit('ཨོཾ་མ་ཎི་པདྨེ་ཧཱུྃ'), 'oM ma Ni padme hU~M')
        self.assertEqual(script.translit('བཅོམ་ལྡན་འདས། །'), "bcom ldan 'das/ /")

    def test_ambiguous_syllable(self):
        self.assertEqual(script.syllable_candidates('དགས'), ['dags', 'dgas'])
        self.assertEqual(script.translit('དགས', known={'dgas'}), 'dgas')  # 辞書にある方


class LhasaTestCase(unittest.TestCase):
    def ipa(self, word, pron='lhasa'):
        return phonology.ipa(word, pron, words=[word])

    def test_initials(self):
        self.assertEqual(self.ipa('ལྷ་ས'), 'l̥a˥.sa˥')                     # 無声の l、高い調子
        self.assertEqual(self.ipa('བླ་མ'), 'la˥.ma˩˧')                     # bl → l (高)、m (低)
        self.assertEqual(self.ipa('དབང'), 'waŋ˩˧')                         # db → w
        self.assertEqual(self.ipa('ཁྲག'), 'ʈʰaʔ˥˩')                        # khr → ʈʰ、-g → ʔ
        self.assertEqual(self.ipa('བསྒྲུབས'), 'ʈup˩˧')                     # 前置字・上に乗る字は読まない、有声は無気に
        self.assertEqual(self.ipa('གཡུ'), 'ju˥')                           # 前置字のある鳴音は高い調子

    def test_rhymes(self):
        self.assertEqual(self.ipa('བོད'), 'pʰø˩˧')                         # -d で o → ø
        self.assertEqual(self.ipa('ཕྱག་འཚལ'), 'cʰaʔ˥˩.tsʰɛː˥')            # -l で a → ɛ、長く
        self.assertEqual(self.ipa('ཕྱག་འཚལ', 'chant'), 'cʰaʔ˥˩.tsʰal˥')   # 読誦式
        self.assertEqual(self.ipa('བཀྲ་ཤིས་བདེ་ལེགས'), 'ʈa˥.ɕi˥˩.te˩˧.leʔ˩˧')  # -gs は母音を変えない
        self.assertEqual(self.ipa('ཨོཾ'), 'om˥')

    def test_nasal_sandhi(self):
        self.assertEqual(self.ipa('དགེ་འདུན'), 'ken˩˧.tyn˩˧')               # 2音節目の ' は前の音節の鼻音に
        self.assertEqual(self.ipa('བཀའ་འགྱུར'), 'kaŋ˥.cur˩˧')

    def test_espeak(self):
        self.assertEqual(phonology.espeak_phonemes('ལྷ་ས།'), "[[l#'A55 s'A55 _:]]")


@unittest.skipUnless(HAVE_DATA and segment.available(), 'no Tibetan dictionary or botok')
class TibetanTestCase(unittest.TestCase):
    def ja(self, text):
        from dragoman.tibetan import analyzer
        return next(analyzer.analyze_text(text)).japanese

    def test_ergative(self):
        self.assertEqual(self.ja('རྒྱལ་པོས་བློན་པོ་ལ་གསེར་བྱིན་ནོ།'), '王が大臣に金を与えた。')
        self.assertEqual(self.ja('ཁོས་སྟ་རེས་ཤིང་བཅད་དོ།'), '彼が斧で木を切った。')    # 能格 (人) と具格 (道具)
        self.assertEqual(self.ja('སངས་རྒྱས་ཀྱིས་ཆོས་བསྟན་ཏོ།'), '仏陀が法を説いた。')

    def test_copula_existential_negation(self):
        self.assertEqual(self.ja('ཁོ་སློབ་མ་ཡིན།'), '彼は弟子である。')
        self.assertEqual(self.ja('ང་ལ་དངུལ་མེད།'), '私にはお金がない。')
        self.assertEqual(self.ja('ང་ནི་ལྷ་སར་མི་འགྲོ།'), '私はラサに行かない。')

    def test_noun_phrase_and_clauses(self):
        self.assertIn('三人の良い人に', self.ja('མི་བཟང་པོ་གསུམ་ལ་ཟས་བྱིན་ནས་ཁོ་རང་གི་ཁྱིམ་དུ་ཕྱིན་ཏོ།'))
        self.assertIn('私が聞いたある時に', self.ja('འདི་སྐད་བདག་གིས་ཐོས་པའི་དུས་གཅིག་ན།'))
        self.assertEqual(self.ja('བུ་མོ་ཆུ་ལེན་དུ་སོང་ངོ༌།'), '娘が水を取りに行った。')
        self.assertEqual(self.ja('སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་ལྡན་པར་གྱུར་ཅིག །'), 'すべての衆生が幸せを具えるようになりますように。')

    def test_segment_fixes(self):
        words = [t.wylie for t in segment.tokenize('བུ་མོ་དེ་རྟ་ལས་ལྷུང་ངོ་།')]
        self.assertIn('las', words)                                       # རྟ་ལ + ས → རྟ + ལས
        self.assertEqual([t.wylie for t in segment.tokenize('ཁོས་')][:2], ['kho', 's'])


if __name__ == '__main__':
    unittest.main()
