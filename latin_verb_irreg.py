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
    perf1sg = prefix + u'fuī'
    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate('', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [inf], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [u'isse'], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [u'tūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present'}),
                       [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'imperfect'}),
                       [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future'}),
                       [u'erō', u'eris', u'erit', u'erimus', u'eritis', u'erunt'])

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 接続法
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'present'}),
                       [u'sim', u'sīs', u'sit', u'sīmus', u'sītis', u'sint'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'imperfect'}),
                       [u'essem', u'essēs', u'esset', u'essēmus', u'essētis', u'essent'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'}),
                       [u'fuerim', u'fueris', u'fuerit', u'fuerimus', u'fueritis', u'fuerint'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'}),
                       [u'fuissem', u'fuissēs', u'fuisset', u'fuissēmus', u'fuissētis', u'fuissent'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, u'es', None, None, u'este', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, u'estō', u'estō', None, u'estōte', u'suntō'])

    # 分詞
    items += conjugate_participle(u'sē', u'es##', tags) # no supinum for 'sum'

    # print "(sum)", util.render(items)
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
