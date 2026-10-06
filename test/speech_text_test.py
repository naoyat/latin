#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# テキストをそのまま読む方式 (say, espeak) に渡す形 (core.speech._plain_text)。音声は出さない
#
import unittest

from core import speech


class PlainTextTestCase(unittest.TestCase):
    def setUp(self):
        self.saved = (speech.language, speech.backend)

    def tearDown(self):
        speech.language, speech.backend = self.saved

    def plain(self, language, backend, text):
        speech.language, speech.backend = language, backend
        return speech._plain_text(text)

    def test_russian_stress_marks_are_removed(self):
        self.assertEqual(self.plain('ru', 'say', 'Кни́га'), 'Книга')

    def test_greek_is_monotonic_for_say(self):
        self.assertEqual(self.plain('grc', 'say', 'ἐν ἀρχῇ ἦν ὁ λόγος'), 'εν αρχή ήν ο λόγος')
        self.assertEqual(self.plain('grc', 'espeak', 'ἀρχῇ'), 'ἀρχῇ')  # espeak-ng の古典ギリシア語はそのまま

    def test_say_voices(self):
        self.assertEqual(speech.SAY_VOICES['ru'], 'Milena')
        self.assertEqual(speech.LANGUAGE_BACKENDS['ru'][0], 'say')


if __name__ == '__main__':
    unittest.main()
