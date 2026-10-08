#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# REPL のコマンド (.conjug / .decl) と、入口 (dragoman.py) のテスト
#
import os
import re
import sys
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def repl(*lines):
    result = subprocess.run([sys.executable, 'dragoman.py', '--lang=la'], cwd=ROOT,
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



class DragomanCommandTestCase(unittest.TestCase):
    def test_lang_option(self):
        for command in (['dragoman.py'], ['-m', 'dragoman']):
            result = subprocess.run([sys.executable] + command + ['--lang=la', '-w'], cwd=ROOT,
                                    input='Rōma magna est.\n', capture_output=True, text=True)
            self.assertIn('→', ANSI_ESCAPE.sub('', result.stdout))

    def test_detected_language(self):
        # --lang が無ければ文字から推定する (ラテン文字はラテン語)
        result = subprocess.run([sys.executable, 'dragoman.py', '-w'], cwd=ROOT,
                                input='Rōma magna est.\n', capture_output=True, text=True)
        self.assertIn('→', ANSI_ESCAPE.sub('', result.stdout))

    def test_unknown_lang(self):
        for args in (['--lang=xx'], ['xx']):
            result = subprocess.run([sys.executable, 'dragoman.py'] + args, cwd=ROOT, input='',
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('grc', result.stderr)  # 対応している言語の一覧を出す

    def test_positional_lang_and_text_option(self):
        # ./dragoman.py LANG -e TEXT (言語を最初の引数で、文を -e で)
        result = subprocess.run([sys.executable, 'dragoman.py', 'la', '-w', '-e', 'Rōma magna est.'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertIn('→', ANSI_ESCAPE.sub('', result.stdout))
        result = subprocess.run([sys.executable, 'dragoman.py', '-w', '-e', 'Rōma magna est.', '-e', 'Mārcus currit.'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(ANSI_ESCAPE.sub('', result.stdout).count('→'), 2)
        # auto は文字から推定する (ロシア語)
        result = subprocess.run([sys.executable, 'dragoman.py', 'auto', '-w', '-e', 'Мальчик читает книгу.'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertIn('本', ANSI_ESCAPE.sub('', result.stdout))

    def test_language_list(self):
        result = subprocess.run([sys.executable, 'dragoman.py', '--languages'], cwd=ROOT, capture_output=True,
                                text=True)
        for code in ('la', 'grc', 'sa', 'ru', 'he', 'ar', 'fa', 'hi', 'ur'):
            self.assertIn('  %s ' % code, result.stdout)

    def test_detect(self):
        sys.path.insert(0, ROOT)
        from dragoman.main import detect
        cases = {'Gallia est omnis dīvīsa.': 'la', 'ἐν ἀρχῇ ἦν ὁ λόγος.': 'grc', 'Мальчик читает книгу.': 'ru',
                 'בְּרֵאשִׁית בָּרָא אֱלֹהִים': 'he', 'ذهب الولد إلى المدرسة.': 'ar', 'من به مدرسه می‌روم.': 'fa',
                 'लड़के ने किताब पढ़ी।': 'hi', 'रामो वनं गच्छति ।': 'sa', 'لڑکے نے کتاب پڑھی۔': 'ur'}
        for text, lang in cases.items():
            self.assertEqual(detect(text), lang, text)

    def test_language_help(self):
        result = subprocess.run([sys.executable, 'dragoman.py', '--lang=he', '--help'], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertIn('--divine-name', result.stdout)
        self.assertIn('--no-word-detail', result.stdout)


if __name__ == '__main__':
    unittest.main()
