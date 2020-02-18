#!/usr/bin/env python
# -*- coding: utf-8 -*-

LOWER_LONG_VOWELS = [257,275,299,333,363,563] # ā ē ī ō ū ȳ
UPPER_LONG_VOWELS = [256,274,298,332,362,562] # Ā Ē Ī Ō Ū Ȳ

TRANSTABLE_TOLOWER = {}
TRANSTABLE_TOUPPER = {}

for j in range(26): # A-Z / a-z
    TRANSTABLE_TOLOWER[0x41+j] = chr(0x61+j)
    TRANSTABLE_TOUPPER[0x61+j] = chr(0x41+j)

for c in UPPER_LONG_VOWELS:
    TRANSTABLE_TOLOWER[c] = chr(c+1)
    TRANSTABLE_TOUPPER[c+1] = chr(c)

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

def lengthen(ch):
    trans_table = {'a':'ā', 'e':'ē', 'i':'ī', 'o':'ō', 'u':'ū', 'y':'ȳ',
                   'A':'Ā', 'E':'Ē', 'I':'Ī', 'O':'Ō', 'U':'Ū', 'Y':'Ȳ'}
    return ''.join([trans_table.get(ch, ch) for ch in text])

def shorten(ch): # I know this doesn't work becase text is str
    trans_table = {'ā':'a', 'ē':'e', 'ī':'i', 'ō':'o', 'ū':'u', 'ȳ':'y',
                   'Ā':'A', 'Ē':'E', 'Ī':'I', 'Ō':'O', 'Ū':'U', 'Ȳ':'Y'}
    return ''.join([trans_table.get(ch, ch) for ch in text])

def trans(text):
    trans_table = {'A':'ā', 'E':'ē', 'I':'ī', 'O':'ō', 'U':'ū', 'Y':'ȳ'}
    trans_table_upper = {'A':'Ā', 'E':'Ē', 'I':'Ī', 'O':'Ō', 'U':'Ū', 'Y':'Ȳ'}
    res = ''
    caps = False
    for ch in text:
        if ch == '_':
            caps = True
        else:
            if caps:
                res += trans_table_upper.get(ch, ch.upper())
                caps = False
            else:
                res += trans_table.get(ch, ch)
    return res
