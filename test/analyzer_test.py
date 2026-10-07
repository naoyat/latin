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
from core.Absolute import AblativeAbsolute
from core.Participle import ParticiplePhrase
from core.Infinitive import InfinitiveClause
from core.AndOr import AndOr
from core.PrepClause import PrepClause


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


class CoordinatedAdjectiveTestCase(unittest.TestCase):
    """並列した形容詞が名詞の前にあっても名詞に係る (後ろの et を切れ目と見ない)"""

    def modifiers_of_subject(self, text):
        noun = analyze(text).clauses[0].predicate.case_slot['Nom'][0]
        self.assertEqual(noun.surface.lower(), 'puella')
        return noun.modifiers

    def test_before_noun(self):
        modifiers = self.modifiers_of_subject('Magna et pulchra puella cantat.')
        self.assertTrue(any(isinstance(m, AndOr) for m in modifiers))

    def test_after_noun(self):
        modifiers = self.modifiers_of_subject('Puella magna et pulchra cantat.')
        self.assertTrue(any(isinstance(m, AndOr) for m in modifiers))


class ExistentialTestCase(unittest.TestCase):
    """存在・所有の文 (与格の所有者、場所): 「〜には 〜が ある」"""

    def translate(self, text):
        return analyze(text).clauses[0].predicate.translate()[0]

    def test_dative_of_possession(self):
        self.assertEqual(self.translate('Mihi est liber.'), '私には / 本,書物が / ある')

    def test_negated(self):
        self.assertTrue(self.translate('Mihi nōn est liber.').endswith('が / ない'))

    def test_number_agreement(self):
        # templa (中性複数の主格・対格) は単数の動詞 aedificat の主語にならない → 対格「神殿を」
        self.assertEqual(self.translate('Templa aedificat.'), '彼,彼女,それが / 神殿を / 建てる')
        self.assertEqual(self.translate('Templa aedificant.'), '神殿が / 建てる')

    def test_predicate_noun_is_not_existential(self):
        self.assertFalse(self.translate('Mārcus est agricola.').endswith(' / ある'))


class CoordinationBracketTestCase(unittest.TestCase):
    """並列した語の訳語に候補が複数あれば括る ({主,主人}と奴隷。「主人と奴隷」の項に見えないように)"""

    def test_bracket(self):
        from core.AndOr import _bracket
        self.assertEqual(_bracket('主,主人'), '{主,主人}')
        self.assertEqual(_bracket('奴隷'), '奴隷')
        self.assertEqual(_bracket('{美しい,きれいな}花'), '{美しい,きれいな}花')  # 括弧の中の読点だけなら括らない


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


@unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
class ParticiplePhraseTestCase(unittest.TestCase):
    """分詞句。分詞は手作りの辞書にほとんど無いので Wiktionary 辞書を使う"""

    @classmethod
    def setUpClass(cls):
        latindic.LatinDic.use_wiktionary = True

    @classmethod
    def tearDownClass(cls):
        latindic.LatinDic.use_wiktionary = False

    def phrase(self, text):
        a = analyze(text)
        self.assertEqual(len(a.participles), 1, a.participles)
        self.assertIsInstance(a.participles[0], ParticiplePhrase)
        return a, a.participles[0]

    def test_predicative_with_object(self):
        a, p = self.phrase('Puella flōrēs carpēns cantat.')
        self.assertTrue(p.adverbial)
        self.assertEqual(surfaces(p.complements), ['flōrēs'])
        self.assertEqual(p.head.surface, 'Puella')
        pred = a.clauses[0].predicate
        self.assertIn(p, pred.subordinates)
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['Puella'])
        self.assertNotIn('Acc', pred.case_slot)  # flōrēs は分詞の目的語で、cantat の目的語ではない
        self.assertIn('摘みながら', p.translate()[0])

    def test_omitted_subject(self):
        # 主語が省略されていても、主格の分詞は動詞と数が一致すれば述語的
        _, p = self.phrase('Haec locūtus discessit.')
        self.assertTrue(p.adverbial)
        self.assertIsNone(p.head)
        self.assertIn('話して', p.translate()[0])

    def test_attributive(self):
        # 主格以外の名詞に一致する分詞は、その名詞の修飾語
        a, p = self.phrase('Mīlitēs hostem fugientem cēpērunt.')
        self.assertFalse(p.adverbial)
        self.assertEqual(p.head.surface, 'hostem')
        self.assertIn(p, p.head.modifiers)
        self.assertIn('{逃げている}敵を', a.clauses[0].predicate.translate()[0])

    def test_parenthetical(self):
        _, p = self.phrase('Rēgīna, verbīs nūntiī commōta, lacrimāvit.')
        self.assertEqual(p.head.surface, 'Rēgīna')
        self.assertIn('動かされて', p.translate()[0])

    def test_leading_adverb_stays_with_main_verb(self):
        _, p = self.phrase('Tum puer in hortō sedēns cantat.')
        self.assertNotIn('Tum', p.surface)

    def test_periphrastic_passive_is_not_phrase(self):
        self.assertEqual(analyze('Puer ā magistrō laudātus est.').participles, [])


class InfinitiveClauseTestCase(unittest.TestCase):
    """不定詞句 (手作りの辞書にある動詞だけで書いた文)"""

    def infinitive(self, text):
        a = analyze(text)
        self.assertEqual(len(a.infinitives), 1, a.infinitives)
        inf = a.infinitives[0]
        self.assertIsInstance(inf, InfinitiveClause)
        pred = a.clauses[0].predicate
        self.assertIn(inf, pred.case_slot.get('Inf', []))
        return pred, inf

    def test_accusative_subject(self):
        pred, inf = self.infinitive('Videō puellam cantāre.')
        self.assertEqual(inf.kind, 'perception')
        self.assertEqual(surfaces(inf.predicate.case_slot['Nom']), ['puellam'])
        self.assertIn('{少女が 歌う}のを', pred.translate()[0])

    def test_saying(self):
        pred, inf = self.infinitive('Agricola dīcit puerōs in hortō lūdere.')
        self.assertEqual(surfaces(inf.predicate.case_slot['Nom']), ['puerōs'])
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['Agricola'])  # 主節の主語は句に入れない
        self.assertTrue(inf.translate()[0].endswith('遊ぶ}と'))

    def test_reflexive_subject(self):
        _, inf = self.infinitive('Puella dīcit sē rosās amāre.')
        self.assertEqual(surfaces(inf.predicate.case_slot['Nom']), ['sē'])
        self.assertEqual(surfaces(inf.predicate.case_slot['Acc']), ['rosās'])
        self.assertIn('{自分が バラを 愛する}と', inf.translate()[0])

    def test_esse(self):
        _, inf = self.infinitive('Putō Rōmam magnam esse.')
        self.assertIn('{ローマが 大きい}と', inf.translate()[0])

    def test_complementary(self):
        # 補足の不定詞: 対格は不定詞の目的語
        _, inf = self.infinitive('Puer librum legere cupit.')
        self.assertEqual(inf.kind, 'complement')
        self.assertNotIn('Nom', inf.predicate.case_slot)
        self.assertEqual(inf.translate()[0], '{本,書物を 読む}ことを')

    def test_not_across_conjunction(self):
        # 接続詞の向こうの動詞は支配する動詞にしない
        self.assertEqual(analyze('Puella cantat et puer lūdere.').infinitives, [])


class CopulaTestCase(unittest.TestCase):
    """sum の補語は形容詞・形容動詞・名詞の述語の形で訳す"""

    def translation(self, text):
        return analyze(text).clauses[0].predicate.translate()[0]

    def test_adjective(self):
        self.assertTrue(self.translation('Rōma magna est.').endswith('大きい'))
        self.assertTrue(self.translation('Rōma magna erat.').endswith('大きかった'))

    def test_negation(self):
        tr = self.translation('Rōma nōn magna est.')
        self.assertTrue(tr.endswith('大きくない'), tr)
        self.assertNotIn('否定', tr)  # nōn の説明文を訳に出さない

    def test_noun_adjective_sum(self):
        # 名詞 形容詞 sum の順なら形容詞は補語 (少女は美しい)
        tr = self.translation('Puella pulchra est.')
        self.assertTrue(tr.endswith('美しい'), tr)
        self.assertIn('少女は', tr)

    def test_adjective_noun_sum(self):
        # 形容詞 名詞 sum の順は1つの名詞句
        self.assertTrue(self.translation('Magnus vir est.').endswith('である'))

    def test_noun(self):
        self.assertTrue(self.translation('Puella est fīlia agricolae.').endswith('娘である'))

    def test_neuter_subject_is_nominative(self):
        pred = analyze('Templum magnum est.').clauses[0].predicate
        self.assertNotIn('Acc', pred.case_slot)


class NegationTestCase(unittest.TestCase):
    def test_verb_negation(self):
        tr = analyze('Nautae mare nōn timent.').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.endswith('恐れない'), tr)
        self.assertNotIn('¬', tr)


class FixedPhraseTestCase(unittest.TestCase):
    def test_quo_pacto(self):
        a = analyze('Quō pactō puella cantat?')
        self.assertEqual(a.absolutes, [])
        self.assertIn('どのようにして', a.clauses[0].predicate.translate()[0])

    def test_animus_idiom(self):
        # animus + 分詞・形容詞の慣用句は辞書の訳で、動詞の前に置く
        tr = analyze('Puella animō suspēnsō cantat.').clauses[0].predicate.translate()[0]
        self.assertEqual(tr, '少女が / 気をもんで,はらはらして / 歌う')
        tr = analyze('Puella aequō animō cantat.').clauses[0].predicate.translate()[0]
        self.assertIn('平静に', tr)

    def test_negative_adverb(self):
        # 否定の副詞 (nūllō pactō「決して〜ない」) は述語を否定形にする
        tr = analyze('Nūllō pactō puella cantat.').clauses[0].predicate.translate()[0]
        self.assertIn('決して', tr)
        self.assertTrue(tr.endswith('歌わない'), tr)


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

    def test_gerundive_is_not_absolute(self):
        # 動形容詞 (legendus) は独立奪格にしない
        self.assertEqual(analyze('Puer librō legendō studet.').absolutes, [])

    def test_lexicalized_present_participle(self):
        # 形容詞になった現在分詞 (excellēns「優れた」) は、節の途中なら名詞の修飾語
        self.assertEqual(analyze('Vir ingeniō excellentī librum scrīpsit.').absolutes, [])

    def test_present_participle_in_i_is_not_absolute(self):
        # 独立奪格の現在分詞は -e (puellā cantante)。-ī は与格か形容詞的な用法
        self.assertEqual(analyze('Puellae cantantī rosam dat.').absolutes, [])

    def test_manner_and_place_nouns(self):
        # animō, locō + 分詞はふつう様態・場所の奪格 (分詞は名詞の修飾語)
        self.assertEqual(analyze('Puer animō suspēnsō exspectābat.').absolutes, [])
        self.assertEqual(analyze('Mīlitēs locīs apertīs pugnābant.').absolutes, [])
        # 分詞に補語があれば独立奪格
        self.assertEqual(len(analyze('Locō ab hostibus captō Caesar discessit.').absolutes), 1)

    def test_pronoun_subject(self):
        # 主語が代名詞なら独立奪格 (eō absente「彼がいないと」)
        _, aa = self.absolute('Eō absente servī lūdunt.')
        self.assertIn('不在であると', aa.translate()[0])

    def test_inside_prepositional_phrase(self):
        # 前置詞に支配された奪格は独立奪格ではない
        self.assertEqual(analyze('Cum hīs rēbus cognitīs vēnit.').absolutes, [])


if __name__ == '__main__':
    unittest.main()
