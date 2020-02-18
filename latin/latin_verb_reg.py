#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import util

from . import latin_adj
from . import latin_pronoun
from japanese import JaVerb
import Verb

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
def conjugate_present(conj_type, pres1sg, tags={}):
    items = []
    if conj_type == CONJ_1:
        stem = pres1sg[:-1]
        x = ''
        long = y = 'ā'
        short = nt = 'a'
    elif conj_type == CONJ_2:
        stem = pres1sg[:-2]
        x = 'e'
        long = y = 'ē'
        short = nt = 'e'
    elif conj_type == CONJ_3A:
        stem = pres1sg[:-1]
        x = ''
        y = 'e'
        long = short = 'i'
        nt = 'u'
    elif conj_type == CONJ_3B:
        stem = pres1sg[:-2]
        x = 'i'
        y = 'e'
        long = short = 'i'
        nt = 'iu'
    elif conj_type == CONJ_4:
        stem = pres1sg[:-2]
        x = 'i'
        long = y = 'ī'
        short = 'i'
        nt = 'iu'

    # x: -ō
    # long: A(ri)
    # short: a(tur), a(ntur)
    active_present_suffices = [x + 'ō', long + 's', short + 't',
                               long + 'mus', long + 'tis', nt + 'nt']
    passive_present_suffices = [x + 'or', (y + 'ris', y + 're'), long + 'tur',
                                long + 'mur', long + 'minī', nt + 'ntur']

    items += conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       active_present_suffices)
    items += conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'present'}),
                       passive_present_suffices)
    return items


## 命令
def conjugate_imperative(conj_type, pres1sg, tags={}):
    items = []

    if conj_type == CONJ_1:
        stem = pres1sg[:-1]
        long = long0 = 'ā'
        short = 'a'
    elif conj_type == CONJ_2:
        stem = pres1sg[:-2]
        long = long0 = 'ē'
        short = 'e'
    elif conj_type == CONJ_3A:
        stem = pres1sg[:-1]
        long0 = 'e'
        long = 'i'
        short = 'u'
    elif conj_type == CONJ_3B:
        stem = pres1sg[:-2]
        long0 = 'e'
        long = 'i'
        short = 'iu'
    elif conj_type == CONJ_4:
        stem = pres1sg[:-2]
        long = long0 = 'ī'
        short = 'iu'

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, long0, None,
                        None, long + 'te',  None])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}),
                       [None, long0 + 're',  None,
                        None, long + 'minī', None])

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, long + 'tō',   long + 'tō',
                        None, long + 'tōte', short + 'ntō'])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}),
                       [None, long + 'tor',  long + 'tor',
                        None, None,           short + 'ntor'])

    return items


# 未完了
def conjugate_imperfect(conj_type, pres1sg, tags={}):
    if conj_type == CONJ_1:
        stem = pres1sg[:-1] + 'ā'
    elif conj_type == CONJ_2:
        stem = pres1sg[:-2] + 'ē'
    elif conj_type == CONJ_3A:
        stem = pres1sg[:-1] + 'ē'
    elif conj_type == CONJ_3B:
        stem = pres1sg[:-2] + 'iē'
    elif conj_type == CONJ_4:
        stem = pres1sg[:-2] + 'iē'

    return conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                     ['bam', 'bās', 'bat', 'bāmus', 'bātis', 'bant']) + \
           conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'imperfect'}),
                     ['bar', ('bāris', 'bāre'), 'bātur', 'bāmur', 'bāminī', 'bantur'])

# 未来
def conjugate_future(conj_type, pres1sg, tags={}):
    if conj_type == CONJ_1:
        pres_stem = pres1sg[:-1] + 'ā'
    elif conj_type == CONJ_2:
        pres_stem = pres1sg[:-2] + 'ē'
    elif conj_type == CONJ_3A:
        pres_stem = pres1sg[:-1] + 'ē'
    elif conj_type == CONJ_3B:
        pres_stem = pres1sg[:-2] + 'iē'
    elif conj_type == CONJ_4:
        pres_stem = pres1sg[:-2] + 'iē'

    items = []
    if conj_type in [CONJ_1, CONJ_2]:
        items += conjugate(pres_stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                           ['bō', 'bis', 'bit', 'bimus', 'bitis', 'bunt'])
        items += conjugate(pres_stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'future'}),
                           ['bor', ('beris', 'bere'), 'bitur', 'bimur', 'biminī', 'buntur'])
    else:
        stem = pres_stem[:-1]
        items += conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                           ['am', 'ēs', 'et', 'ēmus', 'ētis', 'ent'])
        items += conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'future'}),
                           ['ar', ('ēris', 'ēre'), 'ētur', 'ēmur', 'ēminī', 'entur'])
    # util.pp(items)
    return items


# 完了
def conjugate_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'perfect'}),
                     ['ī', 'istī', 'it', 'imus', 'istis', ('ērunt', 'ēre')])

# 過去完了
def conjugate_past_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'past-perfect'}),
                     ['eram', 'erās', 'erat', 'erāmus', 'erātis', 'erant'])

# 未来完了
def conjugate_future_perfect(perf1sg, tags={}):
    stem = perf1sg[:-1]
    return conjugate(stem, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future-perfect'}),
                     ['erō', 'eris', 'erit', 'erimus', 'eritis', 'erint'])


# 受動 完了
def conjugate_passive_perfect_(supinum, sum, tags={}):
    stem = supinum[:-2]

    items = []
    for gender, suffix in list({'m':'us', 'f':'a', 'n':'um'}.items()):
        for person in [1,2,3]:
            surface = stem + suffix + ' ' + sum[person-1]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'sg'}
            items.append( util.aggregate_dicts(info, tags) )

    for gender, suffix in list({'m':'ī', 'f':'ae', 'n':'a'}.items()):
        for person in [1,2,3]:
            surface = stem + suffix + ' ' + sum[2+person]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'pl'}
            items.append( util.aggregate_dicts(info, tags) )

    # util.pp(items)
    return items

def conjugate_passive_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      ['sum', 'es', 'est', 'sumus', 'estis', 'sunt'],
                                      util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'perfect'}))

def conjugate_passive_past_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      ['eram', 'erās', 'erat', 'erāmus', 'erātis', 'erant'],
                                      util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'past-perfect'}))

def conjugate_passive_future_perfect(supinum, tags={}):
    return conjugate_passive_perfect_(supinum,
                                      ['erō', 'eris', 'erit', 'erimus', 'eritis', 'erunt'],
                                      util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'future-perfect'}))


def conjugate_subjunctive_active_present(conj_type, pres1sg, tags={}):
    stem = pres1sg[:-1]
    if conj_type == CONJ_1:
        suffices = ['em', 'ēs', 'et', 'ēmus', 'ētis', 'ent']
    else:
        suffices = ['am', 'ās', 'at', 'āmus', 'ātis', 'ant']

    items = []
    items += conjugate(stem,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'present'}),
                       suffices)
    return items

def conjugate_subjunctive_passive_present(conj_type, pres1sg, tags={}):
    stem = pres1sg[:-1]
    if conj_type == CONJ_1:
        suffices = ['er', ('ēris', 'ēre'), 'ētur', 'ēmur', 'ēminī', 'entur']
    else:
        suffices = ['ar', ('āris', 'āre'), 'ātur', 'āmur', 'āminī', 'antur']

    return conjugate(stem,
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'present'}),
                     suffices)
    return items


def conjugate_subjunctive_active_imperfect(inf, tags={}):
    return conjugate(inf[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'imperfect'}),
                     ['em', 'ēs', 'et', 'ēmus', 'ētis', 'ent'])

def conjugate_subjunctive_passive_imperfect(inf, tags={}):
    return conjugate(inf[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'imperfect'}),
                     ['er', ('ēris', 'ēre'), 'ētur', 'ēmur', 'ēminī', 'entur'])


def conjugate_subjunctive_active_perfect(perf1sg, tags={}):
    return conjugate(perf1sg[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'}),
                     ['erim', 'eris', 'erit', 'erimus', 'eritis', 'erint'])

def conjugate_subjunctive_active_past_perfect(perf1sg, tags={}):
    return conjugate(perf1sg[:-1],
                     util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'}),
                     ['issem', 'issēs', 'isset', 'issēmus', 'issētis', 'issent'])

# 受動 完了
def conjugate_subjunctive_passive_perfect_(supinum, sum, tags={}):
    stem = supinum[:-2]

    items = []
    for gender, suffix in list({'m':'us', 'f':'a', 'n':'um'}.items()):
        for person in [1,2,3]:
            surface = stem + suffix + ' ' + sum[person-1]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'sg'}
            items.append( util.aggregate_dicts(info, tags) )

    for gender, suffix in list({'m':'ī', 'f':'ae', 'n':'a'}.items()):
        for person in [1,2,3]:
            surface = stem + suffix + ' ' + sum[2+person]
            info = {'surface':surface, 'gender':gender, 'person':person, 'number':'pl'}
            items.append( util.aggregate_dicts(info, tags) )

    # util.pp(items)
    return items

def conjugate_subjunctive_passive_perfect(supinum, tags={}):
    return conjugate_subjunctive_passive_perfect_(supinum,
                                                  ['sim', 'sīs', 'sit', 'sīmus', 'sītis', 'sint'],
                                                  util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'perfect'}))

def conjugate_subjunctive_passive_past_perfect(supinum, tags={}):
    return conjugate_subjunctive_passive_perfect_(supinum,
                                                  ['essem', 'essēs', 'esset', 'essēmus', 'essētis', 'essent'],
                                                  util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'passive', 'tense':'past-perfect'}))


def conjugate_subjunctive(conj_type, pres1sg, perf1sg, supinum, inf, tags={}):
    items = []

    items += conjugate_subjunctive_active_present(conj_type, pres1sg, tags)
    items += conjugate_subjunctive_passive_present(conj_type, pres1sg, tags)
    items += conjugate_subjunctive_active_imperfect(inf, tags)
    items += conjugate_subjunctive_passive_imperfect(inf, tags)

    items += conjugate_subjunctive_active_perfect(perf1sg, tags)
    items += conjugate_subjunctive_passive_perfect(supinum, tags)
    items += conjugate_subjunctive_active_past_perfect(perf1sg, tags)
    items += conjugate_subjunctive_passive_past_perfect(supinum, tags)

    return items


# 受動分詞と動名詞
def conjugate_gerundive(conj_type, pres1sg, tags={}):
    if conj_type in [CONJ_1, CONJ_3A]:
        stem = pres1sg[:-1]
    else:
        stem = pres1sg[:-2]

    return conjugate(stem + 'and',
                     util.aggregate_dicts({'pos':'gerundive'}, tags),
                     ['us', 'a', 'um'],
                     [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])

def conjugate_gerund(conj_type, pres1sg, tags={}):
    if conj_type in [CONJ_1, CONJ_3A]:
        stem = pres1sg[:-1]
    else:
        stem = pres1sg[:-2]

    return conjugate(stem + 'and',
                     util.aggregate_dicts({'pos':'gerund'}, tags),
                     ['um', 'ī'],
                     [{'case':'Acc'}, {'case':'Gen'}])

# 不定形
def conjugate_infinitive(conj_type, inf, perf1sg, supinum, ja='', tags={}):
    if conj_type in [CONJ_3A, CONJ_3B]:
        # regere -> regī
        # capere -> capī
        passive_inf = inf[:-3] + 'ī'
    else:
        # amAre -> amārī
        passive_inf = inf[:-1] + 'ī'

    common_tags = {'mood':'infinitive', 'ja':ja}

    pf_stem = perf1sg[:-1]
    pp_stem = supinum[:-2]

    items = []

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'present'}, tags),
                       [inf], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'perfect'}, tags),
                       ['isse'], [{}])
    items += conjugate(pp_stem, util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'future'}, tags),
                       ['ūrus esse', 'ūra esse', 'ūrum esse'],
                       [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'present'}, tags),
                       [passive_inf], [{}])
    items += conjugate(pp_stem, util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'perfect'}, tags),
                       ['us esse', 'a esse', 'um esse'],
                       [{'gender':'m'}, {'gender':'f'}, {'gender':'n'}])
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'future'}, tags),
                       [supinum + ' īrī'], [{}])

    return items

# 分詞
def conjugate_participle(pres_stem, supinum, tags={}):
    items = []

    jas = tags.get('ja', '').split(',')
    javs = list(map(JaVerb, jas))
    def forms(flag):
        return ','.join([jav.form(flag) for jav in javs])

    # 現在分詞
    # prūdēns型; 〜しつつある
    nom_sg_m = pres_stem + 'ns'
    if pres_stem[-1] == 'ā':
        gen_sg = pres_stem[:-1] + 'antis'
    elif pres_stem == 'iē':
        gen_sg = 'euntis'
    else: # pres_stem[-1] = 'ē'
        gen_sg = pres_stem[:-1] + 'entis'
    items += latin_adj.decline_adj_type2(nom_sg_m, gen_sg, '-',
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'present',
                                                                     'ja':forms(Verb.PARTICIPLE_PRESENT)}))
    # 未来分詞
    if supinum == 'es##':
        nom_sg_m = supinum[:-2] + 'urus'
    else:
        nom_sg_m = supinum[:-2] + 'ūrus'
    nom_sg_f = nom_sg_m[:-2] + 'a'
    items += latin_adj.decline_adj_type1(nom_sg_m, nom_sg_f,
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'future',
                                                                     'ja':forms(Verb.PARTICIPLE_FUTURE)}))

    # 完了分詞
    nom_sg_m = supinum[:-2] + 'us'
    nom_sg_f = nom_sg_m[:-2] + 'a'
    items += latin_adj.decline_adj_type1(nom_sg_m, nom_sg_f,
                                         util.aggregate_dicts(tags, {'pos':'participle', 'tense':'past',
                                                                     'ja':forms(Verb.PARTICIPLE_PERFECT)}))

    return util.aggregate_cases(items)


#
# 規則変化動詞
#
def conjugate_regular_verb(conj_type, pres1sg, perf1sg, supinum, inf, ja, tags):
    if conj_type == CONJ_1: # amō, amāvī, amātum, amāre; amā-
        stem = pres1sg[:-1] # am-
        pres_stem = stem + 'ā'
    elif conj_type == CONJ_2: # moneō, monuī, monitum, monēre
        stem = pres1sg[:-2] # mon-
        pres_stem = stem + 'ē'
    elif conj_type == CONJ_3A: # regō, rēxī, rēctum, regere
        stem = pres1sg[:-1] # reg-
        pres_stem = stem + 'ē'
    elif conj_type == CONJ_3B: # capiō, cēpī, captum, capere
        stem = pres1sg[:-2] # cap-
        pres_stem = stem + 'iē'
    elif conj_type == CONJ_4: # audiō, audīvī, audītum, audīre
        stem = pres1sg[:-2] # aud-
        pres_stem = stem + 'iē'

    items = []
    items += conjugate_infinitive(conj_type, inf, perf1sg, supinum, ja, tags)

    # 現在
    items += conjugate_present(conj_type, pres1sg, tags)

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 未完了
    items += conjugate_imperfect(conj_type, pres1sg, tags)

    # 未来
    items += conjugate_future(conj_type, pres1sg, tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 接続法
    items += conjugate_subjunctive(conj_type, pres1sg, perf1sg, supinum, inf, tags)

    # 命令法
    items += conjugate_imperative(conj_type, pres1sg, tags)

    # 分詞
    items += conjugate_participle(pres_stem, supinum, tags)

    return items


def load_a_verb(line):
    fs = line.split()
    if len(fs) < 3: return None

    conj_type = fs[0]
    if len(fs) == 6:
        pres1sg = fs[1] #.decode('utf-8')
        inf     = fs[2] #.decode('utf-8')
        perf1sg = fs[3] #.decode('utf-8')
        supinum = fs[4] #.decode('utf-8')
        ja      = fs[5]
    elif len(fs) == 3:
        pres1sg = fs[1] #.decode('utf-8')
        perf1sg = supinum = inf = None
        ja      = fs[2]

    tags = {'pos':'verb', 'pres1sg':pres1sg, 'ja':ja, 'type':type}

    if conj_type == CONJ_1:
        stem = pres1sg[:-1]
        if perf1sg is None: perf1sg = stem + 'āvī'
        if supinum is None: supinum = stem + 'ātum'
        if inf is None: inf = stem + 'āre'

    table = conjugate_regular_verb(conj_type, pres1sg, perf1sg, supinum, inf, ja, tags)

    if len(table) == 0: return None

    return table


def load_verbs(file):
    items = []

    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            table = load_a_verb(line.rstrip())
            if table:
                items += table

    return items


def load():
    return load_verbs('words/verb.def')


if __name__ == '__main__':
    load()
