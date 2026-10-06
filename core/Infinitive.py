#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 不定詞句: 不定詞を中心とする述語 (Predicate) と、それを支配する動詞の種類による訳し方
#
#   対格不定詞 (AcI。言う・思う・知る・見る・命じるなどの動詞の目的語。対格が不定詞の主語)
#     Mārcus dīcit puerōs in hortō lūdere.   マルクスが {少年が 庭で 遊ぶ}と 言う
#     Videō puellam cantāre.                  {少女が 歌う}のを 見る
#   補足の不定詞 (できる・望む・始めるなど。主語は主節と同じ)
#     Puer librum legere potest.              少年が {本を 読む}ことが できる
#
from .LatinObject import LatinObject

# 支配する動詞 (直説法現在1人称単数) → 種類
SAYING = {'dīcō', 'aiō', 'nūntiō', 'negō', 'respondeō', 'scrībō', 'putō', 'arbitror', 'exīstimō', 'existimō',
          'crēdō', 'cēnseō', 'iūdicō', 'jūdicō', 'sciō', 'nesciō', 'intellegō', 'cognōscō', 'spērō',
          'cōnfīdō', 'prōmittō', 'polliceor', 'nārrō', 'trādō', 'dēmōnstrō', 'ostendō', 'cōgitō', 'meminī',
          'ignōrō', 'simulō', 'fateor', 'cōnfiteor', 'gaudeō', 'doleō', 'mīror', 'queror', 'clāmō', 'iūrō',
          'jūrō', 'doceō', 'certiōrem faciō'}
PERCEPTION = {'videō', 'audiō', 'sentiō', 'animadvertō', 'cōnspiciō', 'aspiciō'}
COMMAND = {'iubeō', 'jubeō', 'sinō', 'patior', 'cōgō'}
COMPLEMENT = {'possum', 'volō', 'nōlō', 'mālō', 'cupiō', 'dēbeō', 'soleō', 'coepī', 'incipiō', 'audeō',
              'cōnor', 'cōnstituō', 'statuō', 'dēsinō', 'studeō', 'properō', 'parō', 'timeō', 'discō',
              'vetō', 'dubitō', 'optō', 'neglegō', 'recūsō', 'mātūrō', 'contendō', 'pergō'}

PARTICLES = {'saying': 'と', 'perception': 'のを', 'command': 'ように', 'complement': 'ことを'}


def governor_kind(pres1sg):
    """不定詞を支配する動詞の種類: saying / perception / command / complement / None (分からない)"""
    for kind, verbs in (('saying', SAYING), ('perception', PERCEPTION), ('command', COMMAND),
                        ('complement', COMPLEMENT)):
        if pres1sg in verbs:
            return kind
    return None


def takes_accusative_subject(kind):
    return kind in ('saying', 'perception', 'command')


class InfinitiveClause(LatinObject):
    def __init__(self, predicate, governor, kind):
        self.predicate = predicate      # 不定詞を中心とする述語 (Predicate。主語は 'Nom' の枠)
        self.verb = predicate.verb      # 不定詞 (Word)
        self.governor = governor        # 支配する動詞 (Predicate)
        self.kind = kind                # governor_kind の種類 (None なら complement と同じに訳す)
        self.surface = predicate.surface
        self.surface_len = len(self.surface)
        self.case_slot = predicate.case_slot  # 評価用

    def particle(self):
        if self.kind == 'complement' and self.governor is not None and \
                self.governor.first_item.attrib('pres1sg') == 'possum':
            return 'ことが'  # 〜することができる
        if self.kind is None and self.governor is not None and self.governor.is_sum:
            return 'ことは'  # {怠惰な人生を 送る}ことは 恥ずべきである
        return PARTICLES.get(self.kind, 'ことを')

    def translate(self):
        inner, _ = self.predicate.translate()
        return ('{' + inner.replace(' / ', ' ') + '}' + self.particle(), False)
