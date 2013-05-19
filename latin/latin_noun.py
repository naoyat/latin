#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util

#
# 格変化
#
case_tags_6x2 = [
    {'case':'Nom', 'number':'sg'},
    {'case':'Voc', 'number':'sg'},
    {'case':'Acc', 'number':'sg'},
    {'case':'Gen', 'number':'sg'},
    {'case':'Dat', 'number':'sg'},
    {'case':'Abl', 'number':'sg'},

    {'case':'Nom', 'number':'pl'},
    {'case':'Voc', 'number':'pl'},
    {'case':'Acc', 'number':'pl'},
    {'case':'Gen', 'number':'pl'},
    {'case':'Dat', 'number':'pl'},
    {'case':'Abl', 'number':'pl'}
    ]

case_tags_7x2 = [
    {'case':'Nom', 'number':'sg'},
    {'case':'Voc', 'number':'sg'},
    {'case':'Acc', 'number':'sg'},
    {'case':'Gen', 'number':'sg'},
    {'case':'Dat', 'number':'sg'},
    {'case':'Abl', 'number':'sg'},
    {'case':'Loc', 'number':'sg'},

    {'case':'Nom', 'number':'pl'},
    {'case':'Voc', 'number':'pl'},
    {'case':'Acc', 'number':'pl'},
    {'case':'Gen', 'number':'pl'},
    {'case':'Dat', 'number':'pl'},
    {'case':'Abl', 'number':'pl'},
    {'case':'Loc', 'number':'pl'}
    ]

case_tags_5sg = [
    {'case':'Nom', 'number':'sg'},
    {'case':'Acc', 'number':'sg'},
    {'case':'Gen', 'number':'sg'},
    {'case':'Dat', 'number':'sg'},
    {'case':'Abl', 'number':'sg'},
]

case_tags_5pl = [
    {'case':'Nom', 'number':'pl'},
    {'case':'Acc', 'number':'pl'},
    {'case':'Gen', 'number':'pl'},
    {'case':'Dat', 'number':'pl'},
    {'case':'Abl', 'number':'pl'}
    ]

case_tags_5x2 = case_tags_5sg + case_tags_5pl

cases_ja = {
    'Nom':'〜が',
    'Acc':'〜を',
    'Gen':'〜の',
    'Dat':'〜に,〜のために,〜にとって',
    'Abl':'〜によって,〜でもって,〜をもって,〜において,〜から',
    'Voc':'〜よ'
}

#
# (名詞・形容詞の)格変化
#

def declension_table(stem1, stem2, suffices, tags):
    # assert(len(suffices) == 10):
    stems = [stem1, stem1, stem2, stem2, stem2, stem2,
             stem2, stem2, stem2, stem2, stem2, stem2]
    if suffices[0] == suffices[2]:
        # Acc = Nom (= Voc)
        stems[2] = stems[0]

    if len(suffices) == 14:
        stems = stems[0:6] + [stem2] + stems[6:12] + [stem2]
        return util.variate(stems, tags, suffices, case_tags_7x2) # with locative
    else:
        return util.variate(stems, tags, suffices, case_tags_6x2)


def decline_noun_type1(nom_sg, gen_sg, gender, ja, tags={}):
    suffices = [u'a', u'a', u'am', u'ae', u'ae', u'ā',
                u'ae', u'ae', u'ās', u'ārum', u'īs', u'īs']
    if nom_sg in [u'dea', u'fīlia']:
        suffices[10] = suffices[11] = u'ābus'
    return declension_table(nom_sg[:-1], gen_sg[:-2], suffices, tags)


def decline_noun_type2(nom_sg, gen_sg, gender, ja, tags={}):
    last2 = nom_sg[-2:]

    if last2 == u'um':
        suffices = [u'um', u'um', u'um', u'ī', u'ō', u'ō',
                    u'a', u'a', u'a', u'ōrum', u'īs', u'īs']
        stem1 = nom_sg[:-2]
        stem2 = gen_sg[:-1]
    elif last2 == u'us':
        if nom_sg[-3:] == u'ius':
            suffices = [u'ius', u'ī', u'ium', (u'ī', u'iī'), u'iō', u'iō',
                        u'iī', u'iī', u'iōs', u'iōrum', u'iīs', u'iīs']
            stem1 = nom_sg[:-3]
            stem2 = gen_sg[:-2]
        else:
            suffices = [u'us', u'e', u'um', u'ī', u'ō', u'ō',
                        u'ī', u'ī', u'ōs', u'ōrum', u'īs', u'īs']
            stem1 = nom_sg[:-2]
            stem2 = gen_sg[:-1]
            # if nom_sg in (u'deus'):
            #    suffices[1] = u'us' ## 神聖視されるものはVoc=Nomとなる場合がある

        if nom_sg == u'humus':
            suffices = suffices[0:6] + [u'ī'] + suffices[6:12] + [u''] # jacere humi

    elif last2 in [u'er', u'ir']:
        # if gen_sg == nom_sg + u'ī': # puer / puerī
        # else: # ager / agrī
        suffices = [u'', u'', u'um', u'ī', u'ō', u'ō',
                    u'ī', u'ī', u'ōs', u'ōrum', u'īs', u'īs']
        stem1 = nom_sg
        stem2 = gen_sg[:-1]
    else:
        return []

    return declension_table(stem1, stem2, suffices, tags)


def decline_noun_type3_ium(nom_sg, gen_sg, gender, ja, tags={}):
    if gender == 'n':
        if nom_sg[-1] == u'e':
            # (c) mare, maris
            suffices = [u'e', u'e', u'e', u'is', u'ī', u'ī',
                        u'ia', u'ia', u'ia', u'ium', u'ibus', u'ibus']
            stem1 = nom_sg[:-1]
        else: # in [u'al', u'ar']:
            # (c) animal. animālis
            suffices = [u'is', u'is', u'em', u'is', u'ī', u'ī',
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus']
            stem1 = nom_sg[:-2]
    else: # m, f
        if nom_sg == gen_sg:
            # (a) piscis, piscis
            suffices = [u'is', u'is', u'em', u'is', u'ī', u'e',
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
            stem1 = nom_sg[:-2]
        else:
            # (b) mōns, montis
            suffices = [u's', u's', u'em', u'is', u'ī', u'e',
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
            stem1 = nom_sg[:-1]

    stem2 = gen_sg[:-2]
    return declension_table(stem1, stem2, suffices, tags)


def decline_noun_type3_um(nom_sg, gen_sg, gender, ja, tags={}):
    if gender == 'n':
        # (b) corpus, corporis
        # (b) nōmen, nōminis
        suffices = [u'', u'', u'', u'is', u'ī', u'e',
                    u'a', u'a', u'a', u'um', u'ibus', u'ibus']
    else: # m, f
        # (a) dux, ducis
        # (a) nātiō, nātiōnis
        suffices = [u'', u'', u'em', u'is', u'ī', u'e',
                    u'ēs', u'ēs', u'ēs', u'um', u'ibus', u'ibus']

    return declension_table(nom_sg, gen_sg[:-2], suffices, tags)


def decline_noun_type4(nom_sg, gen_sg, gender, ja, tags={}):
    if nom_sg[-1] == u'ū': # cornū, cornūs
        suffices = [u'ū', u'ū', u'ū', u'ūs', u'ū', u'ū',
                    u'ua', u'ua', u'ua', u'uum', u'ibus', u'ibus']
        stem1 = nom_sg[:-1]
        stem2 = gen_sg[:-2]
    elif nom_sg[-2:] == u'us': # manus, manūs
        suffices = [u'us', u'us', u'um', u'ūs', u'uī', u'ū', # (ū for Dat.sg)
                    u'ūs', u'ūs', u'ūs', u'uum', u'ibus', u'ibus']
        stem1 = nom_sg[:-2]
        stem2 = gen_sg[:-2]
    elif nom_sg[-1] == u'ē': # Ariadnē ... あとでちゃんと調べる
        suffices = [u'ē', u'ē', u'ē', u'ēs', u'ē', u'ē',
                    u'ēs', u'ēs', u'ēs', u'ērum', u'ēbus', u'ēbus']
        stem1 = nom_sg[:-1]
        stem2 = gen_sg[:-2]

    return declension_table(stem1, stem2, suffices, tags)


def decline_noun_type5(nom_sg, gen_sg, gender, ja, tags={}):
    stem = nom_sg[:-2]
    if stem[-1] == u'i':
        # diēs diēī
        suffices = [u'ēs', u'ēs', u'em', u'ēī', u'ēī', u'ē',
                    u'ēs', u'ēs', u'ēs', u'ērum', u'ēbus', u'ēbus']
    else:
        # rēs reī
        suffices = [u'ēs', u'ēs', u'em', u'eī', u'eī', u'ē',
                    u'ēs', u'ēs', u'ēs', u'ērum', u'ēbus', u'ēbus']

    return declension_table(stem, stem, suffices, tags)


def decline_noun(type, nom_sg, gen_sg, gender, ja):
    if type == '1':
        decliner = decline_noun_type1
        if gen_sg is None:
            gen_sg = nom_sg + u'e'
    elif type == '2':
        decliner = decline_noun_type2
        if gen_sg is None:
            if nom_sg[-2:] in [u'us', u'um']:
                gen_sg = nom_sg[:-2] + u'ī'
            else: # 'er', 'ir'
                print "(", nom_sg, ")"
                return None
    elif type == '3-ium':
        decliner = decline_noun_type3_ium
    elif type == '3-um':
        decliner = decline_noun_type3_um
    elif type == '4':
        decliner = decline_noun_type4
    elif type == '5':
        decliner = decline_noun_type5
    elif type == '*':
#        forms = [[g.decode('utf-8') for g in f.split(',')] for f in fs[1].split(':')]
        forms = [f.split(',') for f in nom_sg.split(':')]
        if len(forms) == 5:
            forms = forms[0:1] + forms[0:1] + forms[1:5]
            case_tags = case_tags_6x2[0:6]
        elif len(forms) == 6:
            case_tags = case_tags_6x2[0:6]
        elif len(forms) == 10:
            forms = forms[0:1] + forms[0:1] + forms[1:5] \
                + forms[5:6] + forms[5:6] + forms[6:10]
            case_tags = case_tags_6x2
        else:
            case_tags = case_tags_6x2
            # util.pp(forms)

        tags = {'pos':'noun', 'type':'*',
                'base':forms[0][0], 'gen_sg':forms[2][0], 'gender':gender,
                'ja':ja
                }
        table = util.variate(['']*len(forms), tags, forms, case_tags)
        # util.pp(table)
        return table
#        items = util.aggregate_cases(table)
#        return items
    else:
        return None

    tags = {'pos':'noun', 'type':type,
            'base':nom_sg, 'gen_sg':gen_sg, 'gender':gender,
            'ja':ja
            }
    # util.pp( tags )

    table = decliner(nom_sg, gen_sg, gender, ja, tags)
    return table


def load_nouns(file):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            # print line[0],
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) == 4:
                args = (fs[0], # type
                        fs[1].decode('utf-8'), # nom_sg
                        None, # gen_sg
                        fs[2], # gender,
                        fs[3]) # ja
            elif len(fs) == 5:
                args = (fs[0], # type
                        fs[1].decode('utf-8'), # nom_sg
                        fs[2].decode('utf-8'), # gen_sg
                        fs[3], # gender
                        fs[4]) # ja
            else:
                continue

            table = decline_noun(*args)
            if table is not None and len(table) > 0:
                items += util.aggregate_cases(table)

    return items


def load():
    return load_nouns('words/noun.def')
