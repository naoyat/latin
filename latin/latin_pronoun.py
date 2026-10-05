#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import latin_noun
from . import latin_adj
from . import util

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
    common_tags = {'pos':'pronoun', 'person':1, 'gender':'m', 'ja':'私', 'desc':'人称代名詞'} # genderは仮
    forms = ['ego', 'mē', 'meī', 'mihi', 'mē',
             'nōs', 'nōs', 'nostrī', 'nōbīs', 'nōbīs']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)
    items += [util.aggregate_dicts({'surface':'mihī'}, common_tags, latin_noun.case_tags_5x2[3])]
    items += [util.aggregate_dicts({'surface':'nostrum'}, common_tags, latin_noun.case_tags_5x2[7])]

    # 二人称
    common_tags = {'pos':'pronoun', 'person':2, 'gender':'m', 'ja':'あなた', 'desc':'人称代名詞'}
    forms = ['tū', 'tē', 'tuī', 'tibi', 'tē',
             'vōs', 'vōs', 'vestrī', 'vōbīs', 'vōbīs']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)
    items += [util.aggregate_dicts({'surface':'tibī'}, common_tags, latin_noun.case_tags_5x2[3])]
    items += [util.aggregate_dicts({'surface':'vestrum'}, common_tags, latin_noun.case_tags_5x2[7])]

    return util.aggregate_cases(items)


# <28> 所有代名詞
def meus():
    items = []
    # 所有形容詞
    items += latin_adj.decline_adj_type1('meus', 'mea', \
                                             {'ja':'私の', 'base':'meus', 'desc':'所有形容詞'}, False)
    items += latin_adj.decline_adj_type1('noster', 'nostra', \
                                             {'ja':'私たちの', 'base':'noster', 'desc':'所有形容詞'}, False)
    items += latin_adj.decline_adj_type1('tuus', 'tua', \
                                             {'ja':'あなたの', 'base':'tuus', 'desc':'所有形容詞'}, False)
    items += latin_adj.decline_adj_type1('vester', 'vestra', \
                                             {'ja':'あなたたちの', 'base':'vester', 'desc':'所有形容詞'}, False)

    items = util.remove_matched_items(items, {'surface':'mee'})
    items += [{'case':'Voc', 'number':'sg', 'gender':'m', 'base':'meus', 'surface':'mī', 'ja':'私の', 'desc':'所有形容詞'}]

    return util.aggregate_cases(items)


# <29> 再帰代名詞
# 3人称. sē/sēsē, suī, sibi/sibī, sē/sēsē;
def reflexive_pronouns():
    return []


# <30> 強意代名詞(myself,himself,themselves,...)    
def ipse():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'(それ)自身', 'desc':'強意代名詞'}

    forms = ['ipse', 'ipsum', 'ipsīus', 'ipsī', 'ipsō',
             'ipsī', 'ipsōs', 'ipsōrum', 'ipsīs', 'ipsīs']
    common_tags['gender'] = 'm'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['ipsa', 'ipsam', 'ipsīus', 'ipsī', 'ipsā',
             'ipsae', 'ipsās', 'ipsārum', 'ipsīs', 'ipsīs']
    common_tags['gender'] = 'f'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['ipsum', 'ipsum', 'ipsīus', 'ipsī', 'ipsō',
             'ipsa', 'ipsa', 'ipsōrum', 'ipsīs', 'ipsīs']
    common_tags['gender'] = 'n'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <32> 指示詞
# iste istad istud 「その,それ」 like ille

# <33> is,ea,id
def is_ea_id():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'その,それ', 'desc':'指示代名詞'}

    forms = ['is', 'eum', 'ējus', 'eī', 'eō',
             ('eī','iī','ī'), 'eōs', 'eōrum', ('eīs','iīs','īs'), ('eīs','iīs','īs')]
    common_tags['gender'] = 'm'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['ea', 'eam', 'ējus', 'eī', 'eā',
             'eae', 'eās', 'eārum', ('eīs','iīs','īs'), ('eīs','iīs','īs')]
    common_tags['gender'] = 'f'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['id', 'id', 'ējus', 'eī', 'eō',
             'ea', 'ea', 'eōrum', ('eīs','iīs','īs'), ('eīs','iīs','īs')]
    common_tags['gender'] = 'n'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <34> hic,haec,hoc「この、これ」（英:this）
def hic():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'この,これ', 'desc':'指示代名詞'}

    forms = ['hīc', 'hunc', 'hūjus', 'huīc', 'hōc',
             'hī', 'hōs', 'hōrum', 'hīs', 'hīs']
    common_tags['gender'] = 'm'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['haec', 'hanc', 'hūjus', 'huīc', 'hāc',
             'hae', 'hās', 'hārum', 'hīs', 'hīs']
    common_tags['gender'] = 'f'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['hoc', 'hoc', 'hūjus', 'huīc', 'hōc',
             'haec', 'haec', 'hōrum', 'hīs', 'hīs']
    common_tags['gender'] = 'n'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <35> ille,illa,illud「あの、あれ」（英:that）
def ille():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'あの,あれ', 'desc':'指示代名詞'}

    forms = ['ille', 'illum', 'illīus', 'illī', 'illō',
             'illī', 'illōs', 'illōrum', 'illīs', 'illīs']
    common_tags['gender'] = 'm'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['illa', 'illam', 'illīus', 'illī', 'illā',
             'illae', 'illās', 'illārum', 'illīs', 'illīs']
    common_tags['gender'] = 'f'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['illud', 'illud', 'illīus', 'illī', 'illō',
             'illa', 'illa', 'illōrum', 'illīs', 'illīs']
    common_tags['gender'] = 'n'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <36> idem,eadem,idem「同じ」（英:the same）
def idem():
    items = []

    common_tags = {'pos':'pronoun', 'person':3, 'ja':'同じ', 'desc':'指示代名詞'}

    forms = ['īdem', 'eundem', 'ējusdem', 'eīdem', 'eōdem',
             'iīdem', 'eōsdem', 'eōrundem', 'iīsdem', 'iīsdem']
    common_tags['gender'] = 'm'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['eadem', 'eandem', 'ējusdem', 'eīdem', 'eādem',
             'eaedem', 'eāsdem', 'eārundem', 'iīsdem', 'iīsdem']
    common_tags['gender'] = 'f'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    forms = ['idem', 'idem', 'ējusdem', 'eīdem', 'eōdem',
             'eadem', 'eadem', 'eōrundem', 'iīsdem', 'iīsdem']
    common_tags['gender'] = 'n'
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <37> 関係代名詞 quī, quae, quod
def qui():
    items = []

    # 名詞とともに関係形容詞 (which) or 疑問形容詞 (what, which, what kind of) としても用いられる
    common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'関係代名詞', 'base':'quī'}
    forms = ['quī', 'quem', 'cūjus', 'cuī', 'quō',
             'quī', 'quōs', 'quōrum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = ['quae', 'quam', 'cūjus', 'cuī', 'quā',
             'quae', 'quās', 'quārum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
    forms = ['quod', 'quod', 'cūjus', 'cuī', 'quō',
             'quae', 'quae', 'quōrum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})

    return util.aggregate_cases(items)


# <38> 疑問代名詞 quis, quid
def quis():
    items = []
    # 疑問形容詞は関係代名詞と同じであるが、quisが疑問形容詞として用いられることもある
    common_tags = {'pos':'pronoun', 'ja':'誰が', 'desc':'疑問代名詞', 'base':'quis'}
    forms = ['quis', 'quem', 'cūjus', 'cuī', 'quō',
             'quī', 'quōs', 'quōrum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = ['quis', 'quem', 'cūjus', 'cuī', 'quā',
             'quae', 'quās', 'quārum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})

    common_tags = {'pos':'pronoun', 'ja':'何が', 'desc':'疑問代名詞', 'base':'quid', 'gender':'n'}
    forms = ['quid', 'quid', 'cūjus', 'cuī', 'quō',
             'quae', 'quae', 'quōrum', 'quibus', 'quibus']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2)

    return util.aggregate_cases(items)


# <41> quisque「各人(の)」(単数のみ) (英:each, every)
def quisque():
    items = []
    # pronoun.
    common_tags = {'pos':'pronoun', 'ja':'各人(の)', 'desc':'不定代名詞', 'base':'quisque'}
    forms = ['quisque', 'quemque', 'cūjusque', 'cuīque', 'quōque'] # m,f
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
    forms = ['quidque', 'quidque', 'cūjusque', 'cuīque', 'quōque'] # n
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})
    # adj.
    common_tags = {'pos':'adj', 'ja':'各人(の)', 'desc':'不定形容詞', 'base':'quisque'}
    forms = ['quīque', 'quemque', 'cūjusque', 'cuīque', 'quōque']
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'m'})
    forms = ['quaeque', 'quamque', 'cūjusque', 'cuīque', 'quāque']
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'f'})
    forms = ['quodque', 'quodque', 'cūjusque', 'cuīque', 'quōque']
    items += decline('', common_tags, forms, latin_noun.case_tags_5sg, {'gender':'n'})

    return util.aggregate_cases(items)


# <42> quīdam「或る(人,物)」(英:certain)
def quidam():
    items = []
    # pronoun.
    common_tags = {'pos':'pronoun', 'ja':'或る(人,物)', 'desc':'不定代名詞', 'base':'quīdam'}
    forms = ['quīdam', 'quendam', 'cūjusdam', 'cuīdam', 'quōdam',
             'quīdam', 'quōsdam', 'quōrundam', 'quibusdam', 'quibusdam']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})
    forms = ['quaedam', 'quandam', 'cūjusdam', 'cuīdam', 'quādam',
             'quaedam', 'quāsdam', 'quārundam', 'quibusdam', 'quibusdam']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})
    forms = ['quiddam', 'quiddam', 'cūjusdam', 'cuīdam', 'quōdam',
             'quīdam', 'quōsdam', 'quōrundam', 'quibusdam', 'quibusdam']
    items += decline('', common_tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})
    # quiddam<代名詞> -> quoddam<形容詞>

    return util.aggregate_cases(items)


def decline_pronominal_adjective(nom_sg, ja):
    nom_sg_m, nom_sg_f, nom_sg_n = nom_sg

    items = []

    stem1 = nom_sg_m[:-2]
    stem2 = nom_sg_f[:-1]
    if stem2 == 'ali':
        gen_sg = 'alīus'
    else:
        gen_sg = stem2 + 'īus'
    dat_sg = stem2 + 'ī'
    abl_sg_mn = stem2 + 'ō'
    abl_sg_f = stem2 + 'ā'
    dat_abl_pl = stem2 + 'īs'

    tags = {'pos':'pronoun', 'ja':ja}

    forms = [nom_sg_m, stem2 + 'um', gen_sg, dat_sg, abl_sg_mn,
             stem2 + 'ī', abl_sg_mn + 's', abl_sg_mn + 'rum', dat_abl_pl, dat_abl_pl]
    items += decline('', tags, forms, latin_noun.case_tags_5x2, {'gender':'m'})

    forms = [nom_sg_f, nom_sg_f + 'm', gen_sg, dat_sg, abl_sg_f,
             nom_sg_f + 'e', abl_sg_f + 's', abl_sg_f + 'rum', dat_abl_pl, dat_abl_pl]
    items += decline('', tags, forms, latin_noun.case_tags_5x2, {'gender':'f'})

    forms = [nom_sg_n, nom_sg_n, gen_sg, dat_sg, abl_sg_mn,
             nom_sg_f, nom_sg_f, abl_sg_mn + 'rum', dat_abl_pl, dat_abl_pl]
    items += decline('', tags, forms, latin_noun.case_tags_5x2, {'gender':'n'})

    # print ja, util.pp(items)
    return items

def pronominal_adjectives():
    items = []
    items += decline_pronominal_adjective(('alius', 'alia', 'aliud'), '他の')
    items += decline_pronominal_adjective(('tōtus', 'tōta', 'tōtum'), '全体の')
    items += decline_pronominal_adjective(('ūnus', 'ūna', 'ūnum'), 'ひとつの') #数詞でもある
    items += decline_pronominal_adjective(('sōlus', 'sōla', 'sōlum'), '唯一の')
    items += decline_pronominal_adjective(('ūllus', 'ūlla', 'ūllum'), 'どれかひとつの') #any
    items += decline_pronominal_adjective(('nūllus', 'nūlla', 'nūllum'), 'ひとつも...ない')
    items += decline_pronominal_adjective(('alter', 'altera', 'alterum'), '(2つのうち)どれか一方の')
    items += decline_pronominal_adjective(('uter', 'utra', 'utrum'), '(2つのうち)どちらの？,(2つのうち)どちらかの')
    items += decline_pronominal_adjective(('neuter', 'neutra', 'neutrum'), '(2つのうち)どちらも...ない')

    items += decline('', {},
                     ['nihil', 'nihil', ('nūllīus reī', 'nihilī'), 'nūllī reī', ('nūllā rē', 'nihilō')],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'n', 'ja':'なにも...ない'}) # nothing
    items += decline('', {},
                     ['nēmō', 'nēminem', 'nūllīus', 'nēminī', 'nūllō'],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'m', 'ja':'だれも...ない'}) # no one, nobody
    items += decline('', {},
                     ['nēmō', 'nēminem', 'nūllīus', 'nēminī', 'nūllō'],
                     latin_noun.case_tags_5x2[:5],
                     {'pos':'pronoun', 'gender':'f', 'ja':'だれも...ない'}) # no one, nobody
    # util.pp(items)
    return util.aggregate_cases(items)


def load():
    items = ego() + meus() + ipse() + is_ea_id() + hic() + ille() + idem() + qui() + quis() + quisque() + quidam()
    items += pronominal_adjectives()
    return items
