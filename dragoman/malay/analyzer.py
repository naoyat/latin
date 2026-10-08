#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# マレー語の文の解析: インドネシア語の解析器 (indonesian/analyzer.py) を、マレー語の辞書の項目を先に引く設定で使う
# (綴りの違い: kerana / karena、wang / uang、Inggeris / Inggris、bahawa / bahwa など)
#
from dragoman.indonesian import analyzer as indonesian

sentences = indonesian.sentences


def analyze_sentence(surfaces):
    indonesian.set_lang('ms')
    return indonesian.analyze_sentence(surfaces)


def analyze_text(text):
    return indonesian.analyze_text(text, lang='ms')
