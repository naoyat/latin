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

        cases_ja = {'Nom':'が', 'Acc':'を', 'Gen':'の', 'Dat':'に', 'Abl':'で', 'Voc':'よ', 'Loc':'で'}

        # Nominative
        noms = []
        if self.case_slot.has_key('Nom'):
            nom_objs = self.case_slot['Nom']
            self.case_slot['Nom'] = []
            for obj in nom_objs:
                nom, neg = obj.translate()
                if neg: negated = True
                if isinstance(obj, Word) and obj.items[0].pos != 'noun':
                    nom += '(人,物)'
                noms.append(nom)
        else:
            pn = str(self.person()) + str(self.number())
            subj_ja = {'1sg':'私', '2sg':'あなた', '3sg':'彼,彼女,それ',
                       '1pl':'我々', '2pl':'あなた方', '3pl':'彼ら,彼女ら,それら'}
            if subj_ja.has_key(pn):
                noms.append(subj_ja[pn])
#        tr.append(','.join([nom + 'が' for nom in noms]))
        tr.append('='.join(noms) + 'が')

        for case, objs in self.case_slot.items():
            if case == 'Acc': continue
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

        verb = self.first_item
        jas = verb.ja.split(',')

        # flags
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
        tr.append(verb_tr)

#        tr.append(self.first_item.ja )

        return ' / '.join(tr)
