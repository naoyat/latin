#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ノート (HTML) の清書: 行間逐語訳・弧の図のデータ・入れ子の図・訳
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.latin import latindic, analyzer  # noqa: E402
from dragoman.core import notebook  # noqa: E402


class NotebookTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        latindic.load()

    def note(self, text):
        nb = notebook.Notebook('test')
        for a in analyzer.analyze_text(text):
            nb.add(a)
        return nb

    def test_arcs(self):
        nb = self.note('Puella rosam pulchram in hortō videt.')
        arcs = {(a['from'], a['to'], a['label']) for a in nb.sentences[0]['arcs']}
        self.assertIn((5, 0, '主格'), arcs)     # videt → Puella
        self.assertIn((5, 1, '対格'), arcs)     # videt → rosam
        self.assertIn((1, 2, '修飾'), arcs)     # rosam → pulchram
        self.assertIn((5, 3, '前置詞'), arcs)   # videt → in
        self.assertIn((3, 4, '奪格'), arcs)     # in → hortō

    def test_relative_and_question(self):
        nb = self.note('Puella puerum videt quem magister laudat.')
        labels = {a['label'] for a in nb.sentences[0]['arcs']}
        self.assertIn('関係節', labels)
        nb = self.note('Magister rogāvit quis cantāret.')
        self.assertIn('間接疑問', {a['label'] for a in nb.sentences[0]['arcs']})

    def test_html(self):
        page = self.note('Puella rosam pulchram in hortō videt.').html()
        for part in ('行間逐語訳', '図A 弧', '図B 入れ子', '語の詳細', 'class="w c-Nom"', 'videō'):
            self.assertIn(part, page)

    def test_rtl_heading(self):
        self.assertIn('dir="rtl"', notebook.heading('בָּרָא (bārā)'))


if __name__ == '__main__':
    unittest.main()
