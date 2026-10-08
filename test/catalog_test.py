#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import tempfile
import unittest

from dragoman.latin import catalog, macronizer


class CatalogTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        files = {'a.txt': 'puellā rosam dat.', 'b.txt': 'māgnus puellā.', 'c.txt': 'māgnus.',
                 'plain.txt': 'puella puella puella magnus.', 'd.txt': 'rēx.'}
        for name, text in files.items():
            with open(os.path.join(d, name), 'w') as fp:
                fp.write(text)
        data = {'texts': {
            'a.txt': {'macrons': 'full', 'hidden': 'mark', 'family': 'x'},
            'b.txt': {'macrons': 'full', 'hidden': 'mark', 'family': 'x'},
            'c.txt': {'macrons': 'full', 'hidden': 'mixed'},
            'd.txt': {'macrons': 'full', 'used_for_dictionary': True},
            # plain.txt は目録に無い (読む対象のみ)
        }}
        path = os.path.join(d, 'catalog.json')
        with open(path, 'w') as fp:
            json.dump(data, fp)
        self.cat = catalog.Catalog(path, d)
        self.d = d

    def tearDown(self):
        self.tmp.cleanup()

    def p(self, name):
        return os.path.join(self.d, name)

    def test_unlisted_text_is_not_knowledge(self):
        # マクロンの無いテキストを置いても知識に入らない
        self.assertNotIn(self.p('plain.txt'), self.cat.knowledge_files())
        frequency = macronizer.Frequency(self.cat.knowledge_files())
        self.assertEqual(frequency.count('puella'), 0)
        self.assertEqual(frequency.count('puellā'), 2)

    def test_hidden_mark_files(self):
        self.assertEqual(self.cat.hidden_mark_files(), [self.p('a.txt'), self.p('b.txt')])

    def test_evaluation_excludes_dictionary_texts(self):
        self.assertNotIn(self.p('d.txt'), self.cat.evaluation_files())
        self.assertIn(self.p('c.txt'), self.cat.evaluation_files())

    def test_family(self):
        self.assertEqual(self.cat.family_of(self.p('a.txt')), {self.p('a.txt'), self.p('b.txt')})
        self.assertEqual(self.cat.family_of(self.p('c.txt')), {self.p('c.txt')})
        self.assertEqual(self.cat.family_of(self.p('plain.txt')), {self.p('plain.txt')})

    def test_real_catalog(self):
        cat = catalog.default()
        ff = os.path.join(catalog.TEXTS_DIR, 'fabulae_faciles', 'hercules.txt')
        dg = os.path.join(catalog.TEXTS_DIR, 'dooge', 'hercules.txt')
        # D'Ooge のヘラクレスは Fabulae Faciles のヘラクレスと同じ系統
        self.assertEqual(cat.family_of(ff), {ff, dg})
        # 手作りの辞書を作るのに使ったテキストは既定の評価に使わない
        self.assertNotIn(os.path.join(catalog.TEXTS_DIR, '1.TESSEUS_ET_ARIADNE.txt'), cat.evaluation_files())
        # 目録の全テキストが実在する
        self.assertEqual(len(cat.existing()), len(cat.entries))


if __name__ == '__main__':
    unittest.main()
