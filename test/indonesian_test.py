#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語・マレー語: 接辞の解析 (meN- の鼻音の交替、di-、ke-…-an、接語、重複) と文の訳。辞書が無ければ飛ばす
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.indonesian import dictionary, morphology  # noqa: E402

HAVE_DATA = dictionary.available()


class DerivationTestCase(unittest.TestCase):
    def roots(self, word):
        return [(root, kind) for root, _, kind in morphology.derivations(word)]

    def test_men_nasal_alternation(self):
        self.assertIn(('tulis', 'active'), self.roots('menulis'))      # men + t → n
        self.assertIn(('pakai', 'active'), self.roots('memakai'))      # mem + p → m
        self.assertIn(('sapu', 'active'), self.roots('menyapu'))       # meny + s → ny
        self.assertIn(('kirim', 'active'), self.roots('mengirim'))     # meng + k → ng
        self.assertIn(('baca', 'active'), self.roots('membaca'))       # mem + b
        self.assertIn(('lihat', 'active'), self.roots('melihat'))      # me + l
        self.assertIn(('cat', 'active'), self.roots('mengecat'))       # menge + 1音節

    def test_other_affixes(self):
        self.assertIn(('tulis', 'passive'), self.roots('ditulis'))
        self.assertIn(('bersih', 'noun_ke_an'), self.roots('kebersihan'))
        self.assertIn(('rencana', 'ber'), self.roots('berencana'))     # ber + r (r が1つ落ちる)
        self.assertIn(('tahan', 'active'), self.roots('mempertahankan'))


@unittest.skipUnless(HAVE_DATA, 'no Indonesian dictionary (tools/build_indonesian_dic.py)')
class IndonesianTestCase(unittest.TestCase):
    def words(self, text):
        from dragoman.indonesian import analyzer
        return analyzer.lookup_all(analyzer.tokens(text))

    def test_morphology(self):
        items, clitic = morphology.analyze('bukunya')
        self.assertEqual((items[0]['pos'], clitic), ('noun', 'nya'))
        items, _ = morphology.analyze('ditulis')
        self.assertEqual((items[0]['pos'], items[0]['voice']), ('verb', 'passive'))
        items, _ = morphology.analyze('anak-anak')
        self.assertEqual(items[0]['_'][0][1], 'pl')                    # 重複は複数

    def test_roles(self):
        words = self.words('Anak itu membaca buku di sekolah .')
        cases = {w.surface: w.items[0]._[0][0] for w in words if w.items and w.items[0]._}
        self.assertEqual(cases['Anak'], 'Nom')
        self.assertEqual(cases['buku'], 'Acc')
        self.assertEqual(cases['sekolah'], 'Gen')                      # 前置詞句

    def test_copula_and_relative(self):
        words = self.words('Rumah itu besar .')
        self.assertIn('(adalah)', [w.surface for w in words])          # 見えない繋辞を補う
        words = self.words('Orang yang membaca buku itu adalah guru saya .')
        self.assertEqual(words[0].items[0].ja, '本を読む人')            # yang の関係節
        words = self.words('Buku yang ditulis oleh guru itu bagus .')
        self.assertEqual(words[0].items[0].ja, '先生によって書かれる本')

    def test_aspect_modal_and_possessor(self):
        words = self.words('Saya sudah makan nasi .')
        verb = next(w for w in words if w.items and w.items[0].pos == 'verb')
        self.assertEqual(verb.items[0].attrib('tense'), 'perfect')     # sudah → 過去
        words = self.words('Saya ingin belajar bahasa Jepang .')
        verb = next(w for w in words if w.items and w.items[0].pos == 'verb')
        self.assertEqual(verb.items[0].ja, '勉強したい')
        self.assertIn('日本語', [w.items[0].ja for w in words if w.items])  # bahasa + 国名
        words = self.words('Ibu memberikan uang kepada anaknya .')
        self.assertIn('彼の子供', [w.items[0].ja for w in words if w.items])  # 接語 -nya


if __name__ == '__main__':
    unittest.main()
