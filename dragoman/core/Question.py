#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 間接疑問: 疑問詞で始まり、動詞が接続法の節を、問う・知る・教える・言うなどの動詞の目的語として持つ
#
#   Quid fierī vellet docuit.         {何が なる ことを 望んでいた}かを 教えた
#   Rogāvit cūr puer flēret.          {なぜ 少年が 泣いていた}かを 尋ねた
#
# 解析では、述語ごとの節にいったん分けたあとで、隣の節の動詞がこの種類なら、その節の格の枠 ('Q') に入れる
# (不定詞句 InfinitiveClause と同じく入れ子にする)
#
from .LatinObject import LatinObject

# 間接疑問を目的語に取る動詞 (直説法現在1人称単数)
QUESTION_VERBS = {'rogō', 'interrogō', 'quaerō', 'requīrō', 'exquīrō', 'scīscitor', 'percontor', 'cōnsulō',
                  'sciō', 'nesciō', 'ignōrō', 'cognōscō', 'intellegō', 'sentiō', 'videō', 'audiō', 'animadvertō',
                  'doceō', 'ēdoceō', 'dīcō', 'nārrō', 'nūntiō', 'ostendō', 'dēmōnstrō', 'mōnstrō', 'expōnō',
                  'explicō', 'referō', 'prōnūntiō', 'indicō', 'aperiō', 'mīror', 'dubitō', 'cōgitō', 'meminī',
                  'recordor', 'considerō', 'cōnsīderō', 'dēlīberō', 'exspectō', 'experior', 'temptō', 'probō',
                  'cūrō', 'videor'}
# 疑問の副詞・形容詞 (疑問代名詞 quis / quid は辞書の desc で見分ける)
INTERROGATIVES = {'cūr', 'quārē', 'quōmodo', 'quemadmodum', 'unde', 'quō', 'quā', 'quotiēns', 'quandō',
                  'utrum', 'num', 'nōnne', 'quantus', 'quālis', 'quot', 'uter', 'ubi', 'quam'}


def is_interrogative(word):
    """疑問代名詞 (quis, quid …) か、疑問の副詞 (cūr, quōmodo …) の語"""
    items = getattr(word, 'items', None) or []
    if any(item.pos == 'pronoun' and item.attrib('desc') == '疑問代名詞' for item in items):
        return True
    return getattr(word, 'surface', '').lower() in INTERROGATIVES and bool(items)


class QuestionClause(LatinObject):
    def __init__(self, predicate, governor, word):
        self.predicate = predicate      # 間接疑問の節の述語 (接続法の動詞の Predicate)
        self.governor = governor        # 支配する動詞 (Predicate)
        self.word = word                # 疑問詞 (Word)
        self.surface = predicate.surface
        self.surface_len = len(self.surface)
        self.case_slot = predicate.case_slot

    def translate(self):
        inner, _ = self.predicate.translate()
        return ('{' + inner.replace(' / ', ' ') + '}かを', False)
