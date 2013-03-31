#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin_noun
import latin_pronoun
import latin_adj
import latin_conj
import latin_prep
import latin_verb

import util

#
# 辞書
#
latindic = {}

def latindic_register(surface, info):
    if not info.has_key('pos'): return

    if info['pos'] in ('noun', 'adj'):
        cn = [(info['case'], info['number'])]
        del info['case']
        del info['number']
        info['cn'] = cn
    else:
        cn = None

    if latindic.has_key(surface):
        merged = False
        for item in latindic[surface]:
            if cn is not None and item['pos'] == info['pos'] and item['ja'] == info['ja']:
                item['cn'] += cn
                merged = True
        if not merged:
            latindic[surface].append(info)
    else:
        latindic[surface] = [info]

def latindic_register_items(items):
    for item in items:
        latindic_register(item['surface'], item)

def latindic_lookup(word):
    return latindic.get(word, None)

def latindic_dump():
    for k, v in latindic.items():
        print util.render2(k, v)

def load_def(file, tags={}):
    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) < 3: continue

            surface = fs[0].decode('utf-8')
            pos = fs[1]
            ja = fs[2]

            info = util.aggregate_dicts({'surface':surface, 'pos':pos, 'ja':ja}, tags)
            latindic_register(surface, info)


def latindic_load():
    latin_noun.load()
    latin_pronoun.load()
    latin_adj.load()
    latin_conj.load()
    latin_prep.load()
    latin_verb.load()
    load_def('words/adv.def', {'pos':'adv'})
    load_def('words/other.def')

if __name__ == '__main__':
#    for k, v in latindic.items():
#        print util.render(k), util.render(v)
    pass
