#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
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


# 完了
def conjugate_perfect(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'perfect'}),
                     [u'ī', u'istī', u'it', u'imus', u'istis', (u'ērunt', u'ēre')])

# 過去完了
def conjugate_past_perfect(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'past-perfect'}),
                     [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erānt'])
# 未来完了
def conjugate_future_perfect(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future-perfect'}),
                     [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erint'])

# 未完了
def conjugate_imperfect(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}),
                     [u'bam', u'bās', u'bat', u'bāmus', u'bātis', u'bant']) + \
           conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'imperfect'}),
                     [u'bar', (u'bāris', u'bāre'), u'bātur', u'bāmur', u'bāminī', u'bantur'])

# 未来
def conjugate_future_12(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                     [u'bō', u'bis', u'bit', u'bimus', u'bitis', u'bunt']) + \
           conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}),
                     [u'bor', (u'beris', u'bere'), u'bitur', u'bimur', u'biminī', u'buntur'])
def conjugate_future_34(stem, tags):
    return conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                     [u'am', u'ēs', u'et', u'ēmus', u'ētis', u'ent']) + \
           conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}),
                     [u'ar', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur'])

# 受動 完了
def conjugate_passive_perfect_(stem, sum, tags):
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

    return items

def conjugate_passive_perfect(supinum, tags):
    return conjugate_passive_perfect_(supinum[:-2],
                                      [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'perfect'}))

def conjugate_passive_past_perfect(supinum, tags):
    return conjugate_passive_perfect_(supinum[:-2],
                                      [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'past-perfect'}))

def conjugate_passive_future_perfect(supinum, tags):
    return conjugate_passive_perfect_(supinum[:-2],
                                      [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erunt'],
                                      util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future-perfect'}))

# 不定形
def conjugate_infinitive(inf, pf_stem, supinum, ja, tags, typeIII=False):
    if typeIII:
        # regere -> regī
        # capere -> capī
        passive_inf = inf[:-3] + u'ī'
    else:
        # amAre -> amārī
        passive_inf = inf[:-1] + u'ī'

    common_tags = {'mood':'infinitive', 'ja':ja}

    items = []
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'present'}, tags),
                       [inf], [{}])
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'present'}, tags),
                       [passive_inf], [{}])

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'perfect'}, tags),
                       [pf_stem + u'isse'], [{}])
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'perfect'}, tags),
                       [supinum[:-2] + u'us esse'], [{}])

    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'future'}, tags),
                       [supinum[:-2] + u'ūrus esse'], [{}])
    items += conjugate('', util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'future'}, tags),
                       [supinum + u' īrī'], [{}])

    return items

# 分詞
def conjugate_participle(pres_stem, supinum, tags):
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

    return items

#####
def conjugate_verb_eo(prefix=u'', ja=''):
    tags = {'pos':'verb', 'ja':ja}

    inf = u'īre'
    # pres_stem = u''
    # pf_stem = u''
    # īvī iī
    # itum
    items = []
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}),
                       [u'eō', u'īs', u'it', u'īmus', u'ītis', u'eunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}),
                       [u'ībam', u'ībās', u'ībat', u'ībāmus', u'ībātis', u'ībant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                       [u'ībō', u'ībis', u'ībit', u'ībimus', u'ībitis', u'ībunt'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, u'ī', None, None, u'īte', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, u'ītō', u'ītō', None, u'ītōte', u'euntō'])

    # 分詞
    items += conjugate_participle(u'iē', u'itum', tags) # no supinum for 'sum'

    # print "(eo)", util.render(items)
    return items


def conjugate_verb_sum(prefix=u'', ja=''):
    tags = {'pos':'verb', 'ja':ja}

    inf = prefix + u'esse'
    pres_stem = prefix + u'et'
    pf_stem = prefix + u'fu'

    items = []
    items += conjugate('', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [inf], [{}])
    items += conjugate('', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [pf_stem + u'isse'], [{}])
    items += conjugate('', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [pf_stem + u'tūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}),
                       [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}),
                       [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                       [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erunt'])

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, u'es', None, None, u'este', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, u'estō', u'estō', None, u'estōte', u'suntō'])

    # 分詞
    items += conjugate_participle(u'sē', u'es##', tags) # no supinum for 'sum'

    # print "(sum)", util.render(items)
    return items


def conjugate_imperative(type, stem, tags):
    items = []

    if type == CONJ_1:
        long = long0 = u'ā'
        short = u'a'
    elif type == CONJ_2:
        long = long0 = u'ē'
        short = u'e'
    elif type == CONJ_3A:
        long0 = u'e'
        long = u'i'
        short = u'u'
    elif type == CONJ_3B:
        long0 = u'e'
        long = u'i'
        short = u'iu'
    elif type == CONJ_4:
        long = long0 = u'ī'
        short = u'iu'

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, stem + long0, None,
                        None, stem + long  + u'te', None])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}),
                       [None, stem + long0 + u're', None,
                        None, stem + long  + u'minī', None])

    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, stem + long + u'tō',   stem + long  + u'tō',
                        None, stem + long + u'tōte', stem + short + u'ntō'])
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}),
                       [None, stem + long + u'tor', stem + long + u'tor',
                        None, None,                 stem + short + u'ntor'])

    return items


def conjugate_regular_verb(type, pres1sg, perf1sg, supinum, inf, ja, tags):
    if type == CONJ_1:
        # amō, amāvī, amātum, amāre; amā-
        stem = pres1sg[:-1] # am-
        pres_stem = stem + u'ā'

        active_present_suffices = [u'ō', u'ās', u'at', u'āmus', u'ātis', u'ant']
        passive_present_suffices = [u'or', (u'āris', u'āre'), u'ātur', u'āmur', u'āminī', u'antur']
    elif type == CONJ_2:
        # moneō, monuī, monitum, monēre
        stem = pres1sg[:-2] # mon-
        pres_stem = stem + u'ē'

        active_present_suffices = [u'eō', u'ēs', u'et', u'ēmus', u'ētis', u'ent']
        passive_present_suffices = [u'eor', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur']
    elif type == CONJ_3A:
        # regō, rēxī, rēctum, regere
        stem = pres1sg[:-1] # reg-
        pres_stem = stem + u'ē'

        active_present_suffices = [u'ō', u'is', u'it', u'imus', u'itis', u'unt']
        passive_present_suffices = [u'or', (u'eris', u'ere'), u'itur', u'imur', u'iminī', u'untur']
    elif type == CONJ_3B:
        # capiō, cēpī, captum, capere
        stem = pres1sg[:-2] # cap-
        pres_stem = stem + u'iē'

        active_present_suffices = [u'iō', u'is', u'it', u'imus', u'itis', u'iunt']
        passive_present_suffices = [u'ior', (u'eris', u'ere'), u'itur', u'imur', u'iminī', u'iuntur']
    elif type == CONJ_4:
        # audiō, audīvī, audītum, audīre
        stem = pres1sg[:-2] # aud-
        pres_stem = stem + u'iē'

        active_present_suffices = [u'iō', u'īs', u'īt', u'īmus', u'ītis', u'iunt']
        passive_present_suffices = [u'ior', (u'īris', u'īre'), u'ītur', u'īmur', u'īminī', u'iuntur']
    else:
        return []

    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags, typeIII=(type in [CONJ_3A, CONJ_3B]))

    # 現在
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}),
                       active_present_suffices)
    items += conjugate(stem, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}),
                       passive_present_suffices)

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)

    # 未完了
    items += conjugate_imperfect(pres_stem, tags)

    # 未来
    if type in [CONJ_1, CONJ_2]:
        items += conjugate_future_12(pres_stem[:-1], tags)
    else:
        items += conjugate_future_34(pres_stem[:-1], tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate_imperative(type, stem, tags)

    # 分詞
    items += conjugate_participle(pres_stem, supinum, tags)

    # print "(%s) %s" % (type, util.render(items))
    return items


def conjugate_verb_eo_composites():
    items = []
    items += conjugate_verb_eo(u'', '行く')
    items += conjugate_verb_eo(u'red', '戻る,帰る')

    latin.latindic_register_items(items)


def conjugate_verb_sum_composites():
    items = []
    items += conjugate_verb_sum(u'', '〜である')
    items += conjugate_verb_sum(u'ab', '不在である,離れている')
    items += conjugate_verb_sum(u'ad', '出席している,助力する')
    items += conjugate_verb_sum(u'dē', '欠けている,存在しない')
    items += conjugate_verb_sum(u'inter', '間にある,相違する')
    items += conjugate_verb_sum(u'ob', '妨げになる')
    items += conjugate_verb_sum(u'prae', '先頭に立つ')
    items += conjugate_verb_sum(u'pos', 'できる') # possum potuI posse
    items += conjugate_verb_sum(u'prō', '役に立つ') # prOsum prOfuI prOfutUrus prOdesse

    latin.latindic_register_items(items)


def load_verbs(file):
    with open(file, 'r') as fp:
        for line in fp:
            if len(line) == 0: continue
            if line[0] == '#': continue

            fs = line.rstrip().split()
            if len(fs) < 3: continue

            type = fs[0]
            pres1sg = fs[1].decode('utf-8')
            if len(fs) == 6:
                perf1sg = fs[2].decode('utf-8')
                supinum = fs[3].decode('utf-8')
                inf = fs[4].decode('utf-8')
                ja = fs[5]
            elif len(fs) == 3:
                perf1sg = supinum = inf = None
                ja = fs[2]

            tags = {'pos':'verb', 'pres1sg':pres1sg, 'ja':ja, 'type':type}

            if type == CONJ_1:
                stem = pres1sg[:-1]
                if perf1sg is None: perf1sg = stem + u'āvī'
                if supinum is None: supinum = stem + u'ātum'
                if inf is None: inf = stem + u'āre'

            table = conjugate_regular_verb(type, pres1sg, perf1sg, supinum, inf, ja, tags)

            if len(table) == 0: continue

#            # printing table
#            maxlen = max([len(item['surface']) for item in table])
#            casename = ['Nom','Voc','Acc','Gen','Dat','Abl']
#            for y in xrange(6):
#                line = u"%s: %-*s   %-*s" % (casename[y], maxlen, table[y]['surface'], maxlen, table[y+6]['surface'])
#                print line.encode('utf-8')
#            print

            latin.latindic_register_items(table)


def load():
    load_verbs('words/verb.def')

    conjugate_verb_sum_composites()
    # items += conjugate_irregular_verb(u'edō', '食べる') # edO EdI Esum edere/Esse
    # items += conjugate_irregular_verb(u'eō', '行く') # eO IvI/iI itum Ire
    # items += conjugate_irregular_verb(u'ferō', '運ぶ') # ferO tulI lAtum ferre
    # items += conjugate_irregular_verb(u'fīō', '成る,生ずる') # fIO factus sum, fierI
    # items += conjugate_irregular_verb(u'volō', '欲する') # volO voluI velle
    # items += conjugate_irregular_verb(u'mālō', 'むしろ〜を欲する') # mAlO mAluI mAlle
    # items += conjugate_irregular_verb(u'nōlō', '欲しない') # nOlO nOluI nOlle
    conjugate_verb_eo_composites()


if __name__ == '__main__':
    load()
    latin.latindic_dump()
