#!/usr/bin/env python
# -*- coding: utf-8 -*-
VOWEL = 0
CONSONANT = 1

def joint(chunk):
    def cc(c1, c2):
        if c1 in [u'p', u'b', u't', u'd', u'c', u'g', u'f'] and c2 in [u'l', u'r']:
            return [c1+c2]
        elif c1 == u's' and c2 in [u'p', u't', u'c']:
            return [c1+c2]
        else:
            return [c1, c2]

    chunk_len = len(chunk) - 1
    if chunk_len == 1:
        return chunk
    elif chunk_len == 2:
        if chunk[0] == VOWEL:
            if chunk[1:] == [u'a', u'e']:
                return [VOWEL, u'ae']
            elif chunk[1:] == [u'a', u'u']:
                return [VOWEL, u'au']
            elif chunk[1:] == [u'o', u'e']:
                return [VOWEL, u'oe']
            else:
                return chunk
        # consonant
        return [CONSONANT] + cc(chunk[1], chunk[2])
    elif chunk_len == 3:
        if chunk[0] == VOWEL:
            if chunk[2] == u'a' and chunk[3] == u'e':
                return [VOWEL, chunk[1], u'ae']
            print chunk
            raise "Too long vowel chunk"
        # consonant
        return [CONSONANT, chunk[1]] + cc(chunk[2], chunk[3])
    elif chunk_len == 4:
        if chunk[0] == VOWEL:
            print chunk
            raise "Too long vowel chunk"
        # consonant
        return [CONSONANT, chunk[1], chunk[2]] + cc(chunk[3], chunk[4])
    else:
        print chunk
        raise "Too long chunk"


def is_vowel(ch):
    return ch in [u'a', u'e', u'i', u'o', u'u', u'y', u'ā', u'ē', u'ī', u'ō', u'ū', u'ȳ']


def separate_syllaba(word_uc):
    def type(ch):
        return VOWEL if is_vowel(ch) else CONSONANT

    last_type = None
    chunks = []
    for ch in word_uc:
        curr_type = type(ch)
        if last_type != curr_type:
            chunks.append([curr_type])
            last_type = curr_type
        chunks[-1].append(ch)
    # caesar: [1 c] [0 a e] [1 s] [0 a] [1 r]
    # novembris: [1 n] [0 o] [1 v] [0 e] [1 m b r] [0 i] [1 s]
    # deus: [1 d] [0 e u] [1 s]

    chunks = map(joint, chunks)
    # caesar: [1 c] [0 ae] [1 s] [0 a] [1 r]
    # novembris: [1 n] [0 o] [1 v] [0 e] [1 m br] [0 i] [1 s]
    # deus: [1 d] [0 e u] [1 s]

    pre = []
    vowel = []

    res = []

    for i, chunk in enumerate(chunks):
        if chunk[0] == VOWEL:
            vowel = chunk[1:]
        else: # consonant
            if len(chunk[1:]) == 1:
                # 排出
                if vowel != []:
                    if len(vowel) == 2 and i == len(chunks)-1:
                        res.append(pre + vowel[:1] + [])
                        res.append(vowel[1:] + chunk[1:])
                        pre = []
                        vowel = []
                    else:
                        res.append(pre + vowel + [])
                        pre = chunk[1:]
                        vowel = []
                else:
                    pre = chunk[1:]
            else:
                res.append(pre + vowel + [chunk[1]])
                pre = chunk[2:]
                vowel = []

    if vowel != []:
        res.append(pre + vowel)
    elif pre != []:
        if res:
            res[-1] += pre
        else:
            res = pre
    # caesar: [c ae] [s a r]
    # novembris: [n o] [v e m] [br i s]
    # deus: [d e] [u s]

    syl = [u''.join(r) for r in res]
    # caesar: [cae sar]
    # novembris: [no vem bris]
    # deus: [de us]

    return syl


def locate_accent(syllables):
    def is_long(syl):
        if is_vowel(syl[-1]):
            return syl[-1] in [u'ā', u'ē', u'ī', u'ō', u'ū', u'ȳ']
        else:
            return True
    len_syl = len(syllables)
    if len_syl == 1:
        return None
    elif len_syl == 2:
        return 0
    elif len_syl >= 3:
        paenultima = len_syl-2
        if is_long(syllables[paenultima]):
            return paenultima
        else:
            return paenultima-1
