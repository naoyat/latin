#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の文の解析 (greek.analyzer)。辞書 (tools/build_greek_dic.py) が無ければ飛ばす
#
import unittest

from greek import analyzer, dictionary


def analyze(text):
    analyses = list(analyzer.analyze_text(text))
    assert len(analyses) == 1, analyses
    return analyses[0]


def surfaces(nodes):
    return [node.surface for node in nodes]


@unittest.skipUnless(dictionary.available(), 'ギリシア語の辞書 (tools/build_greek_dic.py) が無い')
class GreekAnalyzerTestCase(unittest.TestCase):
    def test_case_frame(self):
        pred = analyze('ὁ ἄνθρωπος τὸν ἵππον βλέπει.').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['ἄνθρωπος'])
        self.assertEqual(surfaces(pred.case_slot['Acc']), ['ἵππον'])

    def test_article_is_attached_and_not_translated(self):
        a = analyze('ὁ ἄνθρωπος τὸν ἵππον βλέπει.')
        noun = a.clauses[0].predicate.case_slot['Acc'][0]
        self.assertEqual([m.surface for m in noun.modifiers], ['τόν'])
        self.assertNotIn('その', a.clauses[0].predicate.translate()[0])

    def test_article_before_adjective_and_noun(self):
        pred = analyze('ὁ ἀγαθὸς ἀνὴρ τῷ παιδὶ βιβλίον δίδωσιν.').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['ἀνήρ'])
        self.assertEqual(surfaces(pred.case_slot['Dat']), ['παιδί'])

    def test_copula_subject_has_article(self):
        # θεὸς ἦν ὁ λόγος: 冠詞の付いた ὁ λόγος が主語、θεός が補語
        tr = analyze('θεὸς ἦν ὁ λόγος.').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.startswith('ロゴスは'), tr)
        self.assertIn('神', tr)

    def test_negation(self):
        tr = analyze('ὁ ἄνθρωπος οὐ βλέπει τὸν ἵππον.').clauses[0].predicate.translate()[0]
        self.assertIn('否定', tr)


    def test_genitive_absolute(self):
        a = analyze('τοῦ βασιλέως ἐλθόντος οἱ πολῖται ἔφυγον.')
        self.assertEqual([(x.subject.surface, x.verb.surface) for x in a.absolutes], [('βασιλέως', 'ἐλθόντος')])
        self.assertEqual(surfaces(a.clauses[0].predicate.case_slot['Nom']), ['πολῖται'])

    def test_generated_participle(self):
        # 変化形の項目の無い分詞 (活用表の主格から作った形): αὐτοῦ καθίσαντος
        a = analyze('αὐτοῦ καθίσαντος οἱ μαθηταὶ ἦλθον.')
        self.assertEqual(len(a.absolutes), 1)

    def test_not_absolute(self):
        # 冠詞と名詞の間の分詞は修飾 / 属格を取る動詞 (ἀκούω) の目的語
        self.assertEqual(analyze('τοῦ λέγοντος ἀνθρώπου ἤκουσα.').absolutes, [])
        self.assertEqual(analyze('ἤκουσα φωνῆς λεγούσης.').absolutes, [])


if __name__ == '__main__':
    unittest.main()
