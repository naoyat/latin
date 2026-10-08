#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 一般のサンスクリットの訳語を直す表
#
# 訳語は Wiktionary の語義の先頭から取るが、先頭の語義が外れているものがある (ārya の先頭は民族名「Indo-Aryan」、
# pustaka は「突起のある飾り」、śruta は「筒抜け」)。見出し (IAST) → [(訳語, 品詞)]。品詞は noun / adj / name / root。
# dictionary.lemmas が Wiktionary の項目より先に返す (仏典の語彙の表 buddhist.py を使うときは、そちらが先)。
#
from . import script

GLOSSES = {
    'ārya': [('高貴な,尊い', 'adj'), ('高貴な人,聖者', 'noun')],
    'pustaka': [('本', 'noun')],
    'śruta': [('聞かれた', 'adj')],
    'pīta': [('黄色い,飲まれた', 'adj')],
    'ambara': [('衣,空', 'noun')],
    'kṛṣṇa': [('クリシュナ', 'name'), ('黒い', 'adj')],
    'sūrya': [('太陽', 'noun')],
    'śakti': [('力', 'noun')],
    'putra': [('息子', 'noun')],
    'vaṇij': [('商人', 'noun')],
    'megha': [('雲', 'noun')],
    # 語根
    'vṛṣ': [('雨が降る', 'root')],
    'utthā': [('立ち上がる', 'root')],
}

_by_slp1 = None


def lemmas(key):
    """見出し (SLP1) → dictionary.lemmas と同じ形の項目 (表に無ければ空)"""
    global _by_slp1
    if _by_slp1 is None:
        _by_slp1 = {script.to_slp1(k): v for k, v in GLOSSES.items()}
    return [{'pos': pos, 'ja': ja, 'gloss_lang': 'ja', 'word': script.iast(key), 'gana': None, 'causative': False,
             'senses': 100, 'override': True} for ja, pos in _by_slp1.get(key, [])]
