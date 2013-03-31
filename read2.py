#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

import util
import text
import latin
import latin_char
import latin_noun

import ansi_color

latin.latindic_load()

def lookup(word, is_first=False):
    res = latin.latindic_lookup(word)
    if res: return res

    if is_first and latin_char.isupper(word[0]):
        l = latin_char.tolower(word)
        res = latin.latindic_lookup(l)
        if res: return res

    if word[-3:] == u'que':
        res = latin.latindic_lookup(word[:-3])
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

#    def pp(info):
#        pos = info['pos']
#        if pos == 'n':
#            cases_ja = [latin_noun.cases_ja[case[0:3]] + case[3:6] for case in info['case'].split('/')]
#            return util.render([pos, info['base'], info['case'], info['gender'], info['ja'], cases_ja])
#        else:
#            return util.render(info)

    first = True

    l = len(sentence_uc)

    def render_info(item):
        name = {'present':'現在', 'imperfect':'未完了', 'perfect':'完了', 'future':'未来',
                'active':'能動', 'passive':'受動',
                'imperative':'命令', 'infinitive':'不定',
                '-':'-'}
        if item['pos'] == 'noun':
            return '%s %s' % (item['ja'], item.get('cn', "-"))
        elif item['pos'] == 'adj':
            return 'a.%s %s' % (item['ja'], item.get('cn', "-"))
        elif item['pos'] == 'verb':
            return 'v.%s %s%s %s.%s.%s' % (item['ja'],
                                           item['person'], item['number'],
                                           name[item.get('mood','-')],
                                           name[item.get('voice','-')],
                                           name[item.get('tense','-')],
                                           )
        else:
            info = item.copy()
            del info['surface']
            del info['pos']
            del info['ja']
            if len(info) > 0:
                return '%s %s %s' % (item['pos'], item['ja'], util.render(info))
            else:
                return '%s %s' % (item['pos'], item['ja'])

    for i in xrange(l):
        word = sentence_uc[i]
        print ansi_color.bold((u'    %*s' % (-maxlen, word)).encode('utf-8')),
        # print u"    %*s" % (-maxlen, word),
        c0 = ord(word[0])
        if c0 > 64:
            info = lookup(word, first)
            first = False
            if info:
                print ' | '.join(map(render_info, info))
            else:
                print "(?)"
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
