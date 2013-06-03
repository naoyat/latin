#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject
from latin.Word import Word

from japanese import JaVerb
import Verb

class Predicate (LatinObject):
    def __init__(self, verb):
        self.verb = verb
        self.case_slot = {}
        self.modifiers = []
        self.first_item = verb.items[0]
        self.surface = verb.surface
        self.surface_len = len(self.surface)
        self.conjunction = None
        self.is_sum = self.first_item.item.get('pres1sg', None) == u'sum'

    def add_nominal(self, case, obj):
        # self.objects[case] = self.objects.get(case, []).append(obj)
        if self.case_slot.has_key(case):
            self.case_slot[case].append(obj)
        else:
            self.case_slot[case] = [obj]

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
        verb_items = filter(lambda item:item.pos == 'verb', word.items)
        modes = '|'.join([item.item['mood'][:3] for item in verb_items])
        print '  %d [%s <%s>]' % (i, ansi_color.bold(surface.encode('utf-8')), modes),
        for item in verb_items:
            print "{", item.description(), "}",
            print

    def translate(self):
        tr = []
        negated = False

        verb = self.first_item
        person = verb.attrib('person', 0)

        if self.conjunction:
            if self.conjunction.surface == u'et':
                t = 'そして'
            else:
                t, neg = self.conjunction.translate()
                if neg: negated = True
            tr.append(t)

        cases_ja = {'Nom':'が', 'Acc':'を', 'Gen':'の', 'Dat':'に', 'Abl':'で', 'Voc':'よ', 'Loc':'で'}

        sum_complement = []
        # Nominative
        noms = []
        nom_acc_objs = self.case_slot.get('Nom/Acc', [])
        if self.case_slot.has_key('Nom') or (person == 3 and nom_acc_objs):
            nom_objs = self.case_slot.get('Nom', [])
            # nom_acc_objs = self.case_slot.get('Nom/Acc', [])

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
            self.case_slot['Acc'] = self.case_slot.get('Acc', []) + nom_acc_objs
            self.case_slot['Nom/Acc'] = []

        if not noms and verb.attrib('mood') != 'imperative':
            pn = str(self.person()) + str(self.number())
            subj_ja = {'1sg':'私', '2sg':'あなた', '3sg':'彼,彼女,それ',
                       '1pl':'我々', '2pl':'あなた方', '3pl':'彼ら,彼女ら,それら'}
            if subj_ja.has_key(pn):
                noms.append(subj_ja[pn])

        if noms:
            nom_case_ja = 'が'
            if self.is_sum:
                nom_case_ja = 'は'
            tr.append('='.join(noms) + nom_case_ja)

        for case, objs in self.case_slot.items():
            if case in ('Nom', 'Nom/Acc', 'Acc'): continue
            if not objs: continue
            if isinstance(case, unicode):
                # prep-clause
                case_ja = '' # case.encode('utf-8')
            else:
                case_ja = cases_ja[case]
            trs = [obj.translate()[0] for obj in objs]
            tr.append('='.join(trs) + case_ja)

        # Accusative
        if self.case_slot.has_key('Acc'):
            acc_objs = self.case_slot['Acc']
            self.case_slot['Acc'] = []
            accs = [obj.translate()[0] for obj in acc_objs]
            accs = [acc[:-3] if acc[-3:] == 'が' else acc for acc in accs]
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
        verb_tr = ','.join([JaVerb(ja).form(flag) for ja in jas])
        if negated:
            verb_tr = '¬'+ verb_tr

        if self.is_sum and sum_complement:
            adj = ','.join(sum_complement)
            verb_tr = verb_tr.replace('〜', adj)

        tr.append(verb_tr)

#        tr.append(self.first_item.ja )

        return (' / '.join(tr), False)
