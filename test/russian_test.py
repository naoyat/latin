#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語: 文字 (russian.script)、語形の解析 (russian.morphology)、文の解析 (russian.analyzer)。
# pymorphy3 が無ければ解析を、辞書 (tools/build_russian_dic.py) が無ければ訳語と強勢の試験を飛ばす
#
import unittest

from russian import script

try:
    from russian import morphology, analyzer, dictionary
    HAVE_PYMORPHY = morphology.available()
except ImportError:
    HAVE_PYMORPHY = False
HAVE_DATA = HAVE_PYMORPHY and dictionary.available()


def analyze(text):
    analyses = list(analyzer.analyze_text(text))
    assert len(analyses) == 1, analyses
    return analyses[0]


def surfaces(nodes):
    return [node.surface for node in nodes]


class ScriptTestCase(unittest.TestCase):
    def test_key(self):
        self.assertEqual(script.key('Кни́га'), 'книга')
        self.assertEqual(script.key('Ёлка'), 'елка')

    def test_stress_index(self):
        self.assertEqual(script.stress_index('кни́га'), 2)
        self.assertEqual(script.stress_index('ёлка'), 0)  # ё は常に強勢がある
        self.assertIsNone(script.stress_index('книга'))

    def test_translit(self):
        self.assertEqual(script.translit('Кни́га'), 'Kníga')
        self.assertEqual(script.translit('щи'), 'šči')


@unittest.skipUnless(HAVE_PYMORPHY, 'pymorphy3 が無い')
class MorphologyTestCase(unittest.TestCase):
    def test_noun_case(self):
        item = morphology.analyze('книгу')[0]
        self.assertEqual((item['pos'], item['base']), ('noun', 'книга'))
        self.assertIn(('Acc', 'sg', 'f'), item['_'])

    def test_aspect_and_past(self):
        self.assertEqual(morphology.analyze('читал')[0]['tense'], 'imperfect')    # 不完了体の過去「読んでいた」
        self.assertEqual(morphology.analyze('прочитал')[0]['tense'], 'perfect')   # 完了体の過去「読んだ」

    def test_prepositions(self):
        self.assertEqual({i['dominates'] for i in morphology.analyze('в')}, {'Acc', 'Loc'})
        self.assertEqual([i['dominates'] for i in morphology.analyze('со')], ['Ins', 'Gen', 'Acc'])  # со = с

    def test_pronoun_readings_are_kept(self):
        # pymorphy3 は все を助詞「まだ」と読むのを一番にする
        self.assertEqual(morphology.analyze('все')[0]['base'], 'весь')
        self.assertTrue(any(i['pos'] == 'pronoun' for i in morphology.analyze('что')))

    def test_plural_adjective_agrees_with_any_gender(self):
        self.assertIn(('Nom', 'pl', 'n'), morphology.analyze('германские')[0]['_'])


@unittest.skipUnless(HAVE_DATA, 'pymorphy3 かロシア語の辞書 (tools/build_russian_dic.py) が無い')
class AnalyzerTestCase(unittest.TestCase):
    def test_case_frame(self):
        pred = analyze('Я дал книгу брату.').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['Я'])
        self.assertEqual(surfaces(pred.case_slot['Acc']), ['книгу'])
        self.assertEqual(surfaces(pred.case_slot['Dat']), ['брату'])

    def test_preposition_governs_genitive(self):
        # из дома: 副詞 дома「家で」でなく、前置詞の支配する属格に。係り先の無い属格を対格に読み替えない
        pred = analyze('Я пришёл из дома.').clauses[0].predicate
        clause = pred.case_slot[('prep', 'из')][0]
        self.assertEqual(clause.dominated_case, 'Gen')
        self.assertEqual(surfaces(clause.words)[0], 'дома')

    def test_zero_copula(self):
        a = analyze('Он студент.')
        pred = a.clauses[0].predicate
        self.assertTrue(pred.is_sum)
        self.assertTrue(pred.translate()[0].startswith('彼は'))

    def test_passive_with_byt(self):
        a = analyze('Книга была прочитана.')
        self.assertEqual(surfaces(a.verbs), ['была прочитана'])

    def test_genitive_does_not_cross_verb(self):
        pred = analyze('Рефери дисквалифицировал боксёра.').clauses[0].predicate
        self.assertIn('боксёра', surfaces(pred.case_slot.get('Acc', [])))

    def test_svo_clauses(self):
        a = analyze('Германские войска атаковали советские войска, но успеха не имели.')
        first = a.clauses[0].predicate
        self.assertEqual(len(first.case_slot.get('Nom', []) + first.case_slot.get('Nom/Acc', [])), 2)
        self.assertEqual(len(a.clauses), 2)

    def test_possession_and_existence(self):
        self.assertEqual(analyze('У меня есть книга.').clauses[0].predicate.translate()[0].split(' / ')[-1], 'ある')
        tr = analyze('У меня нет книги.').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.endswith('本,書物,書籍,著書が / ない'), tr)  # 生格の книги が主語
        self.assertTrue(tr.startswith('{私}〜には'), tr)
        self.assertTrue(analyze('Мы были в театре.').clauses[0].predicate.translate()[0].startswith('私たちは'))
        self.assertTrue(analyze('В лесу есть волк.').clauses[0].predicate.translate()[0].endswith('狼が / いる'))
        self.assertTrue(analyze('У меня не было времени.').clauses[0].predicate.translate()[0].endswith('なかった'))

    def test_est_after_modal_is_eat(self):
        a = analyze('Я хочу есть.')
        self.assertNotIn('ある', a.clauses[0].predicate.translate()[0])

    def test_stressed_form(self):
        self.assertEqual(morphology.stressed('книги'), 'кни́ги')


if __name__ == '__main__':
    unittest.main()
