#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin

latin_prepositions = {
    ## Acc/Abl
    'in':{'ja':'[+Acc]〜の中へ,〜の上へ,〜に向かって,〜に対して/[+Abl]〜の中で,〜の上で'},
    'sub':{'ja':'[+Acc]〜の下へ,〜のもとへ/[+Abl]〜の下で,〜のもとで'},

    ## Acc
    'ad':{'ja':'〜の方へ,〜のところまで'},
    'ante':{'ja':'〜の前に,〜以前に'},
    'apud':{'ja':'〜の家で,〜のもとで'},
    'circum':{'ja':'〜のまわりに'},
    'circā':{'ja':'〜のまわりに'},
    'contrā':{'ja':'〜に対抗して,〜に反して'},
    'extrā':{'ja':'〜の外側で,〜の外へ'},
    'praeter':{'ja':'〜の傍らをすぎて,〜に反して'},
    'prope':{'ja':'〜の近くで'},
    'propter':{'ja':'〜の近くで,〜のゆえに'},
    'īnfrā':{'ja':'〜の下方へ,〜に劣って'},
    'inter':{'ja':'〜の間に'},
    'intrā':{'ja':'〜の内側で,〜の中へ'},
    'ob':{'ja':'〜の前へ,〜ゆえに,〜の代わりに'},
    'per':{'ja':'〜を通って,〜を通じて,〜により'},
    'post':{'ja':'〜のうしろで,〜以後'},
    'suprā':{'ja':'〜の上方に,〜をこえて'},
    'trāns':{'ja':'〜をこえて,〜を通過して'},
    'ultrā':{'ja':'〜の向こうに,〜をこえて'},

    ## Abl
    'ā':{'ja':'〜から(離れて),〜によって'}, # ā 子音 / ab 母音
    'ab':{'ja':'〜から(離れて),〜によって'},
    'cum':{'ja':'〜とともに,〜をもって'},
    'dē':{'ja':'〜から(離れて)下へ,〜について'},
    'ē':{'ja':'〜(の中)から外へ'},
    'ex':{'ja':'〜(の中)から外へ'},
    'prae':{'ja':'〜の前に,〜のあまり,〜に比して'},
    'prō':{'ja':'〜の前に,〜のために,〜の代わりに'},
    'sine':{'ja':'〜なしに'},
}

def check_prepositions(surface):
    if surface in latin_prepositions:
        tags = {'pos':'prep'}
        info = dict(latin_prepositions[surface], **tags)
        return {'_':info}
    else:
        return {}


latindic = {
    'et': {'pos':'conj', 'en':'and', 'ja':'と,そして'},
    'sed': {'pos':'conj', 'en':'but', 'ja':'しかし'},
    'saepe': {'pos':'adv', 'en':'often'},
    'hodiē': {'pos':'adv', 'ja':'今日'},
    'rēctē': {'pos':'adv', 'ja':'正しく,まっすぐに,その通り'},
    'satis': {'pos':'adv', 'ja':'十分に'},
    'quam': {'pos':'prep', 'ja':'〜より(than)'},
    }


latin_pronouns = {
    # 人称代名詞 personal pronoun
    'ego':{'case':'Nom.sg', 'pers':1, 'type':'personal'},
    'mē':{'case':'Acc.sg/Abl.sg', 'pers':1, 'type':'personal'},
    'meī':{'case':'Gen.sg', 'pers':1, 'type':'personal'},
    'mihi':{'case':'Nom.sg', 'pers':1, 'type':'personal'},
    'mihī':{'case':'Dat.sg', 'pers':1, 'type':'personal'},
    'nōs':{'case':'Nom.pl/Acc.pl', 'pers':1, 'type':'personal'},
    'nostrī':{'case':'Gen.pl', 'pers':1, 'type':'personal'},
    'nostrum':{'case':'Gen.pl', 'pers':1, 'type':'personal'}, # 部分属格
    'nōbīs':{'case':'Dat.pl/Abl.pl', 'pers':1, 'type':'personal'},

    'tū':{'case':'Nom.sg', 'pers':2, 'type':'personal'},
    'tē':{'case':'Acc.sg/Abl.sg', 'pers':2, 'type':'personal'},
    'tuī':{'case':'Gen.sg', 'pers':2, 'type':'personal'},
    'tibi':{'case':'Dat.sg', 'pers':2, 'type':'personal'},
    'tibī':{'case':'Dat.sg', 'pers':2, 'type':'personal'},
    'vōs':{'case':'Nom.pl/Acc.pl', 'pers':2, 'type':'personal'},
    'vestrī':{'case':'Gen.pl', 'pers':2, 'type':'personal'},
    'vestrum':{'case':'Gen.pl', 'pers':2, 'type':'personal'}, # 部分属格
    'vōbīs':{'case':'Dat.pl/Abl.pl', 'pers':2, 'type':'personal'},

    # 関係代名詞 relative pronoun
    'quī':{'case':'Nom.sg/Nom.pl', 'gender':'m', 'type':'relative'},
    'quae':{'case':'Nom.sg/Nom.pl', 'gender':'f/n', 'type':'relative/interrogative'},
    'quod':{'case':'Nom.sg/Acc.sg', 'gender':'n', 'type':'relative'},
    'quem':{'case':'Acc.sg', 'gender':'m/f', 'type':'relative/interrogative'},
    'quam':{'case':'Acc.sg', 'gender':'f', 'type':'relative'},
    'cūjus':{'case':'Gen.sg', 'gender':'m/f/n', 'type':'relative/interrogative'},
    'cuī':{'case':'Dat.sg', 'gender':'m/f/n', 'type':'relative/interrogative'},
    'quō':{'case':'Abl.sg', 'gender':'m/n', 'type':'relative/interrogative'},
    'quā':{'case':'Abl.sg', 'gender':'f', 'type':'relative'},
    'quōs':{'case':'Acc.pl', 'gender':'m', 'type':'relative/interrogative'},
    'quās':{'case':'Acc.pl', 'gender':'f', 'type':'relative/interrogative'},
    'quōrum':{'case':'Gen.pl', 'gender':'m', 'type':'relative/interrogative'},
    'quārum':{'case':'Gen.pl', 'gender':'f', 'type':'relative/interrogative'},
    'quibus':{'case':'Dat.pl/Abl.pl', 'gender':'m/f/n', 'type':'relative/interrogative'},

    # 疑問代名詞 interrogative pronoun
    'quis':{'case':'Nom.sg', 'gender':'m/f', 'type':'interrogative'},
    'quid':{'case':'Nom.sg/Acc.sg', 'gender':'n', 'type':'interrogative'},
    'quō':{'case':'Abl.sg', 'gender':'m/f/n', 'type':'interrogative'},

}

latin_adjectives = {
    # I: -us -a -um
    'bonus':{'ja':'良い', 'decl':'I'},
    'malus':{'ja':'悪い', 'decl':'I'},
    'longus':{'ja':'長い,広い', 'decl':'I'},
    'māgnus':{'ja':'大きい', 'decl':'I'},
    'parvus':{'ja':'小さい', 'decl':'I'},
    'jūcundus':{'ja':'快適な', 'decl':'I'},
    'albus':{'ja':'白い', 'decl':'I'},
    'altus':{'ja':'高い,深い', 'decl':'I'},
    'vānus':{'ja':'空虚な', 'decl':'I'},
    'multus':{'ja':'多くの', 'decl':'I'},
    'clārus':{'ja':'明瞭な,素晴らしい', 'decl':'I'},
    # u'rectus':{'ja':'正しい,まっすぐな', 'decl':'I'},
    # I: (puer) -er -era -erum
    'līber':{'Nom.f':'lībera', 'ja':'自由な', 'decl':'I'},
    'miser':{'Nom.f':'misera', 'ja':'みじめな', 'decl':'I'},
    # I: (ager) -er -ra -rum
    'pulcher':{'Nom.f':'pulchra', 'ja':'美しい', 'decl':'I'},
    'niger':{'Nom.f':'nigra', 'ja':'黒い', 'decl':'I'},
    'aeger':{'Nom.f':'aegra', 'ja':'病める', 'decl':'I'},

    'Trōjānus':{'ja':'トロヤの', 'decl':'I'},
    'Graecus':{'ja':'ギリシアの', 'decl':'I'},

    # II (1) -is -is e
    'fortis':{'ja':'勇敢な', 'decl':'II'},
    'brevis':{'ja':'短い', 'decl':'II'},
    'levis':{'ja':'軽い', 'decl':'II'},
    'omnis':{'ja':'すべての', 'decl':'II'},
    'facilis':{'ja':'容易な', 'decl':'II'},
    'mortālis':{'ja':'死すべき', 'decl':'II'},
    'viridis':{'ja':'緑の', 'decl':'II'},
    'ūtilis':{'ja':'有用な', 'decl':'II'},
    'dulcis':{'ja':'甘い', 'decl':'II'},
    'similis':{'ja':'似た', 'decl':'II'},
    'gravis':{'ja':'重い', 'decl':'II'},
    'lēnis':{'ja':'穏やかな', 'decl':'II'},
    'turpis':{'ja':'恥ずべき', 'decl':'II'},
    'suāvis':{'ja':'快適な', 'decl':'II'},

    'ācer':{'Gen.sg':'ācris', 'ja':'鋭い', 'decl':'II'},
    'celeber':{'Gen.sg':'celebris', 'ja':'名士の', 'decl':'II'},
    'alacer':{'Gen.sg':'alacris', 'ja':'活発な', 'decl':'II'},
    # II (2) -x
    'audāx':{'Gen.sg':'audācis', 'ja':'大胆な', 'decl':'II'},
    'ferōx':{'Gen.sg':'ferōcis', 'ja':'凶暴な', 'decl':'II'},
    'fēlīx':{'Gen.sg':'fēlīcis', 'ja':'幸福な', 'decl':'II'},
    'simplex':{'Gen.sg':'simplicis', 'ja':'単純な', 'decl':'II'},
    # II (2) -ns -ntis
    'prūdēns':{'Gen.sg':'prūdentis', 'ja':'思慮ある', 'decl':'II'},
    'arrogāns':{'Gen.sg':'arrogantis', 'ja':'不遜な', 'decl':'II'},
    'amāns':{'Gen.sg':'amantis', 'ja':'情の厚い', 'decl':'II'},
    'sapiēns':{'Gen.sg':'sapientis', 'ja':'賢い', 'decl':'II'},
    # vetus : Abl=vetere
    'vetus':{'Gen.sg':'veteris', 'ja':'古い,老いた', 'decl':'II'},
    'dīves':{'Gen.sg':'dīvitis', 'ja':'富める', 'decl':'II'},
}

latin_nouns = {
    # I
    'rosa':{'gender':'f', 'ja':'バラ', 'decl':'I'},
    'aqua':{'gender':'f', 'ja':'水', 'decl':'I'},
    'vīta':{'gender':'f', 'ja':'人生', 'decl':'I'},
    'terra':{'gender':'f', 'ja':'地,大地', 'decl':'I'},
    'preada':{'gender':'f', 'ja':'戦利品', 'decl':'I'},
    'puella':{'gender':'f', 'ja':'少女', 'decl':'I'},
    'agricola':{'gender':'m', 'ja':'農夫', 'decl':'I'},
    'herba':{'gender':'f', 'ja':'草', 'decl':'I'},
    'dea':{'gender':'f', 'ja':'女神', 'decl':'I'},
    'via':{'gender':'f', 'ja':'道', 'decl':'I'},
    'Graecia':{'gender':'f', 'ja':'ギリシア', 'decl':'I'},
    'Rōma':{'gender':'f', 'ja':'ローマ', 'decl':'I'},
    'poēta':{'gender':'m', 'ja':'詩人', 'decl':'I'},

    'schola':{'gender':'f', 'ja':'学校', 'decl':'I'},
    'fīlia':{'gender':'f', 'ja':'娘', 'decl':'I'},
    'incola':{'gender':'f', 'ja':'住人', 'decl':'I'},
    'rēgīna':{'gender':'f', 'ja':'女王', 'decl':'I'},
    'laetitia':{'gender':'f', 'ja':'喜び', 'decl':'I'},
    'prūdentia':{'gender':'f', 'ja':'思慮深さ', 'decl':'I'},
    'patria':{'gender':'f', 'ja':'故郷,祖国', 'decl':'I'},

    'īnsula':{'gender':'f', 'ja':'島', 'decl':'I'},

    'Thessalia':{'gender':'f', 'ja':'テッサリア', 'decl':'I'},
    'Phthia':{'gender':'f', 'ja':'プティア', 'decl':'I'},
    'Trōja':{'gender':'f', 'ja':'トロヤ', 'decl':'I'},

    # II (1)-n
    'templum':{'gender':'n', 'ja':'神殿', 'decl':'II'},
    'bellum':{'gender':'n', 'ja':'戦争', 'decl':'II'},
    'dōnum':{'gender':'n', 'ja':'贈物', 'decl':'II'},
    'saeculum':{'gender':'n', 'ja':'時代', 'decl':'II'},
    'gaudium':{'gender':'n', 'ja':'喜び', 'decl':'II'},
    'vīnum':{'gender':'n', 'ja':'ワイン', 'decl':'II'},
    'ōvum':{'gender':'n', 'ja':'卵', 'decl':'II'},
    'oppidum':{'gender':'n', 'ja':'町', 'decl':'II'},
    'rēgnum':{'gender':'n', 'ja':'王国', 'decl':'II'},
    'ingenium':{'gender':'n', 'ja':'才能', 'decl':'II'},
    'studium':{'gender':'n', 'ja':'努力,研究', 'decl':'II'},
    # II (1)-m
    'dominus':{'gender':'m', 'ja':'主,主人', 'decl':'II'},
    'amīcus':{'gender':'m', 'ja':'友人', 'decl':'II'},
    'famulus':{'gender':'m', 'ja':'奉公人', 'decl':'II'},
    'servus':{'gender':'m', 'ja':'奴隷', 'decl':'II'},
    'populus':{'gender':'m', 'ja':'人民', 'decl':'II'},
    'campus':{'gender':'m', 'ja':'平原', 'decl':'II'},
    'mundus':{'gender':'m', 'ja':'世界', 'decl':'II'},
    'Aegyptus':{'gender':'f', 'ja':'エジプト', 'decl':'II'},
    'fīlius':{'gender':'m', 'ja':'息子', 'decl':'II'},
    'animus':{'gender':'m', 'ja':'精神', 'decl':'II'},
    'Homērus':{'gender':'m', 'ja':'ホメルス', 'decl':'II'},
    # II (2)
    'puer':{'gender':'m', 'ja':'少年', 'decl':'II'},
    'ager':{'gender':'m', 'ja':'少年', 'decl':'II'},
    'liber':{'gender':'m', 'ja':'本', 'decl':'II'},
    'faber':{'gender':'m', 'ja':'職人', 'decl':'II'},
    'Alexander':{'gender':'m', 'ja':'アレクサンダー', 'decl':'II'},
    'vir':{'gender':'m', 'ja':'男,夫', 'decl':'II'},
    'magister':{'gender':'m', 'ja':'先生', 'decl':'II'},

    # III -ium (a)
    'piscis':{'gender':'m', 'ja':'魚', 'decl':'III'},
    'tēstis':{'gender':'m', 'ja':'証人', 'decl':'III'},
    'auris':{'gender':'f', 'ja':'耳', 'decl':'III'},
    'hostis':{'gender':'m', 'ja':'敵', 'decl':'III'},
    'cīvis':{'gender':'m', 'ja':'市民', 'decl':'III'},
    'fīnis':{'gender':'m', 'ja':'境界', 'decl':'III'},
    'clāssis':{'gender':'f', 'ja':'艦隊', 'decl':'III'},
    'īgnis':{'gender':'m', 'ja':'火', 'decl':'III'},
    'amnis':{'gender':'m', 'ja':'川', 'decl':'III'},
    'nūbēs':{'gender':'f', 'ja':'雲', 'decl':'III'},

    'Ulixēs':{'Gen.sg':'Ulixis', 'gender':'m', 'ja':'ウリクセス', 'decl':'III'},

    # III -ium (b)
    'mōns':{'Gen.sg':'montis', 'gender':'m', 'ja':'山', 'decl':'III'},
    'dēns':{'Gen.sg':'dentis', 'gender':'m', 'ja':'歯', 'decl':'III'},
    'gēns':{'Gen.sg':'gentis', 'gender':'f', 'ja':'種族', 'decl':'III'},
    'pōns':{'Gen.sg':'pontis', 'gender':'m', 'ja':'橋', 'decl':'III'},
    'fōns':{'Gen.sg':'fontis', 'gender':'m', 'ja':'泉', 'decl':'III'},
    'mēns':{'Gen.sg':'mentis', 'gender':'f', 'ja':'精神', 'decl':'III'},
    'ars':{'Gen.sg':'artis', 'gender':'f', 'ja':'術', 'decl':'III'},
    'mors':{'Gen.sg':'mortis', 'gender':'f', 'ja':'死', 'decl':'III'},
    'nox':{'Gen.sg':'noctis', 'gender':'f', 'ja':'夜', 'decl':'III'},
    'urbs':{'Gen.sg':'urbis', 'gender':'f', 'ja':'都市', 'decl':'III', },
    'pars':{'Gen.sg':'partis', 'gender':'f', 'ja':'部分', 'decl':'III', },
    # III -ium (c)
    'cubīle':{'Gen.sg':'cubīlis', 'gender':'n', 'ja':'寝台', 'decl':'III'},
    'exemplar':{'Gen.sg':'exemplāris', 'gender':'n', 'ja':'模範', 'decl':'III'},
    # III -um (a)
    'dux':{'Gen.sg':'ducis', 'gender':'m', 'ja':'指導者', 'decl':'III'},
    'nātiō':{'Gen.sg':'nātiōnis', 'gender':'f', 'ja':'国民', 'decl':'III'},
    'rēx':{'Gen.sg':'rēgis', 'gender':'m', 'ja':'指導者', 'decl':'III'},
    'lēx':{'Gen.sg':'lēgis', 'gender':'f', 'ja':'法律', 'decl':'III'},
    'vōx':{'Gen.sg':'vōcis', 'gender':'f', 'ja':'声', 'decl':'III'},
    'mīles':{'Gen.sg':'mīlitis', 'gender':'m', 'ja':'兵士', 'decl':'III'},
    'pēs':{'Gen.sg':'pedis', 'gender':'m', 'ja':'足', 'decl':'III'},
    'cīvitās':{'Gen.sg':'cīvitātis', 'gender':'f', 'ja':'国歌', 'decl':'III'},
    'legiō':{'Gen.sg':'legiōnis', 'gender':'f', 'ja':'軍団', 'decl':'III'},
    'uxor':{'Gen.sg':'uxōris', 'gender':'f', 'ja':'妻', 'decl':'III'},
    'amor':{'Gen.sg':'amōris', 'gender':'m', 'ja':'愛', 'decl':'III'},
    'color':{'Gen.sg':'colōris', 'gender':'m', 'ja':'色', 'decl':'III'},
    'ōrātor':{'Gen.sg':'ōrātōris', 'gender':'m', 'ja':'弁論家', 'decl':'III'},
    'sōl':{'Gen.sg':'sōlis', 'gender':'m', 'ja':'太陽', 'decl':'III'},
    'homō':{'Gen.sg':'hominis', 'gender':'m', 'ja':'人間', 'decl':'III'},
    'imāgō':{'Gen.sg':'imāginis', 'gender':'f', 'ja':'像,似姿', 'decl':'III'},
    # III -um (b)
    'corpus':{'Gen.sg':'corporis', 'gender':'n', 'ja':'身体', 'decl':'III'},
    'nōmen':{'Gen.sg':'nōminis', 'gender':'n', 'ja':'名', 'decl':'III'},
    'tempus':{'Gen.sg':'temporis', 'gender':'n', 'ja':'時', 'decl':'III'},
    'genus':{'Gen.sg':'generis', 'gender':'n', 'ja':'種類', 'decl':'III'},
    'opus':{'Gen.sg':'operis', 'gender':'n', 'ja':'仕事', 'decl':'III'},
    'flūmen':{'Gen.sg':'flūminis', 'gender':'n', 'ja':'川', 'decl':'III'},
    'lūmen':{'Gen.sg':'lūminis', 'gender':'n', 'ja':'光', 'decl':'III'},
    'ōmen':{'Gen.sg':'ōminis', 'gender':'n', 'ja':'前兆', 'decl':'III'},
    'cor':{'Gen.sg':'cordis', 'gender':'n', 'ja':'心,心臓', 'decl':'III'},
    # Gen.pl = "patrum"
    'pater':{'Gen.sg':'patris', 'gender':'m', 'ja':'父', 'decl':'III'},
    'frāter':{'Gen.sg':'frātris', 'gender':'m', 'ja':'兄弟', 'decl':'III'},
    'canis':{'Gen.sg':'canis', 'gender':'m', 'ja':'犬', 'decl':'III'},
    'māter':{'Gen.sg':'mātris', 'gender':'f', 'ja':'母', 'decl':'III'},
    'juvenis':{'Gen.sg':'juvenis', 'gender':'m', 'ja':'若者', 'decl':'III'},

    # IV
    'manus':{'Gen.sg':'manūs', 'gender':'f', 'ja':'手', 'decl':'IV'},
    'cornū':{'Gen.sg':'cornūs', 'gender':'n', 'ja':'角(つの)', 'decl':'IV'},
    'exercitus':{'Gen.sg':'exercitūs', 'gender':'m', 'ja':'軍隊', 'decl':'IV'},
    'cursus':{'Gen.sg':'cursūs', 'gender':'m', 'ja':'コース', 'decl':'IV'},
    'domus':{'Gen.sg':'domūs', 'gender':'f', 'ja':'家', 'decl':'IV'}, ## IIと混合
    'senātus':{'Gen.sg':'senātūs', 'gender':'m', 'ja':'元老院', 'decl':'IV'},
    'currus':{'Gen.sg':'currūs', 'gender':'m', 'ja':'馬車', 'decl':'IV'},
    'adventus':{'Gen.sg':'adventūs', 'gender':'m', 'ja':'到着', 'decl':'IV'},
    'genū':{'Gen.sg':'genūs', 'gender':'n', 'ja':'ひざ', 'decl':'IV'},
    'specus':{'Gen.sg':'specūs', 'gender':'m', 'ja':'洞穴', 'decl':'IV'}, # Dat/Abl pl "specubus"
    'fructus':{'Gen.sg':'fructūs', 'gender':'m', 'ja':'果実', 'decl':'IV'},
    'gradus':{'Gen.sg':'gradūs', 'gender':'m', 'ja':'階段,段階', 'decl':'IV'},

    ## V
    'diēs':{'Gen.sg':'diēī', 'gender':'m/f', 'ja':'日,昼', 'decl':'V'},
    'rēs':{'Gen.sg':'reī', 'gender':'f', 'ja':'物,事', 'decl':'V'},
    'spēs':{'Gen.sg':'speī', 'gender':'f', 'ja':'希望', 'decl':'V'},
    'aciēs':{'Gen.sg':'aciēī', 'gender':'f', 'ja':'戦列', 'decl':'V'},
    'faciēs':{'Gen.sg':'faciēī', 'gender':'f', 'ja':'顔', 'decl':'V'},
    'speciēs':{'Gen.sg':'speciēī', 'gender':'f', 'ja':'姿', 'decl':'V'},
    'seriēs':{'Gen.sg':'seriēī', 'gender':'f', 'ja':'連続,シリーズ', 'decl':'V'},
}


latin_nouns_from_Gen_sg = {}
for nom_sg in latin_nouns:
    info = latin_nouns[nom_sg]
    if 'Gen.sg' in info:
        latin_nouns_from_Gen_sg[ info['Gen.sg'] ] = nom_sg

latin_adjectives_from_Gen_sg_stem = {}
for nom_sg in latin_adjectives:
    info = latin_adjectives[nom_sg]
    if 'Gen.sg' in info:
        stem = info['Gen.sg'][:-2]
    elif nom_sg[-2:] in ['us', 'is']:
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
    if surface in latin_pronouns:
        tags = {'pos':'pron'}
        info = dict(latin_pronouns[surface], **tags)
        return {'_':info}
    else:
        return {}


def check_adjective_declensions(surface):
    ## check_noun_declensions() と共通
    results = {}

    def new_result(nom_sg, info):
        if nom_sg in results:
            old_cases = set(results[nom_sg]['case'].split('/'))
            new_cases = set(info['case'].split('/'))
            results[nom_sg]['case'] = '/'.join([c for c in old_cases.union(new_cases)])
        else:
            results[nom_sg] = info

    def check_nom_sg(surface, ending, substitute, case, tags={}):
        p, prefix = ends_with(surface, ending)
        if p:
            nom_sg = prefix + substitute
            if nom_sg in latin_adjectives:
                info = latin_adjectives[nom_sg]
                tags = dict({'surface':surface, 'base':nom_sg, 'pos':'adj', 'case':case}, **tags)
                new_result(nom_sg, dict(info, **tags))

    def check_gen_sg_stem(surface, ending, case, tags={}):
        p, gen_sg_stem = ends_with(surface, ending)
        if p:
            if gen_sg_stem in latin_adjectives_from_Gen_sg_stem:
                nom_sg = latin_adjectives_from_Gen_sg_stem[gen_sg_stem]
                info = latin_adjectives[nom_sg]
                tags = dict({'surface':surface, 'base':nom_sg, 'pos':'adj', 'case':case}, **tags)
                new_result(nom_sg, dict(info, **tags))

    check_nom_sg(surface, '', '', 'Nom.sg')
    check_gen_sg_stem(surface, 'is', 'Gen.sg')

    # I
    check_nom_sg(surface, 'e', 'us', 'Voc.sg.m')
    check_nom_sg(surface, 'um', 'us', 'Acc.sg.m/Nom.sg.n/Acc.sg.n')
    check_nom_sg(surface, 'ī', 'us', 'Gen.sg.m/Gen.sg.n/Nom.pl.m/Voc.pl.m')
    check_nom_sg(surface, 'ō', 'us', 'Dat.sg.m/Dat.sg.n/Abl.sg.m/Abl.sg.n')
    check_nom_sg(surface, 'a', 'us', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, 'am', 'us', 'Acc.sg.f')
    check_nom_sg(surface, 'ae', 'us', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, 'ā', 'us', 'Abl.sg.f')
    check_nom_sg(surface, 'ōs', 'us', 'Acc.pl.m')
    check_nom_sg(surface, 'ās', 'us', 'Acc.pl.f')
    check_nom_sg(surface, 'ōrum', 'us', 'Gen.pl.m/Gen.pl.n')
    check_nom_sg(surface, 'ārum', 'us', 'Gen.pl.f')
    check_nom_sg(surface, 'īs', 'us', 'Dat.pl/Abl.pl')
    # I līber (puer) - lībera, līberum
    check_nom_sg(surface, 'rum', 'r', 'Acc.sg')
    check_nom_sg(surface, 'rī', 'r', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, 'rō', 'r', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'rōs', 'r', 'Acc.pl')
    check_nom_sg(surface, 'rōrum', 'r', 'Gen.pl')
    check_nom_sg(surface, 'rīs', 'r', 'Dat.pl/Abl.pl')
    check_nom_sg(surface, 'ra', 'r', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, 'rae', 'r', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, 'ram', 'r', 'Acc.sg.f')
    check_nom_sg(surface, 'rās', 'r', 'Acc.pl.f')
    check_nom_sg(surface, 'rārum', 'r', 'Gen.pl.f')
    # I pulcher (ager) - pulchra, pulchrum
    check_nom_sg(surface, 'rum', 'er', 'Acc.sg')
    check_nom_sg(surface, 'rī', 'er', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, 'rō', 'er', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'rōs', 'er', 'Acc.pl')
    check_nom_sg(surface, 'rōrum', 'er', 'Gen.pl')
    check_nom_sg(surface, 'rīs', 'er', 'Dat.pl/Abl.pl')
    check_nom_sg(surface, 'ra', 'er', 'Nom.sg.f/Voc.sg.f/Nom.pl.n/Voc.pl.n/Acc.pl.n')
    check_nom_sg(surface, 'rae', 'er', 'Gen.sg.f/Dat.sg.f/Nom.pl.f/Voc.pl.f')
    check_nom_sg(surface, 'ram', 'er', 'Acc.sg.f')
    check_nom_sg(surface, 'rās', 'er', 'Acc.pl.f')
    check_nom_sg(surface, 'rārum', 'er', 'Gen.pl.f')

    check_nom_sg(surface, 'rī', 'er', 'Gen.sg/Nom.pl/Voc.pl')

    # II (1)
    check_nom_sg(surface, 'em', 'is', 'Acc.sg.m/Acc.sg.f')
    check_nom_sg(surface, 'e', 'is', 'Nom.sg.n/Acc.sg.n')
    # check_nom_sg(surface, u'is', u'is', 'Gen.sg')
    check_nom_sg(surface, 'ī', 'is', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'ēs', 'is', 'Nom.pl.m/Nom.pl.f/Acc.pl.m/Acc.pl.f')
    check_nom_sg(surface, 'īs', 'is', 'Acc.pl.m/Acc.pl.f')
    check_nom_sg(surface, 'ia', 'is', 'Nom.pl.n/Acc.pl.n')
    check_nom_sg(surface, 'ium', 'is', 'Gen.pl')
    check_nom_sg(surface, 'ibus', 'is', 'Dat.pl/Acc.pl')
    # II (2)
    check_gen_sg_stem(surface, 'em', 'Acc.sg.m/Acc.sg.f')
    check_gen_sg_stem(surface, 'ī', 'Dat.sg/Abl.sg')
    check_gen_sg_stem(surface, 'e', 'Abl.sg')
    check_gen_sg_stem(surface, 'ēs', 'Nom.pl.m/Nom.pl.f/Acc.pl.m/Acc.pl.f')
    check_gen_sg_stem(surface, 'īs', 'Acc.pl.m/Acc.pl.f')
    check_gen_sg_stem(surface, 'ia', 'Nom.pl.n/Acc.pl.n')
    check_gen_sg_stem(surface, 'ium', 'Gen.pl')
    check_gen_sg_stem(surface, 'ibus', 'Dat.pl/Acc.pl')
    # veter
    check_gen_sg_stem(surface, 'a', 'Nom.pl.n/Acc.pl.n')
    check_gen_sg_stem(surface, 'um', 'Gen.pl')
    

    # 比較級
    tags = {'desc':'比較級'}
    check_gen_sg_stem(surface, 'ior', 'Nom.sg.mf', tags)
    check_gen_sg_stem(surface, 'iōrem', 'Acc.sg.mf', tags)
    check_gen_sg_stem(surface, 'iōris', 'Gen.sg', tags)
    check_gen_sg_stem(surface, 'iōri', 'Dat.sg/Abl.sg', tags)
    check_gen_sg_stem(surface, 'iōre', 'Abl.sg', tags)
    check_gen_sg_stem(surface, 'iōres', 'Nom.pl.mf', tags)
    check_gen_sg_stem(surface, 'iōrīs', 'Acc.pl.mf', tags)
    check_gen_sg_stem(surface, 'iōra', 'Nom.pl.n/Acc.pl.n', tags)
    check_gen_sg_stem(surface, 'iōrum', 'Gen.pl', tags)
    check_gen_sg_stem(surface, 'iōribus', 'Dat.pl/Abl.pl', tags)

    # 最上級
    tags = {'desc':'最上級'}
    check_gen_sg_stem(surface, 'issimus', 'Nom.sg.m', tags)
    check_gen_sg_stem(surface, 'issima', 'Nom.sg.f', tags)
    check_gen_sg_stem(surface, 'issimum', 'Nom.sg.n', tags)
    # あとはI型で
    # Nom.sgが-er -> (GenではなくNomに）-errimus
    # -ilis -> -illimus
    # bonus,malus,mAgnus,parvus,multus,multIは不規則変化

    return results


def check_noun_declensions(surface):
    results = {}

    def new_result(nom_sg, info):
        if nom_sg in results:
            old_cases = set(results[nom_sg]['case'].split('/'))
            new_cases = set(info['case'].split('/'))
            results[nom_sg]['case'] = '/'.join([c for c in old_cases.union(new_cases)])
        else:
            results[nom_sg] = info

    def check_nom_sg(surface, ending, substitute, case):
        p, prefix = ends_with(surface, ending)
        if p:
            nom_sg = prefix + substitute
            if nom_sg in latin_nouns:
                info = latin_nouns[nom_sg]
                tags = {'surface':surface, 'base':nom_sg, 'pos':'n', 'case':case}
                new_result(nom_sg, dict(info, **tags))

    def check_gen_sg(surface, ending, substitute, case):
        p, prefix = ends_with(surface, ending)
        if p:
            gen_sg = prefix + substitute
            if gen_sg in latin_nouns_from_Gen_sg:
                nom_sg = latin_nouns_from_Gen_sg[gen_sg]
                info = latin_nouns[nom_sg]
                tags = {'surface':surface, 'base':nom_sg, 'pos':'n', 'case':case}
                new_result(nom_sg, dict(info, **tags))

    check_nom_sg(surface, '', '', 'Nom.sg')
    check_gen_sg(surface, '', '', 'Gen.sg')
    # I
    # check_nom_sg(surface, 'a', 'a', 'Nom', 'sg')
    check_nom_sg(surface, 'am', 'a', 'Acc.sg')
    check_nom_sg(surface, 'ae', 'a', 'Gen.sg/Dat.sg')
    check_nom_sg(surface, 'ā', 'a', 'Abl.sg')
    check_nom_sg(surface, 'ās', 'a', 'Acc.pl')
    check_nom_sg(surface, 'ārum', 'a', 'Gen.pl')
    check_nom_sg(surface, 'īs', 'a', 'Dat.pl/Abl.pl')

    # II
    check_nom_sg(surface, 'um', 'um', 'Voc.sg/Acc.sg')
    check_nom_sg(surface, 'ī', 'um', 'Gen.sg')
    check_nom_sg(surface, 'ō', 'um', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'a', 'um', 'Nom.pl/Voc.pl/Acc.pl')
    check_nom_sg(surface, 'ōrum', 'um', 'Gen.pl')
    check_nom_sg(surface, 'īs', 'um', 'Dat.pl/Abl.pl')

    # check_nom_sg(surface, 'us', 'us', 'Nom', 'sg')
    check_nom_sg(surface, 'e', 'us', 'Voc.sg')
    check_nom_sg(surface, 'um', 'us', 'Acc.sg')
    check_nom_sg(surface, 'ī', 'us', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, 'ō', 'us', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'ōs', 'us', 'Acc.pl')
    check_nom_sg(surface, 'ōrum', 'us', 'Gen.pl')
    check_nom_sg(surface, 'īs', 'us', 'Dat.pl/Abl.pl')

    # check_nom_sg(surface, 'r', 'r', 'Nom', 'sg')
    check_nom_sg(surface, 'rum', 'r', 'Acc.sg')
    check_nom_sg(surface, 'rī', 'r', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, 'rō', 'r', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'rōs', 'r', 'Acc.pl')
    check_nom_sg(surface, 'rōrum', 'r', 'Gen.pl')
    check_nom_sg(surface, 'rīs', 'r', 'Dat.pl/Abl.pl')

    check_nom_sg(surface, 'rum', 'er', 'Acc.sg')
    check_nom_sg(surface, 'rī', 'er', 'Gen.sg/Nom.pl/Voc.pl')
    check_nom_sg(surface, 'rō', 'er', 'Dat.sg/Abl.sg')
    check_nom_sg(surface, 'rōs', 'er', 'Acc.pl')
    check_nom_sg(surface, 'rōrum', 'er', 'Gen.pl')
    check_nom_sg(surface, 'rīs', 'er', 'Dat.pl/Abl.pl')

    # III -ium (a) piscis, is
    # check_nom_sg(surface, u'is', u'is', 'Nom/Gen', 'sg')
    check_nom_sg(surface, 'em', 'is', 'Acc.sg')
    check_nom_sg(surface, 'is', 'is', 'Gen.sg')
    check_nom_sg(surface, 'ī', 'is', 'Dat.sg')
    check_nom_sg(surface, 'e', 'is', 'Abl.sg')
    check_nom_sg(surface, 'ēs', 'is', 'Nom.pl/Acc.pl')
    # check_nom_sg(surface, u'īs', u'is', 'Acc', 'pl')
    check_nom_sg(surface, 'ium', 'is', 'Gen.pl')
    check_nom_sg(surface, 'ibus', 'is', 'Dat.pl/Abl.pl')

    # III -ium (b) mōns, montis
    # check_nom_sg(surface, u's', u's', 'Nom/Gen', 'sg')
    check_gen_sg(surface, 'em', 'is', 'Acc.sg')
    # check_gen_sg(surface, u'is', u'is', 'Gen', 'sg')
    check_gen_sg(surface, 'ī', 'is', 'Dat.sg')
    check_gen_sg(surface, 'e', 'is', 'Abl.sg')
    check_gen_sg(surface, 'ēs', 'is', 'Nom.pl/Acc.pl')
    # check_gen_sg(surface, u'īs', u'is', 'Acc', 'pl')
    check_gen_sg(surface, 'ium', 'is', 'Gen.pl')
    check_gen_sg(surface, 'ibus', 'is', 'Dat.pl/Abl.pl')

    # III -ium (c) animal, animālis
    check_nom_sg(surface, 'al', 'al', 'Acc.sg')
    check_nom_sg(surface, 'ar', 'ar', 'Acc.sg')
    check_gen_sg(surface, 'ī', 'is', 'Dat.sg/Abl.sg')
    check_gen_sg(surface, 'ia', 'is', 'Nom.pl/Acc.pl')
    check_gen_sg(surface, 'ium', 'is', 'Gen.pl')
    check_gen_sg(surface, 'ibus', 'is', 'Dat.pl/Abl.pl')
    # III -ium (c) mare, maris
    check_nom_sg(surface, 'e', 'e', 'Acc.sg')

    # III -um (a) dux, ducis / nātiō, nātiōnis
    check_gen_sg(surface, 'em', 'is', 'Acc.sg')
    check_gen_sg(surface, 'ī', 'is', 'Dat.sg')
    check_gen_sg(surface, 'e', 'is', 'Abl.sg')
    check_gen_sg(surface, 'ēs', 'is', 'Nom.pl/Acc.pl')
    check_gen_sg(surface, 'um', 'is', 'Gen.pl')
    check_gen_sg(surface, 'ibus', 'is', 'Dat.pl/Abl.pl')
    # III -um (b)
    check_gen_sg(surface, 'a', 'is', 'Nom.pl/Acc.pl')

    # IV manus
    check_nom_sg(surface, 'um', 'us', 'Acc.sg')
    check_nom_sg(surface, 'ūs', 'us', 'Gen.sg/Nom.pl/Acc/pl')
    check_nom_sg(surface, 'uī', 'us', 'Dat.sg')
    check_nom_sg(surface, 'ū', 'us', 'Abl.sg/Dat.sg')
    check_nom_sg(surface, 'uum', 'us', 'Gen.pl')
    check_nom_sg(surface, 'ibus', 'us', 'Dat.pl/Abl.pl')
    # cornū
    check_nom_sg(surface, 'ū', 'is', 'Acc.sg')
    check_nom_sg(surface, 'ua', 'is', 'Nom.pl/Acc.pl')

    # V
    # check_nom_sg(surface, u'ēs', u'ēs', 'Nom', 'sg')
    check_nom_sg(surface, 'em', 'ēs', 'Acc.sg')
    check_nom_sg(surface, 'ēi', 'ēs', 'Gen.sg/Dat.sg') # 母音の後
    check_nom_sg(surface, 'ē', 'ēs', 'Abl.sg')
    check_nom_sg(surface, 'ēs', 'ēs', 'Nom.pl/Acc.pl')
    check_nom_sg(surface, 'ērum', 'ēs', 'Gen.pl')
    check_nom_sg(surface, 'ēbus', 'ēs', 'Dat.pl/Abl.pl')

    check_nom_sg(surface, 'ei', 'es', 'Gen.sg/Dat.sg') # 子音の後

    return results


def lookup(word):
    # if isupper(word[0]): return None
    if word[-3:] == 'que':
        word = word[:-3]

    # print "[%s]" % word.encode('utf-8'),

    results = []

    results += list(check_prepositions(word).values())
    results += list(check_noun_declensions(word).values())
    results += list(check_adjective_declensions(word).values())
    results += list(check_pronoun_declensions(word).values())

    if word in latindic:
        results.append(latindic[word])

    return results

