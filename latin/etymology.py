#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 語源の表示 (Wiktionary 由来。説明文は英語のまま)
#
#   pater  系統: イタリック祖語 *patēr ← 印欧祖語 *ph₂tḗr (語根 印欧祖語 *peh₂-)
#          同源: 古ラテン Diēspiter “Father Jove”, ラテン Iuppiter “Jupiter”
#          From Proto-Italic *patēr, from Proto-Indo-European *ph₂tḗr. ...
#
from . import wiktionary
from .languages import lang_name
from .descendants import lemma_of

KIND_MARKS = {'bor': '借用', 'der': '派生'}


def _term(code, term, tr='', gloss=''):
    text = '%s %s' % (lang_name(code), term)
    if tr:
        text += ' (%s)' % tr
    if gloss:
        text += ' “%s”' % gloss
    return text


def describe(lemma):
    """見出し語の語源を行のリストで。無ければ []"""
    lines = []
    for ety in wiktionary.etymology(lemma):
        chain, roots = [], []
        for kind, code, term, gloss in ety['ancestors']:
            if kind == 'root':
                roots.append(_term(code, term, gloss=gloss))
            else:
                mark = KIND_MARKS.get(kind)
                chain.append(_term(code, term, gloss=gloss) + (' [%s]' % mark if mark else ''))
        if chain or roots:
            line = '系統: ' + ' ← '.join(chain) if chain else '語根:'
            if roots:
                line += (' (語根 %s)' if chain else ' %s') % ', '.join(roots)
            lines.append(line)
        if ety['cognates']:
            lines.append('同源: ' + ', '.join(_term(*c) for c in ety['cognates']))
        if ety['text']:
            lines.append(ety['text'])
    return lines


def describe_word(word):
    """語 (Word) の候補の見出し語ごとの語源。[(見出し語, [行, ...])]"""
    result, seen = [], set()
    for item in word.items or []:
        lemmas = [lemma_of(item)]
        if item.pos == 'participle':
            lemmas.append(item.attrib('pres1sg'))  # 分詞に無ければ元の動詞
        for lemma in lemmas:
            if not lemma or lemma in seen:
                continue
            seen.add(lemma)
            lines = describe(lemma)
            if lines:
                result.append((lemma, lines))
                break
    return result
