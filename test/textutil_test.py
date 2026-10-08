#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from dragoman.latin.textutil import word_stream_from_text, sentence_stream


def sentences(text):
    return list(sentence_stream(word_stream_from_text(text)))


class TextutilTestCase(unittest.TestCase):
    def test_punctuation(self):
        self.assertEqual(sentences('Rōma est. Valē, amīce!'),
                         [['Rōma', 'est', '.'], ['Valē', ',', 'amīce', '!']])

    def test_parentheses(self):
        self.assertEqual(sentences('Rēx (quī erat) vēnit.'),
                         [['Rēx', '(', 'quī', 'erat', ')', 'vēnit', '.']])
        self.assertEqual(sentences('nāvigābant (vehēbantur).'),
                         [['nāvigābant', '(', 'vehēbantur', ')', '.']])

    def test_symbol_only_token(self):
        # 記号だけの語で落ちない
        self.assertEqual(sentences('// MDLV : x'), [['//', 'MDLV', ':'], ['x']])


if __name__ == '__main__':
    unittest.main()
