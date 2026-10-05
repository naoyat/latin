#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary 由来の補助辞書のテスト
#   ImportTestCase: 項目の変換 (データのダウンロード不要)
#   LookupTestCase: 作成済みの辞書の検索 (辞書ファイルが無ければスキップ)
#
import unittest

from latin import wiktionary, latindic, analyzer
from latin.wiktionary_import import convert_entry, make_item, japanese_gloss, english_glosses


def form(text, *tags):
    return {'form': text, 'tags': list(tags)}


ARVUM = {
    'word': 'arvum', 'lang_code': 'la', 'pos': 'noun',
    'head_templates': [{'expansion': 'arvum n (genitive arvī); second declension'}],
    'senses': [{'glosses': ['field'], 'tags': ['declension-2', 'neuter']},
               {'glosses': ['farm land'], 'tags': ['declension-2', 'neuter']}],
    'forms': [form('arvī', 'genitive'), form('no-table-tags', 'table-tags'),
              form('arvum', 'nominative', 'singular'), form('arva', 'nominative', 'plural'),
              form('arvī', 'genitive', 'singular'), form('arvum', 'accusative', 'singular'),
              form('arva', 'accusative', 'plural')],
}

AMO = {
    'word': 'amo', 'lang_code': 'la', 'pos': 'verb',
    'senses': [{'glosses': ['to love, be fond of']}],
    'forms': [form('amō', 'canonical'), form('amāre', 'infinitive', 'present'),
              form('amat', 'active', 'indicative', 'present', 'singular', 'third-person'),
              form('amāverit', 'active', 'future', 'indicative', 'perfect', 'singular', 'third-person'),
              form('amāverant', 'active', 'indicative', 'pluperfect', 'plural', 'third-person'),
              form('amātus + present active indicative of sum', 'indicative', 'passive', 'perfect'),
              form('amāssō', 'active', 'first-person', 'future', 'sigmatic', 'singular'),
              form('-', 'active', 'first-person', 'imperative', 'present', 'singular'),
              form('amārī', 'infinitive', 'passive', 'present'),
              form('amātus', 'participle', 'passive', 'perfect'),
              form('amandī', 'genitive', 'gerund', 'noun-from-verb')],
}

IN = {
    'word': 'in', 'lang_code': 'la', 'pos': 'prep',
    'head_templates': [{'expansion': 'in (+ ablative)'}],
    'senses': [{'glosses': ['in, at, on'], 'tags': ['with-ablative']},
               {'glosses': ['into, to'], 'tags': ['with-accusative']}],
}

AMATUS = {
    'word': 'amatus', 'lang_code': 'la', 'pos': 'verb',
    'senses': [{'glosses': ['loved; having been loved'],
                'tags': ['form-of', 'participle', 'passive', 'perfect'],
                'form_of': [{'word': 'amō'}]}],
    'forms': [form('amātus', 'canonical'), form('amātus', 'masculine', 'nominative', 'singular'),
              form('amāta', 'feminine', 'nominative', 'singular'),
              form('amāta', 'neuter', 'nominative', 'plural')],
}


def items_of(entry, ja_glosses=None):
    info, forms = convert_entry(entry, ja_glosses)
    return [make_item(surface, info, features) for surface, features in forms]


class VariantsTestCase(unittest.TestCase):
    def test_variants(self):
        self.assertEqual(wiktionary._variants('juvenēs'), ['juvenēs', 'iuvenēs'])
        self.assertEqual(wiktionary._variants('Inrūpit'), ['Inrūpit', 'Irrūpit'])
        self.assertEqual(wiktionary._variants('arva'), ['arva'])


class ImportTestCase(unittest.TestCase):
    def test_noun(self):
        items = {item['surface']: item for item in items_of(ARVUM)}
        self.assertEqual(items['arvum']['_'], [('Nom', 'sg', 'n'), ('Acc', 'sg', 'n')])
        self.assertEqual(items['arva']['base'], 'arvum')
        self.assertEqual(items['arva']['gen_sg'], 'arvī')
        self.assertEqual(items['arva']['ja'], 'field,farm land')
        self.assertEqual(items['arva']['gloss_lang'], 'en')

    def test_japanese_gloss_preferred(self):
        items = items_of(ARVUM, {('arvum', 'noun'): '畑,耕地'})
        self.assertEqual(items[0]['ja'], '畑,耕地')
        self.assertEqual(items[0]['gloss_lang'], 'ja')

    def test_verb_tenses(self):
        items = items_of(AMO)
        by_surface = {}
        for item in items:
            by_surface.setdefault(item['surface'], []).append(item)
        amat, = by_surface['amat']
        self.assertEqual((amat['mood'], amat['voice'], amat['tense'], amat['person'], amat['number']),
                         ('indicative', 'active', 'present', 3, 'sg'))
        self.assertEqual(by_surface['amāverit'][0]['tense'], 'future-perfect')
        self.assertEqual(by_surface['amāverant'][0]['tense'], 'past-perfect')
        self.assertEqual(by_surface['amārī'][0]['mood'], 'infinitive')
        self.assertEqual(amat['pres1sg'], 'amō')
        self.assertEqual(amat['ja'], 'love,be fond of')

    def test_perfect_passive_is_generated(self):
        surfaces = {item['surface']: item for item in items_of(AMO)}
        self.assertEqual(surfaces['amāta est']['tense'], 'perfect')
        self.assertEqual(surfaces['amāta est']['gender'], 'f')
        self.assertEqual(surfaces['amātī erant']['tense'], 'past-perfect')
        self.assertEqual(surfaces['amātī erant']['number'], 'pl')

    def test_skipped_forms(self):
        surfaces = {item['surface'] for item in items_of(AMO)}
        for skipped in ('amāssō', '-', 'amandī', 'amātus + present active indicative of sum'):
            self.assertNotIn(skipped, surfaces)

    def test_preposition_per_case(self):
        items = items_of(IN)
        self.assertEqual([(i['dominates'], i['ja']) for i in items], [('Acc', 'into,to'), ('Abl', 'in,at,on')])

    def test_participle(self):
        items = {item['surface']: item for item in items_of(AMATUS)}
        self.assertEqual(items['amāta']['pos'], 'participle')
        self.assertEqual(items['amāta']['pres1sg'], 'amō')
        self.assertEqual(items['amāta']['tense'], 'past')
        self.assertEqual(items['amāta']['_'], [('Nom', 'sg', 'f'), ('Nom', 'pl', 'n')])

    def test_form_of_entry_is_skipped(self):
        entry = {'word': 'amat', 'lang_code': 'la', 'pos': 'verb',
                 'senses': [{'glosses': ['third-person singular'], 'form_of': [{'word': 'amō'}]}]}
        self.assertIsNone(convert_entry(entry))

    def test_japanese_gloss_cleanup(self):
        def gloss(text):
            return japanese_gloss({'senses': [{'glosses': [text]}]})
        self.assertEqual(gloss('道、道路、通路。'), '道,道路,通路')
        self.assertEqual(gloss('（動詞不定形）愛でる。好む。'), '愛でる,好む')
        self.assertEqual(gloss('dareの直説法現在第一人称単数形。'), '')

    def test_english_gloss(self):
        entry = {'senses': [{'glosses': ['to love, be fond of']}, {'glosses': ['to like (something)']}]}
        self.assertEqual(english_glosses(entry), 'love,be fond of,like')


@unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
class LookupTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        latindic.load()
        cls.saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = True

    @classmethod
    def tearDownClass(cls):
        latindic.LatinDic.use_wiktionary = cls.saved

    def test_exact(self):
        items = wiktionary.lookup('arva')
        self.assertTrue(any(i['base'] == 'arvum' for i in items))

    def test_assimilated_prefix(self):
        # テキストは adficiō、Wiktionary は afficiō
        self.assertTrue(any(i.get('pres1sg') == 'afficiō' for i in wiktionary.lookup('adficī')))

    def test_j_to_i(self):
        # Wiktionary は iuvenis、テキストは juvenis
        self.assertTrue(any(i.get('base') == 'iuvenis' for i in wiktionary.lookup('juvenēs')))

    def test_hand_dictionary_has_priority(self):
        items = latindic.lookup('rēgis')
        self.assertTrue(items)
        self.assertTrue(all(i.get('source') != 'wiktionary' for i in items))

    def test_capitalized_word_prefers_hand_lowercase(self):
        word = analyzer.lookup_all(['Virī'])[0]
        self.assertTrue(all(i.attrib('source') != 'wiktionary' for i in word.items))

    def test_two_word_form_does_not_override_hand_dictionary(self):
        # īgnōta (手作りの辞書) + erant が、Wiktionary の完了受動 (īgnōta erant) にならない
        words = analyzer.lookup_all(['īgnōta', 'erant'])
        self.assertEqual([w.surface for w in words], ['īgnōta', 'erant'])


if __name__ == '__main__':
    unittest.main()
