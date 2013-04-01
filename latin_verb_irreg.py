#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
import util

from latin_verb_reg import *

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


def load():
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
