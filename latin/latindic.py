#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from . import orthography

from .words import words_path
from . import latin_noun
from . import latin_pronoun
from . import latin_adj
from . import latin_conj
from . import latin_prep
from . import latin_verb_reg
from . import latin_verb_irreg

from . import util
from . import wiktionary


class LatinDic:
    dic = {}
    # Wiktionary 由来の補助辞書を使うか (環境変数 LATIN_WIKTIONARY=0 で無効)
    use_wiktionary = os.environ.get('LATIN_WIKTIONARY', '1') != '0'


def register(surface, info):
    if 'pos' not in info: return

    if surface in LatinDic.dic:
        LatinDic.dic[surface].append(info)
    else:
        LatinDic.dic[surface] = [info]


def register_items(items):
    for item in items:
        register(item['surface'], item)


_ortho_index = None


def _orthography_index():
    """綴りの流儀 (i/j, u/v) を同一視したキー → 辞書の表層形"""
    global _ortho_index
    if _ortho_index is None:
        _ortho_index = {}
        for surface in LatinDic.dic:
            _ortho_index.setdefault(orthography.uv(orthography.ij(surface)), []).append(surface)
    return _ortho_index


def lookup_hand(word):
    """手作りの辞書 (words/*.def から生成) を引く。
    表記どおりで無ければ、i/j を同一視 → u/v も同一視 (入力に v が無ければ) の順で探す
    (手作りの辞書は juvenis, Jovis のように j で書いている)"""
    items = LatinDic.dic.get(word, None)
    if items:
        return items
    candidates = _orthography_index().get(orthography.uv(orthography.ij(word)), [])
    for allowed in (lambda s: orthography.ij(s) == orthography.ij(word),        # i/j だけ違う
                    lambda s: orthography.may_merge_uv(word)):                  # u/v も違う
        surfaces = [s for s in candidates if allowed(s)]
        if surfaces:
            return [item for s in surfaces for item in LatinDic.dic[s]]
    return None


def lookup_wiktionary(word):
    """Wiktionary 由来の補助辞書を引く (tools/build_wiktionary_dic.py で作成)"""
    if not LatinDic.use_wiktionary:
        return None
    return wiktionary.lookup(word)


def lookup(word):
    """手作りの辞書を優先し、無ければ Wiktionary 由来の補助辞書を引く"""
    return lookup_hand(word) or lookup_wiktionary(word)


def dump():
    for k, v in list(LatinDic.dic.items()):
        print(util.render2(k, v))


def load_def(file, tags={}):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split('\t')
            if len(fs) < 3: continue

            surface = fs[0] #.decode('utf-8')
            pos = fs[1]
            ja = fs[2]

            items.append(util.aggregate_dicts({'surface':surface, 'pos':pos, 'ja':ja}, tags))

    return items


def load():
    global _ortho_index
    _ortho_index = None

    items = []

    items += latin_noun.load()
    items += latin_pronoun.load()
    items += latin_adj.load()
    items += latin_conj.load()
    items += latin_prep.load()
    items += latin_verb_reg.load()
    items += latin_verb_irreg.load()

    items += load_def(words_path('adv.def'), {'pos':'adv'})
    items += load_def(words_path('other.def'))

    register_items(items)

    # return ld


if __name__ == '__main__':
#    for k, v in dic.items():
#        print util.render(k), util.render(v)
    pass
