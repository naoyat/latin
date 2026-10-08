#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文: 品詞分解 (MeCab + 中古和文UniDic) と現代語への組み立て直し。辞書が無ければ飛ばす
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.kobun import mecab, modernize  # noqa: E402

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

    def test_auxiliary_meaning_in_context(self):
        def chosen(text):
            a = self.modern(text)
            return a.modern, [t.chosen for t in a.tokens if t.chosen]
        self.assertEqual(chosen('人に笑はれけり。'), ('人に笑われた。', ['受身']))          # 「人に」があれば受身
        self.assertEqual(chosen('物も言はれず。'), ('物も言うことができない。', ['可能']))  # 打消と組んで可能
        self.assertEqual(chosen('帝、笑はれけり。'), ('帝、笑いなさった。', ['尊敬']))      # 身分の高い主語は尊敬
        self.assertIn('自発', chosen('昔のこと思ひ出でられけり。')[1])                     # 心情の動詞は自発
        self.assertEqual(chosen('我、京へ行かむ。'), ('我、京へ行こう。', ['意志']))        # 一人称の主語は意志
        self.assertIn('思うような子', chosen('思はむ子を法師になしたらむこそ心苦しけれ。')[0])  # 連体形 + 体言は婉曲
        self.assertEqual(chosen('この人こそ行かめ。')[1], ['適当・勧誘'])                   # こそ〜め
        self.assertEqual(chosen('花散りぬべし。'), ('花がきっと散るはずだ。', ['強意', '当然・推量']))

    def test_honorifics(self):
        a = self.modern('帝、御覧じて、いとあはれとおぼしけり。')
        self.assertTrue(a.modern.startswith('帝、ご覧になって'))
        self.assertTrue(a.modern.endswith('お思いになった。'))
        a = self.modern('宮に見せたてまつりたまふ。')
        self.assertEqual(a.modern, '宮に見せ申し上げなさる。')
        self.assertTrue(any(n.startswith('二方面への敬語') for n in a.notes))
        self.assertTrue(any(n.startswith('主語: 書かれていないが') for n in a.notes))
        self.assertEqual(self.modern('帝の言はせたまふ。').modern, '帝が言いなさる。')      # 最高敬語 (せたまふ)
        self.assertEqual(self.modern('心ざしのほど、思ひ知りはべりぬ。').modern, '心ざしのほど、思い知りました。')  # 丁寧の補助動詞

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

    def test_obsolete_words(self):
        a = self.modern('やうやう白くなりゆく山ぎは、すこしあかりて、紫だちたる雲のほそくたなびきたる。')
        self.assertIn('すこし明るくなって', a.modern)    # 廃語の表: 明かる → 明るくなる
        self.assertTrue(any('現代語に無い語' in n and 'あかる' in n for n in a.notes))
        self.assertIn('行き悩んで去る', self.modern('行きなづみて往ぬ。').modern)
        self.assertFalse(modernize.modern_known('あかる', '動詞'))  # 現代語では形容詞「明るい」に読まれる
        self.assertTrue(modernize.modern_known('行く', '動詞'))
        self.assertIn('〔', self.modern('花ぞむつれたる。').modern)  # 表に無い語は形だけ直して印を付ける


if __name__ == '__main__':
    unittest.main()
