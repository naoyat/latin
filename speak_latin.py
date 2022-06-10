#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# なんちゃってラテン語スピーチ (on MacOSX)
# by naoya_t
#
import sys
import time
import math
from subprocess import Popen, PIPE

from latin.latin_syllable import separate_syllaba, locate_accent


def say(text, input='TEXT', show_phonemes=False, pause=False):
    if input in ('PHON', 'TUNE'):
        text = '[[inpt '+ input +']]' + text + '[[inpt TEXT]]'

    if show_phonemes:
        print text

    p = Popen(["say", "-v", "Alex"], stdout=PIPE, stdin=PIPE, stderr=PIPE)
    p.stdin.write(text)


latin_phoneme_dic = {
    u'a':'AA', u'ā':'AA', u'A':'AA', u'Ā':'AA', # AA in father
    u'e':'EH', u'ē':'EH', u'E':'EH', u'Ē':'EH', # EH in bet
    u'i':'IY', u'ī':'IY', u'I':'IY', u'Ī':'IY', # IY in beet
    u'o':'OW', u'ō':'OW', u'O':'OW', u'Ō':'OW', # OW in boat
    u'u':'UW', u'ū':'UW', u'U':'UW', u'Ū':'UW', # UW in boot
    u'y':'yUW', u'ȳ':'yUW', u'Y':'yUW', u'Ȳ':'yUW', # emulated by [ju:]
    u'v':'w', u'V':'w',

    u'æ':'AAEH', u'Æ':'AAEH',
    u'œ':'OWEH', u'Œ':'OWEH',

    u'c':'k', u'C':'k',
    u'k':'k', u'K':'k',
    u'q':'k', u'Q':'k',
    u'g':'g', u'G':'g',
    u'x':'ks', u'X':'ks',

    u'j':'y', u'J':'Y',
    u't':'~t', u'T':'~t',
    u'd':'d', u'D':'d',

    u'p':'p', u'P':'p',
    u'b':'b', u'B':'b',

    u'h':'h', u'H':'h',
    u'f':'f', u'F':'f',

    u'l':'l', u'L':'l',
    u'm':'m', u'M':'m',
    u'n':'n', u'N':'n',
    u'r':'r', u'R':'r',
    u's':'s', u'S':'s' }

latin_time_unit = 110
latin_freq_low = 135
latin_freq_high = latin_freq_low * 1.33333 # math.pow(2.0, 5.0/12) # 4度

def analyze_latin_word_phonemes(word_uc, debug_mode=False):
    syllables = separate_syllaba(word_uc)
    acc_idx = locate_accent(syllables)

    if debug_mode:
#    if True:
        syllables_ = [u'[' + syl + u']' if i == acc_idx else syl for i, syl in enumerate(syllables)]
        print '\n>', u'-'.join(syllables_).encode('utf-8')

    phonemes = []

    for i, syl in enumerate(syllables):
        if i == acc_idx:
            pitch = latin_freq_high
        else:
            pitch = latin_freq_low

        # qu [kw]
        syl.replace(u'QU', u'kv')
        syl.replace(u'qu', u'kv')
        # gu [gw]
        syl.replace(u'GU', u'gv')
        syl.replace(u'gu', u'gv')

        # bs [ps], bt [pt]
        if syl[-1] in (u'B', u'b') and i < len(syllables)-1:
            if syllables[i+1][0] in (u's', u'S', u't', u'T'):
                syl[-1] = u'p'

        for c in syl:
            # print acc_idx, i, syl, c, pitch
            phoneme = latin_phoneme_dic.get(c, '~')

            if c in (u'ā', u'ē', u'ī', u'ō', u'ū',
                     u'Ā', u'Ē', u'Ī', u'Ō', u'Ū',
                     u'ȳ', u'Ȳ',
                     u'æ', u'Æ',
                     u'œ', u'Œ',
                     u'x', u'X' ):
                # longer
                duration = latin_time_unit * 2
            # elif c in (u't', u'T'):
            #    duration = latin_time_unit * 1.25
            else:
                # shorter
                duration = latin_time_unit

            phonemes.append("%s {D %d; P %g:0}" % (phoneme, duration, pitch))

    return phonemes


def analyze_latin_sentence(sentence_uc, debug_mode=False):
    phonemes = []

    for word_uc in sentence_uc.split(u' '):
        phonemes_in_word = analyze_latin_word_phonemes(word_uc, debug_mode=debug_mode)
        # silence
        duration = latin_time_unit
        phonemes_in_word.append('%s {D %d}' % ('%', duration))
        # phonemes.append('~')
        phonemes_in_word.append('.')

        if debug_mode:
            for phoneme in phonemes_in_word:
                print "  ", phoneme

        phonemes += phonemes_in_word

    return phonemes


def say_latin(text_uc, debug_mode=False, pause=False):
    phonemes = analyze_latin_sentence(text_uc, debug_mode)
    tune_text = ''.join(phonemes)
    say(tune_text, input='TUNE', show_phonemes=False, pause=pause)

if __name__ == '__main__':
    buf = []
    for line in sys.stdin:
        buf.append(line.rstrip().decode("utf-8"))

    if buf:
        text = " ".join(buf)
    else:
        text = u'In Crētā īnsulā māgnum labyrinthum Daedalus aedificāvit plēnum viārum flexuōsārum.'

    say_latin(text, debug_mode=False, pause=True)
