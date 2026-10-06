#!/usr/bin/env python
# -*- coding: utf-8 -*-

def ends_with(end, string):
    # assert(isinstance(end, basestring))
    # assert(isinstance(string, basestring))
    end_len = len(end)
    if end_len == 0: return True
    return end == string[-end_len:]
