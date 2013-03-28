#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin
import latin_noun
import latin_adj
import util

#def make_declined_tags(prefix, prefix_tag, suffix, suffix_tag):
#    d = prefix_tag.copy()
#    d.update(suffix_tag)
#    d['surface'] = surface = prefix + suffix
#    return d

def decline(common_prefix, common_tag, suffices, suffices_tags, extra_tags={}):
    def add_suffix(suffix, suffix_tags):
        surface = common_prefix + suffix
        return util.aggregate_dicts(common_tag, {'surface':surface}, suffix_tags, extra_tags)

    return map(add_suffix, suffices, suffices_tags)


items = []

# <27> 人称代名詞
## 一人称
common_tags = {'pos':'pronoun', 'person':1, 'ja':'私', 'desc':'人称代名詞'}
forms = [u'ego', u'mē', u'meī', u'mihi', u'mē',
         u'nōs', u'nōs', u'nostrī', u'nōbīs', u'nōbīs']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)
items += [util.aggregate_dicts({'surface':u'mihī'}, common_tags, latin_noun.case_tags_5x2[3])]
items += [util.aggregate_dicts({'surface':u'nostrum'}, common_tags, latin_noun.case_tags_5x2[7])]

## 二人称
common_tags = {'pos':'pronoun', 'person':2, 'ja':'あなた', 'desc':'人称代名詞'}
forms = [u'tū', u'tē', u'tuī', u'tibi', u'tē',
         u'vōs', u'vōs', u'vestrī', u'vōbīs', u'vōbīs']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)
items += [util.aggregate_dicts({'surface':u'tibī'}, common_tags, latin_noun.case_tags_5x2[3])]
items += [util.aggregate_dicts({'surface':u'vestrum'}, common_tags, latin_noun.case_tags_5x2[7])]

# <28> 所有代名詞
## 所有形容詞
items += latin_adj.decline_adj_type1(u'meus', u'mea', \
                                  {'ja':'私の', 'base':u'meus', 'desc':'所有形容詞'}, False)
items += latin_adj.decline_adj_type1(u'noster', u'nostra', \
                                  {'ja':'私たちの', 'base':u'noster', 'desc':'所有形容詞'}, False)
items += latin_adj.decline_adj_type1(u'tuus', u'tua', \
                                  {'ja':'あなたの', 'base':u'tuus', 'desc':'所有形容詞'}, False)
items += latin_adj.decline_adj_type1(u'vester', u'vestra', \
                                  {'ja':'あなたたちの', 'base':u'vester', 'desc':'所有形容詞'}, False)

items = util.remove_matched_items(items, {'surface':u'mee'})
items += [{'case':'Voc', 'number':'sg', 'gender':'m', 'base':u'meus', 'surface':u'mī', 'ja':'私の', 'desc':'所有形容詞'}]


# <29> 再帰代名詞

# <30> 強意代名詞(myself,himself,themselves,...)
common_tags = {'pos':'pronoun', 'person':3, 'ja':'(それ)自身', 'desc':'強意代名詞'}

forms = [u'ipse', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
         u'ipsī', u'ipsōs', u'ipsōrum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'm'
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

forms = [u'ipsa', u'ipsam', u'ipsīus', u'ipsī', u'ipsā',
         u'ipsae', u'ipsās', u'ipsārum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'f'
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

forms = [u'ipsum', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
         u'ipsa', u'ipsa', u'ipsōrum', u'ipsīs', u'ipsīs']
common_tags['gender'] = 'n'
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)



# <37> 関係代名詞 quī, quae, quod
# 名詞とともに関係形容詞 (which) or 疑問形容詞 (what, which, what kind of) としても用いられる
common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'関係代名詞', 'base':u'quī'}
forms = [u'quī', u'quem', u'cūjus', u'cuī', u'quō',
         u'quī', u'quōs', u'quōrum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
forms = [u'quae', u'quam', u'cūjus', u'cuī', u'quā',
         u'quae', u'quās', u'quārum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
forms = [u'quod', u'quod', u'cūjus', u'cuī', u'quō',
         u'quae', u'quae', u'quōrum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})


# <38> 疑問代名詞 quis, quid
# 疑問形容詞は関係代名詞と同じであるが、quisが疑問形容詞として用いられることもある
common_tags = {'pos':'pronoun', 'ja':'誰が', 'desc':'疑問代名詞', 'base':u'quis'}
forms = [u'quis', u'quem', u'cūjus', u'cuī', u'quō',
         u'quī', u'quōs', u'quōrum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
forms = [u'quis', u'quem', u'cūjus', u'cuī', u'quā',
         u'quae', u'quās', u'quārum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})

common_tags = {'pos':'pronoun', 'ja':'何が', 'desc':'疑問代名詞', 'base':u'quid', 'gender':'n'}
forms = [u'quid', u'quid', u'cūjus', u'cuī', u'quō',
         u'quae', u'quae', u'quōrum', u'quibus', u'quibus']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2)










# <41> quisque「各人(の)」(単数のみ) (英:each, every)
# pronoun.
common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'不定代名詞', 'base':u'quisque'}
forms = [u'quisque', u'quemque', u'cūjusque', u'cuīque', u'quōque'] # m,f
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
forms = [u'quidque', u'quidque', u'cūjusque', u'cuīque', u'quōque'] # n
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})
# adj.
common_tags = {'pos':'adj', 'ja':'各人(の)', 'desc':'不定形容詞', 'base':u'quisque'}
forms = [u'quīque', u'quemque', u'cūjusque', u'cuīque', u'quōque']
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
forms = [u'quaeque', u'quamque', u'cūjusque', u'cuīque', u'quāque']
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
forms = [u'quodque', u'quodque', u'cūjusque', u'cuīque', u'quōque']
items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})

# <42> quīdam「或る(人,物)」(英:certain)
# pronoun.
common_tags = {'pos':'pronoun', 'ja':'或る(人,物)', 'desc':'不定代名詞', 'base':u'quīdam'}
forms = [u'quīdam', u'quendam', u'cūjusdam', u'cuīdam', u'quōdam',
         u'quīdam', u'quōsdam', u'quōrundam', u'quibusdam', u'quibusdam']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
forms = [u'quaedam', u'quandam', u'cūjusdam', u'cuīdam', u'quādam',
         u'quaedam', u'quāsdam', u'quārundam', u'quibusdam', u'quibusdam']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
forms = [u'quiddam', u'quiddam', u'cūjusdam', u'cuīdam', u'quōdam',
         u'quīdam', u'quōsdam', u'quōrundam', u'quibusdam', u'quibusdam']
items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})

#  quiddam<代名詞> -> quoddam<形容詞>

def load():
    for item in items:
        latin.latindic_register(item['surface'], item)
