#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject
from latin.Word import Word

from .japanese import JaVerb
from . import verb_flags as Verb

TENSE_LABELS = {'imperfect': '未完了', 'future': '未来', 'perfect': '完了',
                'past-perfect': '過去完了', 'future-perfect': '未来完了'}


def english_verb_label(verb):
    labels = [TENSE_LABELS[verb.attrib('tense')]] if verb.attrib('tense') in TENSE_LABELS else []
    if verb.attrib('voice') == 'passive':
        labels.append('受動')
    if verb.attrib('mood') in ('subjunctive', 'imperative'):
        labels.append({'subjunctive': '接続法', 'imperative': '命令'}[verb.attrib('mood')])
    return '[%s]' % '・'.join(labels) if labels else ''


class Predicate (LatinObject):
    def __init__(self, verb):
        self.verb = verb
        self.case_slot = {}
        self.modifiers = []
        self.first_item = verb.items[0]
        self.surface = verb.surface
        self.surface_len = len(self.surface)
        self.conjunction = None
        self.subordinates = []  # 従属節 (独立奪格など)
        self.is_sum = self.first_item.item.get('pres1sg', None) == 'sum'

    def add_nominal(self, case, obj):
        # self.objects[case] = self.objects.get(case, []).append(obj)
        if case in self.case_slot:
            self.case_slot[case].append(obj)
        else:
            self.case_slot[case] = [obj]

    def add_subordinate(self, clause):
        self.subordinates.append(clause)

    def add_modifier(self, adv):
        self.modifiers.append(adv)

    def is_verb(self):
        return True

    def person(self):
        return self.first_item.attrib('person')
    def number(self):
        return self.first_item.attrib('number')
    def mood(self):
        return self.first_item.attrib('mood')

    def detail(self):
        return self.verb.detail()

    def translate(self):
        # 訳の組み立てで格スロットを並べ替えるので、作業用のコピーを使う
        # (self.case_slot を書き換えると、表示や再度の translate() の結果が変わってしまう)
        case_slot = {case: list(objs) for case, objs in self.case_slot.items()}
        tr = []
        negated = False

        verb = self.first_item
        person = verb.attrib('person', 0)

        if self.conjunction:
            if self.conjunction.surface == 'et':
                t = 'そして'
            else:
                t, neg = self.conjunction.translate()
                if neg: negated = True
            tr.append(t)

        # 従属節 (独立奪格など) は文の頭に置く
        for clause in self.subordinates:
            tr.append(clause.translate()[0])

        cases_ja = {'Nom':'が', 'Acc':'を', 'Gen':'の', 'Dat':'に', 'Abl':'で', 'Voc':'よ', 'Loc':'で'}

        sum_complement = []
        # Nominative
        noms = []
        nom_acc_objs = case_slot.get('Nom/Acc', [])
        if 'Nom' in case_slot or (person == 3 and nom_acc_objs):
            nom_objs = case_slot.get('Nom', [])
            # nom_acc_objs = case_slot.get('Nom/Acc', [])

            demand = 2 if self.is_sum else 1
            supply = len(nom_objs)
            if supply < demand and nom_acc_objs:
                insufficient = demand - supply
                nom_objs += nom_acc_objs[0:insufficient]
                nom_acc_objs = nom_acc_objs[insufficient:]

            for obj in nom_objs:
                nom, neg = obj.translate()
                if neg: negated = True

                if self.is_sum:
                    # 形容詞（修飾語）の場合
                    if isinstance(obj, Word) and obj.items[0].pos != 'noun':
                        # sum なら補語として
                        sum_complement.append(nom)
                    elif (len(noms) > 0 or len(nom_objs) == 1):
                        sum_complement.append(nom)
                    else:
                        noms.append(nom)
                else:
                    # 形容詞（修飾語）の場合
                    if isinstance(obj, Word) and obj.items[0].pos != 'noun':
                        # sumでなければそういう人や物として
                        nom += '(人,物)'
                    noms.append(nom)

        if nom_acc_objs:
            case_slot['Acc'] = case_slot.get('Acc', []) + nom_acc_objs
            case_slot['Nom/Acc'] = []

        if not noms and verb.attrib('mood') != 'imperative':
            pn = str(self.person()) + str(self.number())
            subj_ja = {'1sg':'私', '2sg':'あなた', '3sg':'彼,彼女,それ',
                       '1pl':'我々', '2pl':'あなた方', '3pl':'彼ら,彼女ら,それら'}
            if pn in subj_ja:
                noms.append(subj_ja[pn])

        if noms:
            nom_case_ja = 'が'
            if self.is_sum:
                nom_case_ja = 'は'
            tr.append('='.join(noms) + nom_case_ja)

        for case, objs in list(case_slot.items()):
            if case in ('Nom', 'Nom/Acc', 'Acc'): continue
            if not objs: continue
            if isinstance(case, tuple):
                # prep-clause
                case_ja = '' # case.encode('utf-8')
            else:
                case_ja = cases_ja[case]
            trs = []
            for obj in objs:
                t, neg = obj.translate()
                if neg: negated = True  # neque ... neque ... は主語以外の枠にも現れる
                trs.append(t)
            tr.append('='.join(trs) + case_ja)

        # Accusative
        if 'Acc' in case_slot:
            acc_objs = case_slot['Acc']
            case_slot['Acc'] = []
            accs = []
            for obj in acc_objs:
                t, neg = obj.translate()
                if neg: negated = True
                accs.append(t)
            accs = [acc[:-1] if acc[-1:] == 'が' else acc for acc in accs]
            tr.append('='.join(accs) + 'を') #[acc for acc in accs]))

        # adverb
        for adv in self.modifiers:
            s = adv.items[0].ja
            tr.append(s)

        jas = verb.ja.split(',')

        # flags
        if verb.attrib('mood') == 'imperative':
            flag = Verb.IMPERATIVE
        else:
        # elif verb.attrib('mood') == 'indicative':
            # とりあえず直説法で出しておく
            flag = Verb.INDICATIVE

        if verb.attrib('voice') == 'passive':
            flag |= Verb.PASSIVE

        tense = verb.attrib('tense')
        if tense == 'imperfect':
            flag |= Verb.PAST | Verb.ING
        elif tense == 'perfect':
            flag |= Verb.PERFECT
        elif tense == 'future':
            flag |= Verb.FUTURE

#        if advs != []:
#            print "{", ', '.join(advs), "}",
        if verb.attrib('gloss_lang') == 'en':
            # 英語の訳語 (Wiktionary 由来) は活用させず、時制などを添える
            verb_tr = jas[0] + english_verb_label(verb)
        else:
            verb_tr = ','.join([JaVerb(ja).form(flag) for ja in jas])
        if negated:
            verb_tr = '¬'+ verb_tr

        if self.is_sum and sum_complement:
            adj = ','.join(sum_complement)
            verb_tr = verb_tr.replace('〜', adj)

        tr.append(verb_tr)

#        tr.append(self.first_item.ja )

        return (' / '.join(tr), False)
