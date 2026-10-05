#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# REPL のコマンド (.conjug / .decl) のテスト
#
import os
import re
import sys
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def repl(*lines):
    result = subprocess.run([sys.executable, 'latin.py'], cwd=ROOT,
                            input='\n'.join(lines) + '\n',
                            capture_output=True, text=True)
    return ANSI_ESCAPE.sub('', result.stdout)


class DeclTestCase(unittest.TestCase):
    def test_noun(self):
        out = repl('.decl rēx')
        self.assertIn('rēx (noun, m), 王,指導者', out)
        self.assertIn('    Acc: rēgem', out)
        self.assertIn('    Dat: rēgibus', out)

    def test_multiple_forms(self):
        # 同じ欄に入る複数の形がすべて表示される
        out = repl('.decl fīlius')
        self.assertIn('    Gen: fīlī, fīliī', out)


class ConjugTestCase(unittest.TestCase):
    def test_sum(self):
        out = repl('.conjug sum')
        self.assertIn('          3: est', out)
        self.assertIn('    present: esse', out)


if __name__ == '__main__':
    unittest.main()
