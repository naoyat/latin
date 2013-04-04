#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import select
import getopt

import latin.util
import latin.textutil
import latin.latin_char
import latin.latin_noun
import latin.latindic

import latin.ansi_color


def lookup(word):
    if ord(word[0]) <= 64: return None

    res = latin.latindic.lookup(word)
    if res: return res

    if latin.latin_char.isupper(word[0]):
        word_lower = latin.latin_char.tolower(word)
        res = latin.latindic.lookup(word_lower)
        if res: return res

    if word[-3:] == u'que':
        res = latin.latindic.lookup(word[:-3])
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
                                       name[item.get('mood','indicative')],
                                       name[item.get('voice','active')],
                                       name[item.get('tense','present')],
                                       )
    elif pos == 'preposition':
        return 'prep<%s> %s' % (item['dominates'], item['ja'])
    else:
        item_ = item.copy()
        del item_['surface'], item_['pos'], item_['ja']
        if len(item_) > 0:
            return '%s %s %s' % (item['pos'], item['ja'], latin.util.render(item_))
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


def lookup_all_words(sentence_uc):
    res = []
    l = len(sentence_uc)
    i = 0
    while i < l:
        word = sentence_uc[i]
        if i < l-1:
            word2 = word + u' ' + sentence_uc[i+1]
            lu2 = lookup(word2)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if lu2 is not None and len(lu2) > 0:
                res.append([word2, lu2])
                i += 2
                continue
        lu = lookup(word)
        res.append([word, lu])
        i += 1

    return res


def dump_res(res):
    # （表示の都合で）単語の最大長を得ておく
    maxlen_uc = max(map(lambda r:len(r[0]), res))

    def match_case(item, pos, case):
        return item['pos'] in pos and item.has_key('_') and any([it[0] == case for it in item['_']])

    def has_subst_case(items, case):
        # subst = ['noun','pronoun','adj','participle']
        subst = ['noun','pronoun']
        # return items and any([match_case(item,subst,case) for item in items])
        if not items: return False
        elif any([match_case(item,subst,case) for item in items]): return True
        elif any([item['pos'] == 'preposition' and item['dominates'] == case for item in items]): return True
        else: return False

    for surface, items in res:
        is_verb = False
        if items and any([item['pos'] == 'verb' for item in items]):
            color = latin.ansi_color.RED
            is_verb = True
#            if verb_count == 0:
#                st['predicate'] = item
#        elif items and any([item['pos'] in ['noun','pronoun'] for item in items]):
        elif has_subst_case(items, 'Nom'):
            color = latin.ansi_color.BLUE
        elif has_subst_case(items, 'Acc'):
            color = latin.ansi_color.BLACK
        elif has_subst_case(items, 'Gen'):
            color = latin.ansi_color.GREEN
        elif has_subst_case(items, 'Abl'):
            color = latin.ansi_color.YELLOW
        elif has_subst_case(items, 'Dat'):
            color = latin.ansi_color.MAGENTA
        else:
            color = None # latin.ansi_color.DEFAULT

        text = surface.encode('utf-8')
#1        print "/%s/ %s" % (text, str(color))
        # text = (u'%*s' % (-maxlen_uc, surface)).encode('utf-8')
        if color is not None:
            text = latin.ansi_color.bold(text, color)
        if is_verb:
            text = latin.ansi_color.underline(text)

        print '  ' + text + ' '*(maxlen_uc - len(surface) + 1),

        if items is None:
            print
        elif items == []:
            print '(?)'
        else:
            print ' | '.join(map(render_item, items))
    print


def split_sentence(res):
    verbs_indices = []

    def is_verb(r):
        word, items = r
        if items is None: return False
        return any([item['pos'] == 'verb' and item.get('mood','-') != 'infinitive' for item in items])

    for i, r in enumerate(res):
        if is_verb(r):
            verbs_indices.append(i)
    # verbs = filter(is_verb, res)
    num_verbs = len(verbs_indices)

    sentences = []

    if num_verbs <= 1:
        sentences.append(res)
    else:
        head = 0
        for i, idx in enumerate(verbs_indices):
            if i == num_verbs-1: # last one
                sentences.append(res[head:])
            else:
                next_idx = verbs_indices[i+1]
                tail = idx + 1
                while tail < next_idx:
                    if res[tail][1] is None:
                        break
                    tail += 1
                sentences.append(res[head:tail+1])
                head = tail + 1

    return sentences


def analyse_sentence(sentence):
    # string(utf-8) --> unicode
    sentence_uc = [word.decode('utf-8') for word in sentence]

    res = lookup_all_words(sentence_uc)
    # dump_res(res)
    # util.pp(map(lambda r:r[0], res))

    for res in split_sentence(res):
        # print "  ==="
        # dump_res(res)

        # 前置詞の各支配を利用して絞り込む
        res = prep_constraint(res)

        print "  ---"
        dump_res(res)


def repl(do_trans=False, show_prompt=False):
    while True:
        if show_prompt:
            sys.stdout.write("> ")
            sys.stdout.flush()

        line = sys.stdin.readline()
        if not line: break

        text = line.rstrip()
        if do_trans:
            text = latin.latin_char.trans(text)

        latin.textutil.analyse_text(text, analyse_sentence)

    if show_prompt:
        print


def usage():
    print "Usage: python %s [options] [FILENAME]" % sys.argv[0]
    print "Options:"
    print "  -t, --trans                        Truncate feature-collection at first."
    print "  -n, --no-macron                    No-macron mode."
    print "  -h, --help                         Print this message and exit."


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "thn", ["trans", "help", "no-macron"])
    except getopt.GetoptError:
        usage()
        sys.exit()

    do_trans = False
    no_macron_mode = False

    for option, arg in opts:
        if option in ('-t', '--trans'):
            do_trans = True
        elif option in ('-n', '--no-macron'):
            no_macron_mode = True
        elif option in ('-h', '--help'):
            usage()
            sys.exit()

    latin.latindic.load(no_macron_mode=no_macron_mode)

    if len(args) == 0:
        # repl mode
        if select.select([sys.stdin,],[],[],0.0)[0]:
            # have data from pipe. no prompt.
            repl(do_trans=do_trans)
        else:
            repl(do_trans=do_trans, show_prompt=True)
    else:
        # file mode
        for file in args:
            text = latin.textutil.load_text_from_file(file)
            if do_trans:
                text = latin.latin_char.trans(text)
            latin.textutil.analyse_text(text, analyse_sentence, echo_on=True)


if __name__ == '__main__':
    main()
