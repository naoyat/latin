#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 独立奪格 (ablative absolute): 奪格の名詞 + 奪格の分詞 で「〜が〜していると / 〜が〜されて」
# (理由・時・付帯状況などを表すので、完了分詞は「〜されて」と幅を持たせて訳す)
#
#   Caesare veniente        カエサルが来ていると
#   hīs rēbus cognitīs      これらの事が知られて
#   obsidibus datīs         人質が与えられて
#
# サンスクリットの処格独立 (locative absolute)、ギリシア語の属格独立と同じ種類の構文
#
from .LatinObject import LatinObject
from .Word import Word
from .Participle import participle_kind, participle_translation
from . import language


class AblativeAbsolute(LatinObject):
    def __init__(self, subject, participle, complements=()):
        self.language = language.current()  # 訳すときにもこの言語の設定 (辞書の引き先) を使う
        self.subject = subject              # 意味上の主語 (奪格の名詞・代名詞。修飾語付き)
        self.verb = participle              # 分詞 (Word)
        self.complements = list(complements)  # 間に挟まった語 (分詞の補語: 前置詞句・対格など)
        self.surface = ' '.join(n.surface for n in [subject] + self.complements + [participle])
        self.surface_len = len(self.surface)
        # 評価 (tools/ud_eval.py) で述語と同じように扱えるよう、主語と目的語の枠を持たせる
        self.case_slot = {'Nom': [subject]}
        objects = [c for c in self.complements if isinstance(c, Word) and c.items and c.items[0]._ and
                   any(case == 'Acc' for case, _, _ in c.items[0]._)]
        if objects:
            self.case_slot['Acc'] = objects

    def kind(self):
        return participle_kind(self.verb)

    def translate(self):
        subject = self.subject.translate()[0]
        complements = [c.translate()[0] for c in self.complements]
        verb = participle_translation(self.verb, 'absolute', self.language)
        return ('{' + subject + 'が' + ''.join(' ' + c for c in complements) + ' ' + verb + '}', False)
