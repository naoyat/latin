#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語: 表記の正規化 (greek.orthography)、Wiktionary の項目の変換 (greek.wiktionary_import)、
# 辞書引き (greek.dictionary。辞書が無ければ飛ばす)
#
import unittest

from greek import orthography, dictionary
from greek.wiktionary_import import convert_entry


def form(text, *tags):
    return {'form': text, 'tags': list(tags)}


# 項目の例 (この試験のために作った最小のもの。形は kaikki.org の抽出データに合わせる)
HIPPOS = {
    'word': 'ἵππος', 'lang_code': 'grc', 'pos': 'noun',
    'head_templates': [{'name': 'grc-noun', 'args': {'1': 'ἵππου', '2': 'm', '3': 'second'}}],
    'senses': [{'glosses': ['horse']}],
    'forms': [form('ῐ̔́ππος', 'canonical'), form('Attic declension-2', 'table-tags'),
              form('ὁ', 'nominative', 'singular'),  # 変化表の冠詞の欄 (名詞の形ではない)
              form('ῐ̔́ππος', 'nominative', 'singular'), form('ῐ̔́ππον', 'accusative', 'singular'),
              form('ῐ̔́ππω', 'dual', 'nominative')],
}
LUO = {
    'word': 'λύω', 'lang_code': 'grc', 'pos': 'verb',
    'senses': [{'glosses': ['to loose']}],
    'forms': [form('λῡ̆́ω', 'canonical'), form('present', 'table-tags'),
              form('λῡ́ει', 'active', 'indicative', 'singular', 'third-person'),
              form('imperfect', 'table-tags'),
              form('ἔλῡε', 'active', 'indicative', 'singular', 'third-person'),
              form('Epic aorist', 'table-tags'),
              form('λῦσε', 'active', 'indicative', 'singular', 'third-person'),
              form('λῡόμενος', 'masculine', 'middle', 'participle', 'passive')],
}
EN = {
    'word': 'ἐν', 'lang_code': 'grc', 'pos': 'prep',
    'head_templates': [{'name': 'grc-preposition', 'args': {'1': 'dat'}}],
    'senses': [{'glosses': ['(with dative) in, on'], 'tags': ['with-dative']}],
}


class OrthographyTestCase(unittest.TestCase):
    def test_key(self):
        self.assertEqual(orthography.key('τὸν'), 'τόν')            # 重アクセント → 鋭アクセント
        self.assertEqual(orthography.key('ῐ̔́ππος'), 'ἵππος')        # 長短の印を除く
        self.assertEqual(orthography.key('ἄνθρωπός'), 'ἄνθρωπος')  # 前接語で付いた2つ目のアクセント
        self.assertEqual(orthography.key("δ'"), 'δ’')

    def test_flat(self):
        self.assertEqual(orthography.flat('Ἀθῆναι'), 'αθηναι')
        self.assertEqual(orthography.flat('λόγος'), 'λογοσ')


class ImportTestCase(unittest.TestCase):
    def test_noun(self):
        (info, forms), = convert_entry(HIPPOS)
        table = dict(forms)
        self.assertEqual(info['base'], 'ἵππος')
        self.assertEqual(table['ἵππον']['_'], [('Acc', 'sg', 'm')])  # 性は見出しのテンプレートから
        self.assertEqual(table['ἵππω']['_'], [('Nom', 'du', 'm')])   # 双数
        self.assertNotIn('ὁ', table)

    def test_verb_tenses(self):
        (info, forms), = convert_entry(LUO)
        by_surface = {surface: f for surface, f in forms}
        self.assertEqual(info['pres1sg'], 'λύω')
        self.assertEqual(by_surface['λύει']['tense'], 'present')
        self.assertEqual(by_surface['ἔλυε']['tense'], 'imperfect')  # 'perfect' と取り違えない
        self.assertEqual((by_surface['λῦσε']['tense'], by_surface['λῦσε']['dialect']), ('aorist', 'Epic'))
        self.assertEqual(by_surface['λυόμενος']['voice'], 'middle-passive')

    def test_preposition(self):
        (info, _), = convert_entry(EN)
        self.assertEqual((info['pos'], info['dominates']), ('preposition', 'Dat'))


@unittest.skipUnless(dictionary.available(), 'ギリシア語の辞書 (tools/build_greek_dic.py) が無い')
class DictionaryTestCase(unittest.TestCase):
    def test_lookup(self):
        poses = {i['pos'] for i in dictionary.lookup('τὸν')}
        self.assertIn('article', poses)
        verb, = [i for i in dictionary.lookup('ἦν') if i.get('pres1sg') == 'εἰμί']
        self.assertEqual((verb['tense'], verb['person'], verb['number']), ('imperfect', 3, 'sg'))

    def test_lookup_without_accents(self):
        self.assertTrue(any(i.get('base') == 'λόγος' for i in dictionary.lookup('λογος')))


if __name__ == '__main__':
    unittest.main()
