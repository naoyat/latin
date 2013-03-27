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

case_tags_6x2 = [
    {'case':'Nom', 'number':'sg'},
    {'case':'Voc', 'number':'sg'},
    {'case':'Acc', 'number':'sg'},
    {'case':'Gen', 'number':'sg'},
    {'case':'Dat', 'number':'sg'},
    {'case':'Abl', 'number':'sg'},

    {'case':'Nom', 'number':'pl'},
    {'case':'Voc', 'number':'pl'},
    {'case':'Acc', 'number':'pl'},
    {'case':'Gen', 'number':'pl'},
    {'case':'Dat', 'number':'pl'},
    {'case':'Abl', 'number':'pl'}
    ]

case_tags_5sg = [
    {'case':'Nom', 'number':'sg'},
    {'case':'Acc', 'number':'sg'},
    {'case':'Gen', 'number':'sg'},
    {'case':'Dat', 'number':'sg'},
    {'case':'Abl', 'number':'sg'},
]

case_tags_5pl = [
    {'case':'Nom', 'number':'pl'},
    {'case':'Acc', 'number':'pl'},
    {'case':'Gen', 'number':'pl'},
    {'case':'Dat', 'number':'pl'},
    {'case':'Abl', 'number':'pl'}
    ]

case_tags_5x2 = case_tags_5sg + case_tags_5pl

cases_ja = {
    'Nom':'〜が',
    'Acc':'〜を',
    'Gen':'〜の',
    'Dat':'〜に,〜のために,〜にとって',
    'Abl':'〜によって,〜でもって,〜をもって,〜において,〜から',
    'Voc':'〜よ'
}
