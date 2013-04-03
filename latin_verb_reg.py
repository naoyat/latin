#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util

import latin_adj
import latin_pronoun

CONJ_1 = '1'
CONJ_2 = '2'
CONJ_3A = '3a'
CONJ_3B = '3b'
CONJ_4 = '4'

persons_and_numbers = [
    {'person':1, 'number':'sg'},
    {'person':2, 'number':'sg'},
    {'person':3, 'number':'sg'},
    {'person':1, 'number':'pl'},
    {'person':2, 'number':'pl'},
    {'person':3, 'number':'pl'}
    ]

def conjugate(stem, common_tags, suffices, suffices_tags=persons_and_numbers):
    return util.variate(stem, common_tags, suffices, suffices_tags)


## 現在形
def conjugate_present(type, pres1sg, tags={}):
    items = []
    if type == CONJ_1:
        stem = pres1sg[:-1]
        x = u''
        long = y = u'ā'
        short = nt = u'a'
    elif type == CONJ_2:
        stem = pres1sg[:-2]
        x = u'e'
        long = y = u'ē'
        short = nt = u'e'
    elif type == CONJ_3A:
        stem = pres1sg[:-1]
        x = u''
        y = u'e'
        long = short = u'i'
        nt = u'u'
    elif type == CONJ_3B:
        stem = pres1sg[:-2]
        x = u'i'
        y = u'e'
        long = short = u'i'
        nt = u'iu'
    elif type == CONJ_4:
        stem = pres1sg[:-2]
        x = u'i'
        long = y = u'ī'
        short = u'i'
        nt = u'iu'

    # x: -ō
    # long: A(ri)
    # short: a(tur), a(ntur)
    active_present_suffices = [x + u'ō', long + u's', short + u't',
                               long + u'mus', long + u'tis', nt + u'nt']
    passive_present_suffices = [x + u'or', (y + u'ris', y + u're'), long + u'tur',
                                long + u'mur', long + u'minī', nt + u'ntur']

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}),
                       active_present_suffices)
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}),
                       passive_present_suffices)
    return items


## 命令
def conjugate_imperative(type, pres1sg, tags={}):
    items = []

    if type == CONJ_1:
        stem = pres1sg[:-1]
        long = long0 = u'ā'
        short = u'a'
    elif type == CONJ_2:
        stem = pres1sg[:-2]
        long = long0 = u'ē'
        short = u'e'
    elif type == CONJ_3A:
        stem = pres1sg[:-1]
        long0 = u'e'
        long = u'i'
        short = u'u'
    elif type == CONJ_3B:
        stem = pres1sg[:-2]
        long0 = u'e'
        long = u'i'
        short = u'iu'
    elif type == CONJ_4:
        stem = pres1sg[:-2]
        long = long0 = u'ī'
        short = u'iu'

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, long0, None,
                        None, long  + u'te',  None])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}),
                       [None, long0 + u're',  None,
                        None, long  + u'minī', None])

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, long + u'tō',   long  + u'tō',
                        None, long + u'tōte', short + u'ntō'])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}),
                       [None, long + u'tor',  long + u'tor',
                        None, None,           short + u'ntor'])

    return items


# 未完了
def conjugate_imperfect(type, pres1sg, tags={}):
    if type == CONJ_1:
        stem = pres1sg[:-1] + u'ā'
    elif type == CONJ_2:
        stem = pres1sg[:-2] + u'ē'
    elif type == CONJ_3A:
        stem = pres1sg[:-1] + u'ē'
    elif type == CONJ_3B:
        stem = pres1sg[:-2] + u'iē'
    elif type == CONJ_4:
        stem = pres1sg[:-2] + u'iē'

    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}),
                     [u'bam', u'bās', u'bat', u'bāmus', u'bātis', u'bant']) + \
           conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'imperfect'}),
                     [u'bar', (u'bāris', u'bāre'), u'bātur', u'bāmur', u'bāminī', u'bantur'])

# 未来
def conjugate_future(type, pres1sg, tags={}):
    if type == CONJ_1:
        pres_stem = pres1sg[:-1] + u'ā'
    elif type == CONJ_2:
        pres_stem = pres1sg[:-2] + u'ē'
    elif type == CONJ_3A:
        pres_stem = pres1sg[:-1] + u'ē'
    elif type == CONJ_3B:
        pres_stem = pres1sg[:-2] + u'iē'
    elif type == CONJ_4:
        pres_stem = pres1sg[:-2] + u'iē'

    items = []
    if type in [CONJ_1, CONJ_2]:
        items += conjugate(pres_stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                           [u'bō', u'bis', u'bit', u'bimus', u'bitis', u'bunt'])
        items += conjugate(pres_stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}),
                           [u'bor', (u'beris', u'bere'), u'bitur', u'bimur', u'biminī', u'buntur'])
    else:
        stem = pres_stem[:-1]
        items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                           [u'am', u'ēs', u'et', u'ēmus', u'ētis', u'ent'])
        items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}),
                           [u'ar', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur'])
    # util.pp(items)
    return items


# 完了
def conjugate_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'perfect'}),
                     [u'ī', u'istī', u'it', u'imus', u'istis', (u'ērunt', u'ēre')])

# 過去完了
def conjugate_past_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'past-perfect'}),
                     [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erānt'])

# 未来完了
def conjugate_future_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future-perfect'}),
                     [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erint'])


# 受動 完了
def conjugate_passive_perfect_(supinum, sum, tags={}):
    stem = supinum[:-2]

    items = []
    for gender, suffix in {'m':u'us', 'f':u'a', 'n':u'um'}.items():
        for person in [1,2,3]:
            surface = stem + suffix + u' ' + sum[person-1]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'sg'}
            items.append( util.aggregate_dicts(info, tags) )

    for gender, suffix in {'m':u'ī', 'f':u'ae', 'n':u'a'}.items():
        for person in [1,2,3]:
            surface = stem + suffix + u' ' + sum[2+person]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'pl'}
            items.append( util.aggregate_dicts(info, tags) )

    # util.pp(items)
    return items

def conjugate_passive_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'perfect'}))

def conjugate_passive_past_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'past-perfect'}))

def conjugate_passive_future_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erunt'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future-perfect'}))


def conjugate_subjunctive_active_present(type, pres1sg, tags={}):
    stem = pres1sg[:-1]
    if type == CONJ_1:
        suffices = [u'em', u'ēs', u'et', u'ēmus', u'ētis', u'ent']
    else:
        suffices = [u'am', u'ās', u'at', u'āmus', u'ātis', u'ant']

    items = []
    items += conjugate(stem,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'present'}),
                       suffices)
    return items

def conjugate_subjunctive_passive_present(type, pres1sg, tags={}):
    stem = pres1sg[:-1]
    if type == CONJ_1:
        suffices = [u'er', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur']
    else:
        suffices = [u'ar', (u'āris', u'āre'), u'ātur', u'āmur', u'āminī', u'antur']

    return conjugate(stem,
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'present'}),
                     suffices)
    return items


def conjugate_subjunctive_active_imperfect(inf, tags={}):
    return conjugate(inf[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'imperfect'}),
                     [u'em', u'ēs', u'et', u'ēmus', u'ētis', u'ent'])

def conjugate_subjunctive_passive_imperfect(inf, tags={}):
    return conjugate(inf[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'imperfect'}),
                     [u'er', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur'])


def conjugate_subjunctive_active_perfect(perf1sg, tags={}):
    return conjugate(perf1sg[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'}),
                     [u'erim', u'eris', u'erit', u'erimus', u'eritis', u'erint'])

def conjugate_subjunctive_active_past_perfect(perf1sg, tags={}):
    return conjugate(perf1sg[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'}),
                     [u'issem', u'issēs', u'isset', u'issēmus', u'issētis', u'issent'])

# 受動 完了
def conjugate_subjunctive_passive_perfect_(supinum, sum, tags={}):
    stem = supinum[:-2]

    items = []
    for gender, suffix in {'m':u'us', 'f':u'a', 'n':u'um'}.items():
        for person in [1,2,3]:
            surface = stem + suffix + u' ' + sum[person-1]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'sg'}
            items.append( util.aggregate_dicts(info, tags) )

    for gender, suffix in {'m':u'ī', 'f':u'ae', 'n':u'a'}.items():
        for person in [1,2,3]:
            surface = stem + suffix + u' ' + sum[2+person]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'pl'}
            items.append( util.aggregate_dicts(info, tags) )

    # util.pp(items)
    return items

def conjugate_subjunctive_passive_perfect(supinum, tags={}):
    return conjugate_subjunctive_passive_perfect_(supinum,
                                                  [u'sim', u'sīs', u'sit', u'sīmus', u'sītis', u'sint'],
                                                  util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'perfect'}))

def conjugate_subjunctive_passive_past_perfect(supinum, tags={}):
    return conjugate_subjunctive_passive_perfect_(supinum,
                                                  [u'essem', u'essēs', u'esset', u'essēmus', u'essētis', u'essent'],
                                                  util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'past-perfect'}))


def conjugate_subjunctive(type, pres1sg, perf1sg, supinum, inf, tags={}):
    items = []

    items += conjugate_subjunctive_active_present(type, pres1sg, tags)
    items += conjugate_subjunctive_passive_present(type, pres1sg, tags)
    items += conjugate_subjunctive_active_imperfect(inf, tags)
    items += conjugate_subjunctive_passive_imperfect(inf, tags)

    items += conjugate_subjunctive_active_perfect(perf1sg, tags)
    items += conjugate_subjunctive_passive_perfect(supinum, tags)
    items += conjugate_subjunctive_active_past_perfect(perf1sg, tags)
    items += conjugate_subjunctive_passive_past_perfect(supinum, tags)

    return items


# 受動分詞と動名詞
def conjugate_gerundive(type, pres1sg, tags={}):
    if type in [CONJ_1, CONJ_3A]:
        stem = pres1sg[:-1]
    else:
        stem = pres1sg[:-2]

    return conjugate(stem + u'and',
                     util.aggregate_dicts({'pos':'gerundive'}, tags),
                     [u'us', u'a', u'um'],
                     [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])

def conjugate_gerund(type, pres1sg, tags={}):
    if type in [CONJ_1, CONJ_3A]:
        stem = pres1sg[:-1]
    else:
        stem = pres1sg[:-2]

    return conjugate(stem + u'and',
                     util.aggregate_dicts({'pos':'gerund'}, tags),
                     [u'um', u'ī'],
                     [{'case':'Acc'}, {'case':'Gen'}])

# 不定形
def conjugate_infinitive(type, inf, perf1sg, supinum, ja='', tags={}):
    if type in [CONJ_3A, CONJ_3B]:
        # regere -> regī
        # capere -> capī
        passive_inf = inf[:-3] + u'ī'
    else:
        # amAre -> amārī
        passive_inf = inf[:-1] + u'ī'

    common_tags = {'mood':'infinitive', 'ja':ja}

    pf_stem = perf1sg[:-1]
    pp_stem = supinum[:-2]

    items = []

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'present'}, tags),
                       [inf], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'perfect'}, tags),
                       [u'isse'], [{}])
    items += conjugate(pp_stem, util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'future'}, tags),
                       [u'ūrus esse', u'ūra esse', u'ūrum esse'],
                       [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'present'}, tags),
                       [passive_inf], [{}])
    items += conjugate(pp_stem, util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'perfect'}, tags),
                       [u'us esse', u'a esse', u'um esse'],
                       [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'future'}, tags),
                       [supinum + u' īrī'], [{}])

    return items

# 分詞
def conjugate_participle(pres_stem, supinum, tags={}):
    items = []

    ja = tags.get('ja', '')

    # 現在分詞
    # prūdēns型; 〜しつつある
    nom_sg_m = pres_stem + u'ns'
    if pres_stem[-1] == u'ā':
        gen_sg = pres_stem[:-1] + u'antis'
    elif pres_stem == u'iē':
        gen_sg = u'euntis'
    else: # pres_stem[-1] = 'ē'
        gen_sg = pres_stem[:-1] + u'entis'
    items += latin_adj.decline_adj_type2(nom_sg_m, gen_sg, '-',
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'present',
                                                                     'ja':ja+'+しつつある'}))
    # 未来分詞
    if supinum == 'es##':
        nom_sg_m = supinum[:-2] + u'urus'
    else:
        nom_sg_m = supinum[:-2] + u'ūrus'
    nom_sg_f = nom_sg_m[:-2] + u'a'
    items += latin_adj.decline_adj_type1(nom_sg_m, nom_sg_f,
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'future',
                                                                     'ja':ja+'+しようとしている'}))

    # 完了分詞
    nom_sg_m = supinum[:-2] + u'us'
    nom_sg_f = nom_sg_m[:-2] + u'a'
    items += latin_adj.decline_adj_type1(nom_sg_m, nom_sg_f,
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'past',
                                                                     'ja':ja+'+された'}))

    return util.aggregate_cases(items)


#
# 規則変化動詞
#
def conjugate_regular_verb(type, pres1sg, perf1sg, supinum, inf, ja, tags):
    if type == CONJ_1: # amō, amāvī, amātum, amāre; amā-
        stem = pres1sg[:-1] # am-
        pres_stem = stem + u'ā'
    elif type == CONJ_2: # moneō, monuī, monitum, monēre
        stem = pres1sg[:-2] # mon-
        pres_stem = stem + u'ē'
    elif type == CONJ_3A: # regō, rēxī, rēctum, regere
        stem = pres1sg[:-1] # reg-
        pres_stem = stem + u'ē'
    elif type == CONJ_3B: # capiō, cēpī, captum, capere
        stem = pres1sg[:-2] # cap-
        pres_stem = stem + u'iē'
    elif type == CONJ_4: # audiō, audīvī, audītum, audīre
        stem = pres1sg[:-2] # aud-
        pres_stem = stem + u'iē'

    items = []
    items += conjugate_infinitive(type, inf, perf1sg, supinum, ja, tags)

    # 現在
    items += conjugate_present(type, pres1sg, tags)

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 未完了
    items += conjugate_imperfect(type, pres1sg, tags)

    # 未来
    items += conjugate_future(type, pres1sg, tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 接続法
    items += conjugate_subjunctive(type, pres1sg, perf1sg, supinum, inf, tags)

    # 命令法
    items += conjugate_imperative(type, pres1sg, tags)

    # 分詞
    items += conjugate_participle(pres_stem, supinum, tags)

    return items


def load_verbs(file):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) < 3: continue

            type = fs[0]
            if len(fs) == 6:
                pres1sg = fs[1].decode('utf-8')
                inf     = fs[2].decode('utf-8')
                perf1sg = fs[3].decode('utf-8')
                supinum = fs[4].decode('utf-8')
                ja      = fs[5]
            elif len(fs) == 3:
                pres1sg = fs[1].decode('utf-8')
                perf1sg = supinum = inf = None
                ja      = fs[2]

            tags = {'pos':'verb', 'pres1sg':pres1sg, 'ja':ja, 'type':type}

            if type == CONJ_1:
                stem = pres1sg[:-1]
                if perf1sg is None: perf1sg = stem + u'āvī'
                if supinum is None: supinum = stem + u'ātum'
                if inf is None: inf = stem + u'āre'

            table = conjugate_regular_verb(type, pres1sg, perf1sg, supinum, inf, ja, tags)

            if len(table) == 0: continue

            items += table

    return items


def load():
    return load_verbs('words/verb.def')


if __name__ == '__main__':
    load()
#    latindic.dump()
