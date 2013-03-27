#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import util
import text
import latin
import latin_noun

def lookup(word, is_first=False):
    res = latin.latindic_lookup(word)
    if res: return res

    if is_first and latin_char.isupper(word[0]):
        l = latin_char.tolower(word)
        res = latin.latindic_lookup(l)
        if res: return res

    return None

def analyse(sentence):
    print ' '.join(sentence)

    sentence_uc = []
    maxlen = 0
    for word in sentence:
        word_uc = word.decode('utf-8')
        maxlen = max(maxlen, len(word_uc))
        sentence_uc.append(word_uc)

    def pp(info):
#        if not info.has_key('pos'):
#            print "NO pos IN", util.render(info)
#            return "(NO POS)"
        pos = info['pos']
        if pos == 'n':
            cases_ja = [latin_noun.cases_ja[case[0:3]] + case[3:6] for case in info['case'].split('/')]
            return util.render([pos, info['base'], info['case'], info['gender'], info['ja'], cases_ja])
        else:
            return util.render(info)

    first = True
    for word in sentence_uc:
        print "    %*s" % (-maxlen, word.encode('utf-8')),
        # print u"    %*s" % (-maxlen, word),
        c0 = ord(word[0])
        if c0 > 64:
            info = lookup(word, first)
            first = False
            if info:
                print ', '.join(map(pp, info))
            else:
                print "(UNKNOWN)"
        else:
            print
    print

def main():
    if len(sys.argv) == 2:
        file = sys.argv[1]
        text.analyse_textfile(file, analyse)
    else:
        print "usage: %s <filename>" % sys.argv[0]

if __name__ == '__main__':
    main()
