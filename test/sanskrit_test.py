#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリット: 文字の変換 (sanskrit.script)、語末の連声を戻す辞書引き (sanskrit.morphology)、文の解析 (sanskrit.analyzer)。
# vidyut が無ければ全部、vidyut のデータと辞書 (tools/build_sanskrit_dic.py) が無ければ辞書引き・解析を飛ばす
#
import unittest

try:
    from dragoman.sanskrit import script, morphology, dictionary, analyzer, compound
    HAVE_VIDYUT = True
except ImportError:
    HAVE_VIDYUT = False

HAVE_DATA = HAVE_VIDYUT and morphology.available() and dictionary.available()


def analyze(text):
    analyses = list(analyzer.analyze_text(text))
    assert len(analyses) == 1, analyses
    return analyses[0]


def surfaces(nodes):
    return [node.surface for node in nodes]


@unittest.skipUnless(HAVE_VIDYUT, 'vidyut が無い')
class ScriptTestCase(unittest.TestCase):
    def test_devanagari_and_iast_to_slp1(self):
        self.assertEqual(script.to_slp1('गच्छति'), 'gacCati')
        self.assertEqual(script.to_slp1('gacchati'), 'gacCati')

    def test_vedic_accents_are_removed_but_not_sibilants(self):
        self.assertEqual(script.to_slp1('agnír'), 'agnir')
        self.assertEqual(script.to_slp1('śrapayati'), 'Srapayati')
        self.assertEqual(script.to_slp1('kṛ́ta'), 'kfta')
        self.assertEqual(script.to_slp1('अ॒ग्निः'), 'agniH')

    def test_danda_does_not_make_iast_devanagari(self):
        self.assertEqual(script.to_slp1('yadā ।'), 'yadA ।')


@unittest.skipUnless(HAVE_DATA, 'vidyut のデータかサンスクリットの辞書 (tools/build_sanskrit_dic.py) が無い')
class MorphologyTestCase(unittest.TestCase):
    def test_final_sandhi_is_undone(self):
        self.assertEqual(morphology.lookup('rAmo')[0], 'rAmas')    # -o ← -aḥ (有声音の前)
        self.assertEqual(morphology.lookup('vanaM')[0], 'vanam')   # -ṃ ← -m

    def test_sa_before_consonant(self):
        key, items = morphology.lookup('sa')
        self.assertEqual(key, 'sas')
        self.assertEqual(items[0]['pos'], 'pronoun')

    def test_homonymous_roots_are_chosen_by_class(self):
        # pā「飲む」(第1類 pibati) と pā「守る」(第2類 pāti)
        self.assertIn('drink', morphology.lookup('pibanti')[1][0]['ja'])
        self.assertIn('watch', morphology.lookup('pAti')[1][0]['ja'])

    def test_causative_and_prefixed_roots(self):
        self.assertIn('cause to stand', morphology.lookup('sTApayati')[1][0]['ja'])
        self.assertTrue(morphology.lookup('udeti')[1][0]['ja'].startswith('ud-'))

    def test_vocative_is_not_preferred(self):
        _, items = morphology.lookup('tat')
        self.assertNotEqual(items[0]['_'][0][0], 'Voc')


@unittest.skipUnless(HAVE_DATA, 'vidyut のデータかサンスクリットの辞書 (tools/build_sanskrit_dic.py) が無い')
class CompoundTestCase(unittest.TestCase):
    def first_split(self, word):
        return compound.split(word)[0]

    def test_split_with_sandhi(self):
        self.assertEqual(self.first_split('rAjaputraH'), (('rAja',), 'putras'))
        self.assertEqual(self.first_split('nIlotpalam'), (('nIla',), 'utpalam'))      # a + u → o
        self.assertEqual(self.first_split('gajendraH'), (('gaja',), 'indras'))        # a + i → e
        self.assertEqual(self.first_split('mahArAjaH'), (('mahat',), 'rAjas'))       # mahā- ← mahat

    def test_pada_forms_and_anusvara(self):
        self.assertEqual(self.first_split('vaRikputreRa')[0], ('vaRij',))             # vaṇik ← vaṇij
        self.assertEqual(self.first_split('SrISAradAgaRapatiguruByaH')[0], ('SrI', 'SAradA', 'gaRapati'))

    def test_upasarga_is_not_a_member(self):
        for members, _ in compound.split('anucitasTAne')[:1]:
            self.assertNotIn('anu', members)

    def kinds(self, word):
        return [item['compound'] for item in compound.analyze(word)]

    def test_kinds(self):
        self.assertEqual(self.kinds('mahArAjaH')[0], 'karmadharaya')
        self.assertEqual(self.kinds('rAmalakzmaRO')[0], 'dvandva')
        self.assertEqual(self.kinds('trilokaH')[0], 'dvigu')
        self.assertEqual(self.kinds('aDarmaH')[0], 'negation')
        self.assertEqual(self.kinds('yaTASakti')[0], 'avyayibhava')
        self.assertEqual(self.kinds('vaRikputreRa')[0], 'tatpurusa')
        # ambara は中性なので、男性の pītāmbaraḥ は「黄色い衣を持つ (者)」(bahuvrīhi)
        self.assertEqual(self.kinds('pItAmbaraH')[0], 'bahuvrihi')

    def test_gloss(self):
        items = compound.analyze('mahArAjaH')
        self.assertEqual(items[0]['_'], [('Nom', 'sg', 'm')])  # rāja (a 語幹) の単数主格。rāj の複数ではなく
        self.assertTrue(items[0]['ja'].startswith('偉大な'))
        self.assertEqual(compound.analyze('rAmalakzmaRO')[0]['ja'], 'RāmaとLakshmana')

    def test_label_styles(self):
        try:
            compound.set_label_style('ja')
            self.assertIn('相違釈', compound.analyze('rAmalakzmaRO')[0]['base'])
            compound.set_label_style('en')
            self.assertIn('copulative', compound.analyze('rAmalakzmaRO')[0]['base'])
        finally:
            compound.set_label_style('sa')

    def test_known_compound_is_annotated(self):
        word = analyzer.lookup_all(['rAjaputraH'])[0]
        self.assertIn('rāja-putra tatpuruṣa', word.items[0].attrib('base'))


@unittest.skipUnless(HAVE_DATA, 'vidyut のデータかサンスクリットの辞書 (tools/build_sanskrit_dic.py) が無い')
class AnalyzerTestCase(unittest.TestCase):
    def test_case_frame(self):
        pred = analyze('बालकः ग्रामात् फलानि आनयति ।').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['bālakas'])
        self.assertEqual(surfaces(pred.case_slot['Abl']), ['grāmāt'])
        self.assertEqual(surfaces(pred.case_slot.get('Acc') or pred.case_slot['Nom/Acc']), ['phalāni'])

    def test_postpositive_ca(self):
        pred = analyze('रामः लक्ष्मणः च वनं गच्छतः ।').clauses[0].predicate
        self.assertEqual(len(pred.case_slot['Nom']), 1)
        self.assertIn('Lakshmana', pred.translate()[0])

    def test_adjective_and_determiner_agreement(self):
        pred = analyze('महान् देवः गच्छति ।').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['devas'])
        pred = analyze('स राजा नगरं गच्छति ।').clauses[0].predicate
        self.assertEqual(surfaces(pred.case_slot['Nom']), ['rājā'])

    def test_copula(self):
        self.assertIn('あなたである', analyze('तत् त्वम् असि ।').clauses[0].predicate.translate()[0])

    def test_possession_and_existence(self):
        self.assertTrue(analyze('मम पुस्तकम् अस्ति ।').clauses[0].predicate.translate()[0].startswith('私には'))
        # 森にライオンがいる (処格の場所を先に「に」、生き物は「いる」)
        tr = analyze('वने सिंहः अस्ति ।').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.endswith('に / ライオンが / いる'), tr)
        # nāsti = na asti。否定の存在文の場所は「〜には」
        tr = analyze('वने सिंहः नास्ति ।').clauses[0].predicate.translate()[0]
        self.assertTrue(tr.endswith('には / ライオンが / いない'), tr)

    def test_locative_absolute(self):
        a = analyze('सूर्ये उदिते सर्वे जनाः उत्तिष्ठन्ति ।')
        self.assertEqual(len(a.absolutes), 1)
        self.assertEqual(a.absolutes[0].verb.surface, 'udite')

    def test_two_finite_verbs(self):
        a = analyze('यदा मेघः वर्षति तदा मयूरः नृत्यति ।')
        self.assertEqual(len(a.clauses), 2)



@unittest.skipUnless(HAVE_DATA, 'vidyut のデータかサンスクリットの辞書 (tools/build_sanskrit_dic.py) が無い')
class BuddhistTestCase(unittest.TestCase):
    def tearDown(self):
        from dragoman.sanskrit import buddhist
        buddhist.set_forced(None)
        buddhist.set_active(False)

    def glosses(self, text):
        return [w.items[0].ja for w in analyzer.lookup_all(analyzer.tokens(text)) if w.items]

    def test_auto_detection(self):
        from dragoman.sanskrit import buddhist
        buddhist.detect('इह शारिपुत्र रूपं शून्यता')                  # śāriputra があれば仏典の語彙
        self.assertEqual([self.glosses(w)[0] for w in ('रूपं', 'वेदना', 'संज्ञा')], ['色', '受', '想'])
        buddhist.detect('देवाः सुरां पिबन्ति ।')                       # 無ければ一般の訳語
        self.assertNotEqual(self.glosses('देवाः')[0], '天')

    def test_general_glosses(self):
        from dragoman.sanskrit import buddhist
        buddhist.set_forced(False)
        buddhist.detect('')
        self.assertTrue(self.glosses('आर्यः')[0].startswith('高貴な'))  # Wiktionary の先頭は民族名 Indo-Aryan
        self.assertEqual(self.glosses('पुस्तकम्'), ['本'])                 # 先頭は「突起のある飾り」

    def test_terms_and_verbs(self):
        from dragoman.sanskrit import buddhist
        buddhist.set_forced(True)
        buddhist.detect('')
        self.assertEqual(self.glosses('बोधिसत्त्वः प्रज्ञापारमितायां'), ['菩薩', '般若波羅蜜多'])
        self.assertEqual(self.glosses('व्यवलोकयति'), ['観察する'])         # 接頭辞つきの語根
        self.assertEqual(self.glosses('अमला'), ['不垢の'])                 # 形容詞の女性形


if __name__ == '__main__':
    unittest.main()
