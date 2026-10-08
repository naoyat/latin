#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語の設定 (共通の解析器 core/analyzer.py と訳 core/Predicate.py などで使う。core/language.py)
#
from dragoman.core.language import Language
from . import latindic, wiktionary


def _lexicalized_participle(base, comparatives):
    """形容詞になった分詞 (acūtus, apertus, patēns): 比較級が形容詞として Wiktionary にあるもの。
    手作りの辞書は分詞からも比較級を作るので、Wiktionary の項目だけを見る"""
    return latindic.LatinDic.use_wiktionary and any(
        any(i.get('pos') == 'adj' for i in (latindic.lookup_wiktionary(form) or [])) for form in comparatives)


LATIN = Language(
    name='la',
    and_words=('et',),
    nor_words=('neque',),
    or_words=('aut',),
    copulas=frozenset({'sum'}),
    negations=frozenset({'nōn', 'non'}),
    vocative_particles=frozenset({'ō', 'Ō'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の', 'Dat': 'に', 'Abl': 'で', 'Voc': 'よ', 'Loc': 'で'},
    lookup=latindic.lookup,
    lexicalized_participle=_lexicalized_participle,
    dictionary=wiktionary,
)
