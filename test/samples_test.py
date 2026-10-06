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

    def test_other_languages(self):
        from greek import dictionary as greek_dictionary
        langs = [('grc', greek_dictionary.available())]
        try:
            from sanskrit import dictionary as sanskrit_dictionary, morphology
            langs.append(('sa', sanskrit_dictionary.available() and morphology.available()))
        except ImportError:
            pass
        try:
            from russian import dictionary as russian_dictionary, morphology as russian_morphology
            langs.append(('ru', russian_dictionary.available() and russian_morphology.available()))
        except ImportError:
            pass
        from hebrew import dictionary as hebrew_dictionary
        langs.append(('he', hebrew_dictionary.available()))
        for lang, available in langs:
            sections = samples.read_sections(samples.LANG_FILES[lang])
            self.assertTrue(all(title and sentences for title, sentences in sections), lang)
            if available:
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    samples.show(sections, 'tree', lang=lang)
                self.assertIn('→', buf.getvalue())

    def test_show_all_modes(self):
        sections = samples.read_sections(samples.DEFAULT_FILE)
        for mode in ('brief', 'tree', 'detail'):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                samples.show(sections, mode)
            self.assertIn('→', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
