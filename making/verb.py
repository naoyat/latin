#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import strutil


# 1
verb_g1 = set(['am', 'dElect', 'laud', 'pUgn', 'clAm'])
# 2
verb_g2 = set(['mone', 'mane', 'doce', 'move', 'pAre'])
# 3A
verb_g3a = set(['reg', 'scrIb', 'bib', 'vinc', 'fall', 'can', 'leg', 'cEd', 'dIc', 'laed', 'lUd', 'pell',
                'vIv', 'ed', 'dUc', 'em', 'ag'])
# 3B
verb_g3b = set(['capi', 'fugi', 'rapi', 'cupi', 'faci', 'accipi', 'jaci'])
# 4
verb_g4 = set(['audi', 'vesti', 'vinci', 'sali', 'pUni', 'aperi', 'veni', 'dormi', 'feri', 'reperi', 'senti'])

CONJ_1 = 10
CONJ_2 = 20
CONJ_3A = 30
CONJ_3B = 31
CONJ_4 = 40

def conjug_type(pres1sg):
    assert(pres1sg[-1] == "O") # ends with -O

    pre = pres1sg[:-1]
    if pre in verb_g1:
        return CONJ_1
    elif pre in verb_g2:
        return CONJ_2
    elif pre in verb_g3a:
        return CONJ_3A
    elif pre in verb_g3b:
        return CONJ_3B
    elif pre in verb_g4:
        return CONJ_4
    else:
        return CONJ_1


def pres1sg_to_presstem(pres1sg):
    # amO -> amA
    # moneO -> monE
    type = conjug_type(pres1sg)

    if type < 0:
        return None
    elif type == CONJ_1: # am|O
        return pres1sg[:-1] + "A"
    elif type == CONJ_2: # mon|eO
        return pres1sg[:-2] + "E"
    elif type == CONJ_3A: # reg|O
        return pres1sg[:-1] + "e"
    elif type == CONJ_3B: # cap|iO
        return pres1sg[:-2] + "e"
    elif type == CONJ_4: # aud|iO
        return pres1sg[:-2] + "I"


def pres1sg_to_inf(pres1sg):
    return pres1sg_to_presstem(pres1sg) + "re"


def inf_to_pres1sg(inf):
    # amAre -> amO
    # monEre -> moneO
    assert(inf[-2:] == "re") # ends with "-re"

    vowel = inf[-3] # A E
    before = inf[:-3] # am|Are, mon|Ere
    # print inf, vowel, before

    if vowel == 'A': # 1
        pres1sg = before + "O"
    elif vowel == 'E': # 2
        pres1sg = before + "eO"
    elif vowel == 'e': # 3
        if (before + 'i') in verb_g3b:
            pres1sg = before + "iO"
        else:
            pres1sg = before + "O"
    elif vowel == "I": # 4
        pres1sg = before + "iO"

    return pres1sg


def append_suffices(stem, suffices):
    return [stem + suffix for suffix in suffices]

def conj_present(pres1sg):
    type = conjug_type(pres1sg)
    presstem = pres1sg_to_presstem(pres1sg)
    stem = presstem[:-1]

    if type == CONJ_1: # amO : amA[re]
        forms = append_suffices(stem, ["O", "As", "at", "Amus", "Atis", "ant"])
    elif type == CONJ_2: # moneO : monE[re]
        forms = append_suffices(stem, ["eO", "Es", "et", "Emus", "Etis", "ent"])
    elif type == CONJ_3A: # regO : rege[re]
        forms = append_suffices(stem, ["O", "is", "it", "imus", "itis", "unt"])
    elif type == CONJ_3B: # capiO : cape[re]
        forms = append_suffices(stem, ["iO", "is", "it", "imus", "itis", "iunt"])
    elif type == CONJ_4: # audiO : audI[re]
        forms = append_suffices(stem, ["iO", "Is", "It", "Imus", "Itis", "iunt"])
    else:
        forms = []

    return forms


def conj_present_passive(pres1sg):
    type = conjug_type(pres1sg)
    presstem = pres1sg_to_presstem(pres1sg)
    stem = presstem[:-1]

    if type == CONJ_1: # amO : am|Are
        forms = append_suffices(stem, ["or", "Aris", "Atur", "Amur", "AminI", "antur"])
    elif type == CONJ_2: # moneO : mon|Ere
        forms = append_suffices(stem, ["eor", "Eris", "Etur", "Emur", "EminI", "entur"])
    elif type == CONJ_3A: # regO : reg|ere
        forms = append_suffices(stem, ["or", "eris", "itur", "imur", "iminI", "untur"])
    elif type == CONJ_3B: # capiO : cap|ere
        forms = append_suffices(stem, ["ior", "eris", "itur", "imur", "iminI", "iuntur"])
    elif type == CONJ_4: # audiO : aud|Ire
        forms = append_suffices(stem, ["ior", "Iris", "Itur", "Imur", "IminI", "iuntur"])
    else:
        forms = []

    return forms

