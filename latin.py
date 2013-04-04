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


def is_not_none(x): return x is not None

class Item:
    def __init__(self, item):
        self.item = item
        self.surface = item['surface']
        self.pos = item['pos']
        self.ja = item['ja']

        self._ = item.get('_', None)
        self.dominates = item.get('dominates', None)
        self.target = []
        self.modifiers = []

    def attrib(self, name, default=None):
        return self.item.get(name, default)

    def match_case(self, pos, case):
        return self.pos in pos and any([it[0] == case for it in self._])

#    def modified(self):
#        return '<%s>'

    # itemをレンダリング
    def description(self):
        name = {'indicative':'直説法', 'subjunctive':'接続法', 'imperative':'命令法', 'infinitive':'不定法',
                'present':'現在', 'imperfect':'未完了', 'perfect':'完了', 'future':'未来',
                'past-perfect': '過去完了',
                'active':'能動', 'passive':'受動',
                '-':'-'}
        # pos = item['pos']
        if self.pos == 'noun':
            return '%s %s' % (self.ja, self._) +' // '+ util.render(self.modifiers)
        elif self.pos == 'adj':
            return 'a.%s %s' % (self.ja, self._)
        elif self.pos == 'verb':
            return 'v.%s %s%s %s.%s.%s' % (self.ja,
                                           self.item['person'],
                                           self.item['number'],
                                           name[self.item.get('mood', 'indicative')],
                                           name[self.item.get('voice', 'active')],
                                           name[self.item.get('tense', 'present')],
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
    def __init__(self, surface, items=None, extra_info={}):
        self.surface = surface
        self.surface_len = len(surface)
        if items is not None:
            self.items = map(Item, items) # へぇーこれで行けるんだ
        else:
            self.items = None
        self.extra_info = extra_info
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

    def description(self):
        if not self.items: return ''
        return util.render(self.surface) +":"+ util.render([item.description() for item in self.items])


class Sentence:
    def __init__(self, words):
        self.len = len(words)
        self.words = words
        self.pred_idx = None
        for i, word in enumerate(words):
            if word.is_verb():
                self.pred_idx = i
                break
#        print self.pred_idx

    # 前置詞の格支配を制約として可能性を絞り込む
    def prep_constraint(self):
        for i, word in enumerate(self.words):
            if i == self.len-1: break # これが最後の単語ならチェック不要
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

#            if len(dominates) == 0 or non_prep_exists: continue
            if len(dominates) == 0: continue

            # Acc/Ablになり得ない語をスキップしながら。
            actual = set()
            targets = []
            target_case = None
            for j in range(i+1, self.len):
                word = self.words[j]
                if word.items is None: continue #break
                to_skip = to_stop = False
                target = None
                for k, item in enumerate(word.items):
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
                                target = (j, k)
                                target_case = 'Abl'
                            break
                        if 'Acc' in dominates and any([case == 'Acc' for case in cases]):
                            if target_case == 'Abl':
                                to_stop = True
                            else: # None or already 'Acc'
                                target = (j, k)
                                target_case = 'Acc'
                            break
                        if any([case in ['Nom','Acc'] for case in cases]):
                            to_stop = True
                            break
                if to_stop: break
                if to_skip: continue
                if target:
                    targets.append(target)
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

            for j, k in targets:
                self.words[j].items = filter(lambda x:x is not None, map(filter_noun, self.words[j].items))

    def attach_modifier(self, target, modifier):
        ti, tj = target
        # mi, mj = modifier
        if modifier not in self.words[ti].items[tj].modifiers:
            self.words[ti].items[tj].modifiers.append(modifier)

    # 形容詞などの性・数・格一致を利用して絞り込む
    def modifier_constraint(self):
        for i, word in enumerate(self.words):
            if word.items is None: continue # 句読点はスキップ
            for j, item in enumerate(word.items):
                if item.pos in ['adj', 'participle']:
                    # targets = []
                    valid_cngs = []
                    for cng in item._: # case, number, gender
                        def find_targets(range_from, range_to):
                            target = None
                            if range_from < range_to:
                                rng = range(range_from, range_to+1, 1)
                            else:
                                rng = range(range_from, range_to-1, -1)
                            for i2 in rng:
                                w = self.words[i2]
                                if w.items is None: continue
                                # stop_here = False
                                for j2, item2 in enumerate(w.items):
                                    if item2._ is None or item2._ == []: continue
                                    if item2.pos not in ['noun']: continue
                                    if cng in item2._:
                                        target = (i2, j2)
                                        return [target]
                                        # stop_here = True
                                        # break
                                # if stop_here: break
                            # return target
                            return []
                        targets = find_targets(i-1, 0) + find_targets(i+1, self.len-1)
                        if targets != []:
                            # valid cng
                            print "%s(%d,%d)<%s> -> %s" % (word.surface.encode('utf-8'), i, j,
                                                           '.'.join(cng), util.render(targets))
                            for t in targets:
                                self.attach_modifier(t, (i,j))
                            valid_cngs.append(cng)
                    if valid_cngs != []:
                        word.items[j]._ = valid_cngs


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
                print ' | '.join([item.description() for item in word.items])
        print


    def item_at(self, i, j):
        return self.words[i].items[j]


    def translate(self):
        # assert(atmost only one predicate included in *res*)
        used = set()
        once_said = set()

        # 述語動詞と人称＆単複が一致したNomのみを主語としたい
        # A et B の場合複数形になるよね（未チェック）
        pred_person = pred_number = None
        if self.pred_idx is not None:
            predicate = self.words[self.pred_idx]
            pred_person = predicate.items[0].attrib('person')
            pred_number = predicate.items[0].attrib('number')
            # print "{%d, %s}" % (pred_person, pred_number)
            used.add(self.pred_idx)
        else:
            predicate = None

        def render_item(i, j):
            if i in once_said: return None
            target_item = self.item_at(i, j)
            ja = target_item.ja
            mods = [self.item_at(i,j).ja for i,j in target_item.modifiers]
            [used.add(i) for i,j in target_item.modifiers]
            if mods != []:
                ja = '<' + '&'.join(mods) + '>' + ja
            once_said.add(i)
            return ja

        def translate_prep(i, j):
            prep_item = self.item_at(i, j)
            used.add(i)
            prep_ja = prep_item.ja
            targets = prep_item.target
            jas = filter(is_not_none, [render_item(ti, tj) for ti, tj in targets])
            return '( ' + ' '.join(jas) + ' ) ' + prep_ja

        slot = {}
        # 前置詞とそれに支配された語
        for i, word in enumerate(self.words):
            if i in used: continue
            if word.items is None: continue
            for j, item in enumerate(word.items):
                if item.pos == 'preposition':
                    print translate_prep(i, j)
                    used.add(i)
                    break
                elif item.pos == 'adv':
                    print '[adv] ' + item.ja
                    used.add(i)
                    break
                elif item.pos == 'conj':
                    if item.surface == u'et':
                        pass
                    else:
                        print '[conj] ' + item.ja
                        used.add(i)
                    break

        # 動詞と合致した主格名詞を探す
        if predicate is not None:
            for i, word in enumerate(self.words):
                if i in used: continue
                if word.items is None: continue
                if not word.has_subst_case('Nom'): continue
                for j, item in enumerate(word.items):
                    to_skip = False
                    if item.pos in ['noun', 'pronoun']:
                        person = item.attrib('person')
                        if person and person != pred_person: continue
                        for case, number, gender in item._:
                            if case == 'Nom' and number == pred_number:
                                if gender == 'n': continue ## 中性主格をskipしているがこれはcase-by-case
                                if not slot.has_key('Nom'): slot['Nom'] = []
                                slot['Nom'].append((i,j))
                                used.add(i)
                                # to_skip = True
                                break
                        # if to_skip: break

        # （Nom, Vocを除く）
        for i, word in enumerate(self.words):
            if i in used: continue
            if word.items is None: continue
            for j, item in enumerate(word.items):
                if item.pos in ['noun', 'pronoun']:
                    # print item._
                    for case, number, gender in item._:
                        # if predicate is not None:
                        if predicate is not None and case in ['Nom', 'Voc']: continue
                        if not slot.has_key(case):
                            slot[case] = []
                        slot[case].append((i,j))

        # case, aux = ('Gen','の')

        # output
        subject_exists = False
        for case, aux in [('Nom','が'), ('Dat','に'), ('Acc','を'), ('Abl','で')]:
            ids = slot.get(case, None)
            if ids is None: continue

#            ids_not_used = filter(lambda ij:ij[0] not in used, ids)
            jas = filter(is_not_none, [render_item(i, j) for i, j in ids])
            if case == 'Nom' and jas != []:
                subject_exists = True
            if len(jas) > 0:
                print '(', '='.join(jas), ')', aux
            del slot[case]
            [used.add(i) for i, j in ids]

        # prep
 #       for prep, ids in slot.items():
 #           jas = [self.words[i].items[j].ja for i, j in ids]
 #           print '(', '='.join(jas), ')',
 #           i, j = prep_loc[prep]
 #           prep_item = self.words[i].items[j]
 #           print prep_item.ja

        if predicate:
            if not subject_exists:
                ja = {'1sg':'私', '1pl':'我々',
                      '2sg':'あなた', '2pl':'あなたがた',
                      '3sg':'彼,彼女,それ', '3pl':'彼ら,彼女ら,それら'}
                print '[' + ja['%d%s' % (pred_person, pred_number)] + ']が',
            verb = predicate.items[0]
            jas = verb.ja.split(',')
            voice = verb.attrib('voice')
            tense = verb.attrib('tense')
            if tense in ['imperfect', 'perfect']:
                if voice == 'passive':
                    suffix = "された"
                else:
                    suffix = "した"
            elif tense in ['future']:
                if voice == 'passive':
                    suffix = "されるだろう"
                else:
                    suffix = "するだろう"
            else:
                if voice == 'passive':
                    suffix = "される"
                else:
                    suffix = "する"

            print ','.join([ja + 'など' + suffix for ja in jas])
        else:
            print "NO VERB FOUND"

        print
        for i in range(self.len):
            if i in used: continue
            word = self.words[i]
            if not word.items: continue
            print 'UNSOLVED (%d):' % i, word.description()


def lookup_all(surfaces_uc):
    def lookup(surface):
        items = latindic.lookup(surface)
        if items: return Word(surface, items)
        if char.isupper(surface[0]):
            surface_lower = char.tolower(surface)
            items = latindic.lookup(surface_lower)
            if items: return Word(surface, items)
        if surface[-3:] == u'que':
            items = latindic.lookup(surface[:-3])
            if items:
                return Word(surface[:-3], items, {'enclitic':'que'})
        return None

    words = []

    l = len(surfaces_uc)
    i = 0
    while i < l:
        surface = surfaces_uc[i]
        if ord(surface[0]) <= 64: # 辞書引き（記号のみから成る語を除く）
            words.append(Word(surface, None))
            i += 1
            continue
        if i < l-1:
            surface2 = surface + u' ' + surfaces_uc[i+1]
            word2 = lookup(surface2)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if word2 is not None: # len(word2.items) > 0: #is not None: and len(lu2) > 0:
                words.append(word2)
                i += 2
                continue
        word = lookup(surface)
        if word is not None:
            words.append(word)
        else:
            words.append(Word(surface, []))
        i += 1

    return words


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


def analyse_sentence(surfaces):
    # words: string(utf-8)
    surfaces_uc = [surface.decode('utf-8') for surface in surfaces]
    # words = [Word(surface, items) for surface, items in lookup_all_words(words_uc)]
    words = lookup_all(surfaces_uc)
    # dump_res(res)
    # util.pp(map(lambda r:r[0], res))

    for sentence in split_sentence_by_verb(words):
        # 前置詞の格支配を利用して絞り込む
        sentence.prep_constraint()
        # 形容詞などの性・数・格一致を利用して絞り込む
        sentence.modifier_constraint()
        # sentence = prep_constraint(sentence)

        # print "  ---"
        sentence.dump()
#        print ansi_color.ANSI_FGCOLOR_BLUE
        print " ↓ "
        sentence.translate()
#        print ansi_color.ANSI_FGCOLOR_DEFAULT
        print
        print


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
