#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin

cases_ja = {
    'Nom':'〜が',
    'Acc':'〜を',
    'Gen':'〜の',
    'Dat':'〜に,〜のために,〜にとって',
    'Abl':'〜によって,〜でもって,〜をもって,〜において,〜から',
    'Voc':'〜よ'
}

latin_prepositions = {
    ## Acc/Abl
    u'in':{'ja':'[+Acc]〜の中へ,〜の上へ,〜に向かって,〜に対して/[+Abl]〜の中で,〜の上で'},
    u'sub':{'ja':'[+Acc]〜の下へ,〜のもとへ/[+Abl]〜の下で,〜のもとで'},

    ## Acc
    u'ad':{'ja':'〜の方へ,〜のところまで'},
    u'ante':{'ja':'〜の前に,〜以前に'},
    u'apud':{'ja':'〜の家で,〜のもとで'},
    u'circum':{'ja':'〜のまわりに'},
    u'circā':{'ja':'〜のまわりに'},
    u'contrā':{'ja':'〜に対抗して,〜に反して'},
    u'extrā':{'ja':'〜の外側で,〜の外へ'},
    u'praeter':{'ja':'〜の傍らをすぎて,〜に反して'},
    u'prope':{'ja':'〜の近くで'},
    u'propter':{'ja':'〜の近くで,〜のゆえに'},
    u'īnfrā':{'ja':'〜の下方へ,〜に劣って'},
    u'inter':{'ja':'〜の間に'},
    u'intrā':{'ja':'〜の内側で,〜の中へ'},
    u'ob':{'ja':'〜の前へ,〜ゆえに,〜の代わりに'},
    u'per':{'ja':'〜を通って,〜を通じて,〜により'},
    u'post':{'ja':'〜のうしろで,〜以後'},
    u'suprā':{'ja':'〜の上方に,〜をこえて'},
    u'trāns':{'ja':'〜をこえて,〜を通過して'},
    u'ultrā':{'ja':'〜の向こうに,〜をこえて'},

    ## Abl
    u'ā':{'ja':'〜から(離れて),〜によって'}, # ā 子音 / ab 母音
    u'ab':{'ja':'〜から(離れて),〜によって'},
    u'cum':{'ja':'〜とともに,〜をもって'},
    u'dē':{'ja':'〜から(離れて)下へ,〜について'},
    u'ē':{'ja':'〜(の中)から外へ'},
    u'ex':{'ja':'〜(の中)から外へ'},
    u'prae':{'ja':'〜の前に,〜のあまり,〜に比して'},
    u'prō':{'ja':'〜の前に,〜のために,〜の代わりに'},
    u'sine':{'ja':'〜なしに'},
}

def check_prepositions(surface):
    if latin_prepositions.has_key(surface):
        tags = {'pos':'prep'}
        info = dict(latin_prepositions[surface], **tags)
        return {'_':info}
    else:
        return {}


latindic = {
    u'et': {'pos':'conj', 'en':'and', 'ja':'と,そして'},
    u'sed': {'pos':'conj', 'en':'but', 'ja':'しかし'},
    u'saepe': {'pos':'adv', 'en':'often'},
    u'hodiē': {'pos':'adv', 'ja':'今日'},
    u'rēctē': {'pos':'adv', 'ja':'正しく,まっすぐに,その通り'},
    u'satis': {'pos':'adv', 'ja':'十分に'},
    u'quam': {'pos':'prep', 'ja':'〜より(than)'},
    }


latin_pronouns = {
    # 人称代名詞 personal pronoun
    u'ego':{'case':'Nom.sg', 'pers':1, 'type':'personal'},
    u'mē':{'case':'Acc.sg/Abl.sg', 'pers':1, 'type':'personal'},
    u'meī':{'case':'Gen.sg', 'pers':1, 'type':'personal'},
    u'mihi':{'case':'Nom.sg', 'pers':1, 'type':'personal'},
    u'mihī':{'case':'Dat.sg', 'pers':1, 'type':'personal'},
    u'nōs':{'case':'Nom.pl/Acc.pl', 'pers':1, 'type':'personal'},
    u'nostrī':{'case':'Gen.pl', 'pers':1, 'type':'personal'},
    u'nostrum':{'case':'Gen.pl', 'pers':1, 'type':'personal'}, # 部分属格
    u'nōbīs':{'case':'Dat.pl/Abl.pl', 'pers':1, 'type':'personal'},

    u'tū':{'case':'Nom.sg', 'pers':2, 'type':'personal'},
    u'tē':{'case':'Acc.sg/Abl.sg', 'pers':2, 'type':'personal'},
    u'tuī':{'case':'Gen.sg', 'pers':2, 'type':'personal'},
    u'tibi':{'case':'Dat.sg', 'pers':2, 'type':'personal'},
    u'tibī':{'case':'Dat.sg', 'pers':2, 'type':'personal'},
    u'vōs':{'case':'Nom.pl/Acc.pl', 'pers':2, 'type':'personal'},
    u'vestrī':{'case':'Gen.pl', 'pers':2, 'type':'personal'},
    u'vestrum':{'case':'Gen.pl', 'pers':2, 'type':'personal'}, # 部分属格
    u'vōbīs':{'case':'Dat.pl/Abl.pl', 'pers':2, 'type':'personal'},

    # 関係代名詞 relative pronoun
    u'quī':{'case':'Nom.sg/Nom.pl', 'gender':'m', 'type':'relative'},
    u'quae':{'case':'Nom.sg/Nom.pl', 'gender':'f/n', 'type':'relative/interrogative'},
    u'quod':{'case':'Nom.sg/Acc.sg', 'gender':'n', 'type':'relative'},
    u'quem':{'case':'Acc.sg', 'gender':'m/f', 'type':'relative/interrogative'},
    u'quam':{'case':'Acc.sg', 'gender':'f', 'type':'relative'},
    u'cūjus':{'case':'Gen.sg', 'gender':'m/f/n', 'type':'relative/interrogative'},
    u'cuī':{'case':'Dat.sg', 'gender':'m/f/n', 'type':'relative/interrogative'},
    u'quō':{'case':'Abl.sg', 'gender':'m/n', 'type':'relative/interrogative'},
    u'quā':{'case':'Abl.sg', 'gender':'f', 'type':'relative'},
    u'quōs':{'case':'Acc.pl', 'gender':'m', 'type':'relative/interrogative'},
    u'quās':{'case':'Acc.pl', 'gender':'f', 'type':'relative/interrogative'},
    u'quōrum':{'case':'Gen.pl', 'gender':'m', 'type':'relative/interrogative'},
    u'quārum':{'case':'Gen.pl', 'gender':'f', 'type':'relative/interrogative'},
    u'quibus':{'case':'Dat.pl/Abl.pl', 'gender':'m/f/n', 'type':'relative/interrogative'},

    # 疑問代名詞 interrogative pronoun
    u'quis':{'case':'Nom.sg', 'gender':'m/f', 'type':'interrogative'},
    u'quid':{'case':'Nom.sg/Acc.sg', 'gender':'n', 'type':'interrogative'},
    u'quō':{'case':'Abl.sg', 'gender':'m/f/n', 'type':'interrogative'},

}

latin_adjectives = {
    # I: -us -a -um
    u'bonus':{'ja':'良い', 'decl':'I'},
    u'malus':{'ja':'悪い', 'decl':'I'},
    u'longus':{'ja':'長い,広い', 'decl':'I'},
    u'māgnus':{'ja':'大きい', 'decl':'I'},
    u'parvus':{'ja':'小さい', 'decl':'I'},
    u'jūcundus':{'ja':'快適な', 'decl':'I'},
    u'albus':{'ja':'白い', 'decl':'I'},
    u'altus':{'ja':'高い,深い', 'decl':'I'},
    u'vānus':{'ja':'空虚な', 'decl':'I'},
    u'multus':{'ja':'多くの', 'decl':'I'},
    u'clārus':{'ja':'明瞭な,素晴らしい', 'decl':'I'},
    # u'rectus':{'ja':'正しい,まっすぐな', 'decl':'I'},
    # I: (puer) -er -era -erum
    u'līber':{'Nom.f':'lībera', 'ja':'自由な', 'decl':'I'},
    u'miser':{'Nom.f':'misera', 'ja':'みじめな', 'decl':'I'},
    # I: (ager) -er -ra -rum
    u'pulcher':{'Nom.f':'pulchra', 'ja':'美しい', 'decl':'I'},
    u'niger':{'Nom.f':'nigra', 'ja':'黒い', 'decl':'I'},
    u'aeger':{'Nom.f':'aegra', 'ja':'病める', 'decl':'I'},

    u'Trōjānus':{'ja':'トロヤの', 'decl':'I'},
    u'Graecus':{'ja':'ギリシアの', 'decl':'I'},

    # II (1) -is -is e
    u'fortis':{'ja':'勇敢な', 'decl':'II'},
    u'brevis':{'ja':'短い', 'decl':'II'},
    u'levis':{'ja':'軽い', 'decl':'II'},
    u'omnis':{'ja':'すべての', 'decl':'II'},
    u'facilis':{'ja':'容易な', 'decl':'II'},
    u'mortālis':{'ja':'死すべき', 'decl':'II'},
    u'viridis':{'ja':'緑の', 'decl':'II'},
    u'ūtilis':{'ja':'有用な', 'decl':'II'},
    u'dulcis':{'ja':'甘い', 'decl':'II'},
    u'similis':{'ja':'似た', 'decl':'II'},
    u'gravis':{'ja':'重い', 'decl':'II'},
    u'lēnis':{'ja':'穏やかな', 'decl':'II'},
    u'turpis':{'ja':'恥ずべき', 'decl':'II'},
    u'suāvis':{'ja':'快適な', 'decl':'II'},

    u'ācer':{'Gen.sg':u'ācris', 'ja':'鋭い', 'decl':'II'},
    u'celeber':{'Gen.sg':u'celebris', 'ja':'名士の', 'decl':'II'},
    u'alacer':{'Gen.sg':u'alacris', 'ja':'活発な', 'decl':'II'},
    # II (2) -x
    u'audāx':{'Gen.sg':u'audācis', 'ja':'大胆な', 'decl':'II'},
    u'ferōx':{'Gen.sg':u'ferōcis', 'ja':'凶暴な', 'decl':'II'},
    u'fēlīx':{'Gen.sg':u'fēlīcis', 'ja':'幸福な', 'decl':'II'},
    u'simplex':{'Gen.sg':u'simplicis', 'ja':'単純な', 'decl':'II'},
    # II (2) -ns -ntis
    u'prūdēns':{'Gen.sg':u'prūdentis', 'ja':'思慮ある', 'decl':'II'},
    u'arrogāns':{'Gen.sg':u'arrogantis', 'ja':'不遜な', 'decl':'II'},
    u'amāns':{'Gen.sg':u'amantis', 'ja':'情の厚い', 'decl':'II'},
    u'sapiēns':{'Gen.sg':u'sapientis', 'ja':'賢い', 'decl':'II'},
    # vetus : Abl=vetere
    u'vetus':{'Gen.sg':u'veteris', 'ja':'古い,老いた', 'decl':'II'},
    u'dīves':{'Gen.sg':u'dīvitis', 'ja':'富める', 'decl':'II'},
}

latin_nouns = {
    # I
    u'rosa':{'gender':'f', 'ja':'バラ', 'decl':'I'},
    u'aqua':{'gender':'f', 'ja':'水', 'decl':'I'},
    u'vīta':{'gender':'f', 'ja':'人生', 'decl':'I'},
    u'terra':{'gender':'f', 'ja':'地,大地', 'decl':'I'},
    u'preada':{'gender':'f', 'ja':'戦利品', 'decl':'I'},
    u'puella':{'gender':'f', 'ja':'少女', 'decl':'I'},
    u'agricola':{'gender':'m', 'ja':'農夫', 'decl':'I'},
    u'herba':{'gender':'f', 'ja':'草', 'decl':'I'},
    u'dea':{'gender':'f', 'ja':'女神', 'decl':'I'},
    u'via':{'gender':'f', 'ja':'道', 'decl':'I'},
    u'Graecia':{'gender':'f', 'ja':'ギリシア', 'decl':'I'},
    u'Rōma':{'gender':'f', 'ja':'ローマ', 'decl':'I'},
    u'poēta':{'gender':'m', 'ja':'詩人', 'decl':'I'},

    u'schola':{'gender':'f', 'ja':'学校', 'decl':'I'},
    u'fīlia':{'gender':'f', 'ja':'娘', 'decl':'I'},
    u'incola':{'gender':'f', 'ja':'住人', 'decl':'I'},
    u'rēgīna':{'gender':'f', 'ja':'女王', 'decl':'I'},
    u'laetitia':{'gender':'f', 'ja':'喜び', 'decl':'I'},
    u'prūdentia':{'gender':'f', 'ja':'思慮深さ', 'decl':'I'},
    u'patria':{'gender':'f', 'ja':'故郷,祖国', 'decl':'I'},

    u'īnsula':{'gender':'f', 'ja':'島', 'decl':'I'},

    u'Thessalia':{'gender':'f', 'ja':'テッサリア', 'decl':'I'},
    u'Phthia':{'gender':'f', 'ja':'プティア', 'decl':'I'},
    u'Trōja':{'gender':'f', 'ja':'トロヤ', 'decl':'I'},

    # II (1)-n
    u'templum':{'gender':'n', 'ja':'神殿', 'decl':'II'},
    u'bellum':{'gender':'n', 'ja':'戦争', 'decl':'II'},
    u'dōnum':{'gender':'n', 'ja':'贈物', 'decl':'II'},
    u'saeculum':{'gender':'n', 'ja':'時代', 'decl':'II'},
    u'gaudium':{'gender':'n', 'ja':'喜び', 'decl':'II'},
    u'vīnum':{'gender':'n', 'ja':'ワイン', 'decl':'II'},
    u'ōvum':{'gender':'n', 'ja':'卵', 'decl':'II'},
    u'oppidum':{'gender':'n', 'ja':'町', 'decl':'II'},
    u'rēgnum':{'gender':'n', 'ja':'王国', 'decl':'II'},
    u'ingenium':{'gender':'n', 'ja':'才能', 'decl':'II'},
    u'studium':{'gender':'n', 'ja':'努力,研究', 'decl':'II'},
    # II (1)-m
    u'dominus':{'gender':'m', 'ja':'主,主人', 'decl':'II'},
    u'amīcus':{'gender':'m', 'ja':'友人', 'decl':'II'},
    u'famulus':{'gender':'m', 'ja':'奉公人', 'decl':'II'},
    u'servus':{'gender':'m', 'ja':'奴隷', 'decl':'II'},
    u'populus':{'gender':'m', 'ja':'人民', 'decl':'II'},
    u'campus':{'gender':'m', 'ja':'平原', 'decl':'II'},
    u'mundus':{'gender':'m', 'ja':'世界', 'decl':'II'},
    u'Aegyptus':{'gender':'f', 'ja':'エジプト', 'decl':'II'},
    u'fīlius':{'gender':'m', 'ja':'息子', 'decl':'II'},
    u'animus':{'gender':'m', 'ja':'精神', 'decl':'II'},
    u'Homērus':{'gender':'m', 'ja':'ホメルス', 'decl':'II'},
    # II (2)
    u'puer':{'gender':'m', 'ja':'少年', 'decl':'II'},
    u'ager':{'gender':'m', 'ja':'少年', 'decl':'II'},
    u'liber':{'gender':'m', 'ja':'本', 'decl':'II'},
    u'faber':{'gender':'m', 'ja':'職人', 'decl':'II'},
    u'Alexander':{'gender':'m', 'ja':'アレクサンダー', 'decl':'II'},
    u'vir':{'gender':'m', 'ja':'男,夫', 'decl':'II'},
    u'magister':{'gender':'m', 'ja':'先生', 'decl':'II'},

    # III -ium (a)
    u'piscis':{'gender':'m', 'ja':'魚', 'decl':'III'},
    u'tēstis':{'gender':'m', 'ja':'証人', 'decl':'III'},
    u'auris':{'gender':'f', 'ja':'耳', 'decl':'III'},
    u'hostis':{'gender':'m', 'ja':'敵', 'decl':'III'},
    u'cīvis':{'gender':'m', 'ja':'市民', 'decl':'III'},
    u'fīnis':{'gender':'m', 'ja':'境界', 'decl':'III'},
    u'clāssis':{'gender':'f', 'ja':'艦隊', 'decl':'III'},
    u'īgnis':{'gender':'m', 'ja':'火', 'decl':'III'},
    u'amnis':{'gender':'m', 'ja':'川', 'decl':'III'},
    u'nūbēs':{'gender':'f', 'ja':'雲', 'decl':'III'},

    u'Ulixēs':{'Gen.sg':u'Ulixis', 'gender':'m', 'ja':'ウリクセス', 'decl':'III'},

    # III -ium (b)
    u'mōns':{'Gen.sg':u'montis', 'gender':'m', 'ja':'山', 'decl':'III'},
    u'dēns':{'Gen.sg':u'dentis', 'gender':'m', 'ja':'歯', 'decl':'III'},
    u'gēns':{'Gen.sg':u'gentis', 'gender':'f', 'ja':'種族', 'decl':'III'},
    u'pōns':{'Gen.sg':u'pontis', 'gender':'m', 'ja':'橋', 'decl':'III'},
    u'fōns':{'Gen.sg':u'fontis', 'gender':'m', 'ja':'泉', 'decl':'III'},
    u'mēns':{'Gen.sg':u'mentis', 'gender':'f', 'ja':'精神', 'decl':'III'},
    u'ars':{'Gen.sg':u'artis', 'gender':'f', 'ja':'術', 'decl':'III'},
    u'mors':{'Gen.sg':u'mortis', 'gender':'f', 'ja':'死', 'decl':'III'},
    u'nox':{'Gen.sg':u'noctis', 'gender':'f', 'ja':'夜', 'decl':'III'},
    u'urbs':{'Gen.sg':u'urbis', 'gender':'f', 'ja':'都市', 'decl':'III', },
    u'pars':{'Gen.sg':u'partis', 'gender':'f', 'ja':'部分', 'decl':'III', },
    # III -ium (c)
    u'cubīle':{'Gen.sg':u'cubīlis', 'gender':'n', 'ja':'寝台', 'decl':'III'},
    u'exemplar':{'Gen.sg':u'exemplāris', 'gender':'n', 'ja':'模範', 'decl':'III'},
    # III -um (a)
    u'dux':{'Gen.sg':u'ducis', 'gender':'m', 'ja':'指導者', 'decl':'III'},
    u'nātiō':{'Gen.sg':u'nātiōnis', 'gender':'f', 'ja':'国民', 'decl':'III'},
    u'rēx':{'Gen.sg':u'rēgis', 'gender':'m', 'ja':'指導者', 'decl':'III'},
    u'lēx':{'Gen.sg':u'lēgis', 'gender':'f', 'ja':'法律', 'decl':'III'},
    u'vōx':{'Gen.sg':u'vōcis', 'gender':'f', 'ja':'声', 'decl':'III'},
    u'mīles':{'Gen.sg':u'mīlitis', 'gender':'m', 'ja':'兵士', 'decl':'III'},
    u'pēs':{'Gen.sg':u'pedis', 'gender':'m', 'ja':'足', 'decl':'III'},
    u'cīvitās':{'Gen.sg':u'cīvitātis', 'gender':'f', 'ja':'国歌', 'decl':'III'},
    u'legiō':{'Gen.sg':u'legiōnis', 'gender':'f', 'ja':'軍団', 'decl':'III'},
    u'uxor':{'Gen.sg':u'uxōris', 'gender':'f', 'ja':'妻', 'decl':'III'},
    u'amor':{'Gen.sg':u'amōris', 'gender':'m', 'ja':'愛', 'decl':'III'},
    u'color':{'Gen.sg':u'colōris', 'gender':'m', 'ja':'色', 'decl':'III'},
    u'ōrātor':{'Gen.sg':u'ōrātōris', 'gender':'m', 'ja':'弁論家', 'decl':'III'},
    u'sōl':{'Gen.sg':u'sōlis', 'gender':'m', 'ja':'太陽', 'decl':'III'},
    u'homō':{'Gen.sg':u'hominis', 'gender':'m', 'ja':'人間', 'decl':'III'},
    u'imāgō':{'Gen.sg':u'imāginis', 'gender':'f', 'ja':'像,似姿', 'decl':'III'},
    # III -um (b)
    u'corpus':{'Gen.sg':u'corporis', 'gender':'n', 'ja':'身体', 'decl':'III'},
    u'nōmen':{'Gen.sg':u'nōminis', 'gender':'n', 'ja':'名', 'decl':'III'},
    u'tempus':{'Gen.sg':u'temporis', 'gender':'n', 'ja':'時', 'decl':'III'},
    u'genus':{'Gen.sg':u'generis', 'gender':'n', 'ja':'種類', 'decl':'III'},
    u'opus':{'Gen.sg':u'operis', 'gender':'n', 'ja':'仕事', 'decl':'III'},
    u'flūmen':{'Gen.sg':u'flūminis', 'gender':'n', 'ja':'川', 'decl':'III'},
    u'lūmen':{'Gen.sg':u'lūminis', 'gender':'n', 'ja':'光', 'decl':'III'},
    u'ōmen':{'Gen.sg':u'ōminis', 'gender':'n', 'ja':'前兆', 'decl':'III'},
    u'cor':{'Gen.sg':u'cordis', 'gender':'n', 'ja':'心,心臓', 'decl':'III'},
    # Gen.pl = "patrum"
    u'pater':{'Gen.sg':u'patris', 'gender':'m', 'ja':'父', 'decl':'III'},
    u'frāter':{'Gen.sg':u'frātris', 'gender':'m', 'ja':'兄弟', 'decl':'III'},
    u'canis':{'Gen.sg':u'canis', 'gender':'m', 'ja':'犬', 'decl':'III'},
    u'māter':{'Gen.sg':u'mātris', 'gender':'f', 'ja':'母', 'decl':'III'},
    u'juvenis':{'Gen.sg':u'juvenis', 'gender':'m', 'ja':'若者', 'decl':'III'},

    # IV
    u'manus':{'Gen.sg':u'manūs', 'gender':'f', 'ja':'手', 'decl':'IV'},
    u'cornū':{'Gen.sg':u'cornūs', 'gender':'n', 'ja':'角(つの)', 'decl':'IV'},
    u'exercitus':{'Gen.sg':u'exercitūs', 'gender':'m', 'ja':'軍隊', 'decl':'IV'},
    u'cursus':{'Gen.sg':u'cursūs', 'gender':'m', 'ja':'コース', 'decl':'IV'},
    u'domus':{'Gen.sg':u'domūs', 'gender':'f', 'ja':'家', 'decl':'IV'}, ## IIと混合
    u'senātus':{'Gen.sg':u'senātūs', 'gender':'m', 'ja':'元老院', 'decl':'IV'},
    u'currus':{'Gen.sg':u'currūs', 'gender':'m', 'ja':'馬車', 'decl':'IV'},
    u'adventus':{'Gen.sg':u'adventūs', 'gender':'m', 'ja':'到着', 'decl':'IV'},
    u'genū':{'Gen.sg':u'genūs', 'gender':'n', 'ja':'ひざ', 'decl':'IV'},
    u'specus':{'Gen.sg':u'specūs', 'gender':'m', 'ja':'洞穴', 'decl':'IV'}, # Dat/Abl pl "specubus"
    u'fructus':{'Gen.sg':u'fructūs', 'gender':'m', 'ja':'果実', 'decl':'IV'},
    u'gradus':{'Gen.sg':u'gradūs', 'gender':'m', 'ja':'階段,段階', 'decl':'IV'},

    ## V
    u'diēs':{'Gen.sg':u'diēī', 'gender':'m/f', 'ja':'日,昼', 'decl':'V'},
    u'rēs':{'Gen.sg':u'reī', 'gender':'f', 'ja':'物,事', 'decl':'V'},
    u'spēs':{'Gen.sg':u'speī', 'gender':'f', 'ja':'希望', 'decl':'V'},
    u'aciēs':{'Gen.sg':u'aciēī', 'gender':'f', 'ja':'戦列', 'decl':'V'},
    u'faciēs':{'Gen.sg':u'faciēī', 'gender':'f', 'ja':'顔', 'decl':'V'},
    u'speciēs':{'Gen.sg':u'speciēī', 'gender':'f', 'ja':'姿', 'decl':'V'},
    u'seriēs':{'Gen.sg':u'seriēī', 'gender':'f', 'ja':'連続,シリーズ', 'decl':'V'},
}


latin_nouns_from_Gen_sg = {}
for nom_sg in latin_nouns:
    info = latin_nouns[nom_sg]
    if info.has_key('Gen.sg'):
        latin_nouns_from_Gen_sg[ info['Gen.sg'] ] = nom_sg

latin_adjectives_from_Gen_sg_stem = {}
for nom_sg in latin_adjectives:
    info = latin_adjectives[nom_sg]
    if info.has_key('Gen.sg'):
        stem = info['Gen.sg'][:-2]
    elif nom_sg[-2:] in [u'us', u'is']:
        stem = nom_sg[:-2]
    latin_adjectives_from_Gen_sg_stem[stem] = nom_sg


def ends_with(string, ending):
    ending_len = len(ending)
    # print "> |", string[-ending_len:].encode('utf-8'), "|", ending.encode('utf-8'), "|"
    if ending_len == 0:
        return (True, string)
    elif string[-ending_len:] == ending:
        return (True, string[:-ending_len])
    else:
        return (False, string)

def check_pronoun_declensions(surface):
    if latin_pronouns.has_key(surface):
        tags = {'pos':'pron'}
        info = dict(latin_pronouns[surface], **tags)
        return {'_':info}
    else:
        return {}


def check_adjective_declensions(surface):
    ## check_noun_declensions() と共通
    results = {}

    def new_result(nom_sg, info):
        if results.has_key(nom_sg):
            old_cases = set(results[nom_sg]['case'].split('/'))
            new_cases = set(info['case'].split('/'))
            results[nom_sg]['case'] = '/'.join([c for c in old_cases.union(new_cases)])
        else:
            results[nom_sg] = info

    def check_nom_sg(surface, ending, substitute, case, tags={}):
        p, prefix = ends_with(surface, ending)
        if p:
            nom_sg = prefix + substitute
            if latin_adjectives.has_key(nom_sg):
                info = latin_adjectives[nom_sg]
                tags = dict({'surface':surface, 'base':nom_sg, 'pos':'adj', 'case':case}, **tags)
                new_result(nom_sg, dict(info, **tags))

    def check_gen_sg_stem(surface, ending, case, tags={}):
        p, gen_sg_stem = ends_with(surface, ending)
        if p:
            if latin_adjectives_from_Gen_sg_stem.has_key(gen_sg_stem):
                nom_sg = latin_adjectives_from_Gen_sg_stem[gen_sg_stem]
                info = latin_adjectives[nom_sg]
                tags = dict({'surface':surface, 'base':nom_sg, 'pos':'adj', 'case':case}, **tags)
                new_result(nom_sg, dict(info, **tags))

    check_nom_sg(surface, u'', u'', 'Nom.sg')
    check_gen_sg_stem(surface, u'is', 'Gen.sg')

    # I
    check_nom_sg(surface, u'e', u'us', 'Voc.sg.m')
    check_nom_sg(surface, u'um', u'us', 'Acc.sg.m/Nom.sg.n/Acc.sg.n')
    check_nom_sg(surface, u'ī', u'us', 'Gen.sg.m/Gen.sg.n/Nom.pl.m/Voc.pl.m')
    check_nom_sg(surface, u'ō', u'us', 'Dat.sg.m/Dat.sg.n/Abl.sg.m/Abl.sg.n')
    check_nom_sg(surface, u'a', u'us', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, u'am', u'us', 'Acc.sg.f')
    check_nom_sg(surface, u'ae', u'us', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, u'ā', u'us', 'Abl.sg.f')
    check_nom_sg(surface, u'ōs', u'us', 'Acc.pl.m')
    check_nom_sg(surface, u'ās', u'us', 'Acc.pl.f')
    check_nom_sg(surface, u'ōrum', u'us', 'Gen.pl.m/Gen.pl.n')
    check_nom_sg(surface, u'ārum', u'us', 'Gen.pl.f')
    check_nom_sg(surface, u'īs', u'us', 'Dat.pl/Abl.pl')
    # I līber (puer) - lībera, līberum
    check_nom_sg(surface, u'rum', u'r', 'Acc.sg')
    check_nom_sg(surface, u'rī', u'r', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, u'rō', u'r', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'rōs', u'r', 'Acc.pl')
    check_nom_sg(surface, u'rōrum', u'r', 'Gen.pl')
    check_nom_sg(surface, u'rīs', u'r', 'Dat.pl/Abl.pl')
    check_nom_sg(surface, u'ra', u'r', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, u'rae', u'r', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, u'ram', u'r', 'Acc.sg.f')
    check_nom_sg(surface, u'rās', u'r', 'Acc.pl.f')
    check_nom_sg(surface, u'rārum', u'r', 'Gen.pl.f')
    # I pulcher (ager) - pulchra, pulchrum
    check_nom_sg(surface, u'rum', u'er', 'Acc.sg')
    check_nom_sg(surface, u'rī', u'er', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, u'rō', u'er', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'rōs', u'er', 'Acc.pl')
    check_nom_sg(surface, u'rōrum', u'er', 'Gen.pl')
    check_nom_sg(surface, u'rīs', u'er', 'Dat.pl/Abl.pl')
    check_nom_sg(surface, u'ra', u'er', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, u'rae', u'er', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, u'ram', u'er', 'Acc.sg.f')
    check_nom_sg(surface, u'rās', u'er', 'Acc.pl.f')
    check_nom_sg(surface, u'rārum', u'er', 'Gen.pl.f')

    check_nom_sg(surface, u'rī', u'er', 'Gen.sg/Nom.pl/Voc.pl')

    # II (1)
    check_nom_sg(surface, u'em', u'is', 'Acc.sg.m/Acc.sg.f')
    check_nom_sg(surface, u'e', u'is', 'Nom.sg.n/Acc.sg.n')
    # check_nom_sg(surface, u'is', u'is', 'Gen.sg')
    check_nom_sg(surface, u'ī', u'is', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'ēs', u'is', 'Nom.pl.m/Nom.pl.f/Acc.pl.m/Acc.pl.f')
    check_nom_sg(surface, u'īs', u'is', 'Acc.pl.m/Acc.pl.f')
    check_nom_sg(surface, u'ia', u'is', 'Nom.pl.n/Acc.pl.n')
    check_nom_sg(surface, u'ium', u'is', 'Gen.pl')
    check_nom_sg(surface, u'ibus', u'is', 'Dat.pl/Acc.pl')
    # II (2)
    check_gen_sg_stem(surface, u'em', 'Acc.sg.m/Acc.sg.f')
    check_gen_sg_stem(surface, u'ī', 'Dat.sg/Abl.sg')
    check_gen_sg_stem(surface, u'e', 'Abl.sg')
    check_gen_sg_stem(surface, u'ēs', 'Nom.pl.m/Nom.pl.f/Acc.pl.m/Acc.pl.f')
    check_gen_sg_stem(surface, u'īs', 'Acc.pl.m/Acc.pl.f')
    check_gen_sg_stem(surface, u'ia', 'Nom.pl.n/Acc.pl.n')
    check_gen_sg_stem(surface, u'ium', 'Gen.pl')
    check_gen_sg_stem(surface, u'ibus', 'Dat.pl/Acc.pl')
    # veter
    check_gen_sg_stem(surface, u'a', 'Nom.pl.n/Acc.pl.n')
    check_gen_sg_stem(surface, u'um', 'Gen.pl')
    

    # 比較級
    tags = {'desc':'比較級'}
    check_gen_sg_stem(surface, u'ior', 'Nom.sg.mf', tags)
    check_gen_sg_stem(surface, u'iōrem', 'Acc.sg.mf', tags)
    check_gen_sg_stem(surface, u'iōris', 'Gen.sg', tags)
    check_gen_sg_stem(surface, u'iōri', 'Dat.sg/Abl.sg', tags)
    check_gen_sg_stem(surface, u'iōre', 'Abl.sg', tags)
    check_gen_sg_stem(surface, u'iōres', 'Nom.pl.mf', tags)
    check_gen_sg_stem(surface, u'iōrīs', 'Acc.pl.mf', tags)
    check_gen_sg_stem(surface, u'iōra', 'Nom.pl.n/Acc.pl.n', tags)
    check_gen_sg_stem(surface, u'iōrum', 'Gen.pl', tags)
    check_gen_sg_stem(surface, u'iōribus', 'Dat.pl/Abl.pl', tags)

    # 最上級
    tags = {'desc':'最上級'}
    check_gen_sg_stem(surface, u'issimus', 'Nom.sg.m', tags)
    check_gen_sg_stem(surface, u'issima', 'Nom.sg.f', tags)
    check_gen_sg_stem(surface, u'issimum', 'Nom.sg.n', tags)
    # あとはI型で
    # Nom.sgが-er -> (GenではなくNomに）-errimus
    # -ilis -> -illimus
    # bonus,malus,mAgnus,parvus,multus,multIは不規則変化

    return results


def check_noun_declensions(surface):
    results = {}

    def new_result(nom_sg, info):
        if results.has_key(nom_sg):
            old_cases = set(results[nom_sg]['case'].split('/'))
            new_cases = set(info['case'].split('/'))
            results[nom_sg]['case'] = '/'.join([c for c in old_cases.union(new_cases)])
        else:
            results[nom_sg] = info

    def check_nom_sg(surface, ending, substitute, case):
        p, prefix = ends_with(surface, ending)
        if p:
            nom_sg = prefix + substitute
            if latin_nouns.has_key(nom_sg):
                info = latin_nouns[nom_sg]
                tags = {'surface':surface, 'base':nom_sg, 'pos':'n', 'case':case}
                new_result(nom_sg, dict(info, **tags))

    def check_gen_sg(surface, ending, substitute, case):
        p, prefix = ends_with(surface, ending)
        if p:
            gen_sg = prefix + substitute
            if latin_nouns_from_Gen_sg.has_key(gen_sg):
                nom_sg = latin_nouns_from_Gen_sg[gen_sg]
                info = latin_nouns[nom_sg]
                tags = {'surface':surface, 'base':nom_sg, 'pos':'n', 'case':case}
                new_result(nom_sg, dict(info, **tags))

    check_nom_sg(surface, u'', u'', 'Nom.sg')
    check_gen_sg(surface, u'', u'', 'Gen.sg')
    # I
    # check_nom_sg(surface, 'a', 'a', 'Nom', 'sg')
    check_nom_sg(surface, u'am', u'a', 'Acc.sg')
    check_nom_sg(surface, u'ae', u'a', 'Gen.sg/Dat.sg')
    check_nom_sg(surface, u'ā', u'a', 'Abl.sg')
    check_nom_sg(surface, u'ās', u'a', 'Acc.pl')
    check_nom_sg(surface, u'ārum', u'a', 'Gen.pl')
    check_nom_sg(surface, u'īs', u'a', 'Dat.pl/Abl.pl')

    # II
    check_nom_sg(surface, u'um', u'um', 'Voc.sg/Acc.sg')
    check_nom_sg(surface, u'ī', u'um', 'Gen.sg')
    check_nom_sg(surface, u'ō', u'um', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'a', u'um', 'Nom.pl/Voc.pl/Acc.pl')
    check_nom_sg(surface, u'ōrum', u'um', 'Gen.pl')
    check_nom_sg(surface, u'īs', u'um', 'Dat.pl/Abl.pl')

    # check_nom_sg(surface, 'us', 'us', 'Nom', 'sg')
    check_nom_sg(surface, u'e', u'us', 'Voc.sg')
    check_nom_sg(surface, u'um', u'us', 'Acc.sg')
    check_nom_sg(surface, u'ī', u'us', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, u'ō', u'us', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'ōs', u'us', 'Acc.pl')
    check_nom_sg(surface, u'ōrum', u'us', 'Gen.pl')
    check_nom_sg(surface, u'īs', u'us', 'Dat.pl/Abl.pl')

    # check_nom_sg(surface, 'r', 'r', 'Nom', 'sg')
    check_nom_sg(surface, u'rum', u'r', 'Acc.sg')
    check_nom_sg(surface, u'rī', u'r', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, u'rō', u'r', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'rōs', u'r', 'Acc.pl')
    check_nom_sg(surface, u'rōrum', u'r', 'Gen.pl')
    check_nom_sg(surface, u'rīs', u'r', 'Dat.pl/Abl.pl')

    check_nom_sg(surface, u'rum', u'er', 'Acc.sg')
    check_nom_sg(surface, u'rī', u'er', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, u'rō', u'er', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, u'rōs', u'er', 'Acc.pl')
    check_nom_sg(surface, u'rōrum', u'er', 'Gen.pl')
    check_nom_sg(surface, u'rīs', u'er', 'Dat.pl/Abl.pl')

    # III -ium (a) piscis, is
    # check_nom_sg(surface, u'is', u'is', 'Nom/Gen', 'sg')
    check_nom_sg(surface, u'em', u'is', 'Acc.sg')
    check_nom_sg(surface, u'is', u'is', 'Gen.sg')
    check_nom_sg(surface, u'ī', u'is', 'Dat.sg')
    check_nom_sg(surface, u'e', u'is', 'Abl.sg')
    check_nom_sg(surface, u'ēs', u'is', 'Nom.pl/Acc.pl')
    # check_nom_sg(surface, u'īs', u'is', 'Acc', 'pl')
    check_nom_sg(surface, u'ium', u'is', 'Gen.pl')
    check_nom_sg(surface, u'ibus', u'is', 'Dat.pl/Abl.pl')

    # III -ium (b) mōns, montis
    # check_nom_sg(surface, u's', u's', 'Nom/Gen', 'sg')
    check_gen_sg(surface, u'em', u'is', 'Acc.sg')
    # check_gen_sg(surface, u'is', u'is', 'Gen', 'sg')
    check_gen_sg(surface, u'ī', u'is', 'Dat.sg')
    check_gen_sg(surface, u'e', u'is', 'Abl.sg')
    check_gen_sg(surface, u'ēs', u'is', 'Nom.pl/Acc.pl')
    # check_gen_sg(surface, u'īs', u'is', 'Acc', 'pl')
    check_gen_sg(surface, u'ium', u'is', 'Gen.pl')
    check_gen_sg(surface, u'ibus', u'is', 'Dat.pl/Abl.pl')

    # III -ium (c) animal, animālis
    check_nom_sg(surface, u'al', u'al', 'Acc.sg')
    check_nom_sg(surface, u'ar', u'ar', 'Acc.sg')
    check_gen_sg(surface, u'ī', u'is', 'Dat.sg/Abl.sg')
    check_gen_sg(surface, u'ia', u'is', 'Nom.pl/Acc.pl')
    check_gen_sg(surface, u'ium', u'is', 'Gen.pl')
    check_gen_sg(surface, u'ibus', u'is', 'Dat.pl/Abl.pl')
    # III -ium (c) mare, maris
    check_nom_sg(surface, u'e', u'e', 'Acc.sg')

    # III -um (a) dux, ducis / nātiō, nātiōnis
    check_gen_sg(surface, u'em', u'is', 'Acc.sg')
    check_gen_sg(surface, u'ī', u'is', 'Dat.sg')
    check_gen_sg(surface, u'e', u'is', 'Abl.sg')
    check_gen_sg(surface, u'ēs', u'is', 'Nom.pl/Acc.pl')
    check_gen_sg(surface, u'um', u'is', 'Gen.pl')
    check_gen_sg(surface, u'ibus', u'is', 'Dat.pl/Abl.pl')
    # III -um (b)
    check_gen_sg(surface, u'a', u'is', 'Nom.pl/Acc.pl')

    # IV manus
    check_nom_sg(surface, u'um', u'us', 'Acc.sg')
    check_nom_sg(surface, u'ūs', u'us', 'Gen.sg/Nom.pl/Acc/pl')
    check_nom_sg(surface, u'uī', u'us', 'Dat.sg')
    check_nom_sg(surface, u'ū', u'us', 'Abl.sg/Dat.sg')
    check_nom_sg(surface, u'uum', u'us', 'Gen.pl')
    check_nom_sg(surface, u'ibus', u'us', 'Dat.pl/Abl.pl')
    # cornū
    check_nom_sg(surface, u'ū', u'is', 'Acc.sg')
    check_nom_sg(surface, u'ua', u'is', 'Nom.pl/Acc.pl')

    # V
    # check_nom_sg(surface, u'ēs', u'ēs', 'Nom', 'sg')
    check_nom_sg(surface, u'em', u'ēs', 'Acc.sg')
    check_nom_sg(surface, u'ēi', u'ēs', 'Gen.sg/Dat.sg') # 母音の後
    check_nom_sg(surface, u'ē', u'ēs', 'Abl.sg')
    check_nom_sg(surface, u'ēs', u'ēs', 'Nom.pl/Acc.pl')
    check_nom_sg(surface, u'ērum', u'ēs', 'Gen.pl')
    check_nom_sg(surface, u'ēbus', u'ēs', 'Dat.pl/Abl.pl')

    check_nom_sg(surface, u'ei', u'es', 'Gen.sg/Dat.sg') # 子音の後

    return results


def lookup(word):
    # if isupper(word[0]): return None
    if word[-3:] == 'que':
        word = word[:-3]

    # print "[%s]" % word.encode('utf-8'),

    results = []

    results += check_prepositions(word).values()
    results += check_noun_declensions(word).values()
    results += check_adjective_declensions(word).values()
    results += check_pronoun_declensions(word).values()

    if latindic.has_key(word):
        results.append(latindic[word])

    return results

