#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
import util

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


def flatten_1(items):
    res = []
    for item in items:
        if isinstance(item, list):
            res += item
        else:
            res.append(item)
    return res

def conjugate(stem, suffices, pn=persons_and_numbers, common_tags={}):
    def add_suffix(suffix, suffix_tags):
        if suffix is None:
            return []
        elif isinstance(suffix, tuple) or isinstance(suffix, list):
            return [util.aggregate_dicts({'surface':stem + suf_i}, suffix_tags, common_tags) for suf_i in suffix]
        else:
            surface = stem + suffix
            return util.aggregate_dicts({'surface':surface}, suffix_tags, common_tags)

    return flatten_1(map(add_suffix, suffices, pn))

# 完了
def conjugate_perfect(stem, tags):
    return conjugate(stem, [u'ī', u'istī', u'it', u'imus', u'istis', (u'ērunt', u'ēre')],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'perfect'}))
# 過去完了
def conjugate_past_perfect(stem, tags):
    return conjugate(stem, [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erānt'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'past-perfect'}))
# 未来完了
def conjugate_future_perfect(stem, tags):
    return conjugate(stem, [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erint'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future-perfect'}))

# 未完了
def conjugate_imperfect(stem, tags):
    return conjugate(stem, [u'bam', u'bās', u'bat', u'bāmus', u'bātis', u'bant'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'})) + \
           conjugate(stem, [u'bar', (u'bāris', u'bāre'), u'bātur', u'bāmur', u'bāminī', u'bantur'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'imperfect'}))
# 未来
def conjugate_future_12(stem, tags):
    return conjugate(stem, [u'bō', u'bis', u'bit', u'bimus', u'bitis', u'bunt'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'})) + \
           conjugate(stem, [u'bor', (u'beris', u'bere'), u'bitur', u'bimur', u'biminī', u'buntur'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}))
def conjugate_future_34(stem, tags):
    return conjugate(stem, [u'am', u'ēs', u'et', u'ēmus', u'ētis', u'ent'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'})) + \
           conjugate(stem, [u'ar', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur'],
                     common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future'}))


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
    items += conjugate('', [inf], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'present'}, tags))
    items += conjugate('', [passive_inf], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'present'}, tags))

    items += conjugate('', [pf_stem + u'isse'], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'perfect'}, tags))
    items += conjugate('', [supinum[:-2] + u'us esse'], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'perfect'}, tags))

    items += conjugate('', [supinum[:-2] + u'ūrus esse'], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'active', 'tense':'future'}, tags))
    items += conjugate('', [supinum + u' īrī'], [{}],
                       util.aggregate_dicts(common_tags, {'voice':'passive', 'tense':'future'}, tags))

    return items

#####
def conjugate_verb_sum(prefix, ja):
    tags = {'pos':'verb', 'ja':ja}

    inf = prefix + u'esse'
    pf_stem = prefix + u'fu'

    items = []
    items += conjugate('', [inf], [{}], util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}))
    items += conjugate('', [pf_stem + u'isse'], [{}], util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}))
    items += conjugate('', [pf_stem + u'tūrus esse'], [{}], util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}))

    # 能動態 現在・過去・未来
    items += conjugate(prefix, [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(prefix, [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}))
    items += conjugate(prefix, [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erunt'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}))

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)

    # 命令形
    items += conjugate(prefix, [None, u'es', None, None, u'este', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(prefix, [None, u'estō', u'estō', None, u'estōte', u'suntō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    # print "(sum)", util.render(items)
    return items


def conjugate_verb_type1(pres1sg, perf1sg, supinum, inf, ja, tags):
    # amō, amāvī, amātum, amāre; amā-
    stem = pres1sg[:-1] # am-
    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags)

    # 現在
    items += conjugate(stem, [u'ō', u'ās', u'at', u'āmus', u'ātis', u'ant'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(stem, [u'or', (u'āris', u'āre'), u'ātur', u'āmur', u'āminī', u'antur'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}))
    # 受動2sgで āris の代わりに āre (=? inf) とするのは何

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)
    # 未完了
    items += conjugate_imperfect(stem + u'ā', tags)
    # 未来
    items += conjugate_future_12(stem + u'ā', tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate(stem, [None, u'ā', None, None, u'āte', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ātō', u'ātō', None, u'ātōte', u'antō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    items += conjugate(stem, [None, u'āre', None, None, u'āminī', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ātor', u'ātor', None, None, u'antor'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}))

    # print "(1)", util.render(items)
    return items


def conjugate_verb_type2(pres1sg, perf1sg, supinum, inf, ja, tags):
    # moneō, monuī, monitum, monēre
    stem = pres1sg[:-2] # mon-
    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags)

    # 現在
    items += conjugate(stem, [u'eō', u'ēs', u'et', u'ēmus', u'ētis', u'ent'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(stem, [u'eor', (u'ēris', u'ēre'), u'ētur', u'ēmur', u'ēminī', u'entur'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}))

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)
    # 未完了
    items += conjugate_imperfect(stem + u'ē', tags)
    # 未来
    items += conjugate_future_12(stem + u'ē', tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate(stem, [None, u'ē', None, None, u'ēte', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ētō', u'ētō', None, u'ētōte', u'entō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    items += conjugate(stem, [None, u'ēre', None, None, u'ēminī', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ētor', u'ētor', None, None, u'entor'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}))

    # print "(2)", util.render(items)
    return items


def conjugate_verb_type3A(pres1sg, perf1sg, supinum, inf, ja, tags):
    # regō, rēxī, rēctum, regere
    stem = pres1sg[:-1] # reg-
    pf_stem = perf1sg[:-1] # rēx-

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags, typeIII=True)

    # 現在
    items += conjugate(stem, [u'ō', u'is', u'it', u'imus', u'itis', u'unt'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(stem, [u'or', (u'eris', u'ere'), u'itur', u'imur', u'iminī', u'untur'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}))

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)
    # 未完了
    items += conjugate_imperfect(stem + u'ē', tags)
    # 未来
    items += conjugate_future_34(stem, tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate(stem, [None, u'e', None, None, u'ite', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'itō', u'itō', None, u'itōte', u'untō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    items += conjugate(stem, [None, u'ere', None, None, u'iminī', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'itor', u'itor', None, None, u'untor'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}))

    # print "(3a)", util.render(items)
    return items


def conjugate_verb_type3B(pres1sg, perf1sg, supinum, inf, ja, tags):
    # capiō, cēpī, captum, capere
    stem = pres1sg[:-2] # cap-
    pf_stem = perf1sg[:-1] # cēp-

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags, typeIII=True)

    # 現在
    items += conjugate(stem, [u'iō', u'is', u'it', u'imus', u'itis', u'iunt'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(stem, [u'ior', (u'eris', u'ere'), u'itur', u'imur', u'iminī', u'iuntur'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present'}))

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)
    # 未完了
    items += conjugate_imperfect(stem + u'iē', tags)
    # 未来
    items += conjugate_future_34(stem + u'i', tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate(stem, [None, u'e', None, None, u'ite', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'itō', u'itō', None, u'itōte', u'iuntō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    items += conjugate(stem, [None, u'ere', None, None, u'iminī', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'itor', u'itor', None, None, u'iuntor'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}))

    # print "(3b)", util.render(items)
    return items


def conjugate_verb_type4(pres1sg, perf1sg, supinum, inf, ja, tags):
    # audiō, audīvī, audītum, audīre
    stem = pres1sg[:-2] # aud-
    pf_stem = perf1sg[:-1] # audīv-

    items = []
    items += conjugate_infinitive(inf, pf_stem, supinum, ja, tags)

    # 現在
    items += conjugate(stem, [u'iō', u'īs', u'īt', u'īmus', u'ītis', u'iunt'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))
    items += conjugate(stem, [u'ior', (u'īris', u'īre'), u'ītur', u'īmur', u'īminī', u'iuntur'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}))

    # 能動態 完了
    items += conjugate_perfect(pf_stem, tags)
    items += conjugate_past_perfect(pf_stem, tags)
    items += conjugate_future_perfect(pf_stem, tags)
    # 未完了
    items += conjugate_imperfect(stem + u'iē', tags)
    # 未来
    items += conjugate_future_34(stem + u'i', tags)

    # 受動態
    items += conjugate_passive_perfect(supinum, tags)
    items += conjugate_passive_past_perfect(supinum, tags)
    items += conjugate_passive_future_perfect(supinum, tags)

    # 命令法
    items += conjugate(stem, [None, u'ī', None, None, u'īte', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ītō', u'ītō', None, u'ītōte', u'iuntō'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}))

    items += conjugate(stem, [None, u'īre', None, None, u'īminī', None],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}))
    items += conjugate(stem, [None, u'ītor', u'ītor', None, None, u'iuntor'],
                       common_tags=util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}))

    # print "(4)", util.render(items)
    return items


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

    for item in items:
        latin.latindic_register(item['surface'], item)


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
            args = (pres1sg, perf1sg, supinum, inf, ja, tags)

            if type == CONJ_1:
                stem = pres1sg[:-1]
                if perf1sg is None: perf1sg = stem + u'āvī'
                if supinum is None: supinum = stem + u'ātum'
                if inf is None: inf = stem + u'āre'
                args = (pres1sg, perf1sg, supinum, inf, ja, tags)
                table = conjugate_verb_type1(*args)
            elif type == CONJ_2:
                table = conjugate_verb_type2(*args)
            elif type == CONJ_3A:
                table = conjugate_verb_type3A(*args)
            elif type == CONJ_3B:
                table = conjugate_verb_type3B(*args)
            elif type == CONJ_4:
                table = conjugate_verb_type4(*args)
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
                latin.latindic_register(item['surface'], item)

def load():
    load_verbs('verb.def')

    conjugate_verb_sum_composites()
    # items += conjugate_irregular_verb(u'edō', '食べる') # edO EdI Esum edere/Esse
    # items += conjugate_irregular_verb(u'eō', '行く') # eO IvI/iI itum Ire
    # items += conjugate_irregular_verb(u'ferō', '運ぶ') # ferO tulI lAtum ferre
    # items += conjugate_irregular_verb(u'fīō', '成る,生ずる') # fIO factus sum, fierI
    # items += conjugate_irregular_verb(u'volō', '欲する') # volO voluI velle
    # items += conjugate_irregular_verb(u'mālō', 'むしろ〜を欲する') # mAlO mAluI mAlle
    # items += conjugate_irregular_verb(u'nōlō', '欲しない') # nOlO nOluI nOlle


if __name__ == '__main__':
    load()
    latin.latindic_dump()
