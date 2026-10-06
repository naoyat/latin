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

    def test_coordinated_predicative_adjectives(self):
        # 並列した形容詞 (ἀγαθὸς καὶ σοφός) の述語的位置の判定で落ちていた
        pred = analyze('ὁ ἀνὴρ ἀγαθὸς καὶ σοφός ἐστιν.').clauses[0].predicate
        self.assertTrue(pred.is_sum)
        self.assertIn('である', pred.translate()[0])

    def test_coordinated_adjectives_between_article_and_noun(self):
        pred = analyze('οἱ ἀγαθοὶ καὶ σοφοὶ ἄνδρες λέγουσιν.').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['ἄνδρες'])

    def test_dative_of_possession(self):
        tr = analyze('ἔστι μοι βιβλίον.').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.endswith('私には / ある'), tr)

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


    def translation(self, text):
        return analyze(text).clauses[0].predicate.translate()[0]

    def test_verb_government(self):
        # 属格・与格を取る動詞は、その動詞の助詞で (ἀκούω + 属格「〜を聞く」, μάχομαι + 与格「〜と戦う」)
        self.assertIn('人,人間,人類,奴隷を', self.translation('ἤκουσα τοῦ ἀνθρώπου.'))
        self.assertIn('と / ', self.translation('οἱ Ἀθηναῖοι τοῖς Πέρσαις ἐμάχοντο.'))

    def test_time_nouns(self):
        self.assertIn('夜のうちに', self.translation('νυκτὸς ἦλθεν.'))
        self.assertIn('の間', self.translation('τρεῖς ἡμέρας ἔμεινεν.'))

    def test_comparative_genitive(self):
        tr = self.translation('ὁ υἱὸς μείζων ἐστὶ τοῦ πατρός.')
        self.assertIn('父,父親,父なる神より', tr)
        self.assertTrue(tr.startswith('son'), tr)  # 述語的位置の μείζων は補語 (息子は父より大きい)

    def test_predicative_position(self):
        pred = analyze('ὁ ἀνὴρ ἀγαθός ἐστιν.').clauses[0].predicate
        self.assertTrue(pred.translate()[0].endswith('である'))
        self.assertEqual(analyze('ὁ ἀγαθὸς ἀνὴρ λέγει.').words[1].attached_to.surface, 'ἀνήρ')  # 限定的位置


    def test_crasis(self):
        pred = analyze('κἀγὼ τὸν ἵππον βλέπω.').clauses[0].predicate
        self.assertEqual(pred.conjunction.surface, 'καί')
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['ἐγώ'])


if __name__ == '__main__':
    unittest.main()
