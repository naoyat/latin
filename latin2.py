#!/usr/bin/env python
# -*- coding: utf-8 -*-
import latin
import util

latindic = {}

import latin_pronouns

def latindic_register(surface, info):
    if latindic.has_key(surface):
        latindic[surface].append(info)
    else:
        latindic[surface] = [info]


words_to_register = [
    (u'et', {'pos':'conj', 'en':'and', 'ja':'と,そして'}),
    (u'sed', {'pos':'conj', 'en':'but', 'ja':'しかし'}),
    (u'saepe', {'pos':'adv', 'en':'often'}),
    (u'hodiē', {'pos':'adv', 'ja':'今日'}),
    (u'rēctē', {'pos':'adv', 'ja':'正しく,まっすぐに,その通り'}),
    (u'satis', {'pos':'adv', 'ja':'十分に'}),
    (u'semper', {'pos':'adv', 'ja':'いつも,ずっと'}),
    (u'autem', {'pos':'adv', 'ja':'しかし,さらに,一方'}),#
    (u'quam', {'pos':'prep', 'ja':'〜より(than)'}),
]
util.tuple_map(latindic_register, words_to_register)

latin_prepositions = [
    ## Acc/Abl
    (u'in', 'Acc', '〜の中へ,〜の上へ,〜に向かって,〜に対して'),
    (u'sub', 'Acc', '〜の下へ,〜のもとへ'),
    (u'in', 'Abl', '〜の中で,〜の上で'),
    (u'sub', 'Abl', '〜の下で,〜のもとで'),

    ## Acc
    (u'ad', 'Acc', '〜の方へ,〜のところまで'),
    (u'ante', 'Acc', '〜の前に,〜以前に'),
    (u'apud', 'Acc', '〜の家で,〜のもとで'),
    (u'circum', 'Acc', '〜のまわりに'),
    (u'circā', 'Acc', '〜のまわりに'),
    (u'contrā', 'Acc', '〜に対抗して,〜に反して'),
    (u'extrā', 'Acc', '〜の外側で,〜の外へ'),
    (u'praeter', 'Acc', '〜の傍らをすぎて,〜に反して'),
    (u'prope', 'Acc', '〜の近くで'),
    (u'propter', 'Acc', '〜の近くで,〜のゆえに'),
    (u'īnfrā', 'Acc', '〜の下方へ,〜に劣って'),
    (u'inter', 'Acc', '〜の間に'),
    (u'intrā', 'Acc', '〜の内側で,〜の中へ'),
    (u'ob', 'Acc', '〜の前へ,〜ゆえに,〜の代わりに'),
    (u'per', 'Acc', '〜を通って,〜を通じて,〜により'),
    (u'post', 'Acc', '〜のうしろで,〜以後'),
    (u'suprā', 'Acc', '〜の上方に,〜をこえて'),
    (u'trāns', 'Acc', '〜をこえて,〜を通過して'),
    (u'ultrā', 'Acc', '〜の向こうに,〜をこえて'),

    ## Abl
    (u'ā', 'Abl', '〜から(離れて),〜によって'), # ā 子音 / ab 母音
    (u'ab', 'Abl', '〜から(離れて),〜によって'),
    (u'cum', 'Abl', '〜とともに,〜をもって'),
    (u'dē', 'Abl', '〜から(離れて)下へ,〜について'),
    (u'ē', 'Abl', '〜(の中)から外へ'),
    (u'ex', 'Abl', '〜(の中)から外へ'),
    (u'prae', 'Abl', '〜の前に,〜のあまり,〜に比して'),
    (u'prō', 'Abl', '〜の前に,〜のために,〜の代わりに'),
    (u'sine', 'Abl', '〜なしに'),
]

for word, dom, ja in latin_prepositions:
    latindic_register(word, {'pos':'preposition', 'surface':word, 'base':word, 'domines':dom, 'ja':ja})


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

    return map(combine, stems, suffices, latin.case_tags_6x2)


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


def decline_adj_comparative(nom_sg_mf, tags):
    table = []
    stem1 = nom_sg_mf
    stem1_n = nom_sg_mf[:-3] + 'ius'
    stem2 = nom_sg_mf[:-3]+ u'iōr'

    suffices = [u'', u'', u'em', u'is', u'ī', u'e', # (-ī) for Abl.sg
                u'ēs', u'ēs', u'ēs', u'um', u'ibus', u'ibus'] # (īs) for Acc.pl
    tags['gender'] = 'm'
    table += declension_table(stem1, stem2, suffices, tags)
    tags['gender'] = 'f'
    table += declension_table(stem1, stem2, suffices, tags)

    suffices = [u'', u'', u'', u'is', u'ī', u'e', # (-ī) for Abl.sg
                u'a', u'a', u'a', u'um', u'ibus', u'ibus'] # (īs) for Acc.pl
    tags['gender'] = 'n'
    table += declension_table(stem1_n, stem2, suffices, tags)

    return table


def decline_adj_superlative(nom_sg_m, tags):
    return decline_adj_type1(nom_sg_m, nom_sg_m[:-2]+u'a', tags, False)


def decline_adj_type1(nom_sg_m, nom_sg_f, tags, comp=True):
    suffix = nom_sg_m[-2:]
    if suffix == u'us':
        stem1 = nom_sg_m[:-2]
        stem2 = stem1 # + u'ī'
    elif suffix == u'er':
        if nom_sg_m[-3:] == nom_sg_f[-4:-1]:
            # lī-ber lī-ber-a
            stem1 = nom_sg_m
            stem2 = stem1
        else:
            stem1 = nom_sg_m
            stem2 = nom_sg_m[:-2] + u'r'

    my_tags = util.aggregate_dicts({'pos':'adj', 'base':nom_sg_m, 'type':'I'}, tags)

    table = []
    my_tags['gender'] = 'm'
    table += decline_noun_type2(nom_sg_m, stem2 + u'ī', 'm', ja, my_tags)
    my_tags['gender'] = 'f'
    table += decline_noun_type1(nom_sg_f, stem2 + u'ae', 'f', ja, my_tags)
    my_tags['gender'] = 'n'
    table += decline_noun_type2(stem2 + u'um', stem2 + u'ī', 'n', ja, my_tags)

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
        table += declension_table(stem1, stem2, suffices, my_tags)
        my_tags['gender'] = 'f'
        table += declension_table(stem1, stem2, suffices, my_tags)

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
        table += declension_table(stem1, stem2, suffices, my_tags)
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
        table += declension_table(stem1, stem2, suffices, my_tags)

        # f
        stem1 = stem2 = gen_sg[:-2]
        suffices = [u'is', u'is', u'em', u'is', u'ī', u'ī',
                    u'ēs', u'ēs', u'ēs', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        my_tags['gender'] = 'f'
        table += declension_table(stem1, stem2, suffices, my_tags)

        # n
        suffices = [u'e', u'e', u'e', u'is', u'ī', u'ī',
                    u'ia', u'ia', u'ia', u'ium', u'ibus', u'ibus'] # (īs) for Acc.pl
        my_tags['gender'] = 'n'
        stem1 = stem2
        table += declension_table(stem1, stem2, suffices, my_tags)

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
                latindic_register(item['surface'], item)



def decline_adj(type, f1, f2, f3, ja):
    f1_uc = f1.decode('utf-8')
    f2_uc = f2.decode('utf-8')
    f3_uc = f3.decode('utf-8')

    table = []
    if type == '1':
        nom_sg_m = f1_uc
        nom_sg_f = f2_uc
        # nom_sg_n = f3_uc
        table = decline_adj_type1(nom_sg_m, nom_sg_f, {'ja':ja})
    elif type == '2':
        nom_sg_mf = f1_uc
        gen_sg    = f2_uc
        nom_sg_n  = f3_uc
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
    with open(file, 'r') as fp:
        for line in fp:
            if line[0] == '#': continue
            fs = line.rstrip().split()
            if len(fs) < 5: continue

            table = decline_adj(*fs)
            # pp_adj_declension(table)
            for item in table:
                latindic_register(item['surface'], item)

def lookup(word):
    if latindic.has_key(word):
        return latindic[word]
    else:
        return None


load_nouns('noun.def')
load_adjs('adj.def')

if __name__ == '__main__':
#    for k, v in latindic.items():
#        print util.render(k), util.render(v)
    pass
