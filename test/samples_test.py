#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンプル (samples/samples.txt) を tools/samples.py で例外なく表示できるか
#
import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))

import samples
from latin import latindic, analyzer


class SamplesTestCase(unittest.TestCase):
    def setUp(self):
        latindic.load()
        self.saved = (latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER)
        latindic.LatinDic.use_wiktionary = False
        analyzer.USE_TAGGER = False

    def tearDown(self):
        latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER = self.saved

    def test_sections(self):
        sections = samples.read_sections(samples.DEFAULT_FILE)
        self.assertTrue(sections)
        for title, sentences in sections:
            self.assertTrue(title)
            self.assertTrue(sentences, title)

    def test_show_all_modes(self):
        sections = samples.read_sections(samples.DEFAULT_FILE)
        for mode in ('brief', 'tree', 'detail'):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                samples.show(sections, mode)
            self.assertIn('→', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
