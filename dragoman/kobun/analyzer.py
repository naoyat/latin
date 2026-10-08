#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文 (平安の和文) の解析: 品詞分解 (MeCab + 中古和文UniDic) と現代語への組み立て直し (modernize.py)
#
import re
from dataclasses import dataclass, field

from . import mecab, modernize

SENTENCE_END = re.compile('(?<=[。！？])')


@dataclass
class KobunAnalysis:
    text: str
    tokens: list = field(default_factory=list)
    bunsetsu: list = field(default_factory=list)
    modern: str = ''
    notes: list = field(default_factory=list)

    @property
    def reading(self):
        """現代仮名遣いの読み (音読に使う)"""
        return ''.join(t.kana if t.pos != '補助記号' else t.surface for t in self.tokens)


def sentences(text):
    for line in text.splitlines():
        for s in SENTENCE_END.split(line.strip()):
            if s.strip():
                yield s.strip()


def analyze_sentence(text):
    tokens = mecab.parse(text)
    bunsetsu, modern, notes = modernize.modernize(tokens)
    return KobunAnalysis(text, tokens, bunsetsu, modern, notes)


def analyze_text(text):
    for s in sentences(text):
        yield analyze_sentence(s)
