#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語の語の分解: 人称の接辞 (ku= / e= / ci= / a= / en= / un= / i= …) と語幹、人称の接尾辞 (-as, -an)、
# 動詞の複数形 (単数形と訳語)、名詞の所属形 (概念形と訳語)
#
# 訳語は、手作りの語彙表 (grammar.LEXICON) → Wiktionary (kaikki。英語の語義を英語 → 日本語の表で) → ainu-morphology-data
# (動詞の単複・名詞の所属形の表。$DRAGOMAN_DATA/ain/morphology-data。出典は既存の辞典なので手元だけで使う) の順に引く
#
import csv
import functools
import json
import os
from dataclasses import dataclass, field

from dragoman.core import en_ja, paths
from . import grammar, script

DATA = paths.data('ain')


@dataclass
class Morph:
    surface: str
    key: str
    gloss: str = ''          # 日本語の訳語
    pos: str = ''            # noun / vi / vt / adj / adv / pron / num / det / postp / particle / neg / aux / unknown
    subject: str = ''        # 人称の接辞・接尾辞からの主語 (私・あなた …)
    object: str = ''         # 人称の接辞からの目的語
    parts: list = field(default_factory=list)  # 分解 (ku= + kor)
    source: str = ''         # 訳語の出典 (表 / Wiktionary / 単複の表 …)


@functools.lru_cache(maxsize=1)
def _kaikki():
    """Wiktionary: 見出し → [(品詞, 英語の語義)]"""
    out = {}
    path = os.path.join(DATA, 'kaikki.org-dictionary-Ainu.jsonl')
    if not os.path.exists(path):
        return out
    from dragoman.core.wiktionary_import import english_glosses
    with open(path, encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            en = english_glosses(entry)
            if en and entry.get('pos') in ('noun', 'verb', 'adj', 'adv', 'pron', 'num', 'particle', 'name', 'postp'):
                out.setdefault(script.key(entry['word']), []).append((entry['pos'], en))
    return out


def _tsv(name):
    path = os.path.join(DATA, 'morphology-data', name)
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


@functools.lru_cache(maxsize=1)
def _plurals():
    """動詞の複数形 → (単数形, 訳語, 品詞)"""
    return {script.key(r['plural']): (r['singular'], r['gloss_ja'], r['pos']) for r in _tsv('verb_plurals.tsv')
            if r.get('plural')}


@functools.lru_cache(maxsize=1)
def _possessives():
    """名詞の所属形 → (概念形, 訳語)"""
    out = {}
    for r in _tsv('noun_possessives.tsv'):
        for col in ('possessed_short', 'possessed_long'):
            if r.get(col):
                out[script.key(r[col])] = (r['term'], r['gloss_ja'])
    return out


def available():
    return bool(_kaikki()) or True  # 語彙表だけでも動く


def lookup(key):
    """語幹 → (訳語, 品詞, 出典)。無ければ None"""
    if key in grammar.LEXICON:
        ja, pos = grammar.LEXICON[key]
        return ja, pos, '表'
    plural = _plurals().get(key)
    if plural and plural[1]:
        pos = 'vt' if '他動詞' in (plural[2] or '') else 'vi'
        return plural[1] + ' (複数)', pos, '単複の表'
    possessed = _possessives().get(key)
    if possessed and possessed[1]:
        return possessed[1], 'noun', '所属形の表'
    for pos, en in _kaikki().get(key, []):
        ja_pos = {'verb': 'verb', 'adj': 'adj', 'adv': 'adv'}.get(pos, 'noun')
        ja = en_ja.translate(en, ja_pos)
        mapped = {'verb': 'vt', 'adj': 'adj', 'adv': 'adv', 'pron': 'pron', 'num': 'num', 'particle': 'particle',
                  'postp': 'postp'}.get(pos, 'noun')
        return (ja or en).split(',')[0], mapped, 'Wiktionary'
    return None


@functools.lru_cache(maxsize=20000)
def analyze(surface):
    """語 → Morph。人称の接辞を外して語幹を引く (kukor → ku= + kor「私が持つ」、enkore → en= + kore「私に与える」)"""
    key = script.key(surface)
    if not key:
        return Morph(surface, key, pos='punct')
    found = lookup(key)
    if found:
        return Morph(surface, key, found[0], found[1], parts=[key], source=found[2])
    # 主語の接辞 + 目的語の接辞 + 語幹 (e=en=kore はまれなので、どちらか一つ)
    for prefixes, role in ((grammar.SUBJECT_PREFIXES, 'subject'), (grammar.OBJECT_PREFIXES, 'object')):
        for prefix in sorted(prefixes, key=len, reverse=True):
            if key.startswith(prefix) and len(key) > len(prefix) + 1:
                stem = key[len(prefix):]
                found = lookup(stem)
                if found and found[1] in ('vi', 'vt', 'adj'):
                    m = Morph(surface, key, found[0], found[1], parts=[prefix + '=', stem], source=found[2])
                    setattr(m, role, prefixes[prefix][1])
                    return m
    # 人称の接尾辞 -as / -an (自動詞: sapas → sap + -as「私が下る」)
    for suffix, person in list(grammar.SUBJECT_SUFFIXES.items()) + [('y' + k, v) for k, v in grammar.SUBJECT_SUFFIXES.items()]:
        if key.endswith(suffix) and len(key) > len(suffix) + 1:
            found = lookup(key[:-len(suffix)])   # okayas ← oka + (y) + -as
            if found and found[1] in ('vi', 'adj'):
                return Morph(surface, key, found[0], found[1], subject=person, parts=[key[:-len(suffix)], '-' + suffix],
                             source=found[2])
    return Morph(surface, key, surface, 'unknown', parts=[key])
