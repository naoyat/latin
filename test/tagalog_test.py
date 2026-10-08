#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語: 焦点の接辞とアスペクト (重複) の解析、名詞句の標識と焦点からの格、焦点の名詞を「は」で先頭に。
# 辞書が無ければ飛ばす
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.tagalog import dictionary, morphology, script  # noqa: E402

HAVE_DATA = dictionary.available()


class CandidatesTestCase(unittest.TestCase):
    def test_affixes_and_aspect(self):
        c = morphology.candidates
        self.assertIn(('bili', 'actor', 'progressive'), c('bumibili'))      # -um- + 重複
        self.assertIn(('bili', 'object', 'completive'), c('binili'))         # -in-
        self.assertIn(('sulat', 'actor', 'progressive'), c('nagsusulat'))    # nag- + 重複
        self.assertIn(('sulat', 'conveyance', 'completive'), c('isinulat'))  # i- + -in-
        self.assertIn(('linis', 'object', 'contemplative'), c('lilinisin'))  # 重複 + -in
        self.assertIn(('alis', 'actor', 'completive'), c('umalis'))          # 母音で始まる語根は um-
        self.assertIn(('bili', 'object', 'infinitive'), c('bilhin'))         # 母音の脱落 (bili + hin)

    def test_voice_of_lemmas(self):
        self.assertEqual(script.verb_voice('bumili', 'buy'), 'actor')
        self.assertEqual(script.verb_voice('bilhin', 'buy something'), 'object')
        self.assertEqual(script.verb_voice('makita', 'happen to see'), 'object')


@unittest.skipUnless(HAVE_DATA, 'no Tagalog dictionary (tools/build_tagalog_dic.py)')
class TagalogTestCase(unittest.TestCase):
    def ja(self, text):
        from dragoman.tagalog import analyzer
        a = next(analyzer.analyze_text(text))
        return ' / '.join(c.predicate.translate()[0] for c in a.clauses if c.predicate)

    def test_focus(self):
        self.assertEqual(self.ja('Bumili ang lalaki ng isda.'), '男は / 魚を / 買った')       # 行為者焦点
        self.assertEqual(self.ja('Binili ng lalaki ang isda.'), '魚は / 男が / 買った')       # 対象焦点
        self.assertEqual(self.ja('Binilhan ng lalaki ng isda ang tindahan.'), '店には / 男が / 魚を / 買った')  # 場所焦点
        self.assertEqual(self.ja('Kumakain ako ng kanin.'), '私は / ご飯を / 食べている')    # 進行

    def test_possessor_copula_relative(self):
        self.assertIn('子供の', self.ja('Binili ng lalaki ang libro ng bata.'))
        self.assertEqual(self.ja('Maganda ang bahay.'), '家は / 美しい')
        self.assertEqual(self.ja('Si Juan ay guro.'), 'Juanは / 先生である')
        self.assertIn('魚を買った男は', self.ja('Ang lalaking bumili ng isda ay guro.'))

    def test_contractions_and_gerunds(self):
        from dragoman.tagalog import analyzer
        self.assertEqual(analyzer.tokens("ngayo'y sa'kin"), ['ngayon', 'ay', 'sa', 'akin'])
        items, _ = morphology.analyze('pag-ikot')
        self.assertEqual(items[0]['pos'], 'noun')                                          # 動名詞 pag-
        items, _ = morphology.analyze('magandang')
        self.assertEqual(items[0]['pos'], 'adj')                                           # 繋ぎ -ng


if __name__ == '__main__':
    unittest.main()
