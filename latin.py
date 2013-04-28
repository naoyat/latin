#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
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
        self.target = []
        self.modifiers = []

    def attrib(self, name, default=None):
        return self.item.get(name, default)

    def match_case(self, pos, case):
        return self.pos in pos and any([it[0] == case for it in self._])

    def can_be_genitive(self):
        return self._ and any([it[0] == 'Gen' for it in self._])

    # itemをレンダリング
    def description(self):
        name = {
            # tense
            'present':'現在', 'future':'未来', # 'past':'過去',
            'imperfect':'未完了', 'perfect':'完了', 'past-perfect': '過去完了',
            # mode
            'indicative':'直説法', 'subjunctive':'接続法', 'imperative':'命令法', 'infinitive':'不定法',
            #
            'participle':'分詞', 'gerundium':'動名詞',
            # 数
            'sg':'単数', 'pl':'複数',
            # (態:Genus)
            'active':'能動', 'passive':'受動',
            '-':'-'}
        # pos = item['pos']
        def short_(_):
            return '|'.join(map(lambda s:'.'.join(s), _))

        if self.pos == 'noun':
            return '%s [%s]' % (self.ja, short_(self._)) +' // '+ util.render(self.modifiers)
        elif self.pos in ['adj', 'participle']:
            return '%s.%s [%s]' % (self.pos[0], self.ja, short_(self._))
        elif self.pos == 'verb':
            return 'v.%s %s%s %s.%s.%s' % (self.ja,
                                           self.item.get('person', 0),
                                           self.item.get('number', '-'),
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
#                util.pp((self.surface, [item.attrib('mood','*') if item.pos == 'verb' else '-' for item in self.items]))
                self._is_verb = all([item.pos == 'verb' and item.attrib('mood') != 'infinitive' for item in self.items])
        return self._is_verb

    def description(self):
        if not self.items: return ''
        return util.render(self.surface) +":"+ util.render([item.description() for item in self.items])


class Sentence:
    def __init__(self, words):
        self.len = len(words)
        self.words = words
        self.pred_idx = None
        self.pred_word = None
        self.pred_sum = False
        for i, word in enumerate(words):
            if word.is_verb():
                self.pred_idx = i
                self.pred_word = word
                if word.items[0].item.get('pres1sg', None) == 'sum':
                    self.pred_sum = True
                break
#        print self.pred_idx

    def count_patterns(self):
        patterns = 1
        for i, word in enumerate(self.words):
            if word.items is None: continue
            cnt = 0
            for j, item in enumerate(word.items):
                if item._ is not None and item._ != []:
                    cnt += len(item._)
                else:
                    cnt += 1
            print "%s(%d)" % (word.surface.encode('utf-8'), cnt),
            patterns *= cnt
        print " -> %d PATTERNS" % patterns

    # 属格支配をする形容詞
    def genitive_domination(self):
        for i, word in enumerate(self.words):
            if i == self.len-1: break # これが最後の単語ならチェック不要
            if word.items is None: continue # 句読点はスキップ

            for j, item in enumerate(word.items):
                if item.pos == 'adj' and item.attrib('base') == u'plēnus':
                    # util.pp(("DETECTED:", word.surface, item.attrib('base')))
                    def find_targets(range_from, range_to):
                        target = None
                        if range_from < range_to:
                            rng = range(range_from, range_to+1, 1)
                        else:
                            rng = range(range_from, range_to-1, -1)
                        for i2 in rng:
                            w = self.words[i2]
                            if w.items is None: continue
                            if w.surface == u'et': continue
                            for j2, item2 in enumerate(w.items):
                                if item2._ is None or item2._ == []: continue
                                if item2.pos not in ['noun']: continue
#                                if cng in item2._:
#                                    pass
                    targets = find_targets(i+1, self.len-1)

    dot_file_count = 0

    # dotファイルを吐く
    def dot(self, name):
#        self.dot_file_count += 1
#        outfile = '%03d.dot' % self.dot_file_count
        with open('tmp/' + name + '.dot', 'w') as fp:
            fp.write('graph aaa {\n')
#            fp.write('  graph [ center = "false", ordering = out, ranksep = 0.2, nodesep = 0.5 ];\n')
            fp.write('  graph [ rankdir = LR ];\n')
#            fp.write('  node [ fontname = "Courier", fontsize = 11, shape = circle, width = 0.2, height = 0.2, margin = 0.01 ];\n')
            fp.write('  node [ fontname = "Courier", fontsize = 11, shape = circle, width = 0.2, height = 0.2 ];\n')
            fp.write('  edge [ color = black, weight = -1 ];\n')

            last_ks = 0
            for i, word in enumerate(self.words):
                surface = word.surface.encode('utf-8')
                k = 0
                if word.items is None:
                    fp.write('  W%d_0 [ label = "%s" ];\n' % (i, surface))
                    k += 1
                else:
                    for j, item in enumerate(word.items):
                        if isinstance(item._, list):
                            for it in item._:
                                info = '-'.join(it)
                                node = """
  W%d_%d [
    label = "%s\\n%s"
    pos = "%d,%d!"
  ];
""" % (i, k, surface, info, i*2, k*2)
                                fp.write(node)
                                k += 1
                        else:
                            info = item.pos[:4]
                            node = """
  W%d_%d [
    label = "%s\\n%s"
    pos = "%d,%d!"
  ];
""" % (i, k, surface, info, i*2, k*2)
                            fp.write(node)
                            k += 1

                if i > 1:
                    for ki in range(1):#last_ks):
                        for kj in range(k):
                            fp.write('  W%d_%d -- W%d_%d;\n' % (i-2, ki, i, kj))
                last_ks = k
#            fp.write('L2 [ shape = box, width = 0.1, height = 0.1, label = "" ];\n')
#            fp.write('N2 -- L2;\n')
#            fp.write('R2 [ shape = box, width = 0.1, height = 0.1, label = "" ];\n')
#            fp.write('N2 -- R2;\n')

            fp.write('}\n')
        os.system("dot -Kfdp -n -Tpng -o tmp/%s.png tmp/%s.dot" % (name, name))

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
            if self.words[i].items and len(self.words[i].items) > 0:
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
                    def find_targets(range_from, range_to, cng):
                            # print "- find_targets(%d, %d) within %d" % (range_from, range_to, len(self.words))
                        target = None
                        if range_from < range_to:
                            rng = range(range_from, range_to+1, 1)
                        else:
                            rng = range(range_from, range_to-1, -1)
                        for i2 in rng:
                            if i2 < 0 or len(self.words) <= i2: continue
                            w = self.words[i2]
                            if w.items is None: continue
                            # stop_here = False
                            for j2, item2 in enumerate(w.items):
                                if item2._ is None or item2._ == []: continue
                                if item2.pos not in ['noun']: continue
                                if cng in item2._:
                                    target = (i2, j2)
                                    return [target]
                        return []

                    targets = []
                    valid_cngs = []

                    targets_backward = []
                    for cng in item._: # case, number, gender
                        found = find_targets(i-1, 0, cng)
                        targets_backward += [(f,cng) for f in found]
                    if targets_backward != []:
                        targets_backward.sort()
                        #targets_backward.reverse()
                        target, cng = targets_backward[-1]
                        self.attach_modifier(target, (i,j))
                        print "  // %s(%d,%d)<%s> -> %s" % (word.surface.encode('utf-8'), i, j,
                                                            '.'.join(cng), util.render(target))
                        targets.append(target)
                        valid_cngs.append(cng)

#                        if targets != []:
#                            # valid cng
#                            for t in targets:
#                                self.attach_modifier(t, (i,j))
#                            valid_cngs.append(cng)

                    targets_forward = []
                    if targets == []:
                        for cng in item._: # case, number, gender
                            found = find_targets(i+1, self.len-1, cng)
                            targets_forward += [(f,cng) for f in found]
                        if targets_forward != []:
                            targets_forward.sort()
                            target, cng = targets_forward[0]
                            self.attach_modifier(target, (i,j))
                            print "  // %s(%d,%d)<%s> -> %s" % (word.surface.encode('utf-8'), i, j,
                                                                '.'.join(cng), util.render(target))
                            targets.append(target)
                            valid_cngs.append(cng)

#                        if targets != []:
#                            # valid cng
#                            print "  // %s(%d,%d)<%s> -> %s" % (word.surface.encode('utf-8'), i, j,
#                                                           '.'.join(cng), util.render(targets))
#                            for t in targets:
#                                self.attach_modifier(t, (i,j))
#                            valid_cngs.append(cng)

                    if valid_cngs != []:
                        word.items[j]._ = valid_cngs


    def genitive_constraint(self):
        for i, word in enumerate(self.words):
            if word.items is None: continue # 句読点はスキップ
            if not word.has_subst_case('Gen'): continue
            gen_j = None
            for j, item in enumerate(word.items):
                if not item._: continue
                for cng in item._:
                    if cng[0] == 'Gen':
                        gen_j = j
                        break
                if gen_j is not None: break
            if gen_j is None: continue

            def find_targets(range_from, range_to):
                target = None
                if range_from < range_to:
                    rng = range(range_from, range_to+1, 1)
                else:
                    rng = range(range_from, range_to-1, -1)
                for i2 in rng:
                    if i2 < 0 or len(self.words) <= i2: continue
                    w = self.words[i2]
                    if w.items is None: continue
                    blocked = True
                    for j2, item2 in enumerate(w.items):
                        # if item2._ is None or item2._ == []: continue
                        if item2._ is not None and item2.pos in ['noun', 'participle']:
                            blocked = False
                            target = (i2, j2)
                            return [target]
                    if blocked: break
                return []

            targets = find_targets(i-1, 0) + find_targets(i+1, self.len-1)

            print "  // %s(%d,%d)<Gen> -> %s" % (word.surface.encode('utf-8'), i, gen_j,
                                            util.render(targets))
            if targets != []:
                for t in targets:
                    self.attach_modifier(t, (i,gen_j))


    def dump(self):
        # （表示用に）単語の最大長を得ておく
        maxlen_uc = max([0] + [word.surface_len for word in self.words])

        for i, word in enumerate(self.words):
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

            print '  %2d  ' % (i) + text + ' '*(maxlen_uc - word.surface_len + 1),

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
        predicate = pred_person = pred_number = None
        if self.pred_idx is not None:
            predicate = self.pred_word
            pred_person = predicate.items[0].attrib('person', 0)
            pred_number = predicate.items[0].attrib('number', '*')
            used.add(self.pred_idx)

        def render_item(i, j):
            if i in once_said: return None
            item = self.item_at(i, j)
            ja = item.ja
            mods = []
            for mi, mj in item.modifiers:
                item_m = self.item_at(mi, mj)
                rendered = render_item(mi, mj)
                if item_m.can_be_genitive() and not item.can_be_genitive():
                    rendered += '-の'
                mods.append(rendered)
                used.add(mi)
            if mods != []:
                ja = '<' + '&'.join(mods) + '>' + ja
            once_said.add(i)
            return ja

        def translate_prep(i, j):
            prep_item = self.item_at(i, j)
            used.add(i)
            prep_ja = prep_item.ja
            targets = prep_item.target
            jas = filter(lambda x:x is not None, [render_item(ti, tj) for ti, tj in targets])
            return '( ' + ' / '.join(jas) + ' ) ' + prep_ja

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
#                    if item.surface == u'et':
#                        pass
#                    else:
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
                    if item.pos in ['noun', 'pronoun']:
                        person = item.attrib('person')
                        if not self.pred_sum:
                            if person and person != pred_person: continue
                        for case, number, gender in item._:
                            if case == 'Nom' and (self.pred_sum or number == pred_number):
                                if not self.pred_sum and gender == 'n': continue ## 中性主格をskipしているがこれはcase-by-case
                                if not slot.has_key('Nom'): slot['Nom'] = []
                                slot['Nom'].append((i,j))
                                used.add(i)
                                break

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
        if self.pred_sum:
            case_and_aux = [('Nom','*'), ('Dat','に'), ('Acc','を'), ('Abl','で')]
        else:
            case_and_aux = [('Nom','が'), ('Dat','に'), ('Acc','を'), ('Abl','で')]
        for case, aux in case_and_aux:
            ids = slot.get(case, None)
            if ids is None: continue

#            ids_not_used = filter(lambda ij:ij[0] not in used, ids)
            jas = filter(lambda x:x is not None, [render_item(i, j) for i, j in ids])
            if case == 'Nom' and jas != []:
                subject_exists = True
            if len(jas) > 0:
                print '(', ' == '.join(jas), ')', aux
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
                      '3sg':'彼,彼女,それ', '3pl':'彼ら,彼女ら,それら',
                      '0*':''}
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
        tail = len(words) - 1
        next_idx = tail + 1
        for i, idx in enumerate(verbs_indices):
            if i == num_verbs-1: # last one
                # print words[idx].surface.encode('utf-8')
                sentences.append(Sentence(words[head:]))
            else:
                next_idx = verbs_indices[i+1]
                # （次の動詞の手前までで）今の動詞の守備範囲を探る
                tail = idx + 1
                while tail < next_idx:
                    if words[tail].items is None: # 句読点系
                        sentences.append(Sentence(words[head:tail+1]))
                        break
                    elif words[tail].surface == u'et':
                        tail -= 1
                        sentences.append(Sentence(words[head:tail+1]))
                        break
                    tail += 1
                if tail == next_idx:
                    # 区切り（句読点）がない場合。とりあえず、次の動詞の直前まで取ってしまう
                    # （あとで検討）
                    sentences.append(Sentence(words[head:next_idx]))
                head = tail + 1

#    for s in sentences:
#        print "  -",
#        for w in s.words:
#            print w.surface.encode('utf-8'),
#        print

    return sentences


def analyse_sentence(surfaces):
    # words: string(utf-8)
    surfaces_uc = [surface.decode('utf-8') for surface in surfaces]
    # words = [Word(surface, items) for surface, items in lookup_all_words(words_uc)]
    words = lookup_all(surfaces_uc)
    # dump_res(res)
    # util.pp(map(lambda r:r[0], res))

    for i, sentence in enumerate(split_sentence_by_verb(words)):
        # sentence.count_patterns()
        # 前置詞の格支配を利用して絞り込む
        sentence.prep_constraint()

        # sentence.dot('_'.join([word.surface.encode('utf-8') for word in sentence.words]))

        # 属格支配する形容詞
        sentence.genitive_domination()
        # 形容詞などの性・数・格一致を利用して絞り込む
        sentence.modifier_constraint()
#        sentence.count_patterns()
        # 属格がどこにかかるか
        sentence.genitive_constraint()

        print "  ---"
        sentence.dump()
#        print ansi_color.ANSI_FGCOLOR_BLUE
        print " ↓ "
        sentence.translate()
#        print ansi_color.ANSI_FGCOLOR_DEFAULT
        print

    print "========"


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
