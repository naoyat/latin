#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import util

from .latin_verb_reg import *

def conjugate_verb_eo(prefix='', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+'eō', 'ja':ja}

    inf = prefix + 'īre'
    perf1sg = prefix + 'iī'

    # pres_stem = u''
    # pf_stem = u''
    # īvī iī
    # itum
    items = []
    items += conjugate(prefix + '', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [inf], [{}])
    items += conjugate(prefix + '', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       [('īsse', 'īvisse')], [{}])
    items += conjugate(prefix + '', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'future'}),
                       ['itūrus esse'], [{}])


    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       ['eō', 'īs', 'it', 'īmus', 'ītis', 'eunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       ['ībam', 'ībās', 'ībat', 'ībāmus', 'ībātis', 'ībant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                       ['ībō', 'ībis', 'ībit', 'ībimus', 'ībitis', 'ībunt'])

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 接続法
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'present'}),
                       ['eam', 'eāe', 'eas', 'eāmus', 'eātis', 'eant'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'imperfect'}),
                       ['īrem', 'īrēs', 'īret', 'īrēmus', 'īrētis', 'īrent'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'}),
                       ['ierim', 'ieris', 'ierit', 'ierimus', 'ieritis', 'ierint'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'}),
                       ['īssem', 'īssēs', 'īsset', 'īssēmus', 'īssētis', 'īssent'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, 'ī', None, None, 'īte', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, 'ītō', 'ītō', None, 'ītōte', 'euntō'])

    # 分詞
    items += conjugate_participle('iē', 'itum', tags)

    # print "(eo)", util.render(items)
    return items


def conjugate_verb_fero(prefix='', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+'ferō', 'ja':ja}

    inf = prefix + 'ferre'
    pres_stem = prefix + 'fer'
    perf1sg = prefix + 'tulī'
    pf_stem = perf1sg[:-1] #tul

    supinum = prefix + 'lātum'

    items = []
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       ['ferre'], [{}])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       ['tulisse'], [{}])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'future'}),
                       ['lātūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       ['ferō', 'fers', 'fert', 'ferimus', 'fertis', 'ferunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       ['ferēbam', 'ferēbās', 'ferēbat', 'ferēbāmus', 'ferēbātis', 'ferēbant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                       ['feram', 'ferēs', 'feret', 'ferēmus', 'ferētis', 'ferent'])

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 受動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'present'}),
                       ['feror', 'ferris', 'fertur', 'ferimur', 'feriminī', 'feruntur'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'imperfect'}),
                       ['ferēbar', 'ferēbāris', 'ferēbātur', 'ferēbāmur', 'ferēbāminī', 'ferēbantur'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'passive', 'tense':'future'}),
                       ['ferar', 'ferēris', 'ferētur', 'ferēmur', 'ferēminī', 'ferentur'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, 'fer', None, None, 'ferte', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, 'fertō', 'fertō', None, 'fertōte', 'feruntō'])

    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'present', 'mood':'imperative'}),
                       [None, 'ferre', None, None, 'feriminī', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'passive', 'tense':'future', 'mood':'imperative'}),
                       [None, 'fertor', 'fertor', None, None, 'feruntor'])

    # 分詞
    items += conjugate_participle(pres_stem, supinum, tags)

#    print "(fero)", util.render(items)
    return items


def conjugate_verb_sum(prefix='', ja=''):
    tags = {'pos':'verb', 'pres1sg':prefix+'sum', 'ja':ja}

    inf = prefix + 'esse'
    pres_stem = prefix + 'et'
    perf1sg = prefix + 'fuī'
    pf_stem = perf1sg[:-1]

    items = []
    items += conjugate(prefix + '', util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'present'}),
                       [inf], [{}])
    items += conjugate(prefix + pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'perfect'}),
                       ['isse'], [{}])
    items += conjugate(prefix + pf_stem, util.aggregate_dicts(tags, {'voice':'active', 'mood':'infinitive', 'tense':'future'}),
                       ['tūrus esse'], [{}])

    # 能動態 現在・過去・未来
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'present'}),
                       ['sum', 'es', 'est', 'sumus', 'estis', 'sunt'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'imperfect'}),
                       ['eram', 'erās', 'erat', 'erāmus', 'erātis', 'erant'])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'mood':'indicative', 'voice':'active', 'tense':'future'}),
                       ['erō', 'eris', 'erit', 'erimus', 'eritis', 'erunt'])

    # 能動態 完了
    items += conjugate_perfect(perf1sg, tags)
    items += conjugate_past_perfect(perf1sg, tags)
    items += conjugate_future_perfect(perf1sg, tags)

    # 接続法
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'present'}),
                       ['sim', 'sīs', 'sit', 'sīmus', 'sītis', 'sint'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'imperfect'}),
                       ['essem', 'essēs', 'esset', 'essēmus', 'essētis', 'essent'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'}),
                       ['fuerim', 'fueris', 'fuerit', 'fuerimus', 'fueritis', 'fuerint'])
    items += conjugate(prefix,
                       util.aggregate_dicts(tags, {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'}),
                       ['fuissem', 'fuissēs', 'fuisset', 'fuissēmus', 'fuissētis', 'fuissent'])

    # 命令形
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'present', 'mood':'imperative'}),
                       [None, 'es', None, None, 'este', None])
    items += conjugate(prefix, util.aggregate_dicts(tags, {'voice':'active', 'tense':'future', 'mood':'imperative'}),
                       [None, 'estō', 'estō', None, 'estōte', 'suntō'])

    # 分詞
    items += conjugate_participle('sē', 'es##', tags) # no supinum for 'sum'

    # print "(sum)", util.render(items)
    return items


def conjugate_verb_eo_composites():
    items = []

    items += conjugate_verb_eo('', '行く')
    items += conjugate_verb_eo('red', '戻る,帰る')

    return items


def conjugate_verb_fero_composites():
    items = []

    items += conjugate_verb_fero('', '運ぶ,耐える')
#    items += conjugate_verb_fero(u'red', '戻る,帰る')

    return items


def conjugate_verb_sum_composites():
    items = []

    items += conjugate_verb_sum('', '〜である')
    items += conjugate_verb_sum('ab', '不在である,離れている')
    items += conjugate_verb_sum('ad', '出席している,助力する')
    items += conjugate_verb_sum('dē', '欠けている,存在しない')
    items += conjugate_verb_sum('inter', '間にある,相違する')
    items += conjugate_verb_sum('ob', '妨げになる')
    items += conjugate_verb_sum('prae', '先頭に立つ')
    items += conjugate_verb_sum('pos', 'できる') # possum potuī posse
    items += conjugate_verb_sum('prō', '役に立つ') # prōsum prōfuī prōfutUrus prōdesse

    return items


def load():
    items = []

    items += conjugate_verb_sum_composites()
    # items += conjugate_irregular_verb(u'edō', '食べる') # edō ēdī ēsum edere/ēsse

    # items += conjugate_irregular_verb(u'eō', '行く') # eō īvī/iī itum īre
    items += conjugate_verb_eo_composites()

    # items += conjugate_irregular_verb(u'ferō', '運ぶ') # ferō tulī lātum ferre
    items += conjugate_verb_fero_composites()

    # items += conjugate_irregular_verb(u'fīō', '成る,生ずる') # fīō factus sum, fierī
    # items += conjugate_irregular_verb(u'volō', '欲する') # volō voluī velle
    # items += conjugate_irregular_verb(u'mālō', 'むしろ〜を欲する') # mālō māluī mālle
    # items += conjugate_irregular_verb(u'nōlō', '欲しない') # nōlō nōluī nōlle

    return items


if __name__ == '__main__':
    load()
#    latindic.dump()
