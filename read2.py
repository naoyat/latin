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


def render_item(item):
    name = {'indicative':'直接法', 'subjunctive':'接続法', 'imperative':'命令法', 'infinitive':'不定法',
            'present':'現在', 'imperfect':'未完了', 'perfect':'完了', 'future':'未来',
            'past-perfect': '過去完了',
            'active':'能動', 'passive':'受動',
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
        item_ = item.copy()
        del item_['surface'], item_['pos'], item_['ja']
        if len(item_) > 0:
            return '%s %s %s' % (item['pos'], item['ja'], util.render(item_))
        else:
            return '%s %s' % (item['pos'], item['ja'])


def prep_constraint(res):
    # 前置詞の格支配を制約として可能性を絞り込む
    l = len(res)
    for i, (word, items) in enumerate(res):
        if items is None: continue
        doms = set()
        non_prep_exists = False
        for item in items:
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
            if len(possible_cases) > 0:
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

    res = []
    l = len(sentence_uc)
    i = 0
    maxlen_uc = 0
    while i < l:
        word = sentence_uc[i]
        if i < l-1:
            word2 = word + u' ' + sentence_uc[i+1]
            lu2 = lookup(word2)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if lu2 is not None and len(lu2) > 0:
                res.append([word2, lu2])
                maxlen_uc = max(maxlen_uc, len(word2))
                i += 2
                continue
        lu = lookup(word)
        res.append([word, lu])
        maxlen_uc = max(maxlen_uc, len(word))
        i += 1

    # （表示の都合で）単語の最大長を得ておく
    # maxlen_uc = max(map(len, sentence_uc))

    # lookupした結果。{wc} = [[word1, [item1, item2, ...]], [word2, [...] ], ...]
    # res = map(lambda word:[word, lookup(word)], sentence_uc) # 上書きするのでtupleでは駄目

    # 前置詞の各支配を利用して絞り込む
    res = prep_constraint(res)

    def is_verb(r):
        word, items = r
        if items is None: return False
        return any([item['pos'] == 'verb' for item in items])

#    def say_verb(verb_item):
#        word, items = verb_item
#        return ansi_color.underline(word.encode('utf-8')) + ' (' + items[0]['ja'] + ')'

    verbs = filter(is_verb, res)
    num_verbs = len(verbs)
#    if num_verbs == 0:
#        print "no verbs"
#    elif num_verbs == 1:
#        print "1 verb:", say_verb(verbs[0])
#    else:
#        print "%d verbs:" % num_verbs,
#        print ' | '.join(map(say_verb, verbs))
#    for i, verb in enumerate(verbs):
#        print "  %d)" % (1+i), util.render(verb)

    def match_case(item, pos, case):
        return item['pos'] in pos and item.has_key('_') and any([it[0] == case for it in item['_']])
    def has_subst_case(items, case):
        subst = ['noun','pronoun','adj','participle']
        # return items and any([match_case(item,subst,case) for item in items])
        if not items: return False
        elif any([match_case(item,subst,case) for item in items]): return True
        elif any([item['pos'] == 'preposition' and item['dominates'] == case for item in items]): return True
        else: return False

    for surface, items in res:
        is_verb = False
        if items and any([item['pos'] == 'verb' for item in items]):
            color = ansi_color.RED
            is_verb = True
#        elif items and any([item['pos'] in ['noun','pronoun'] for item in items]):
        elif has_subst_case(items, 'Nom'):
            color = ansi_color.BLUE
        elif has_subst_case(items, 'Acc'):
            color = ansi_color.BLACK
        elif has_subst_case(items, 'Gen'):
            color = ansi_color.GREEN
        elif has_subst_case(items, 'Abl'):
            color = ansi_color.YELLOW
        elif has_subst_case(items, 'Dat'):
            color = ansi_color.MAGENTA
        else:
            color = None # ansi_color.DEFAULT

        text = surface.encode('utf-8')
#1        print "/%s/ %s" % (text, str(color))
        # text = (u'%*s' % (-maxlen_uc, surface)).encode('utf-8')
        if color is not None:
            text = ansi_color.bold(text, color)
        if is_verb:
            text = ansi_color.underline(text)

        print '  ' + text + ' '*(maxlen_uc - len(surface) + 1),

        if items is None:
            print
        elif items == []:
            print '(?)'
        else:
            print ' | '.join(map(render_item, items))

    print


def main():
    if len(sys.argv) == 2:
        file = sys.argv[1]
        text.analyse_textfile(file, analyse_sentence)
    else:
        print "usage: %s <filename>" % sys.argv[0]

if __name__ == '__main__':
    main()
