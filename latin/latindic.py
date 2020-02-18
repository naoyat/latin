#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import latin_noun
from . import latin_pronoun
from . import latin_adj
from . import latin_conj
from . import latin_prep
from . import latin_verb_reg
from . import latin_verb_irreg

from . import util


class LatinDic:
    dic = {}
    auto_macron_mode = False


def flatten(text):
    return text.replace('ā','a').replace('ē','e').replace('ī','i').replace('ō','o').replace('ū','u').replace('ȳ','y').lower()


def register(surface, info):
    if 'pos' not in info: return

    if LatinDic.auto_macron_mode:
        surface = flatten(surface)

    if surface in LatinDic.dic:
        LatinDic.dic[surface].append(info)
    else:
        LatinDic.dic[surface] = [info]


def register_items(items):
    for item in items:
        register(item['surface'], item)


def lookup(word):
    return LatinDic.dic.get(word, None)


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


def load(auto_macron_mode=False):
    LatinDic.auto_macron_mode = auto_macron_mode

    items = []

    items += latin_noun.load()
    items += latin_pronoun.load()
    items += latin_adj.load()
    items += latin_conj.load()
    items += latin_prep.load()
    items += latin_verb_reg.load()
    items += latin_verb_irreg.load()

    items += load_def('words/adv.def', {'pos':'adv'})
    items += load_def('words/other.def')

    register_items(items)

    # return ld


if __name__ == '__main__':
#    for k, v in dic.items():
#        print util.render(k), util.render(v)
    pass
