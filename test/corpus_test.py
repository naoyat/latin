#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# latin/texts/ 以下の全テキストを、解析から表示まで例外なく通せることを確かめる
# (手作りの辞書だけの場合と、Wiktionary の補助辞書を使う場合)
#
import io
import os
import glob
import contextlib
import unittest

from dragoman.core import render
from dragoman.latin import latindic, analyzer, wiktionary, rftagger
from dragoman.latin.catalog import PRIVATE_TEXTS_DIR

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# リポジトリのテキストと、リポジトリに入れないテキスト (あれば)
TEXTS = (sorted(glob.glob(os.path.join(ROOT, 'latin', 'texts', '**', '*.txt'), recursive=True)) +
         sorted(glob.glob(os.path.join(PRIVATE_TEXTS_DIR, '*.txt'))))


def setUpModule():
    latindic.load()


class CorpusTestCase(unittest.TestCase):
    def analyse_all(self):
        for path in TEXTS:
            with open(path) as fp:
                text = fp.read()
            all_surfaces = list(analyzer.sentences(text))
            all_tags = (rftagger.tag_sentences(all_surfaces) if analyzer.tagger_enabled()
                        else [None] * len(all_surfaces))
            for surfaces, tags in zip(all_surfaces, all_tags):
                with self.subTest(text=os.path.relpath(path, ROOT), sentence=' '.join(surfaces)[:60]):
                    analysis = analyzer.analyze_sentence(surfaces, tags)
                    with contextlib.redirect_stdout(io.StringIO()):
                        render.render_analysis(analysis)

    def test_hand_dictionary_only(self):
        saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = False
        try:
            self.analyse_all()
        finally:
            latindic.LatinDic.use_wiktionary = saved

    @unittest.skipUnless(wiktionary.available(), 'Wiktionary 辞書 (tools/build_wiktionary_dic.py) が無い')
    def test_with_wiktionary(self):
        saved = latindic.LatinDic.use_wiktionary
        latindic.LatinDic.use_wiktionary = True
        try:
            self.analyse_all()
        finally:
            latindic.LatinDic.use_wiktionary = saved


if __name__ == '__main__':
    unittest.main()
