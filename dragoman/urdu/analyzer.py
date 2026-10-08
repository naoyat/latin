#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語の文の解析: ヒンディー語の解析器 (hindi/analyzer.py) の入口
#
# ウルドゥー文字の語を、ヒンディー語の語形の候補 (urdu/dictionary.py: Wiktionary の対応と綴りの骨組み) に引き当て、
# ヒンディー語の解析器が文脈で候補を選ぶ (میں: में「〜で」か मैं「私」か)。解析の後で、語の表示をウルドゥー文字に戻す。
# 転写は選んだヒンディー語の語形から (短母音を書かないウルドゥー文字からは作れない)
#
import dataclasses
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.hindi import analyzer as hindi_analyzer
from . import dictionary, script

PUNCTUATION = {'۔': 'period', '.': 'period', '!': 'period', '?': 'question', '؟': 'question', '،': 'comma',
               ',': 'comma', '؛': 'comma', ';': 'comma', ':': 'comma', '"': None, '«': None, '»': None,
               '(': 'comma', ')': 'comma', '-': 'comma', '–': 'comma', '—': 'comma'}
# 語の字 (句読点の ، ؛ ؟ ۔ は除く)
TOKEN = re.compile('[\u0610-\u061a\u0620-\u065f\u0670-\u06d3\u06d5-\u06ff\u0750-\u077f\u200c\u200d]+'
                   '|[0-9\u06f0-\u06f9]+|[۔.!?؟،,؛;:"«»()\\-–—]')
# 解析の後で語の表示をウルドゥー文字に戻すので、並列の接続詞・否定はウルドゥー文字で
URDU = dataclasses.replace(hindi_analyzer.HINDI, name='ur', and_words=('اور',), or_words=('یا',),
                           negations=hindi_analyzer.KeySet({'نہیں', 'نہ', 'مت'}))


def tokens(text):
    return TOKEN.findall(text)


def sentences(text):
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


def alternatives(surfaces):
    """語ごとのヒンディー語の語形の候補の組 (句読点はヒンディー語の句読点に)"""
    out = []
    for s in surfaces:
        if s in PUNCTUATION:
            out.append({'۔': '।', '؟': '?', '،': ',', '؛': ';'}.get(s, s))
        else:
            out.append(tuple(dictionary.candidates(s)) or s)
    return out


def analyze_sentence(surfaces):
    words = hindi_analyzer.lookup_all(alternatives(surfaces))
    romans = hindi_analyzer._romans(words)
    # 語の表示をウルドゥー文字に戻す (まとめた語は元の語を並べる)
    for word in words:
        ixs = getattr(word, 'token_ixs', None) or (getattr(word, 'token_ix', None),)
        if ixs[0] is None or ixs[0] >= len(surfaces):
            continue
        word.deva = word.surface
        word.surface = ' '.join(surfaces[i] for i in ixs)
        for item in word.items or []:
            item.item['deva'] = item.surface
            item.item['surface'] = item.surface = word.surface
    word_details = [word.detail() for word in words]
    with language.using(URDU):
        analysis = common.analyze_words([w.surface for w in words], words, word_details, [])
    text = ' '.join(s for s in surfaces if s not in PUNCTUATION)
    latin = ' '.join(romans.get(i) or s for i, s in enumerate(surfaces) if s not in PUNCTUATION)
    end = next((s for s in reversed(surfaces) if s in PUNCTUATION), '')
    analysis.forms_text = (text + end, latin + {'۔': '.', '؟': '?'}.get(end, end))
    return analysis


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
