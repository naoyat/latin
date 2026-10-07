#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 初学者向けの解説: 動詞の不定形・現在語幹と過去語幹・時制の作り方、複合動詞、エザーフェ、را、人称の接語
#
#   می‌روم → 不定形 raftan (رفتن)「行く」: 現在語幹 rav / 過去語幹 raft
#            現在 (mi- + 現在語幹 + 人称語尾): mi-rav-am
#
from . import dictionary, script


def _stems(lemma):
    entries = [e for e in dictionary.lemmas(lemma) if e['pos'] == 'verb']
    if not entries:
        return None
    entry = max(entries, key=lambda e: e['senses'] or 0)
    present = ' / '.join(r or script.rough_translit(s) for s, r in entry.get('present') or [])
    past = (entry.get('past') or [None, None])[1]
    return entry, present, past


def notes(word):
    if not word.items:
        return []
    item = word.items[0]
    lines = []
    if item.pos == 'verb' and item.attrib('lemma'):
        lemma = item.attrib('lemma')
        if item.attrib('compound'):
            light = item.attrib('light_verb')
            lines.append('複合動詞: 名詞・形容詞 + 軽動詞 %s (%s)' % (script.isolate(light), _roman_of(light)))
        found = _stems(item.attrib('light_verb') or lemma)
        if found:
            entry, present, past = found
            lines.append('不定形 %s (%s): 現在語幹 %s / 過去語幹 %s' % (
                entry.get('roman') or '', script.isolate(entry['word']), present or '-', past or '-'))
        if item.attrib('form'):
            lines.append('形 ' + item.attrib('form') + ('、否定 (na- / ne-)' if item.attrib('negative') else ''))
    if item.attrib('ezafe'):
        lines.append('エザーフェ -e: 文字には書かれない。後ろの形容詞・名詞と結ぶ (ketâb-e xub「良い本」、ketâb-e Ali「アリの本」)')
    if item.attrib('relational'):
        lines.append('関係形容詞 -i: 名詞 %s から「〜の」' % script.isolate(item.attrib('relational')))
    if item.attrib('indefinite'):
        lines.append('不定の -i「ある〜、一つの〜」')
    return lines


def _roman_of(lemma):
    entries = dictionary.lemmas(lemma)
    return entries[0].get('roman') if entries else ''
