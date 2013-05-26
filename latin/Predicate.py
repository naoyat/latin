#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject

class Predicate (LatinObject):
    def __init__(self, verb):
        self.verb = verb
        self.case_slot = {}
        self.first_item = verb.items[0]
        self.surface = verb.surface
        self.surface_len = len(self.surface)

    def add(self, case, obj):
        # self.objects[case] = self.objects.get(case, []).append(obj)
        if self.case_slot.has_key(case):
            self.case_slot[case].append(obj)
        else:
            self.case_slot[case] = [obj]

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
