#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 回帰テスト: テキストの解析結果を正解ファイル (golden) と比較する
#
#   python3 test/golden_test.py                     # 比較
#   UPDATE_GOLDEN=1 python3 test/golden_test.py     # 意図して出力を変えたときに更新
#
# - パブリックドメインのテキスト: 正解ファイルは test/golden/
# - リポジトリに入れないテキスト ($DRAGOMAN_DATA/private-texts/*.txt): 正解ファイルは private-texts/golden/
#   (フォルダが無ければスキップ)
#
# 日本語訳の動詞の活用は MeCab の辞書に依存する (golden は UniDic (unidic-lite) で生成)
# 解析結果がダウンロードしたデータや環境に左右されないよう、手作りの辞書だけで、タガーを使わずに解析する
# (LATIN_WIKTIONARY=0, LATIN_TAGGER=0)
#
import os
import re
import sys
import glob
import difflib
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_DIR = os.path.join(ROOT, 'test', 'golden')
sys.path.insert(0, ROOT)
from dragoman.latin.catalog import PRIVATE_TEXTS_DIR  # noqa: E402

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

PUBLIC_TEXTS = ['GLORIA.txt', 'RIMINI.txt', 'fabulae_faciles/perseus.txt']


def cases():
    """(テストの名前, テキスト, 正解ファイル) の列"""
    for name in PUBLIC_TEXTS:
        stem = os.path.splitext(name)[0].replace('/', '__')
        yield stem, os.path.join(ROOT, 'latin', 'texts', name), os.path.join(GOLDEN_DIR, stem + '.out')
    for path in sorted(glob.glob(os.path.join(PRIVATE_TEXTS_DIR, '*.txt'))):
        stem = os.path.splitext(os.path.basename(path))[0]
        yield 'private__' + stem, path, os.path.join(PRIVATE_TEXTS_DIR, 'golden', stem + '.out')


def analyse(text_file):
    result = subprocess.run([sys.executable, 'dragoman.py', '--lang=la', text_file],
                            cwd=ROOT, capture_output=True, text=True,
                            env=dict(os.environ, PYTHONHASHSEED='0', LATIN_WIKTIONARY='0', LATIN_TAGGER='0'))
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return ANSI_ESCAPE.sub('', result.stdout)


class GoldenTestCase(unittest.TestCase):
    maxDiff = None


def make_test(name, text_file, golden_file):
    def test(self):
        actual = analyse(text_file)
        if os.environ.get('UPDATE_GOLDEN') or not os.path.exists(golden_file):
            os.makedirs(os.path.dirname(golden_file), exist_ok=True)
            with open(golden_file, 'w') as fp:
                fp.write(actual)
            return
        with open(golden_file) as fp:
            expected = fp.read()
        if actual != expected:
            diff = ''.join(difflib.unified_diff(
                expected.splitlines(True), actual.splitlines(True),
                os.path.basename(golden_file), 'actual', n=2))
            self.fail('%s の解析結果が変わりました:\n%s' % (name, diff))
    return test


for _name, _text, _golden in cases():
    setattr(GoldenTestCase, 'test_' + re.sub(r'\W', '_', _name), make_test(_name, _text, _golden))


if __name__ == '__main__':
    unittest.main()
