#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析器 (latin.analyzer) の単体テスト
#
# @unittest.expectedFailure は「本来こう解析されるべきだが、今はできていない」もの。
# 直ると unexpected success として報告されるので、そのときはデコレータを外す。
# (plēnum の係り先と -que の並列は 2026-10 に解決)
#
import unittest

from latin import latindic, analyzer, wiktionary
from latin.Absolute import AblativeAbsolute
from latin.AndOr import AndOr
from latin.PrepClause import PrepClause


_saved = None


def setUpModule():
    global _saved
    latindic.load()
    # ダウンロードしたデータや環境に左右されないよう、手作りの辞書だけで、タガーを使わずに解析する
    _saved = (latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER)
    latindic.LatinDic.use_wiktionary = False
    analyzer.USE_TAGGER = False


def tearDownModule():
    latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER = _saved


def analyze(text):
    analyses = list(analyzer.analyze_text(text))
    assert len(analyses) == 1, analyses
    return analyses[0]


def surfaces(nodes):
    return [node.surface for node in nodes]


def find(nodes, surface):
    """スロット内から表層形で語を探す (並列句の中も探す)"""
    for node in nodes:
        if isinstance(node, AndOr):
            found = find([words[0] for words in node.words_slots], surface)
            if found: return found
        elif node.surface == surface:
            return node
    return None


# 例文はこのテストのために作ったもの (教科書などからの引用ではない)

class TempleTestCase(unittest.TestCase):
    """In Siciliā īnsulā māgnum templum agricola aedificāvit plēnum dōnōrum pulchrōrum."""

    @classmethod
    def setUpClass(cls):
        cls.a = analyze('In Siciliā īnsulā māgnum templum agricola aedificāvit plēnum dōnōrum pulchrōrum.')
        cls.pred = cls.a.clauses[0].predicate

    def test_single_verb(self):
        self.assertEqual(surfaces(self.a.verbs), ['aedificāvit'])
        self.assertEqual((self.pred.mood(), self.pred.person(), self.pred.number()),
                         ('indicative', 3, 'sg'))

    def test_prep_clause(self):
        clause = self.pred.case_slot[('prep', 'In')][0]
        self.assertIsInstance(clause, PrepClause)
        self.assertEqual(clause.dominated_case, 'Abl')
        self.assertEqual(surfaces(clause.words), ['Siciliā', 'īnsulā'])

    def test_subject(self):
        self.assertEqual(surfaces(self.pred.case_slot['Nom']), ['agricola'])

    def test_adjective_before_noun(self):
        templum = find(self.pred.case_slot['Nom/Acc'], 'templum')
        self.assertIn('māgnum', surfaces(templum.modifiers))

    def test_adjective_after_noun(self):
        donorum = self.a.words[8]
        self.assertEqual(donorum.surface, 'dōnōrum')
        self.assertEqual(surfaces(donorum.modifiers), ['pulchrōrum'])

    def test_adjective_across_verb(self):
        # plēnum (dōnōrum pulchrōrum) は動詞を越えて templum にかかる
        templum = find(self.pred.case_slot['Nom/Acc'], 'templum')
        self.assertIn('plēnum', surfaces(templum.modifiers))


class GloriaTestCase(unittest.TestCase):
    """Templum, glōria rēgis Siciliae, māgnum incolās dēlectābat."""

    @classmethod
    def setUpClass(cls):
        cls.a = analyze('Templum, glōria rēgis Siciliae, māgnum incolās dēlectābat.')
        cls.pred = cls.a.clauses[0].predicate

    def test_chained_genitives(self):
        gloria = find(self.pred.case_slot['Nom'], 'glōria')
        self.assertEqual(surfaces(gloria.genitives), ['rēgis'])
        self.assertEqual(surfaces(gloria.genitives[0].genitives), ['Siciliae'])

    def test_adjective_agreement_across_words(self):
        # māgnum (中性) は間の glōria (女性) を飛ばして Templum にかかる
        templum = find(self.pred.case_slot['Nom/Acc'], 'Templum')
        self.assertEqual(surfaces(templum.modifiers), ['māgnum'])

    def test_object(self):
        self.assertEqual(surfaces(self.pred.case_slot['Acc']), ['incolās'])


class RomaTestCase(unittest.TestCase):
    """Rōma autem, patria agricolae, plēna glōriae, puerō rosam pulchram longamque hastam dat."""

    @classmethod
    def setUpClass(cls):
        cls.a = analyze('Rōma autem, patria agricolae, plēna glōriae, '
                        'puerō rosam pulchram longamque hastam dat.')
        cls.pred = cls.a.clauses[0].predicate

    def test_conjunction(self):
        self.assertEqual(self.pred.conjunction.surface, 'autem')

    def test_apposition(self):
        self.assertEqual(surfaces(self.pred.case_slot['Nom']), ['Rōma', 'patria'])

    def test_dative(self):
        self.assertEqual(surfaces(self.pred.case_slot['Dat']), ['puerō'])

    def test_coordinated_objects(self):
        acc = self.pred.case_slot['Acc']
        self.assertEqual(len(acc), 1)
        self.assertIsInstance(acc[0], AndOr)
        self.assertEqual(acc[0].and_or_word, 'et')
        self.assertEqual([words[0].surface for words in acc[0].words_slots], ['rosam', 'hastam'])

    def test_adjective_modifies_one_conjunct(self):
        # rosam pulchram longamque hastam = 美しいバラと長い槍
        hastam = find(self.pred.case_slot['Acc'], 'hastam')
        self.assertEqual(surfaces(hastam.modifiers), ['longamque'])
        rosam = find(self.pred.case_slot['Acc'], 'rosam')
        self.assertEqual(surfaces(rosam.modifiers), ['pulchram'])


class NoVerbTestCase(unittest.TestCase):
    def test_no_verb(self):
        a = analyze('Rōma et Graecia.')
        self.assertEqual(a.verbs, [])
        self.assertEqual(a.clauses, [])
        self.assertEqual(len(a.nodes), 2)  # [et] Rōma Graecia と句点
        self.assertIsInstance(a.nodes[0], AndOr)


class DeterminismTestCase(unittest.TestCase):
    def test_translate_is_repeatable(self):
        # translate() が格スロットを書き換えないこと
        pred = analyze('Puella puerō rosam dat.').clauses[0].predicate
        self.assertEqual(pred.translate(), pred.translate())



@unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
class AblativeAbsoluteTestCase(unittest.TestCase):
    """独立奪格。分詞は手作りの辞書にほとんど無いので Wiktionary 辞書を使う"""

    @classmethod
    def setUpClass(cls):
        latindic.LatinDic.use_wiktionary = True

    @classmethod
    def tearDownClass(cls):
        latindic.LatinDic.use_wiktionary = False

    def absolute(self, text):
        a = analyze(text)
        self.assertEqual(len(a.absolutes), 1, a.absolutes)
        aa = a.absolutes[0]
        self.assertIsInstance(aa, AblativeAbsolute)
        return a, aa

    def test_perfect_passive(self):
        a, aa = self.absolute('Hīs rēbus cognitīs agricola ad vīllam vēnit.')
        self.assertEqual((aa.subject.surface, aa.verb.surface, aa.kind()), ('rēbus', 'cognitīs', 'passive'))
        self.assertIn('知られて', aa.translate()[0])
        # 文の主語は独立奪格の外の主格
        pred = a.clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['agricola'])
        self.assertIn(aa, pred.subordinates)

    def test_present(self):
        _, aa = self.absolute('Puellā cantante puer dormit.')
        self.assertEqual((aa.subject.surface, aa.kind()), ('Puellā', 'present'))
        self.assertIn('歌っていると', aa.translate()[0])

    def test_deponent_is_active(self):
        # mortuus は morior (形式受動態) の完了分詞なので能動「死んで」
        _, aa = self.absolute('Rēge mortuō populus flēvit.')
        self.assertEqual(aa.kind(), 'active')
        self.assertIn('死んで', aa.translate()[0])

    def test_inside_prepositional_phrase(self):
        # 前置詞に支配された奪格は独立奪格ではない
        self.assertEqual(analyze('Cum hīs rēbus cognitīs vēnit.').absolutes, [])


if __name__ == '__main__':
    unittest.main()
