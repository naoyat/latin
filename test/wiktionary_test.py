#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary 由来の補助辞書のテスト
#   ImportTestCase: 項目の変換 (データのダウンロード不要)
#   LookupTestCase: 作成済みの辞書の検索 (辞書ファイルが無ければスキップ)
#
import unittest

from latin import wiktionary, latindic, analyzer
from core.wiktionary_import import descendants_summary, etymology_summary
from core.wiktionary_import import convert_entry, make_item, japanese_gloss, english_glosses


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

# 見出し語として立っている分詞: form_of が無く、元の動詞は語源欄にだけある
MORTUUS = {
    'word': 'mortuus', 'lang_code': 'la', 'pos': 'verb',
    'etymology_text': 'Perfect active participle of morior (“die”).',
    'senses': [{'glosses': ['dead, having died'], 'tags': ['declension-1', 'declension-2', 'participle']}],
    'forms': [form('mortuus', 'canonical'), form('mortuō', 'ablative', 'masculine', 'singular')],
}


# 子孫語の木 (この試験のために作った最小の例。形は kaikki.org の抽出データに合わせる)
ACUTUS_DESCENDANTS = {
    'word': 'acutus', 'lang_code': 'la', 'pos': 'verb',
    'descendants': [
        {'lang': 'Middle English', 'lang_code': 'enm', 'word': 'acute', 'raw_tags': ['borrowed'],
         'descendants': [{'lang': 'English', 'lang_code': 'en', 'word': 'acute'}]},
        {'lang': 'Old French', 'lang_code': 'fro', 'word': 'agu',
         'descendants': [{'lang': 'French', 'lang_code': 'fr', 'word': 'aigu'}]},
        {'lang': 'English', 'lang_code': 'en', 'word': 'acu-'},
        {'lang': 'English', 'lang_code': 'en', 'word': 'in acuto'},
    ],
}


# 語源 (この試験のために作った例。古い形式 (inh, cog) と新しい形式 (etymon) のテンプレート、頭の系統図)
GENU_ETYMOLOGY = {
    'word': 'genu', 'lang_code': 'la', 'pos': 'noun',
    'etymology_text': 'Etymology tree\nProto-Indo-European *ǵónu\nProto-Italic *genu\nLatin genu\n'
                      'From Proto-Italic *genu, from Proto-Indo-European *ǵónu.',
    'etymology_templates': [
        {'name': 'etymon', 'args': {'1': 'la', '2': ':inh', '3': 'itc-pro:*genu<ety:inh<ine-pro:*ǵónu>>'}},
        {'name': 'inh', 'args': {'1': 'la', '2': 'itc-pro', '3': '*genu'}},
        {'name': 'cog', 'args': {'1': 'grc', '2': 'γόνυ', 't': 'knee'}},
        {'name': 'cog', 'args': {'1': 'hit', '2': 'genu', 'tr': 'ge-e-nu'}},
    ],
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

    def test_lexicalized_participle_verb_from_etymology(self):
        item, = items_of(MORTUUS)
        self.assertEqual((item['pos'], item['pres1sg']), ('participle', 'morior'))

    def test_descendants(self):
        summary = {(d['lang'], d['word']): d for d in descendants_summary(ACUTUS_DESCENDANTS)}
        self.assertEqual(summary[('fr', 'aigu')]['kind'], 'inherited')
        self.assertEqual(summary[('fr', 'aigu')]['via'], [['fro', 'agu']])
        self.assertEqual(summary[('en', 'acute')]['kind'], 'borrowed')
        # 接頭辞と、1語のものがあるときの句は除く
        self.assertNotIn(('en', 'acu-'), summary)
        self.assertNotIn(('en', 'in acuto'), summary)

    def test_english_is_never_inherited(self):
        # 英語に印の無いまま載っている語も借用 (英語はラテン語から語を継承しない)
        entry = {'lang_code': 'la', 'descendants': [{'lang': 'English', 'lang_code': 'en', 'word': 'rebus'}]}
        self.assertEqual(descendants_summary(entry)[0]['kind'], 'borrowed')

    def test_etymology(self):
        ety = etymology_summary(GENU_ETYMOLOGY)
        # 新しい形式の入れ子も系統に。古い形式と重なる語は1つに
        self.assertEqual([(a[1], a[2]) for a in ety['ancestors']], [('itc-pro', '*genu'), ('ine-pro', '*ǵónu')])
        self.assertEqual(ety['cognates'], [['grc', 'γόνυ', '', 'knee'], ['hit', 'genu', 'ge-e-nu', '']])
        # 頭の系統図は説明文から除く
        self.assertEqual(ety['text'], 'From Proto-Italic *genu, from Proto-Indo-European *ǵónu.')

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
        self.assertEqual(gloss('(女性形 (ἡ θεός) で) 女神。'), '女神')  # 入れ子の括弧の注記
        self.assertEqual(gloss('都市、特に、古代の都市国家。'), '都市,古代の都市国家')  # 「特に」は訳語でない

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
