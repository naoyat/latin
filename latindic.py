#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin_noun
import latin_pronoun
import latin_adj
import latin_conj
import latin_prep
import latin_verb_reg
import latin_verb_irreg

import util


class LatinDic:
    dic = {}
    no_macron_mode = False


def flatten(text):
    return text.replace(u'ā',u'a').replace(u'ē',u'e').replace(u'ī',u'i').replace(u'ō',u'o').replace(u'ū',u'u').replace(u'ȳ',u'y').lower()


def register(surface, info):
    if not info.has_key('pos'): return

    if LatinDic.no_macron_mode:
        surface = flatten(surface)

    if LatinDic.dic.has_key(surface):
        LatinDic.dic[surface].append(info)
    else:
        LatinDic.dic[surface] = [info]


def register_items(items):
    for item in items:
        register(item['surface'], item)


def lookup(word):
    return LatinDic.dic.get(word, None)


def dump():
    for k, v in LatinDic.dic.items():
        print util.render2(k, v)


def load_def(file, tags={}):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) < 3: continue

            surface = fs[0].decode('utf-8')
            pos = fs[1]
            ja = fs[2]

            items.append(util.aggregate_dicts({'surface':surface, 'pos':pos, 'ja':ja}, tags))

    return items


def load(no_macron_mode=False):
#    ld = LatinDic(no_macron_mode=no_macron_mode)
    LatinDic.no_macron_mode = no_macron_mode

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
