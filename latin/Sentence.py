#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin.ansi_color as ansi_color
from japanese import JaVerb
import Verb

from latin.AndOr import AndOr
from latin.Word import Word
from latin.Predicate import Predicate

class Sentence:
    def __init__(self, words):
        self.len = len(words)
        self.words = words
        self.pred_idx = None
        self.pred_word_item = None
        self.pred_sum = False
        for i, word in enumerate(words):
            if word.is_verb():
                self.pred_idx = i
                self.pred_word_item = word.first_item
                if self.pred_word_item.item.get('pres1sg', None) == 'sum':
                    self.pred_sum = True
                    break

    def plain_text(self):
        return ' '.join([word.surface for word in self.words])

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
            print("%s(%d)" % (word.surface.encode('utf-8'), cnt), end=' ')
            patterns *= cnt
        print(" -> %d PATTERNS" % patterns)

    # 属格支配をする形容詞
    def genitive_domination(self):
        for i, word in enumerate(self.words):
            if i == self.len-1: break # これが最後の単語ならチェック不要
            if word.items is None: continue # 句読点はスキップ

            for j, item in enumerate(word.items):
                if item.pos == 'adj' and item.attrib('base') == 'plēnus':
                    # util.pp(("DETECTED:", word.surface, item.attrib('base')))
                    def find_targets(range_from, range_to):
                        target = None
                        if range_from < range_to:
                            rng = list(range(range_from, range_to+1, 1))
                        else:
                            rng = list(range(range_from, range_to-1, -1))
                        for i2 in rng:
                            w = self.words[i2]
                            if w.items is None: continue
                            if w.surface == 'et': continue
                            for j2, item2 in enumerate(w.items):
                                if item2._ is None or item2._ == []: continue
                                if item2.pos not in ['noun']: continue
#                                if cng in item2._:
#                                    pass
                    targets = find_targets(i+1, self.len-1)

#    # 前置詞の格支配を制約として可能性を絞り込む
#    def prep_constraint(self):
#        for i, word in enumerate(self.words):
#            if i == self.len-1: break # これが最後の単語ならチェック不要
#            if word.items is None: continue # 句読点はスキップ
#
#            preps = []
#            non_preps = []
#            for item in word.items:
#                if item.pos == 'preposition':
#                    preps.append(item)
#                else:
#                    non_preps.append(item)
#
#            if preps == []: continue
#
#            dominates = set([item.dominates for item in preps])
#            non_prep_exists = False
#            if non_preps != []:
#                print "NON-PREP EXISTS:", [item.surface.encode('utf-8') for item in non_preps]
#                non_prep_exists = True
#
#            if len(dominates) == 0: continue
#
#            # Acc/Ablになり得ない語をスキップしながら。
#            actual = set()
#            targets = []
#            target_case = target_number = target_gender = None
#            for j in range(i+1, self.len):
#                word = self.words[j]
#                if word.items is None: continue #break
#                to_skip = to_stop = False
#                target = None
#                for k, item in enumerate(word.items):
#                    if item.pos in ['verb', 'preposition']: break
#                    if item._: # subst
#                        if item.pos == 'adj': continue ###
#                        here = False
#                        for case, number, gender in item._:
#                            if case == 'Gen':
#                                to_skip = True
#                                break # skip this work
#                            elif case == 'Acc':
#                                if target_case is None:
#                                    target = (j, k)
#                                    here = True
#                                    target_case, target_number, target_gender = (case, number, gender)
#                                elif target_case == 'Acc':
#                                    if number == target_number and gender == target_gender:
#                                        target = (j, k)
#                                        here = True
#                                    else:
#                                        to_skip = True
#                                        break
#                                elif target_case == 'Abl':
#                                    to_skip = True
#                                    break
#                            elif case == 'Abl':
#                                if target_case is None:
#                                    target = (j, k)
#                                    here = True
#                                    target_case, target_number, target_gender = (case, number, gender)
#                                elif target_case == 'Acc':
#                                    to_skip = True
#                                    break
#                                elif target_case == 'Abl':
#                                    if number == target_number and gender == target_gender:
#                                        target = (j, k)
#                                        here = True
#                                    else:
#                                        to_skip = True
#                                        break
#                            elif case in ['Nom','Acc']:
#                                to_stop = True
##                                break
#                            else:
#                                pass
#                if to_stop and not here: break
#                if to_skip: continue
#                if target:
#                    targets.append(target)
#
#            # prep側を絞る
#            def filter_prep(item):
#                # dominatesがtarget_caseでないprepのみを弾く
#                if item.pos != 'preposition': return True
#                return (item.dominates == target_case)
#
#            self.words[i].items = filter(filter_prep, self.words[i].items)
#            if self.words[i].items and len(self.words[i].items) > 0:
#                self.words[i].items[0].target = targets # メモしておく
#
#            # target側を絞る
#            def filter_noun(item):
#                if not item._: return None
#                item._ = filter(lambda a:a[0] == target_case, item._)
#                if item._ == []: return None
#                return item
#
#            for j, k in targets:
#                self.words[j].items = filter(lambda x:x is not None, map(filter_noun, self.words[j].items))

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
                        target = None
                        if range_from < range_to:
                            rng = list(range(range_from, range_to+1, 1))
                        else:
                            rng = list(range(range_from, range_to-1, -1))
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
                        found = find_targets(i-1, 0, cng) if i > 0 else []
                        targets_backward += [(f,cng) for f in found]
                    if targets_backward != []:
                        targets_backward.sort()
                        targets_backward.reverse()
                        nearest = None
                        for target, cng in targets_backward:
                            if nearest is None:
                                nearest = target
                                targets.append(target)
                            if target == nearest:
                                self.attach_modifier(target, (i,j))
                                valid_cngs.append(cng)
                            else:
                                break

                    targets_forward = []
                    if targets == []:
                        for cng in item._: # case, number, gender
                            found = find_targets(i+1, self.len-1, cng)
                            targets_forward += [(f,cng) for f in found]
                        if targets_forward != []:
                            targets_forward.sort()
                            nearest = None
                            for target, cng in targets_forward:
                                if nearest is None:
                                    nearest = target
                                    targets.append(target)
                                if target == nearest:
                                    self.attach_modifier(target, (i,j))
                                    valid_cngs.append(cng)
                                else:
                                    break

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
                    rng = list(range(range_from, range_to+1, 1))
                else:
                    rng = list(range(range_from, range_to-1, -1))
                for i2 in rng:
                    if i2 < 0 or len(self.words) <= i2: continue
                    w = self.words[i2]
                    if w.items is None: continue
                    blocked = True
                    for j2, item2 in enumerate(w.items):
                        if item2._ is None:
                            if item2.pos == 'verb':
                                blocked = False
                            pass
                        elif item2.pos in ['noun', 'participle']:
                            blocked = False
                            target = (i2, j2)
                            return [target]
                        elif item2.pos in ['adj']:
                            if item2.attrib('base') == 'plēnus':
                                target = (i2, j2)
                                return [target]
                            blocked = False
                        elif item2.pos in ['pronoun']:
                            blocked = False
                    if blocked: break
                return []

            targets = []
            targets_backward = find_targets(i-1, 0) if i > 0 else []

            if targets_backward != []:
                targets_backward.sort()
                targets_backward.reverse()
                targets.append(targets_backward[0])
            else:
                targets_forward = find_targets(i+1, self.len-1)
                if targets_forward != []:
                    targets_forward.sort()
                    targets.append(targets_forward[0])
            for t in targets:
                self.attach_modifier(t, (i,gen_j))



    def item_at(self, i, j):
        return self.words[i].items[j]


    def translate(self):
        # assert(atmost only one predicate included in *res*)
        used = set()
        once_said = set()

        # 述語動詞と人称＆単複が一致したNomのみを主語としたい
        # A et B の場合複数形になるよね（未チェック）
        pred_person = pred_number = None
        if self.pred_idx is not None and self.pred_word_item:
            pred_person = self.pred_word_item.attrib('person', 0)
            pred_number = self.pred_word_item.attrib('number', '*')
            used.add(self.pred_idx)

        def render_item(i, j):
            if i in once_said: return None
            once_said.add(i)
            item = self.item_at(i, j)
            ja = item.ja
            mods = []
            for mi, mj in item.modifiers:
                item_m = self.item_at(mi, mj)
                rendered = render_item(mi, mj)
                if rendered is None: continue
                if item_m.can_be_genitive() and not item.can_be_genitive():
                    rendered += '-の'
                mods.append(rendered)
                used.add(mi)
            if mods != []:
                ja = '<' + '&'.join(mods) + '>' + ja
            return ja

        def translate_prep(i, j):
            prep_item = self.item_at(i, j)
            used.add(i)
            prep_ja = prep_item.ja
            targets = prep_item.target
            jas = [x for x in [render_item(ti, tj) for ti, tj in targets] if x is not None]
            return '( ' + ' / '.join(jas) + ' ) ' + prep_ja


        slot = {}
        advs = []

        # 前置詞とそれに支配された語
        for i, word in enumerate(self.words):
            if i in used: continue
            if word.items is None: continue
            for j, item in enumerate(word.items):
                if item.pos == 'preposition':
                    print(translate_prep(i, j))
                    used.add(i)
                    break
                elif item.pos == 'adv':
                    advs.append(item.ja)
                    # print '[adv] ' + item.ja
                    used.add(i)
                    break
                elif item.pos == 'conj':
                    if word.surface == 'et':
                        print('[conj] そして')
                    else:
                        print('[conj] ' + item.ja)
                    used.add(i)
                    break
                elif item.pos == 'indecl':
                    print('[indecl] ' + item.ja)
                    used.add(i)
                    break

        # 動詞と合致した主格名詞を探す
        if self.pred_word_item is not None:
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
                                if (not self.pred_sum) and gender == 'n': continue ## 中性主格をskipしているがこれはcase-by-case
                                if 'Nom' not in slot: slot['Nom'] = []
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
                        if self.pred_word_item is not None and case in ['Nom', 'Voc']: continue
                        if case not in slot:
                            slot[case] = []
                        slot[case].append((i,j))

        # output
        subject_exists = False
        if self.pred_sum:
            case_and_aux = [('Nom','*'), ('Dat','に'), ('Acc','を'), ('Abl','で'), ('Voc','よ')]
        else:
            case_and_aux = [('Nom','が'), ('Dat','に'), ('Acc','を'), ('Abl','で'), ('Voc','よ')]
        for case, aux in case_and_aux:
            ids = slot.get(case, None)
            if ids is None: continue

#            ids_not_used = filter(lambda ij:ij[0] not in used, ids)
            jas = [x for x in [render_item(i, j) for i, j in ids] if x is not None]
            if case == 'Nom' and jas != []:
                subject_exists = True

            if len(jas) > 0:
                if case == 'Nom':
                    joint = ' == '
                else:
                    joint = ' / '
                print('(', joint.join(jas), ')', aux)
            del slot[case]
            [used.add(i) for i, j in ids]

        if self.pred_word_item:
            if not subject_exists:
                ja = {'1sg':'私', '1pl':'我々',
                      '2sg':'あなた', '2pl':'あなたがた',
                      '3sg':'彼,彼女,それ', '3pl':'彼ら,彼女ら,それら',
                      '0*':''}
                subject = '※ ( ' + ja['%d%s' % (pred_person, pred_number)] + ' )'
                if self.pred_sum:
                    subject += ' は'
                else:
                    subject += ' が'
                print(subject)
            verb = self.pred_word_item
            jas = verb.ja.split(',')

            # flags
            flag = Verb.INDICATIVE

            if verb.attrib('voice') == 'passive':
                flag |= Verb.PASSIVE

            tense = verb.attrib('tense')
            if tense == 'imperfect':
                flag |= Verb.PAST
            elif tense == 'perfect':
                flag |= Verb.PERFECT
            elif tense == 'future':
                flag |= Verb.FUTURE

            if advs != []:
                print("{", ', '.join(advs), "}", end=' ')
            print(','.join([JaVerb(ja).form(flag) for ja in jas]))
        else:
            print("\n // NO VERB FOUND")

        print()
        for i in range(self.len):
            if i in used: continue
            word = self.words[i]
            if not word.items: continue
            print(' // UNSOLVED (%d):' % i, word.description())

