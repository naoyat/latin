#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject

def uniq(s):
    return [x for x in set(s)]

def non_genitive(_):
    return 'Gen' not in [x[0] for x in _] if _ else False

def case_intersection(_s):
    cases_x = ['Nom','Voc','Acc','Gen','Dat','Abl','Loc']
    genders_x = []
    for _ in _s: # あとでreduceで書く
        cases = [x[0] for x in _]
        genders = uniq([x[2] for x in _])
        # print " > ", cases, genders
        cases_x = filter(lambda case:case in cases, cases_x)
        genders_x = uniq(genders_x + genders)

    return (cases_x, genders_x)

def group_pos(words):
    num_of_words = len(words)
    if num_of_words == 1:
        item = words[0].items[0]
        if item._ is not None:
            cases = [x[0] for x in item._]
            genders = uniq([x[2] for x in item._])
            return ('noun', (cases, genders))
        else:
            return (item.pos, None)

    surface = u' '.join([word.surface for word in words])
    _s = [word.items[0]._ for word in words]
    # _: [('Nom', 'sg', 'f'), ('Voc', 'sg', 'f')]
    _sg = filter(non_genitive, _s)
    if _sg:
        return ('noun', case_intersection(_sg))
    else:
        return ('noun', case_intersection(_s))


class AndOr (LatinObject):
    def __init__(self, and_or_word):
        self.and_or_word = and_or_word # u'et', u'neque', ...
        self.words_slots = []
        self.pos = None
        self.info = None

        self.cases = None
        self.genders = None

        self.surfaces = []

    def add(self, words):
        self.words_slots.append(words)

        self.surfaces.append(self.and_or_word)
        for word in words:
            self.surfaces.append(word.surface)

        pos, info = group_pos(words)
        # print " // GROUP POS:", pos, info
        if self.pos is None:
            self.pos = pos
            if self.pos == 'noun':
                self.cases, self.genders = info
            else:
                self.info = info
        elif self.pos == 'noun':
            cases, genders = info
            self.cases = filter(lambda case:case in cases, self.cases)
            self.genders = uniq(self.genders + genders)
        elif self.pos == pos:
            if self.info == info:
                pass
            else:
                print "  x info mismatch:", self.info, info
        else:
            print "  x pos mismatch:", (self.pos, self.info), (pos, info)

        # updating
        self.surface = u' '.join(self.surfaces)
        self.surface_len = len(self.surface)

        if len(self.genders) >= 2:
            gender = 'm'
        else:
            gender = self.genders[0]

        self._ = [(case, 'pl', gender) for case in self.cases]


    def dump(self):
#            print "    ET (", surfaces[start_idx:end_idx], "..)"
        for i, words in enumerate(self.words_slots):
            print "    ", self.and_or_word, '#', i, ":", u' '.join([word.surface for word in words]).encode('utf-8')

    def is_verb(self):
        return False

    def has_subst_case(self, case):
        if self.pos != 'noun': return False
        return case in self.cases

    def detail(self):
        if len(self.genders) >= 2:
            gender = 'm'
        else:
            gender = self.genders[0]

        _ng = '.pl.' + gender

        s = '[%s] %s. [%s]' % (
            self.and_or_word.upper().encode('utf-8'),
            self.pos[0],
            '|'.join([case + _ng for case in self.cases])
            )
        return s

    def restrict(self):
        for words in self.words_slots:
            for word in words:
                word.restrict_cases([x[0] for x in self._])

    def translate(self):
        tr = []
        for words in self.words_slots:
            # tr.append(' '.join([word.translate() for word in words]))
            tr.append(words[0].translate()[0])
        return ('と'.join(tr), self.and_or_word in (u'neque'))
