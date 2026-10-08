#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# チベット文字で書いたサンスクリットの音写を、サンスクリットの綴りに戻す (b → v)
#
# チベット文字の བ はサンスクリットの b と v の両方に使う (bodhi の b、bhagavatī の v)。字だけでは決まらないので、
# b を v にした候補をサンスクリットの辞書 (dragoman/sanskrit。vidyut と Wiktionary) で解析し、少ない要素
# (複合語として細かく分けずに済む読み) で解析できるものを選ぶ。同じなら b のまま。
# サンスクリットのデータが無ければ何もしない。
#
import functools
import itertools
import re

MAX_POSITIONS = 4  # b → v を試す位置の数 (2^4 = 16 通りまで)


def _score(word):
    """解析の悪さ: 解析できなければ大きく、複合語の要素・分けた語の数が多いほど大きい"""
    from dragoman.sanskrit import analyzer
    words = analyzer._words(word)
    score = 0
    for w in words:
        if not w.items:
            score += 10
            continue
        ja = w.items[0].ja or ''
        score += 1 + ja.count('の') + ja.count('{') + ja.count('&') + (2 if re.search('[a-z]', ja) else 0)
    return score


@functools.lru_cache(maxsize=4096)
def restore(iast):
    """IAST (チベット文字から写したもの) → b を v に戻した綴り (bhagabatī → bhagavatī)"""
    try:
        from dragoman.sanskrit import dictionary, morphology
        if not (dictionary.available() and morphology.available()):
            return iast
    except ImportError:
        return iast
    positions = [m.start() for m in re.finditer('b(?!h)', iast)][:MAX_POSITIONS]
    if not positions:
        return iast
    best, best_score = iast, _score(iast)
    for n in range(1, len(positions) + 1):
        for chosen in itertools.combinations(positions, n):
            candidate = ''.join('v' if i in chosen else c for i, c in enumerate(iast))
            score = _score(candidate)
            if score < best_score:
                best, best_score = candidate, score
    return best
