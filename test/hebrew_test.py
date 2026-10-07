#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語: 文字 (hebrew.script)、OSHB の語形の符号 (hebrew.morphology)、文の解析 (hebrew.analyzer)。
# 辞書 (tools/build_hebrew_dic.py) が無ければ辞書を使う試験を飛ばす
#
import unittest

from hebrew import script, morphology, dictionary

HAVE_DATA = dictionary.available()


class ScriptTestCase(unittest.TestCase):
    def test_pointed_and_consonants(self):
        self.assertEqual(script.pointed('בְּרֵאשִׁ֖ית'), 'בְּרֵאשִׁית')  # 朗唱記号を除く
        self.assertEqual(script.consonants('בְּרֵאשִׁ֖ית'), 'בראשית')

    def test_translit(self):
        self.assertEqual(script.translit('בְּרֵאשִׁית'), 'bərēʾšît')
        self.assertEqual(script.translit('הַשָּׁמַיִם'), 'haššāmayim')  # 強いダゲシュは子音を重ねる
        self.assertEqual(script.translit('רוּחַ'), 'rûaḥ')              # 盗まれたパタハ
        self.assertEqual(script.translit('יִשְׂרָאֵל'), 'yiśrāʾēl')     # ś
        self.assertEqual(script.translit('מֶלֶךְ'), 'meleḵ')           # 弱いダゲシュの無い כ
        self.assertEqual(script.translit('וַיְהִי־אוֹר'), 'wayhî-ʾôr')  # マカフ

    def test_isolate(self):
        self.assertEqual(script.isolate('אוֹר'), '⁧אוֹר⁩')
        self.assertEqual(script.isolate('abc'), 'abc')


class MorphCodeTestCase(unittest.TestCase):
    """OSHB の語形の符号 → 項目 (辞書を引かない部分)"""

    def test_verb(self):
        item = morphology.segment_item('Vqw3ms', None, 'יֹּאמֶר')
        self.assertEqual((item['pos'], item['form'], item['tense'], item['person'], item['number'], item['gender']),
                         ('verb', 'wayyiqtol', 'perfect', 3, 'sg', 'm'))

    def test_noun_and_construct(self):
        item = morphology.segment_item('Ncfsc', None, 'אִשְׁתּ')
        self.assertEqual((item['pos'], item['state']), ('noun', 'construct'))
        self.assertIn(('Nom', 'sg', 'f'), item['_'])

    def test_prefixes_and_suffix(self):
        self.assertEqual(morphology.segment_item('C', 'c', 'וְ')['pos'], 'conj')
        self.assertEqual(morphology.segment_item('Td', 'd', 'הַ')['pos'], 'article')
        self.assertEqual(morphology.segment_item('R', 'b', 'בְּ')['dominates'], 'Acc')
        suffix = morphology.segment_item('Sp3ms', None, 'וֹ')
        self.assertEqual((suffix['pos'], suffix['ja'], suffix['suffix']), ('pronoun', '彼', True))

    def test_object_marker_is_not_translated(self):
        item = morphology.segment_item('To', '853', 'אֵת')
        self.assertEqual((item['pos'], item['ja']), ('article', ''))


@unittest.skipUnless(HAVE_DATA, 'ヘブライ語の辞書 (tools/build_hebrew_dic.py) が無い')
class ExplainTestCase(unittest.TestCase):
    """初学者向けの解説: 動詞の語根・態の型・時制の型"""

    def notes(self, text, ix):
        from hebrew import analyzer, explain
        return explain.notes(analyzer.lookup_all(analyzer.tokens(text))[ix])

    def test_verb(self):
        lines = self.notes('וַיֹּאמֶר', 1)
        self.assertTrue(lines[0].startswith('語根 '), lines)
        self.assertIn('(ʾ-m-r)', lines[0])
        self.assertIn('qal (paʿal パアル)', lines[1])
        self.assertIn('wayyiqtol', lines[2])

    def test_noun_root(self):
        self.assertIn('(ʾ-l-h)', self.notes('אֱלֹהִים', 0)[0])


@unittest.skipUnless(HAVE_DATA, 'ヘブライ語の辞書 (tools/build_hebrew_dic.py) が無い')
class AnalyzerTestCase(unittest.TestCase):
    def analyze(self, text):
        from hebrew import analyzer
        return list(analyzer.analyze_text(text))

    def test_genesis_1_1(self):
        # 動詞-主語-目的語。אֵת の後ろは対格、אֱלֹהִים は形が複数でも単数の動詞の主語
        pred = self.analyze('בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃')[0].clauses[0].predicate
        tr = pred.translate()[0]
        self.assertTrue(tr.startswith('神'), tr)
        self.assertIn('を / 創造した', tr)

    def test_jussive_and_wayyiqtol(self):
        a = self.analyze('וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃')[0]
        trs = [c.predicate.translate()[0] for c in a.clauses]
        self.assertTrue(trs[0].startswith('そして / 神'), trs)  # 2つの動詞の間の1語 (主語) が落ちない
        self.assertEqual(trs[1], 'ひかりが / あれ')
        self.assertEqual(trs[2], 'そして / ひかりが / あった')

    def test_nominal_sentence_and_vocative(self):
        a = self.analyze('יְהוָ֥ה רֹ֝עִ֗י לֹ֣א אֶחְסָֽר׃')[0]
        self.assertTrue(a.clauses[0].predicate.translate()[0].startswith('主 (ヤハウェ)は / 私の'))
        a = self.analyze('שְׁמַ֖ע יִשְׂרָאֵ֑ל יְהוָ֥ה אֱלֹהֵ֖ינוּ יְהוָ֥ה ׀ אֶחָֽד׃')[0]
        self.assertTrue(a.clauses[0].predicate.translate()[0].startswith('イスラエルよ'))


if __name__ == '__main__':
    unittest.main()
