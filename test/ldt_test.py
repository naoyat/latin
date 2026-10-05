#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# LDT 形式の品詞タグ・Morpheus 由来の辞書・RFTagger のテスト
#
import os
import sys
import unittest

from latin import ldt, morpheus, rftagger

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from build_morpheus_dic import to_macrons


class LdtTestCase(unittest.TestCase):
    def test_parse_noun(self):
        self.assertEqual(ldt.parse('n-s---fb-'),
                         {'pos': 'noun', 'number': 'sg', 'gender': 'f', 'case': 'Abl'})

    def test_parse_verb(self):
        self.assertEqual(ldt.parse('v3sria---'),
                         {'pos': 'verb', 'person': 3, 'number': 'sg', 'tense': 'perfect',
                          'mood': 'indicative', 'voice': 'active'})

    def test_parse_participle_and_dotted_tag(self):
        self.assertEqual(ldt.parse('v.-.s.r.p.p.-.m.n.-')['pos'], 'participle')

    def test_to_item(self):
        item = ldt.to_item('n-s---fb-', 'puella', 'puellā')
        self.assertEqual(item['_'], [('Abl', 'sg', 'f')])
        self.assertEqual(item['base'], 'puella')

    def test_item_matches(self):
        noun = {'pos': 'noun', '_': [('Nom', 'sg', 'f'), ('Abl', 'sg', 'f')]}
        self.assertTrue(ldt.item_matches(noun, ldt.parse('n-s---fb-')))
        self.assertFalse(ldt.item_matches(noun, ldt.parse('n-p---fa-')))
        self.assertTrue(ldt.item_matches(noun, ldt.parse('n-s---mb-')))  # 性は見ない
        self.assertTrue(ldt.item_matches({'pos': 'conj'}, ldt.parse('d--------')))  # 副詞と接続詞は区別しない
        verb = {'pos': 'verb', 'tense': 'perfect', 'mood': 'indicative', 'person': 3, 'number': 'sg'}
        self.assertTrue(ldt.item_matches(verb, ldt.parse('v3sria---')))
        self.assertFalse(ldt.item_matches(verb, ldt.parse('v3spia---')))


class MorpheusTestCase(unittest.TestCase):
    def test_to_macrons(self):
        self.assertEqual(to_macrons('pu^ella_'), 'puellā')
        self.assertEqual(to_macrons('La_o^me^do_n'), 'Lāomedōn')
        self.assertEqual(to_macrons('a+e_r'), 'aēr')

    def test_key(self):
        self.assertEqual(morpheus.key('Juvenī'), 'iuueni')

    @unittest.skipUnless(morpheus.available(), 'Morpheus 辞書 (tools/build_morpheus_dic.py) が無い')
    def test_lookup(self):
        forms = morpheus.lookup_flat('modo')
        self.assertIn('modo', forms)   # 副詞
        self.assertIn('modō', forms)   # 名詞の奪格・与格
        self.assertIn('Peliās', morpheus.lookup_flat('Pelias'))


@unittest.skipUnless(rftagger.available(), 'RFTagger またはモデルが無い')
class RFTaggerTestCase(unittest.TestCase):
    def test_tag(self):
        tags, = rftagger.tag_sentences([['Puella', 'in', 'silvā', 'ambulat', '.']])
        self.assertEqual(len(tags), 5)
        self.assertEqual(ldt.parse(tags[2]).get('case'), 'Abl')  # マクロン付きでも外して渡す
        self.assertEqual(ldt.parse(tags[3]).get('pos'), 'verb')

    def test_enclitic(self):
        tags, = rftagger.tag_sentences([['Arma', 'virumque', 'canō', '.']])
        self.assertEqual(len(tags), 4)
        self.assertEqual(ldt.parse(tags[1]).get('case'), 'Acc')


if __name__ == '__main__':
    unittest.main()
