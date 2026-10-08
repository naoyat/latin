#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ウルドゥー語の語 → ヒンディー語の語形の対応表 (tools/build_urdu_dic.py で作る SQLite) の検索
#
import os
import sqlite3

from dragoman.core import paths
from dragoman.hindi import dictionary as hindi_dictionary
from . import script

DB_PATH = paths.data('ur', 'urdu.sqlite')

_db = None


def _connect():
    global _db
    if _db is None and os.path.exists(DB_PATH):
        _db = sqlite3.connect(DB_PATH, check_same_thread=False)
    return _db


def available():
    return _connect() is not None and hindi_dictionary.available()


def candidates(word, limit=8):
    """ウルドゥー文字の語 → ヒンディー語の語形 (デーヴァナーガリー) の候補。Wiktionary の対応があればそれだけ、
    無ければ綴りの骨組みの合うもの"""
    db = _connect()
    if db is None:
        return []
    exact = [d for d, in db.execute('SELECT deva FROM exact WHERE urdu = ?', (script.normalize(word),))]
    out = []
    for key in script.skeletons(word):
        for d, in db.execute('SELECT deva FROM skeleton WHERE skeleton = ?', (key,)):
            if d not in out:
                out.append(d)
    if exact:
        # Wiktionary の対応があればそれと、骨組みの合う機能語 (یہ は ये と यह の両方)
        extra = [d for d in out if _rank(d)[0] < 2 and d not in exact]
        return sorted(exact + extra, key=_rank)[:limit]
    # 機能語・助動詞を先に (ہے は है「〜である」、یہ は यह「これ」)、次に見出し語の形
    return sorted(out, key=_rank)[:limit]


def _rank(deva):
    from dragoman.hindi import morphology, script as hindi_script
    key = hindi_script.key(deva)
    if key in PREFERRED:
        return (0, PREFERRED.index(key))
    if key in FUNCTION:
        return (1, 0)
    return (2, 0) if hindi_dictionary.lemmas(key) else (3, 0)


def _keys(words):
    from dragoman.hindi import script as hindi_script
    return [hindi_script.key(w) for w in words]


PREFERRED = _keys(['है', 'हैं', 'हूँ', 'हो', 'था', 'थी', 'थे', 'थीं', 'यह', 'वह', 'मैं', 'में', 'के', 'की', 'का', 'को', 'से',
                   'ने', 'पर', 'और', 'नहीं', 'भी', 'तो', 'ही', 'कि', 'मेरे', 'मेरा', 'मेरी'])
FUNCTION = set()


def _init_function():
    from dragoman.hindi import morphology
    FUNCTION.update(_keys(list(morphology.POSTPOSITIONS) + list(morphology.FUNCTION_WORDS) + list(morphology.PRONOUNS)))


_init_function()


# 子孫語・語源はヒンディー語の辞書から
descendants = hindi_dictionary.descendants
etymology = hindi_dictionary.etymology
