#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 日本語の見出し → ラテン語の語 (Lex) の逆引き (日本語の文を文の枠に入れるときの語の置き換え)
#
#   ラテン語の辞書 (手作りの辞書 latin/words/、Wiktionary 由来の wiktionary.sqlite) の日本語の訳語を逆にする。
#   手作りの辞書の語を先に、訳語の並びで前にあるほど良い (見る → videō、少女 → puella)。
#   ラテン語の Lex は、ラテン語に戻す (語形を作る) ときに辞書の項目と照らせるよう、その項目の訳語 (ja) を持つ
#
import functools
import json
import re

from dragoman.latin import latindic, wiktionary
from .frame import Lex

POS = {'noun': 'noun', 'verb': 'verb', 'adj': 'adj', 'adv': 'adv', 'pronoun': 'pronoun'}
NOTE = re.compile(r'[(（][^)）]*[)）]|\[[^\]]*\]|^[〜～]+|[〜～]+$')


def _keys(ja):
    """訳語の並び → 照合の形の列 (注記・〜を除く): '〜を見る,眺める' → ['見る', '眺める']"""
    out = []
    for gloss in (ja or '').split(','):
        gloss = NOTE.sub('', gloss.strip())
        gloss = re.sub('^[をにがでとへの]', '', gloss).strip()
        if gloss and not re.search('[a-zA-Z0-9]', gloss) and len(gloss) <= 8 and gloss not in out:
            out.append(gloss)
    return out


@functools.lru_cache(maxsize=1)
def _index():
    """照合の形 → [(点, Lex, 性)]。点は小さいほど良い (手作りの辞書 0、Wiktionary 10 + 訳語の中の順位)"""
    if not latindic.LatinDic.dic:
        latindic.load()
    index = {}
    seen = set()
    for items in latindic.LatinDic.dic.values():
        for item in items:
            pos = POS.get(item.get('pos'))
            lemma = item.get('base') or item.get('pres1sg')
            if pos is None or not lemma or (lemma, pos, item.get('ja')) in seen:
                continue
            seen.add((lemma, pos, item.get('ja')))
            gender = next((t[2] for t in item.get('_') or [] if len(t) > 2 and t[2]), '')
            for rank, key in enumerate(_keys(item.get('ja'))):
                index.setdefault(key, []).append((rank, Lex(lemma, pos, item.get('ja')), gender))
    db = wiktionary._connect()
    if db is not None:
        for (info,) in db.execute('SELECT info FROM lemmas'):
            item = json.loads(info)
            pos = POS.get(item.get('pos'))
            lemma = item.get('base') or item.get('pres1sg')
            if pos is None or not lemma or item.get('gloss_lang') != 'ja' or (lemma, pos, item.get('ja')) in seen:
                continue
            seen.add((lemma, pos, item.get('ja')))
            for rank, key in enumerate(_keys(item.get('ja'))):
                index.setdefault(key, []).append((10 + rank, Lex(lemma, pos, item.get('ja')), ''))
    return index


def lookup(japanese, pos=None):
    """日本語の見出し → (Lex, 性) か None。pos (noun / verb / adj / adv) があればその品詞だけ"""
    found = [(score, lex, gender) for score, lex, gender in _index().get(japanese, [])
             if pos is None or lex.pos == pos]
    if not found:
        return None
    score, lex, gender = min(found, key=lambda x: (x[0], x[1].lemma[:1].isupper()))
    return lex, gender
