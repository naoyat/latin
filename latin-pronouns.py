#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
import latin2
import util

#def make_declined_tags(prefix, prefix_tag, suffix, suffix_tag):
#    d = prefix_tag.copy()
#    d.update(suffix_tag)
#    d['surface'] = surface = prefix + suffix
#    return d

def decline(common_prefix, common_tag, suffices, suffix_tags):
    def add_suffix(suffix, tags):
        surface = common_prefix + suffix
        return util.aggregate_dicts(common_tag, {'surface':surface}, tags)

    return map(add_suffix, suffices, suffix_tags)


items = []

## 一人称
common_tags = {'pos':'pronoun', 'person':1, 'ja':'私', 'desc':'人称代名詞'}
forms = [u'ego', u'mē', u'meī', u'mihi', u'mē',
         u'nōs', u'nōs', u'nostrī', u'nōbīs', u'nōbīs']
items += decline('', common_tags, forms, latin.case_tags_5x2)
items += [util.aggregate_dicts({'surface':u'mihī'}, common_tags, latin.case_tags_5x2[3])]
items += [util.aggregate_dicts({'surface':u'nostrum'}, common_tags, latin.case_tags_5x2[7])]

## 二人称
common_tags = {'pos':'pronoun', 'person':2, 'ja':'あなた', 'desc':'人称代名詞'}
forms = [u'tū', u'tē', u'tuī', u'tibi', u'tē',
         u'vōs', u'vōs', u'vestrī', u'vōbīs', u'vōbīs']
items += decline('', common_tags, forms, latin.case_tags_5x2)
items += [util.aggregate_dicts({'surface':u'tibī'}, common_tags, latin.case_tags_5x2[3])]
items += [util.aggregate_dicts({'surface':u'vestrum'}, common_tags, latin.case_tags_5x2[7])]


## 所有形容詞
items += latin2.decline_adj_type1(u'meus', u'mea',
                                  {'ja':'私の', 'base':u'meus', 'desc':'所有形容詞'}, False)
items += latin2.decline_adj_type1(u'noster', u'nostra',
                                  {'ja':'私たちの', 'base':u'noster', 'desc':'所有形容詞'}, False)
items += latin2.decline_adj_type1(u'tuus', u'tua',
                                  {'ja':'あなたの', 'base':u'tuus', 'desc':'所有形容詞'}, False)
items += latin2.decline_adj_type1(u'vester', u'vestra',
                                  {'ja':'あなたたちの', 'base':u'vester', 'desc':'所有形容詞'}, False)

items = util.remove_matched_items(items, {'surface':u'mee'})
items += [{'case':'Voc', 'number':'sg', 'gender':'m', 'base':u'meus', 'surface':u'mī', 'ja':'私の', 'desc':'所有形容詞'}]








## 強意代名詞(myself,himself,themselves,...)
common_tags = {'pos':'pronoun', 'person':3, 'ja':'(それ)自身', 'desc':'強意代名詞'}

forms = [u'ipse', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
         u'ipsī', u'ipsōs', u'ipsōrum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'm'
items += decline('', common_tags, forms, latin.case_tags_5x2)

forms = [u'ipsa', u'ipsam', u'ipsīus', u'ipsī', u'ipsā',
         u'ipsae', u'ipsās', u'ipsārum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'f'
items += decline('', common_tags, forms, latin.case_tags_5x2)

forms = [u'ipsum', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
         u'ipsa', u'ipsa', u'ipsōrum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'n'
items += decline('', common_tags, forms, latin.case_tags_5x2)


for item in items:
    surface = item['surface']
    latin2.latindic[surface] = item

# util.pp(items)