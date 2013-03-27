#!/usr/bin/env python
# -*- coding: utf-8 -*-

LOWER_LONG_VOWELS = [257,275,299,333,363,563] # ā ē ī ō ū ȳ
UPPER_LONG_VOWELS = [256,274,298,332,362,562] # Ā Ē Ī Ō Ū Ȳ

TRANSTABLE_TOLOWER = {}
TRANSTABLE_TOUPPER = {}

for j in xrange(26): # A-Z / a-z
    TRANSTABLE_TOLOWER[0x41+j] = unichr(0x61+j)
    TRANSTABLE_TOUPPER[0x61+j] = unichr(0x41+j)

for c in UPPER_LONG_VOWELS:
    TRANSTABLE_TOLOWER[c] = unichr(c+1)
    TRANSTABLE_TOUPPER[c+1] = unichr(c)

def tolower(ustr):
    return ustr.translate(TRANSTABLE_TOLOWER)

def toupper(ustr):
    return ustr.translate(TRANSTABLE_TOUPPER)


def isupper(char):
    c = ord(char)
    if 0x41 <= c <= 0x5A:
        return True
    elif 0x61 <= c <= 0x7A:
        return False
    elif c in UPPER_LONG_VOWELS:
        return True
    else:
        return False

def islower(char):
    c = ord(char)
    if 0x41 <= c <= 0x5A:
        return False
    elif 0x61 <= c <= 0x7A:
        return True
    elif c in LOWER_LONG_VOWELS:
        return True
    else:
        return False

