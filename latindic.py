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

#
# 辞書
#
dic = {}

def register(surface, info):
    if not info.has_key('pos'): return

#    if info['pos'] in ('noun', 'pronoun', 'adj'):
#        if info.has_key('gender'):
#            cn = [(info['case'], info['number'], info['gender'])]
#            del info['gender']
#        else:
#            cn = [(info['case'], info['number'])]
#        del info['case']
#        del info['number']
#        info['cn'] = cn
#    else:
#        cn = None

    if dic.has_key(surface):
#        merged = False
#        for item in latindic[surface]:
#            if cn is not None and item['pos'] == info['pos'] and item['ja'] == info['ja']:
#                item['cn'] += cn
#                merged = True
#        if not merged:
        dic[surface].append(info)
    else:
        dic[surface] = [info]

def register_items(items):
    for item in items:
        register(item['surface'], item)

def lookup(word):
    return dic.get(word, None)

def dump():
    for k, v in dic.items():
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
            register(surface, info)


def load():
    latin_noun.load()
    latin_pronoun.load()
    latin_adj.load()
    latin_conj.load()
    latin_prep.load()
    latin_verb_reg.load()
    latin_verb_irreg.load()
    load_def('words/adv.def', {'pos':'adv'})
    load_def('words/other.def')

if __name__ == '__main__':
#    for k, v in dic.items():
#        print util.render(k), util.render(v)
    pass
