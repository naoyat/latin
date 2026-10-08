#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文: 品詞分解 (MeCab + 中古和文UniDic) と現代語への組み立て直し。辞書が無ければ飛ばす
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.kobun import mecab  # noqa: E402

HAVE_DATA = mecab.available()


@unittest.skipUnless(HAVE_DATA, 'no classical Japanese dictionary (unidic-chuko)')
class KobunTestCase(unittest.TestCase):
    def modern(self, text):
        from dragoman.kobun import analyzer
        return next(analyzer.analyze_text(text))

    def test_parse(self):
        tokens = mecab.parse('竹取の翁といふものありけり。')
        iu = next(t for t in tokens if t.surface == 'いふ')
        self.assertEqual((iu.lemma, iu.form, iu.kana), ('言う', '連体形', 'いう'))  # 語彙素は現代の形、現代仮名遣いの読み

    def test_auxiliary_chains(self):
        self.assertTrue(self.modern('今は昔、竹取の翁といふものありけり。').modern.endswith('というものがいた。'))
        self.assertIn('紫がかっている雲が細くたなびいている', self.modern(
            'すこしあかりて、紫だちたる雲の細くたなびきたる。').modern)       # 存続の「たり」、主格の「の」
        self.assertTrue(self.modern('花の色はうつりにけりな').modern.startswith('花の色はうつってしまったな'))
        self.assertEqual(self.modern('人に笑はれけり。').modern, '人に笑われた。')
        self.assertEqual(self.modern('子を学ばしめけり。').modern, '子を学ばせた。')

    def test_natural_modern_forms(self):
        self.assertEqual(self.modern('昔、男ありけり。').modern, '昔、男がいた。')          # 助詞の無い主語、人の「あり」
        self.assertIn('絶えないで', self.modern('ゆく河の流れは絶えずして、しかももとの水にあらず。').modern)
        self.assertIn('竹を取りながら', self.modern('野山にまじりて竹を取りつつ、よろづのことに使ひけり。').modern)

    def test_nari(self):
        a = self.modern('男もすなる日記といふものを、女もしてみむとてするなり。')
        self.assertIn('するという日記', a.modern)       # 伝聞の「なり」(体言の前)
        self.assertIn('してみようと言って', a.modern)   # 意志の「む」
        self.assertTrue(a.modern.endswith('するのである。'))  # 断定の「なり」
        self.assertIn('もとの水ではない', self.modern('ゆく河の流れは絶えずして、しかももとの水にあらず。').modern)

    def test_kakari_musubi(self):
        a = self.modern('秋来ぬと目にはさやかに見えねども風の音にぞおどろかれぬる')
        self.assertIn('見えないけれども', a.modern)      # 已然形 + ども
        self.assertTrue(any('係助詞「ぞ」' in n and '連体形' in n for n in a.notes))


if __name__ == '__main__':
    unittest.main()
