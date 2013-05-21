#!/usr/bin/env python
# -*- coding: utf-8 -*-

import util

from latin_verb_reg import *

def conjugate_verb_eo(prefix=u'', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+u'eō', 'ja':ja}

    inf = u'īre'
    # pres_stem = u''
    # pf_stem = u''
    # īvī iī
    # itum
    items = []
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       [u'eō', u'īs', u'it', u'īmus', u'ītis', u'eunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       [u'ībam', u'ībās', u'ībat', u'ībāmus', u'ībātis', u'ībant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
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


def conjugate_verb_fero(prefix=u'', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+u'ferō', 'ja':ja}

    inf = prefix + u'ferre'
    pres_stem = prefix + u'fer'
    perf1sg = prefix + u'tulī'
    pf_stem = perf1sg[:-1] #tul

    supinum = prefix + u'lātum'

    items = []
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [u'ferre'], [{}])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [u'tulisse'], [{}])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'future'}),
                       [u'lātūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       [u'ferō', u'fers', u'fert', u'ferimus', u'fertis', u'ferunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       [u'ferēbam', u'ferēbās', u'ferēbat', u'ferēbāmus', u'ferēbātis', u'ferēbant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                       [u'feram', u'ferēs', u'feret', u'ferēmus', u'ferētis', u'ferent'])

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 受動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'present'}),
                       [u'feror', u'ferris', u'fertur', u'ferimur', u'feriminī', u'feruntur'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'imperfect'}),
                       [u'ferēbar', u'ferēbāris', u'ferēbātur', u'ferēbāmur', u'ferēbāminī', u'ferēbantur'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'future'}),
                       [u'ferar', u'ferēris', u'ferētur', u'ferēmur', u'ferēminī', u'ferentur'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, u'fer', None, None, u'ferte', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, u'fertō', u'fertō', None, u'fertōte', u'feruntō'])

    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}),
                       [None, u'ferre', None, None, u'feriminī', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}),
                       [None, u'fertor', u'fertor', None, None, u'feruntor'])

    # 分詞
    items += conjugate_participle(pres_stem, supinum, tags)

#    print "(fero)", util.render(items)
    return items


def conjugate_verb_sum(prefix=u'', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+u'sum', 'ja':ja}

    inf = prefix + u'esse'
    pres_stem = prefix + u'et'
    perf1sg = prefix + u'fuī'
    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate('', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [inf], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [u'isse'], [{}])
    items += conjugate(pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'future'}),
                       [u'tūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       [u'sum', u'es', u'est', u'sumus', u'estis', u'sunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       [u'eram', u'erās', u'erat', u'erāmus', u'erātis', u'erant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
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

    return items


def conjugate_verb_fero_composites():
    items = []

    items += conjugate_verb_fero(u'', '運ぶ,耐える')
#    items += conjugate_verb_fero(u'red', '戻る,帰る')

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
    items += conjugate_verb_sum(u'pos', 'できる') # possum potuī posse
    items += conjugate_verb_sum(u'prō', '役に立つ') # prōsum prōfuī prōfutUrus prōdesse

    return items


def load():
    items = []

    items += conjugate_verb_sum_composites()
    # items += conjugate_irregular_verb(u'edō', '食べる') # edō ēdī ēsum edere/ēsse

    # items += conjugate_irregular_verb(u'eō', '行く') # eō īvī/iī itum īre
    items += conjugate_verb_eo_composites()

    # items += conjugate_irregular_verb(u'ferō', '運ぶ') # ferō tulī lAtum ferre
    items += conjugate_verb_fero_composites()

    # items += conjugate_irregular_verb(u'fīō', '成る,生ずる') # fīō factus sum, fierī
    # items += conjugate_irregular_verb(u'volō', '欲する') # volō voluī velle
    # items += conjugate_irregular_verb(u'mālō', 'むしろ〜を欲する') # mAlō mAluī mAlle
    # items += conjugate_irregular_verb(u'nōlō', '欲しない') # nōlō nōluī nōlle

    return items


if __name__ == '__main__':
    load()
#    latindic.dump()
