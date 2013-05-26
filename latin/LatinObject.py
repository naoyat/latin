#!/usr/bin/env python
# -*- coding: utf-8 -*-

class LatinObject:
    def __init__(self):
        self.negated = False

    def detail(self):
        return '[NOT IMPLEMENTED]'

    def surface_utf8(self):
        return self.surface.encode('utf-8')

    def translate(self):
        return '？？'
