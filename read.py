#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import text
import latin

def render_uc(obj):
    klass = obj.__class__.__name__
    if klass == 'int':
        return str(obj)
    elif klass == 'str':
        return "'" + obj + "'"
    elif klass == 'unicode':
        return "'" + obj.encode('utf-8') + "'"
    elif klass == 'list':
        return '[' + ', '.join(map(render_uc, obj)) + ']'
    elif klass == 'dict':
#        for k in obj:
#            print k, obj[k]
#        return "{ ... }"
        return '{' + ', '.join([render_uc(k)+':'+render_uc(obj[k]) for k in obj]) + '}'
    else:
        return '?'

def lookup(word, is_first=False):
    res = latin.lookup(word)
#    print "res=", res
    if res: return res

    if is_first and latin.isupper(word[0]):
        # print lat_tolower(u"TRŌJĀNŌ").encode('utf-8')
        l = latin.tolower(word)
        res = latin.lookup(l)
#        print "res=", res
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
        pos = info['pos']
        if pos == 'n':
            cases_ja = [latin.cases_ja[case[0:3]] + case[3:6] for case in info['case'].split('/')]
            return render_uc([pos, info['base'], info['case'], info['gender'], info['ja'], cases_ja])
        else:
            return render_uc(info)

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
