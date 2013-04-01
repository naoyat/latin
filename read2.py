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

def lookup(word):
    if ord(word[0]) <= 64: return None

    res = latin.latindic_lookup(word)
    if res: return res

    if latin_char.isupper(word[0]):
        word_lower = latin_char.tolower(word)
        res = latin.latindic_lookup(word_lower)
        if res: return res

    if word[-3:] == u'que':
        res = latin.latindic_lookup(word[:-3])
        if res: return res

    return []


def render_info(item):
    name = {'present':'現在', 'imperfect':'未完了', 'perfect':'完了', 'future':'未来',
            'active':'能動', 'passive':'受動',
            'imperative':'命令', 'infinitive':'不定',
            '-':'-'}
    pos = item['pos']
    if pos == 'noun':
        return '%s %s' % (item['ja'], item.get('_', "-"))
    elif pos == 'adj':
        return 'a.%s %s' % (item['ja'], item.get('_', "-"))
    elif pos == 'verb':
        return 'v.%s %s%s %s.%s.%s' % (item['ja'],
                                       item['person'], item['number'],
                                       name[item.get('mood','-')],
                                       name[item.get('voice','-')],
                                       name[item.get('tense','-')],
                                       )
    elif pos == 'preposition':
        return 'prep<%s> %s' % (item['dominates'], item['ja'])
    else:
        info = item.copy()
        del info['surface'], info['pos'], info['ja']
        if len(info) > 0:
            return '%s %s %s' % (item['pos'], item['ja'], util.render(info))
        else:
            return '%s %s' % (item['pos'], item['ja'])


def analyse(sentence):
    print ' '.join(sentence)

    sentence_uc = [u.decode('utf-8') for u in sentence]
    maxlen_uc = max(map(len, sentence_uc))
    res = zip(sentence_uc, map(lookup, sentence_uc))

    for word, info in res:
        print ansi_color.bold((u'  %*s ' % (-maxlen_uc, word)).encode('utf-8')),
        if info is None:
            print
        elif len(info) > 0:
            print ' | '.join(map(render_info, info))
        else:
            print '(?)'

    print


def main():
    if len(sys.argv) == 2:
        file = sys.argv[1]
        text.analyse_textfile(file, analyse)
    else:
        print "usage: %s <filename>" % sys.argv[0]

if __name__ == '__main__':
    main()
