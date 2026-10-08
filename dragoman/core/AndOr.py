#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dragoman.core.LatinObject import LatinObject
from dragoman.core import language

def uniq(s):
    return list(dict.fromkeys(s))  # 順序を保って重複を除く

def non_genitive(_):
    return 'Gen' not in [x[0] for x in _] if _ else False

def case_intersection(_s):
    cases_x = ['Nom','Voc','Acc','Gen','Dat','Abl','Loc']
    genders_x = []
    for _ in _s: # あとでreduceで書く
        cases = [x[0] for x in _]
        genders = uniq([x[2] for x in _])
        # print " > ", cases, genders
        cases_x = [case for case in cases_x if case in cases]
        genders_x = uniq(genders_x + genders)

    return (cases_x, genders_x)

def group_pos(words):
    num_of_words = len(words)
    if num_of_words == 1:
        if isinstance(words[0], AndOr):  # すでにまとめた並列句 (ἢ … καὶ … ἢ の中の καί の並列)
            return (words[0].pos, (words[0].cases, words[0].genders) if words[0].cases else None)
        if not words[0].items:  # 未知語・記号
            return (None, None)
        item = words[0].items[0]
        if item._ is not None:
            cases = [x[0] for x in item._]
            genders = uniq([x[2] for x in item._])
            return (item.pos, (cases, genders))
        else:
            return (item.pos, None)

    items = [word.items[0] for word in words if getattr(word, 'items', None)]  # 並列句 (AndOr) は除く
    if not items:
        return (None, None)
    # 格変化のある語を代表とする（なければ先頭の語）
    first_item = next((item for item in items if item._), items[0])
    _s = [item._ for item in items if item._]
    if not _s:
        return (first_item.pos, None)
    # _: [('Nom', 'sg', 'f'), ('Voc', 'sg', 'f')]
    _sg = list(filter(non_genitive, _s))
    if _sg:
        return (first_item.pos, case_intersection(_sg))
    else:
        return (first_item.pos, case_intersection(_s))


class AndOr (LatinObject):
    def __init__(self, and_or_word):
        self.and_or_word = and_or_word # u'et', u'neque', ...
        self.language = language.current()  # 訳すときにもこの言語の設定を使う
        self.words_slots = []
        self.pos = None
        self.info = None

        self.cases = None
        self.genders = None

        self.surfaces = []
        self.messages = []  # 解析の途中経過 (品詞・格の不一致など)

    def add(self, words):
        if not words:  # et et のように間に語が無い
            return
        self.words_slots.append(words)
        if len(words) == 1 and getattr(words[0], 'attached_to', None) is None:
            # 1語だけの並列要素 (firma et valida の valida) は付け先が決まっている
            # (形容詞の係り先探しで二重に付けない。puella parva のような複数語の要素の中の形容詞は対象外)
            words[0].attached_to = self

        self.surfaces.append(self.and_or_word)
        for word in words:
            self.surfaces.append(word.surface)

        pos, info = group_pos(words)
        # print " // GROUP POS:", pos, info
        if self.pos is None:
            self.pos = pos
            if self.pos in ('noun', 'pronoun', 'adj'):
                self.cases, self.genders = info or ([], [])
            else:
                self.info = info
        elif self.pos in ('noun', 'pronoun', 'adj'):
            cases, genders = info or ([], [])
            self.cases = [case for case in self.cases if case in cases]
            self.genders = uniq(self.genders + genders)
        elif self.pos == pos:
            if self.info == info:
                pass
            else:
                self.messages.append("  x info mismatch: %s %s" % (self.info, info))
        else:
            self.messages.append("  x pos mismatch: %s %s" % ((self.pos, self.info), (pos, info)))

        # updating
        self.surface = ' '.join(self.surfaces)
        self.surface_len = len(self.surface)


        # print self.surface_utf8()
        if self.cases:
            if self.pos == 'adj':
                # sgとは限らない
                self._ = []
                for case in self.cases:
                    for number in ['sg', 'pl']:
                        for gender in self.genders:
                            self._.append((case, number, gender))
            else:
                if not self.genders:
                    gender = None
                elif len(self.genders) >= 2:
                    gender = 'm'
                else:
                    gender = self.genders[0]
                self._ = [(case, 'pl', gender) for case in self.cases]
        else:
            self._ = []


    def dump(self):
#            print "    ET (", surfaces[start_idx:end_idx], "..)"
        for i, words in enumerate(self.words_slots):
            print("    ", self.and_or_word, '#', i, ":", ' '.join([word.surface for word in words]))

    def is_verb(self):
        return False

    def has_subst_case(self, case):
        if self.pos not in ('noun', 'adj'):
            return False
        return case in self.cases

    def detail(self):
        if len(self.genders) >= 2:
            gender = 'm'
        else:
            gender = self.genders[0]

        _ng = '.pl.' + gender

        s = '[%s] %s. [%s]' % (
            self.and_or_word.upper(),
            self.pos[0],
            '|'.join([case + _ng for case in self.cases])
            )
        return s

    def restrict(self):
        for words in self.words_slots:
            for word in words:
                word.restrict_cases([x[0] for x in self._])

    def restrict_cases(self, possible_cases):
        if self.cases is None:  # 格の無い並列 (動詞・副詞の並列)
            return
        self.cases = [case for case in self.cases if case in possible_cases]

    def translate(self):
        tr = []
        for words in self.words_slots:
            # tr.append(' '.join([word.translate() for word in words]))
            tr.append(words[0].translate()[0])
        if len(tr) > 1:
            # 訳語の候補が複数ある語は括る ({天,天界,天国,神}と{大地,地面,地上}。「神と大地」という項に見えないように)
            tr = [_bracket(t) for t in tr]
        if self.pos == 'adj':
            return ('、かつ'.join(tr), self.language.is_nor(self.and_or_word))
        else:
            return ('と'.join(tr), self.language.is_nor(self.and_or_word))


def _has_top_level_comma(text):
    depth = 0
    for c in text:
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif c == ',' and depth == 0:
            return True
    return False


def _bracket(text):
    """読点 (訳語の候補の区切り) を括弧の外に含む訳を {…} で括る"""
    return '{%s}' % text if _has_top_level_comma(text) else text
