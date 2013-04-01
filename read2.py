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


def prep_constraint(res):
    # 前置詞の格支配を制約として可能性を絞り込む
    l = len(res)
    for i, (word, info) in enumerate(res):
        if info is None: continue
        doms = set()
        non_prep_exists = False
        for item in info:
            if item['pos'] == 'preposition':
                doms.add(item['dominates'])
            else:
                non_prep_exists = True

        if len(doms) > 0:
            actual = set()
            if i+1 == l:
                break
            for item in res[i+1][1]:
                if item.has_key('_'):
                    for case, number, gender in item['_']:
                        actual.add(case)
            possible_cases = actual.intersection(doms)

            # constrain
            if possible_cases != []:
                def filter_prep(item):
                    if item['pos'] != 'preposition': return True
                    return (item['dominates'] in possible_cases)
                res[i][1] = filter(filter_prep, res[i][1])
                if not non_prep_exists:
                    def filter_noun(item):
                        if not item.has_key('_'): return None
                        item['_'] = filter(lambda a:a[0] in possible_cases, item['_'])
                        if item['_'] == []: return None
                        return item
                    res[i+1][1] = filter(lambda x:x is not None, map(filter_noun, res[i+1][1]))

    return res


def analyse_sentence(sentence):
    print ' '.join(sentence)

    # string(utf-8) --> unicode
    sentence_uc = [word.decode('utf-8') for word in sentence]

    # （表示の都合で）単語の最大長を得ておく
    maxlen_uc = max(map(len, sentence_uc))

    # lookupした結果。{wc} = [[word1, [item1, item2, ...]], [word2, [...] ], ...]
    res = map(lambda word:[word, lookup(word)], sentence_uc) # 上書きするのでtupleでは駄目

    # 前置詞の各支配を利用して絞り込む
    res = prep_constraint(res)

    def is_verb(r):
        word, items = r
        if items is None: return False
        # util.pp(items)
        return any([item['pos'] == 'verb' for item in items])

    verbs = filter(is_verb, res)
    print "%d verb(s):" % len(verbs),
    print util.render(verbs)

    for surface, info in res:
        print ansi_color.bold((u'  %*s ' % (-maxlen_uc, surface)).encode('utf-8')),
        if info is None:
            print
        elif info == []:
            print '(?)'
        else:
            print ' | '.join(map(render_info, info))

    print


def main():
    if len(sys.argv) == 2:
        file = sys.argv[1]
        text.analyse_textfile(file, analyse_sentence)
    else:
        print "usage: %s <filename>" % sys.argv[0]

if __name__ == '__main__':
    main()
