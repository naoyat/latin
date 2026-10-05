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
from . import latindic


class AblativeAbsolute(LatinObject):
    def __init__(self, subject, participle, complements=()):
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

    @property
    def participle_item(self):
        return next((item for item in self.verb.items if item.pos == 'participle'), self.verb.items[0])

    def _verb_gloss(self):
        """分詞のもとの動詞の訳語 (日本語なら活用させるため)。(訳語, 言語)"""
        pres1sg = self.participle_item.attrib('pres1sg')
        if pres1sg:
            for item in latindic.lookup(pres1sg) or []:
                if item.get('pos') == 'verb' and item.get('ja'):
                    return item['ja'].split(',')[0], item.get('gloss_lang', 'ja')
        item = self.participle_item
        return item.ja.split(',')[0], item.attrib('gloss_lang', 'ja')

    def kind(self):
        tense = self.participle_item.attrib('tense')
        if tense == 'present':
            return 'present'
        if tense == 'future':
            return 'future'
        pres1sg = self.participle_item.attrib('pres1sg') or ''
        return 'active' if pres1sg.endswith('r') else 'passive'  # 形式受動態動詞 (loquor) の完了分詞は能動

    def translate(self):
        from .japanese import JaVerb
        subject = self.subject.translate()[0]
        complements = [c.translate()[0] for c in self.complements]
        gloss, lang = self._verb_gloss()
        kind = self.kind()
        if lang == 'ja':
            try:
                verb = JaVerb(gloss).clause_form(kind)
            except Exception:
                verb = gloss + '[分詞]'
        else:
            labels = {'present': '現在分詞', 'passive': '完了分詞・受動', 'active': '完了分詞', 'future': '未来分詞'}
            verb = '%s[%s]' % (gloss, labels[kind])
        return ('{' + subject + 'が' + ''.join(' ' + c for c in complements) + ' ' + verb + '}', False)
