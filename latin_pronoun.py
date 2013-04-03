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

def decline(common_prefix, common_tags, suffices, suffices_tags, extra_tags={}):
    return util.variate(common_prefix,
                        util.aggregate_dicts(common_tags, extra_tags),
                        suffices,
                        suffices_tags)


# <27> 人称代名詞
def ego():
    items = []

    # 一人称
    common_tags = {'pos':'pronoun', 'person':1, 'ja':'私', 'desc':'人称代名詞'}
    forms = [u'ego', u'mē', u'meī', u'mihi', u'mē',
             u'nōs', u'nōs', u'nostrī', u'nōbīs', u'nōbīs']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)
    items += [util.aggregate_dicts({'surface':u'mihī'}, common_tags, latin_noun.case_tags_5x2[3])]
    items += [util.aggregate_dicts({'surface':u'nostrum'}, common_tags, latin_noun.case_tags_5x2[7])]

    # 二人称
    common_tags = {'pos':'pronoun', 'person':2, 'ja':'あなた', 'desc':'人称代名詞'}
    forms = [u'tū', u'tē', u'tuī', u'tibi', u'tē',
             u'vōs', u'vōs', u'vestrī', u'vōbīs', u'vōbīs']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)
    items += [util.aggregate_dicts({'surface':u'tibī'}, common_tags, latin_noun.case_tags_5x2[3])]
    items += [util.aggregate_dicts({'surface':u'vestrum'}, common_tags, latin_noun.case_tags_5x2[7])]

    return util.aggregate_cases(items)


# <28> 所有代名詞
def meus():
    items = []
    # 所有形容詞
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

    return util.aggregate_cases(items)


# <29> 再帰代名詞
# 3人称. sē/sēsē, suī, sibi/sibī, sē/sēsē;
def reflexive_pronouns():
    return []


# <30> 強意代名詞(myself,himself,themselves,...)    
def ipse():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'(それ)自身', 'desc':'強意代名詞'}

    forms = [u'ipse', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
             u'ipsī', u'ipsōs', u'ipsōrum', u'ipsīs', u'ipsīs']
    common_tags['gender'] = 'm'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'ipsa', u'ipsam', u'ipsīus', u'ipsī', u'ipsā',
             u'ipsae', u'ipsās', u'ipsārum', u'ipsīs', u'ipsīs']
    common_tags['gender'] = 'f'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'ipsum', u'ipsum', u'ipsīus', u'ipsī', u'ipsō',
             u'ipsa', u'ipsa', u'ipsōrum', u'ipsīs', u'ipsīs']
    common_tags['gender'] = 'n'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <32> 指示詞
# iste istad istud 「その,それ」 like ille

# <33> is,ea,id
def is_ea_id():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'その,それ', 'desc':'指示代名詞'}

    forms = [u'is', u'eum', u'ējus', u'eī', u'eō',
             (u'eī',u'iī',u'ī'), u'eōs', u'eōrum', (u'eīs',u'iīs',u'īs'), (u'eīs',u'iīs',u'īs')]
    common_tags['gender'] = 'm'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'ea', u'eam', u'ējus', u'eī', u'eā',
             u'eae', u'eās', u'eārum', (u'eīs',u'iīs',u'īs'), (u'eīs',u'iīs',u'īs')]
    common_tags['gender'] = 'f'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'id', u'id', u'ējus', u'eī', u'eō',
             u'ea', u'ea', u'eōrum', (u'eīs',u'iīs',u'īs'), (u'eīs',u'iīs',u'īs')]
    common_tags['gender'] = 'n'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <34> hic,haec,hoc「この、これ」（英:this）
def hic():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'この,これ', 'desc':'指示代名詞'}

    forms = [u'hīc', u'hunc', u'hūjus', u'huīc', u'hōc',
             u'hī', u'hōs', u'hōrum', u'hīs', u'hīs']
    common_tags['gender'] = 'm'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'haec', u'hanc', u'hūjus', u'huīc', u'hāc',
             u'hae', u'hās', u'hārum', u'hīs', u'hīs']
    common_tags['gender'] = 'f'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'hoc', u'hoc', u'hūjus', u'huīc', u'hōc',
             u'haec', u'haec', u'hōrum', u'hīs', u'hīs']
    common_tags['gender'] = 'n'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <35> ille,illa,illud「あの、あれ」（英:that）
def ille():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'あの,あれ', 'desc':'指示代名詞'}

    forms = [u'ille', u'illum', u'illīus', u'illī', u'illō',
             u'illī', u'illōs', u'illōrum', u'illīs', u'illīs']
    common_tags['gender'] = 'm'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'illa', u'illam', u'illīus', u'illī', u'illā',
             u'illae', u'illās', u'illārum', u'illīs', u'illīs']
    common_tags['gender'] = 'f'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'illud', u'illud', u'illīus', u'illī', u'illō',
             u'illa', u'illa', u'illōrum', u'illīs', u'illīs']
    common_tags['gender'] = 'n'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <36> idem,eadem,idem「同じ」（英:the same）
def idem():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'同じ', 'desc':'指示代名詞'}

    forms = [u'īdem', u'eundem', u'ējusdem', u'eīdem', u'eōdem',
             u'iīdem', u'eōsdem', u'eōrundem', u'iīsdem', u'iīsdem']
    common_tags['gender'] = 'm'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'eadem', u'eandem', u'ējusdem', u'eīdem', u'eādem',
             u'eaedem', u'eāsdem', u'eārundem', u'iīsdem', u'iīsdem']
    common_tags['gender'] = 'f'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    forms = [u'idem', u'idem', u'ējusdem', u'eīdem', u'eōdem',
             u'eadem', u'eadem', u'eōrundem', u'iīsdem', u'iīsdem']
    common_tags['gender'] = 'n'
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <37> 関係代名詞 quī, quae, quod
def qui():
    items = []

    # 名詞とともに関係形容詞 (which) or 疑問形容詞 (what, which, what kind of) としても用いられる
    common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'関係代名詞', 'base':u'quī'}
    forms = [u'quī', u'quem', u'cūjus', u'cuī', u'quō',
             u'quī', u'quōs', u'quōrum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = [u'quae', u'quam', u'cūjus', u'cuī', u'quā',
             u'quae', u'quās', u'quārum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
    forms = [u'quod', u'quod', u'cūjus', u'cuī', u'quō',
             u'quae', u'quae', u'quōrum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})

    return util.aggregate_cases(items)


# <38> 疑問代名詞 quis, quid
def quis():
    items = []
    # 疑問形容詞は関係代名詞と同じであるが、quisが疑問形容詞として用いられることもある
    common_tags = {'pos':'pronoun', 'ja':'誰が', 'desc':'疑問代名詞', 'base':u'quis'}
    forms = [u'quis', u'quem', u'cūjus', u'cuī', u'quō',
             u'quī', u'quōs', u'quōrum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = [u'quis', u'quem', u'cūjus', u'cuī', u'quā',
             u'quae', u'quās', u'quārum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})

    common_tags = {'pos':'pronoun', 'ja':'何が', 'desc':'疑問代名詞', 'base':u'quid', 'gender':'n'}
    forms = [u'quid', u'quid', u'cūjus', u'cuī', u'quō',
             u'quae', u'quae', u'quōrum', u'quibus', u'quibus']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <41> quisque「各人(の)」(単数のみ) (英:each, every)
def quisque():
    items = []
    # pronoun.
    common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'不定代名詞', 'base':u'quisque'}
    forms = [u'quisque', u'quemque', u'cūjusque', u'cuīque', u'quōque'] # m,f
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
    forms = [u'quidque', u'quidque', u'cūjusque', u'cuīque', u'quōque'] # n
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})
    # adj.
    common_tags = {'pos':'adj', 'ja':'各人(の)', 'desc':'不定形容詞', 'base':u'quisque'}
    forms = [u'quīque', u'quemque', u'cūjusque', u'cuīque', u'quōque']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
    forms = [u'quaeque', u'quamque', u'cūjusque', u'cuīque', u'quāque']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
    forms = [u'quodque', u'quodque', u'cūjusque', u'cuīque', u'quōque']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})

    return util.aggregate_cases(items)


# <42> quīdam「或る(人,物)」(英:certain)
def quidam():
    items = []
    # pronoun.
    common_tags = {'pos':'pronoun', 'ja':'或る(人,物)', 'desc':'不定代名詞', 'base':u'quīdam'}
    forms = [u'quīdam', u'quendam', u'cūjusdam', u'cuīdam', u'quōdam',
             u'quīdam', u'quōsdam', u'quōrundam', u'quibusdam', u'quibusdam']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = [u'quaedam', u'quandam', u'cūjusdam', u'cuīdam', u'quādam',
             u'quaedam', u'quāsdam', u'quārundam', u'quibusdam', u'quibusdam']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
    forms = [u'quiddam', u'quiddam', u'cūjusdam', u'cuīdam', u'quōdam',
             u'quīdam', u'quōsdam', u'quōrundam', u'quibusdam', u'quibusdam']
    items += decline(u'', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})
    # quiddam<代名詞> -> quoddam<形容詞>

    return util.aggregate_cases(items)


def decline_pronominal_adjective(nom_sg, ja):
    nom_sg_m, nom_sg_f, nom_sg_n = nom_sg

    items = []

    stem1 = nom_sg_m[:-2]
    stem2 = nom_sg_f[:-1]
    if stem2 == u'ali':
        gen_sg = u'alīus'
    else:
        gen_sg = stem2 + u'īus'
    dat_sg = stem2 + u'ī'
    abl_sg_mn = stem2 + u'ō'
    abl_sg_f = stem2 + u'ā'
    dat_abl_pl = stem2 + u'īs'

    tags = {'pos':'pronoun', 'ja':ja}

    forms = [nom_sg_m, stem2 + u'um', gen_sg, dat_sg, abl_sg_mn,
             stem2 + u'ī', abl_sg_mn + u's', abl_sg_mn + u'rum', dat_abl_pl, dat_abl_pl]
    items += decline(u'', tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})

    forms = [nom_sg_f, nom_sg_f + u'm', gen_sg, dat_sg, abl_sg_f,
             nom_sg_f + u'e', abl_sg_f + u's', abl_sg_f + u'rum', dat_abl_pl, dat_abl_pl]
    items += decline(u'', tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})

    forms = [nom_sg_n, nom_sg_n, gen_sg, dat_sg, abl_sg_mn,
             nom_sg_f, nom_sg_f, abl_sg_mn + u'rum', dat_abl_pl, dat_abl_pl]
    items += decline(u'', tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})

    # print ja, util.pp(items)
    return items

def pronominal_adjectives():
    items = []
    items += decline_pronominal_adjective((u'alius', u'alia', u'aliud'), '他の')
    items += decline_pronominal_adjective((u'tōtus', u'tōta', u'tōtum'), '全体の')
    items += decline_pronominal_adjective((u'ūnus', u'ūna', u'ūnum'), 'ひとつの') #数詞でもある
    items += decline_pronominal_adjective((u'sōlus', u'sōla', u'sōlum'), '唯一の')
    items += decline_pronominal_adjective((u'ūllus', u'ūlla', u'ūllum'), 'どれかひとつの') #any
    items += decline_pronominal_adjective((u'nūllus', u'nūlla', u'nūllum'), 'ひとつも...ない')
    items += decline_pronominal_adjective((u'alter', u'altera', u'alterum'), '(2つのうち)どれか一方の')
    items += decline_pronominal_adjective((u'uter', u'utra', u'utrum'), '(2つのうち)どちらの？,(2つのうち)どちらかの')
    items += decline_pronominal_adjective((u'neuter', u'neutra', u'neutrum'), '(2つのうち)どちらも...ない')

    items += decline(u'', {},
                     [u'nihil', u'nihil', (u'nūllīus reī', u'nihilī'), u'nūllī reī', (u'nūllā rē', u'nihilō')],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'n', 'ja':'なにも...ない'}) # nothing
    items += decline(u'', {},
                     [u'nēmō', u'nēminem', u'nūllīus', u'nēminī', u'nūllō'],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'m', 'ja':'だれも...ない'}) # no one, nobody
    items += decline(u'', {},
                     [u'nēmō', u'nēminem', u'nūllīus', u'nēminī', u'nūllō'],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'f', 'ja':'だれも...ない'}) # no one, nobody
    # util.pp(items)
    return util.aggregate_cases(items)


def load():
    items = ego() + meus() + ipse() + is_ea_id() + hic() + ille() + idem() + qui() + quis() + quisque() + quidam()
    items += pronominal_adjectives()

    latin.latindic_register_items(items)
