#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin_noun
import util

def decline_adj_comparative(nom_sg_mf, tags):
    table = []
    stem1 = nom_sg_mf
    stem1_n = nom_sg_mf[:-3] + 'ius'
    stem2 = nom_sg_mf[:-3]+ u'iōr'

    suffices = [u'', u'', u'em', u'is', u'ī', u'e', # (-ī) for Abl.sg
                u'ēs', u'ēs', u'ēs', u'um', u'ibus', u'ibus'] # (īs) for Acc.pl
    tags['gender'] = 'm'
    table += latin_noun.declension_table(stem1, stem2, suffices, tags)
    tags['gender'] = 'f'
    table += latin_noun.declension_table(stem1, stem2, suffices, tags)

    suffices = [u'', u'', u'', u'is', u'ī', u'e', # (-ī) for Abl.sg
                u'a', u'a', u'a', u'um', u'ibus', u'ibus'] # (īs) for Acc.pl
    tags['gender'] = 'n'
    table += latin_noun.declension_table(stem1_n, stem2, suffices, tags)

    return table


def decline_adj_superlative(nom_sg_m, tags):
    return decline_adj_type1(nom_sg_m, nom_sg_m[:-2]+u'a', tags, False)


def decline_adj_type1(nom_sg_m, nom_sg_f, tags, comp=True):
    ja = tags['ja']
    suffix = nom_sg_m[-2:]
    if suffix == u'us':
        stem1 = nom_sg_m[:-2]
        stem2 = stem1 # + u'ī'
    elif suffix in [u'er', u'ur']: # ur for "satur"
        if nom_sg_m[-3:] == nom_sg_f[-4:-1]:
            # lī-ber lī-ber-a
            stem1 = nom_sg_m
            stem2 = stem1
        else:
            stem1 = nom_sg_m
            stem2 = nom_sg_m[:-2] + u'r'
#    else:
#        print "decline_adj_type1(%s, %s, %s, %s)" % (str(nom_sg_m), str(nom_sg_f), str(tags), str(comp))
#        return []

    my_tags = util.aggregate_dicts({'pos':'adj', 'base':nom_sg_m, 'type':'I'}, tags)

    table = []
    my_tags['gender'] = 'm'
    table += latin_noun.decline_noun_type2(nom_sg_m, stem2 + u'ī', 'm', ja, my_tags)
    my_tags['gender'] = 'f'
    table += latin_noun.decline_noun_type1(nom_sg_f, stem2 + u'ae', 'f', ja, my_tags)
    my_tags['gender'] = 'n'
    table += latin_noun.decline_noun_type2(stem2 + u'um', stem2 + u'ī', 'n', ja, my_tags)

    if comp:
        # 比較級
        tags_c = {'pos':'adj', 'base':nom_sg_m, 'ja':'より'+my_tags['ja'], 'type':'I', 'rank':'+'}
        table += decline_adj_comparative(stem2 + u'ior', tags_c)

        # 最上級
        tags_s = {'pos':'adj', 'base':nom_sg_m, 'ja':'最も'+my_tags['ja'], 'type':'I', 'rank':'++'}
        if nom_sg_m[-1] == 'r':
            base = nom_sg_m + 'rimus'
        else:
            base = stem2 + u'issimus'
            table += decline_adj_superlative(base, tags_s)

    return table


def decline_adj_type2(nom_sg_mf, gen_sg, nom_sg_n, tags):
    my_tags = util.aggregate_dicts({'pos':'adj', 'base':nom_sg_mf, 'type':'II'}, tags)
    table = []
    if nom_sg_n == u'-':
        if nom_sg_mf[-1:] == 'x':
            pass
        elif nom_sg_mf[-2:] == 'ns':
            pass
        # (2: n=m) -x -cis, -ns -ntis
        stem1 = nom_sg_mf
        stem2 = gen_sg[:-2]
        if nom_sg_mf in [u'vetus', u'dīves']:
            suffices = [u'', u'', u'em', u'is', u'ī', u'e',
                        u'ēs', u'ēs', u'ēs', u'um', u'ibus', u'ibus']
        else:
            suffices = [u'', u'', u'em', u'is', u'ī', u'ī', # (-e) for Abl.sg
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl

        # tags = dict({'pos':'adj', 'base':nom_sg_mf, 'type':'II'}, **tags)

        my_tags['gender'] = 'm'
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)
        my_tags['gender'] = 'f'
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)

        if nom_sg_mf == u'vetus':
            suffices = [u'', u'', u'', u'is', u'ī', u'e',
                        u'a', u'a', u'a', u'um', u'ibus', u'ibus']
        elif nom_sg_mf == u'dīves':
            suffices = [u'', u'', u'', u'is', u'ī', u'e',
                        u'ia', u'ia', u'ia', u'um', u'ibus', u'ibus']
            # Nom/Voc/Acc.pl で dīt-
        else:
            suffices = [u'', u'', u'', u'is', u'ī', u'ī', # (-e) for Abl.sg
                        u'ia', u'ia', u'ia', u'ium', u'ibus', u'ibus']
        my_tags['gender'] = 'n'
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)
    else:
        # (1: n!=m) -is/-e
        if nom_sg_mf[-2:] == 'er':
            stem1 = nom_sg_mf
            stem2 = gen_sg[:-2]
            suffices = [u'', u'', u'em', u'is', u'ī', u'ī',
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        else:
            stem1 = nom_sg_mf[:-2]
            stem2 = gen_sg[:-2]
            suffices = [u'is', u'is', u'em', u'is', u'ī', u'ī',
                        u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        my_tags['gender'] = 'm'
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)

        # f
        stem1 = stem2 = gen_sg[:-2]
        suffices = [u'is', u'is', u'em', u'is', u'ī', u'ī',
                    u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        my_tags['gender'] = 'f'
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)

        # n
        suffices = [u'e', u'e', u'e', u'is', u'ī', u'ī',
                    u'ia', u'ia', u'ia', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        my_tags['gender'] = 'n'
        stem1 = stem2
        table += latin_noun.declension_table(stem1, stem2, suffices, my_tags)

    # 比較級
    tags_c = {'pos':'adj', 'base':nom_sg_mf, 'ja':'より'+my_tags['ja'], 'type':'II', 'rank':'+'}
    table += decline_adj_comparative(gen_sg[:-2] + u'ior', tags_c)

    # 最上級
    tags_s = {'pos':'adj', 'base':nom_sg_mf, 'ja':'最も'+my_tags['ja'], 'type':'II', 'rank':'++'}
    if nom_sg_mf[-4:] == 'ilis':
        base = nom_sg_mf[:-4] + 'illimus'
    else:
        base = gen_sg[:-2] + u'issimus'
    table += decline_adj_superlative(base, tags_s)

    return table


def decline_adj(type, f1, f2, f3, ja):
    table = []
    if type == '1':
        nom_sg_m = f1
        nom_sg_f = f2
        # nom_sg_n = f3
        table = decline_adj_type1(nom_sg_m, nom_sg_f, {'ja':ja})
    elif type == '2':
        nom_sg_mf = f1
        gen_sg    = f2
        nom_sg_n  = f3
        table = decline_adj_type2(nom_sg_mf, gen_sg, nom_sg_n, {'ja':ja})
    else:
        pass

    return table


def pp_adj_declension(table):
    # printing table
    maxlen = max([len(item['surface']) for item in table])
    casename = ['Nom','Voc','Acc','Gen','Dat','Abl']
    for y in xrange(6):
        line = "%s: " % casename[y]
        for x in xrange(3):
            item = table[x*12 + y]
            line += u"%-*s " % (maxlen, item['surface'])
            line += u"    "
        for x in xrange(3):
            item = table[x*12 + y+6]
            line += u"%-*s " % (maxlen, item['surface'])
        print line.encode('utf-8')
    print


def load_adjs(file):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if line[0] == '#': continue
            fs = line.rstrip().split()
            if len(fs) == 5:
                args = (fs[0],
                        fs[1].decode('utf-8'),
                        fs[2].decode('utf-8'),
                        fs[3].decode('utf-8'),
                        fs[4])
            elif len(fs) == 3:
                nom_sg_m = fs[1].decode('utf-8')
                stem = nom_sg_m[:-2]
                args = (fs[0],
                        stem + u'us',
                        stem + u'a',
                        stem + u'um',
                        fs[2])
            else:
                continue

            table = decline_adj(*args)
            if len(table) == 0: continue

            items += util.aggregate_cases(table)

    return items


def load():
    return load_adjs('words/adj.def')
