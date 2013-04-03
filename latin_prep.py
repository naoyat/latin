#!/usr/bin/env python
# -*- coding: utf-8 -*-

def load_preps(file):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) != 3: continue

            word = fs[0].decode('utf-8')
            dom = fs[1]
            ja = fs[2]

            items.append({'pos':'preposition', 'surface':word, 'base':word, 'dominates':dom, 'ja':ja})

    return items


def load():
    return load_preps('words/prep.def')
