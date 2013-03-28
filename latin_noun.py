#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
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
    if suffices[0] == suffices[2]:
        # Acc = Nom (= Voc)
        stems = [stem1, stem1, stem1, stem2, stem2, stem2,
                 stem2, stem2, stem2, stem2, stem2, stem2]
    else:
        stems = [stem1, stem1, stem2, stem2, stem2, stem2,
                 stem2, stem2, stem2, stem2, stem2, stem2]

    def combine(stem, suffix, case_tags={}):
        surface = stem + suffix
        return util.aggregate_dicts(case_tags, {'surface':surface}, tags)

    return map(combine, stems, suffices, case_tags_6x2)


def decline_noun_type1(nom_sg, gen_sg, gender, ja, tags={}):
    suffices = [u'a', u'a', u'am', u'ae', u'ae', u'ā',
                u'ae', u'ae', u'ās', u'ārum', u'īs', u'īs']
    return declension_table(nom_sg[:-1], gen_sg[:-2], suffices, tags)


def decline_noun_type2(nom_sg, gen_sg, gender, ja, tags={}):
    last2 = nom_sg[-2:]

    if last2 == u'um':
        suffices = [u'um', u'um', u'um', u'ī', u'ō', u'ō',
                    u'a', u'a', u'a', u'ōrum', u'īs', u'īs']
        stem1 = nom_sg[:-2]
    elif last2 == u'us':
        suffices = [u'us', u'e', u'um', u'ī', u'ō', u'ō',
                    u'ī', u'ī', u'ōs', u'ōrum', u'īs', u'īs']
        stem1 = nom_sg[:-2]
    elif last2 in [u'er', u'ir']:
        # if gen_sg == nom_sg + u'ī': # puer / puerī
        # else: # ager / agrī
        suffices = [u'', u'', u'um', u'ī', u'ō', u'ō',
                    u'ī', u'ī', u'ōs', u'ōrum', u'īs', u'īs']
        stem1 = nom_sg
    else:
        return []

    stem2 = gen_sg[:-1]
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
    if nom_sg[-1] == u'ū':
        # cornū, cornūs
        suffices = [u'ū', u'ū', u'ū', u'ūs', u'ū', u'ū',
                    u'ua', u'ua', u'ua', u'uum', u'ibus', u'ibus']
        stem1 = nom_sg[:-1]
        stem2 = gen_sg[:-2]
    else: # manus, manūs
        suffices = [u'us', u'us', u'um', u'ūs', u'uī', u'ū', # (ū for Dat.sg)
                    u'ūs', u'ūs', u'ūs', u'uum', u'ibus', u'ibus']
        stem1 = nom_sg[:-2]
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



def load_nouns(file):
    with open(file, 'r') as fp:
        for line in fp:
            # print line[0],
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            # print len(fs)
            if len(fs) < 5: continue
            type = fs[0]
            nom_sg = fs[1].decode('utf-8')
            gen_sg = fs[2].decode('utf-8')
            gender = fs[3]
            ja = fs[4]
#            print fs

            tags = {'pos':'noun', 'base':nom_sg, 'gen_sg':gen_sg, 'gender':gender, 'ja':ja}
            if type == '1':
                tags['type'] = 'I'
                table = decline_noun_type1(nom_sg, gen_sg, gender, ja, tags)
            elif type == '2':
                tags['type'] = 'II'
                table = decline_noun_type2(nom_sg, gen_sg, gender, ja, tags)
            elif type == '3-ium':
                tags['type'] = 'III'
                table = decline_noun_type3_ium(nom_sg, gen_sg, gender, ja, tags)
            elif type == '3-um':
                tags['type'] = 'III'
                table = decline_noun_type3_um(nom_sg, gen_sg, gender, ja, tags)
            elif type == '4':
                tags['type'] = 'IV'
                table = decline_noun_type4(nom_sg, gen_sg, gender, ja, tags)
            elif type == '5':
                tags['type'] = 'V'
                table = decline_noun_type5(nom_sg, gen_sg, gender, ja, tags)
            else:
                table = []

            if len(table) == 0: continue

#            # printing table
#            maxlen = max([len(item['surface']) for item in table])
#            casename = ['Nom','Voc','Acc','Gen','Dat','Abl']
#            for y in xrange(6):
#                line = u"%s: %-*s   %-*s" % (casename[y], maxlen, table[y]['surface'], maxlen, table[y+6]['surface'])
#                print line.encode('utf-8')
#            print

            for item in table:
                # print "noun>", util.render(item)
                latin.latindic_register(item['surface'], item)

def load():
    load_nouns('words/noun.def')
