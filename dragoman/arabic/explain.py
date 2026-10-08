#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 初学者向けの解説: 動詞の語根・型 (I〜X)・時制、名詞の語根・連語形 (iḍāfa)
#
#   كَتَبَ → 語根 ك-ت-ب (k-t-b)
#            型 I (faʿala): 基本の型
#            完了形 (al-māḍī): 完結した行為「〜した」
#
from . import script

# 動詞の型 → (型の形, 解説)
FORMS = {
    'I': ('faʿala', '基本の型'),
    'II': ('faʿʿala', '強意・使役「〜させる」(第2語根字を重ねる)'),
    'III': ('fāʿala', '相手に向けた働きかけ「〜と / 〜に対して〜する」'),
    'IV': ('ʾafʿala', '使役「〜させる」'),
    'V': ('tafaʿʿala', 'II の再帰・受け身「自ら〜する / 〜になる」'),
    'VI': ('tafāʿala', 'III の相互「互いに〜する」'),
    'VII': ('infaʿala', 'I の受け身・自動詞「〜される / 〜になる」'),
    'VIII': ('iftaʿala', 'I の再帰・自分のための動作'),
    'IX': ('ifʿalla', '色・身体の特徴「〜色になる」'),
    'X': ('istafʿala', '求める・みなす「〜を求める / 〜とみなす」'),
}
ASPECTS = {
    'p': '完了形 (al-māḍī): 完結した行為「〜した」',
    'i': '未完了形 (al-muḍāriʿ): 現在・習慣・未来「〜する」',
    'c': '命令形 (al-amr)「〜せよ」',
}
MOODS = {
    'jussive': '要求法 (majzūm): lam と組んで過去の否定、lā と組んで禁止',
    'subjunctive': '接続法 (manṣūb): lan「〜しないだろう」、an「〜すること」の後ろ',
}
CASES = {'Nom': '主格 (marfūʿ, -u)', 'Acc': '対格 (manṣūb, -a)', 'Gen': '属格 (majrūr, -i)'}


def root_text(root):
    """語根 (ك.ت.ب) → ك-ت-ب (k-t-b)"""
    letters = [c if c != '#' else '?' for c in (root or '').split('.') if c]
    if not letters:
        return root
    latin = '-'.join({'?': 'w/y'}.get(c) or script.CONSONANTS.get(c, c) or 'ʾ' for c in letters)
    return '%s (%s)' % (script.isolate('-'.join(letters)), latin)


def construct_note(item):
    own = (item.ja or '').split(',')[0]
    kind, surface, gloss = item.attrib('construct_with') or ('none', '', '')
    if kind == 'suffix':
        return '連語形: 人称接尾辞 -%s (%s)「%sの」が付いた形 →「%sの%s」(定冠詞は付けない)' % (
            script.translit(surface), script.isolate(surface), gloss, gloss, own)
    return '連語形 (iḍāfa): 後ろの %s (%s)「%s」(属格) と組んで「%sの%s」(前の名詞に定冠詞は付けない)' % (
        script.translit(surface), script.isolate(surface), gloss, gloss, own)


def notes(word):
    if not word.items:
        return []
    item = word.items[0]
    lines = []
    root = item.attrib('root')
    if item.attrib('construct_with'):
        lines.append(construct_note(item))
    if item.attrib('inna_subject'):
        lines.append('inna の主語: 形は対格 (manṣūb) だが、文の主語')
    if item.pos == 'verb' and item.attrib('lex'):
        if root:
            lines.append('語根 ' + root_text(root))
        form = item.attrib('form')
        if form in FORMS:
            pattern, desc = FORMS[form]
            lines.append('型 %s (%s): %s' % (form, pattern, desc))
        aspect = item.attrib('aspect') or ('c' if item.attrib('mood') == 'imperative' else None)
        if aspect in ASPECTS:
            lines.append(ASPECTS[aspect])
        if item.attrib('verb_mood') in MOODS:
            lines.append(MOODS[item.attrib('verb_mood')])
    elif item.pos in ('noun', 'adj') and root and not item.attrib('proper'):
        lines.append('語根 ' + root_text(root))
    return lines
