#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# なんちゃってラテン語スピーチ (powered by NSSpeechSynthesizer, available only on MacOSX)
# by naoya_t
#
import sys
import time
import math

from latin.latin_syllable import separate_syllaba, locate_accent

# AppKit
try:
    from AppKit import NSSpeechSynthesizer
    is_appkit_available = True
except:
    is_appkit_available = False


synth = None

def init_synth(voice=None):
    if not is_appkit_available:
        print("speech synthesizer is not available.")
        return None

    def init_(voiceIdentifier):
        return NSSpeechSynthesizer.alloc().initWithVoice_(voiceIdentifier)

    global synth
    if voice is None:
        # no voiceIdentifier is specified
        synth = NSSpeechSynthesizer.alloc().init()
    elif voice[:4] == 'com.apple.speech.synthesis.voice.':
        # an exact voiceIdentifier is specified
        synth = init_(voice)
    else:
        voice1 = 'com.apple.speech.synthesis.voice.' + voice
        voice2 = 'com.apple.speech.synthesis.voice.' + voice.lower() + '.premium'
        synth = init_(voice1) or init_(voice2)


def pause_while_speaking():
    if synth is None: return
    while synth.isSpeaking():
        time.sleep(0.1)


def say(text, input='TEXT', show_phonemes=False, pause=False):
    if synth is None: return None
    # print text
    if input in ('PHON', 'TUNE'):
        text = '[[inpt '+ input +']]' + text + '[[inpt TEXT]]'
    if show_phonemes:
        print(synth.phonemesFromText_(text))
    synth.startSpeakingString_(text)
    if pause:
        pause_while_speaking()


latin_phoneme_dic = {
    'a':'AA', 'ā':'AA', 'A':'AA', 'Ā':'AA', # AA in father
    'e':'EH', 'ē':'EH', 'E':'EH', 'Ē':'EH', # EH in bet
    'i':'IY', 'ī':'IY', 'I':'IY', 'Ī':'IY', # IY in beet
    'o':'OW', 'ō':'OW', 'O':'OW', 'Ō':'OW', # OW in boat
    'u':'UW', 'ū':'UW', 'U':'UW', 'Ū':'UW', # UW in boot
    'y':'yUW', 'ȳ':'yUW', 'Y':'yUW', 'Ȳ':'yUW', # emulated by [ju:]
    'v':'w', 'V':'w',

    'æ':'AAEH', 'Æ':'AAEH',
    'œ':'OWEH', 'Œ':'OWEH',

    'c':'k', 'C':'k',
    'k':'k', 'K':'k',
    'q':'k', 'Q':'k',
    'g':'g', 'G':'g',
    'x':'ks', 'X':'ks',

    'j':'y', 'J':'Y',
    't':'~t', 'T':'~t',
    'd':'d', 'D':'d',

    'p':'p', 'P':'p',
    'b':'b', 'B':'b',

    'h':'h', 'H':'h',
    'f':'f', 'F':'f',

    'l':'l', 'L':'l',
    'm':'m', 'M':'m',
    'n':'n', 'N':'n',
    'r':'r', 'R':'r',
    's':'s', 'S':'s' }

latin_time_unit = 110
latin_freq_low = 135
latin_freq_high = latin_freq_low * 1.33333 # math.pow(2.0, 5.0/12) # 4度

def analyze_latin_word_phonemes(word_uc, debug_mode=False):
    syllables = separate_syllaba(word_uc)
    acc_idx = locate_accent(syllables)

    if debug_mode:
#    if True:
        syllables_ = ['[' + syl + ']' if i == acc_idx else syl for i, syl in enumerate(syllables)]
        print('\n>', '-'.join(syllables_).encode('utf-8'))

    phonemes = []

    for i, syl in enumerate(syllables):
        if i == acc_idx:
            pitch = latin_freq_high
        else:
            pitch = latin_freq_low

        # qu [kw]
        syl.replace('QU', 'kv')
        syl.replace('qu', 'kv')
        # gu [gw]
        syl.replace('GU', 'gv')
        syl.replace('gu', 'gv')

        # bs [ps], bt [pt]
        if syl[-1] in ('B', 'b') and i < len(syllables)-1:
            if syllables[i+1][0] in ('s', 'S', 't', 'T'):
                syl[-1] = 'p'

        for c in syl:
            # print acc_idx, i, syl, c, pitch
            phoneme = latin_phoneme_dic.get(c, '~')

            if c in ('ā', 'ē', 'ī', 'ō', 'ū',
                     'Ā', 'Ē', 'Ī', 'Ō', 'Ū',
                     'ȳ', 'Ȳ',
                     'æ', 'Æ',
                     'œ', 'Œ',
                     'x', 'X' ):
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

    for word_uc in sentence_uc.split(' '):
        phonemes_in_word = analyze_latin_word_phonemes(word_uc, debug_mode=debug_mode)
        # silence
        duration = latin_time_unit
        phonemes_in_word.append('%s {D %d}' % ('%', duration))
        # phonemes.append('~')
        phonemes_in_word.append('.')

        if debug_mode:
            for phoneme in phonemes_in_word:
                print("  ", phoneme)

        phonemes += phonemes_in_word

    return phonemes


def say_latin(text_uc, debug_mode=False, pause=False):
    phonemes = analyze_latin_sentence(text_uc, debug_mode)
    tune_text = ''.join(phonemes)
    say(tune_text, input='TUNE', show_phonemes=False, pause=pause)


if __name__ == '__main__':
    # init_synth('Alex')
    init_synth('Victoria')
    text = 'In Crētā īnsulā māgnum labyrinthum Daedalus aedificāvit plēnum viārum flexuōsārum.'
    #say_latin(text, debug_mode=False, pause=True)
    say_latin(text, debug_mode=True, pause=True)
