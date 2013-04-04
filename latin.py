#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import select
import getopt

import latin.util as util
import latin.textutil as textutil
import latin.latin_char as char
import latin.latin_noun as noun
import latin.latindic as latindic

import latin.ansi_color as ansi_color


class Item:
    def __init__(self, item):
        self.item = item
        self.surface = item['surface']
        self.pos = item['pos']
        self.ja = item['ja']

        self._ = item.get('_', None)
        self.dominates = item.get('dominates', None)

    def attrib(self, name, default=None):
        return self.item.get(name, default)

    def match_case(self, pos, case):
        return self.pos in pos and any([it[0] == case for it in self._])

    # itemをレンダリング
    def render(self):
        name = {'indicative':'直接法', 'subjunctive':'接続法', 'imperative':'命令法', 'infinitive':'不定法',
                'present':'現在', 'imperfect':'未完了', 'perfect':'完了', 'future':'未来',
                'past-perfect': '過去完了',
                'active':'能動', 'passive':'受動',
                '-':'-'}
        # pos = item['pos']
        if self.pos == 'noun':
            return '%s %s' % (self.ja, self._)
        elif self.pos == 'adj':
            return 'a.%s %s' % (self.ja, self._)
        elif self.pos == 'verb':
            return 'v.%s %s%s %s.%s.%s' % (self.ja,
                                           self.item['person'], self.item['number'],
                                           name[self.item.get('mood','indicative')],
                                           name[self.item.get('voice','active')],
                                           name[self.item.get('tense','present')],
                                           )
        elif self.pos == 'preposition':
            return 'prep<%s> %s' % (self.dominates, self.ja)
        else:
            if len(self.item) > 0:
                item_ = self.item.copy()
                del item_['surface'], item_['pos'], item_['ja']
                return '%s %s %s' % (self.pos, self.ja, util.render(item_))
            else:
                return '%s %s' % (self.pos, self.ja)


class Word:
    # has surface
    # has items
    def __init__(self, surface, items):
        self.surface = surface
        self.surface_len = len(surface)
        if items:
            self.items = [Item(item) for item in items]
        else:
            self.items = None
        self._is_verb = None

    def has_subst_case(self, case):
#        def match_case(item, pos, case):
#            return item['pos'] in pos and item.has_key('_') and any([it[0] == case for it in item['_']])
        # subst = ['noun','pronoun','adj','participle']
        subst = ['noun','pronoun']
        # return items and any([match_case(item,subst,case) for item in items])
        if not self.items: return False
        elif any([item.match_case(subst,case) for item in self.items]): return True
        elif any([item.pos == 'preposition' and item.dominates == case for item in self.items]): return True
        else: return False

    # 活用動詞ならtrue
    def is_verb(self):
        if self._is_verb is None: # memoize
            if self.items is None:
                self._is_verb = False
            else:
                self._is_verb = any([item.pos == 'verb' and item.attrib('mood') != 'infinitive' for item in self.items])
        return self._is_verb


class Sentence:
    def __init__(self, words):
        self.len = len(words)
        self.words = words

    # 前置詞の格支配を制約として可能性を絞り込む
    def prep_constraint(self):
        end = self.len
        for i, word in enumerate(self.words):
            if i == end-1: break # これが最後の単語ならチェック不要
            if word.items is None: continue # 句読点はスキップ

            preps = []
            non_preps = []
            for item in word.items:
                if item.pos == 'preposition':
                    preps.append(item)
                else:
                    non_preps.append(item)

            if preps == []: continue

            dominates = set([item.dominates for item in preps])
            non_prep_exists = False
            if non_preps != []:
                print "NON-PREP EXISTS:", [item.surface.encode('utf-8') for item in non_preps]
                non_prep_exists = True

            if len(dominates) == 0 or non_prep_exists: continue

            # Acc/Ablになり得ない語をスキップしながら。
            actual = set()
            targets = []
            target_case = None
            for j in range(i+1, end):
                word = self.words[j]
                if word.items is None: continue #break
                to_skip = to_stop = False
                is_target = False
                for item in word.items:
                    if item.pos in ['verb', 'preposition']: break
                    if item._: # subst
                        cases = [case for case, number, gender in item._]
                        if any([case == 'Gen' for case in cases]):
                            to_skip = True
                            break # skip this work
                        if 'Abl' in dominates and any([case == 'Abl' for case in cases]):
                            if target_case == 'Acc':
                                to_stop = True
                            else: # None or already 'Abl'
                                is_target = True
                                target_case = 'Abl'
                            break
                        if 'Acc' in dominates and any([case == 'Acc' for case in cases]):
                            if target_case == 'Abl':
                                to_stop = True
                            else: # None or already 'Acc'
                                is_target = True
                                target_case = 'Acc'
                            break
                        if any([case in ['Nom','Acc'] for case in cases]):
                            to_stop = True
                            break
                if to_stop: break
                if to_skip: continue
                if is_target:
                    targets.append(j)
            # print "'%s' may dominate: %s" % (util.render(word), util.render([res[j][0] for j in targets]))

            # prep側を絞る
            def filter_prep(item):
                # dominatesがtarget_caseでないprepのみを弾く
                if item.pos != 'preposition': return True
                return (item.dominates == target_case)

            self.words[i].items = filter(filter_prep, self.words[i].items)
            self.words[i].items[0].target = targets # メモしておく

            # target側を絞る
            def filter_noun(item):
                if not item._: return None
                item._ = filter(lambda a:a[0] == target_case, item._)
                if item._ == []: return None
                return item

            for j in targets:
                self.words[j].items = filter(lambda x:x is not None, map(filter_noun, self.words[j].items))


    def dump(self):
        # （表示用に）単語の最大長を得ておく
        maxlen_uc = max([word.surface_len for word in self.words])

        for word in self.words:
            is_verb = False
            if word.is_verb():
                color = ansi_color.RED
                is_verb = True
#            if verb_count == 0:
#                st['predicate'] = item
#        elif items and any([item['pos'] in ['noun','pronoun'] for item in items]):
            elif word.has_subst_case('Nom'):
                color = ansi_color.BLUE
            elif word.has_subst_case('Acc'):
                color = ansi_color.BLACK
            elif word.has_subst_case('Gen'):
                color = ansi_color.GREEN
            elif word.has_subst_case('Abl'):
                color = ansi_color.YELLOW
            elif word.has_subst_case('Dat'):
                color = ansi_color.MAGENTA
            else:
                color = None # ansi_color.DEFAULT

            text = word.surface.encode('utf-8')
#1        print "/%s/ %s" % (text, str(color))
        # text = (u'%*s' % (-maxlen_uc, surface)).encode('utf-8')
            if color is not None:
                text = ansi_color.bold(text, color)
            if is_verb:
                text = ansi_color.underline(text)

            print '  ' + text + ' '*(maxlen_uc - word.surface_len + 1),

            if word.items is None:
                print
            elif word.items == []:
                print '(?)'
            else:
                print ' | '.join([item.render() for item in word.items])
        print

    def translate(self):
        # assert(atmost only one predicate included in *res*)
        for i, word in enumerate(self.words):
            pass


# 辞書引き（記号のみから成る語を除く）
def lookup(word):
    if ord(word[0]) <= 64: return None

    res = latindic.lookup(word)
    if res: return res

    if char.isupper(word[0]):
        word_lower = char.tolower(word)
        res = latindic.lookup(word_lower)
        if res: return res

    if word[-3:] == u'que':
        res = latindic.lookup(word[:-3])
        if res: return res

    return []

def lookup_all_words(words_uc):
    res = []
    l = len(words_uc)
    i = 0
    while i < l:
        word = words_uc[i]
        if i < l-1:
            word2 = word + u' ' + words_uc[i+1]
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




# １文に活用動詞が１つ（あるいは0）になるように分断する
def split_sentence_by_verb(words):
    verbs_indices = []

    for i, word in enumerate(words):
        if word.is_verb():
            verbs_indices.append(i)
    # verbs = filter(is_verb, res)
    num_verbs = len(verbs_indices)

    sentences = []

    if num_verbs <= 1:
        sentences.append(Sentence(words))
    else:
        head = 0
        for i, idx in enumerate(verbs_indices):
            if i == num_verbs-1: # last one
                sentences.append(Sentence(words[head:]))
            else:
                next_idx = verbs_indices[i+1]
                # （次の動詞の手前までで）今の動詞の守備範囲を探る
                tail = idx + 1
                while tail < next_idx:
                    if words[tail].items is None: # 句読点系
                        sentences.append(Sentence(words[head:tail+1]))
                        break
                    tail += 1
                if tail == next_idx:
                    # 区切り（句読点）がない場合。とりあえず、次の動詞の直前まで取ってしまう
                    # （あとで検討）
                    sentences.append(Sentence(words[head:next_idx]))
                head = tail + 1

    return sentences


def analyse_sentence(words):
    # words: string(utf-8)
    words_uc = [word.decode('utf-8') for word in words]
    words = [Word(surface, items) for surface, items in lookup_all_words(words_uc)]
    # dump_res(res)
    # util.pp(map(lambda r:r[0], res))

    for sentence in split_sentence_by_verb(words):
        # 前置詞の格支配を利用して絞り込む
        sentence.prep_constraint()
        # sentence = prep_constraint(sentence)

        print "  ---"
        sentence.dump()
        sentence.translate()


# read-eval-print loop
def repl(do_trans=False, show_prompt=False):
    while True:
        if show_prompt:
            sys.stdout.write("> ")
            sys.stdout.flush()

        line = sys.stdin.readline()
        if not line: break

        text = line.rstrip()
        if do_trans:
            text = char.trans(text)

        textutil.analyse_text(text, analyse_sentence)

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

    latindic.load(no_macron_mode=no_macron_mode)

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
            text = textutil.load_text_from_file(file)
            if do_trans:
                text = char.trans(text)
            textutil.analyse_text(text, analyse_sentence, echo_on=True)


if __name__ == '__main__':
    main()
