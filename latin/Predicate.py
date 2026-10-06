#!/usr/bin/env python
# -*- coding: utf-8 -*-

from latin.LatinObject import LatinObject
from latin.Word import Word

from latin.AndOr import AndOr
from latin import language
from .japanese import JaVerb, copula_predicate, copula_conjunctive
from . import verb_flags as Verb

TENSE_LABELS = {'imperfect': '未完了', 'future': '未来', 'perfect': '完了',
                'past-perfect': '過去完了', 'future-perfect': '未来完了'}


def english_verb_label(verb, negated=False):
    labels = [TENSE_LABELS[verb.attrib('tense')]] if verb.attrib('tense') in TENSE_LABELS else []
    if verb.attrib('voice') == 'passive':
        labels.append('受動')
    if verb.attrib('mood') in ('subjunctive', 'imperative'):
        labels.append({'subjunctive': '接続法', 'imperative': '命令'}[verb.attrib('mood')])
    if negated:
        labels.append('否定')
    return '[%s]' % '・'.join(labels) if labels else ''


class Predicate (LatinObject):
    def __init__(self, verb):
        self.verb = verb
        self.case_slot = {}
        self.modifiers = []
        self.first_item = verb.items[0]
        self.surface = verb.surface
        self.surface_len = len(self.surface)
        self.conjunction = None
        self.subordinates = []  # 従属節 (独立奪格など)
        self.subordinate = False  # 不定詞句の中の述語 (主語は sum でも「は」でなく「が」)
        self.is_sum = language.current().is_copula(self.first_item.item.get('pres1sg', None))  # 繋辞 (sum)

    def add_nominal(self, case, obj):
        # self.objects[case] = self.objects.get(case, []).append(obj)
        if case in self.case_slot:
            self.case_slot[case].append(obj)
        else:
            self.case_slot[case] = [obj]

    def add_subordinate(self, clause):
        self.subordinates.append(clause)

    def add_modifier(self, adv):
        self.modifiers.append(adv)

    def is_verb(self):
        return True

    def person(self):
        return self.first_item.attrib('person')
    def number(self):
        return self.first_item.attrib('number')
    def mood(self):
        return self.first_item.attrib('mood')

    def detail(self):
        return self.verb.detail()

    def translate(self):
        # 訳の組み立てで格スロットを並べ替えるので、作業用のコピーを使う
        # (self.case_slot を書き換えると、表示や再度の translate() の結果が変わってしまう)
        case_slot = {case: list(objs) for case, objs in self.case_slot.items()}
        tr = []
        negated = False

        verb = self.first_item
        person = verb.attrib('person', 0)

        if self.conjunction:
            if self.conjunction.surface in language.current().and_words:
                t = 'そして'
            else:
                t, neg = self.conjunction.translate()
                if neg: negated = True
                if t.endswith(('〜ない', '〜しない')):
                    negated = True  # 文頭の否定の副詞 (nūllō pactō, nōn jam)
                    t = t.split('〜')[0]
            tr.append(t)

        # 独立奪格は文の頭に、述語的な分詞 (花を摘みながら) は主語の後に置く
        for clause in self.subordinates:
            if not getattr(clause, 'adverbial', False):
                tr.append(clause.translate()[0])

        cases_ja = language.current().case_particles

        sum_complement = []
        # Nominative
        noms = []
        nom_acc_objs = case_slot.get('Nom/Acc', [])
        if 'Nom' in case_slot or (person == 3 and nom_acc_objs):
            nom_objs = case_slot.get('Nom', [])
            # nom_acc_objs = case_slot.get('Nom/Acc', [])

            demand = 2 if self.is_sum else 1
            supply = len(nom_objs)
            if supply < demand and nom_acc_objs:
                insufficient = demand - supply
                nom_objs += nom_acc_objs[0:insufficient]
                nom_acc_objs = nom_acc_objs[insufficient:]

            for obj in nom_objs:
                nom, neg = obj.translate()
                if neg: negated = True

                if self.is_sum:
                    # 形容詞（修飾語）の場合
                    if isinstance(obj, Word) and obj.items[0].pos != 'noun':
                        # sum なら補語として
                        sum_complement.append(obj)
                    elif (len(noms) > 0 or len(nom_objs) == 1):
                        sum_complement.append(obj)
                    else:
                        noms.append(nom)
                else:
                    # 形容詞（修飾語）の場合
                    # (代名詞は訳語が「〜の」のもの (他の, 各人(の)) だけ)
                    if isinstance(obj, Word) and (obj.items[0].pos not in ('noun', 'pronoun') or
                                                  obj.items[0].pos == 'pronoun' and nom.endswith(('の', '(の)'))):
                        # sumでなければそういう人や物として
                        nom += '(人,物)'
                    noms.append(nom)

        if nom_acc_objs:
            case_slot['Acc'] = case_slot.get('Acc', []) + nom_acc_objs
            case_slot['Nom/Acc'] = []

        if not noms and verb.attrib('mood') != 'imperative' and not (self.is_sum and case_slot.get('Inf')):
            pn = str(self.person()) + str(self.number())
            subj_ja = {'1sg':'私', '2sg':'あなた', '3sg':'彼,彼女,それ',
                       '1pl':'我々', '2pl':'あなた方', '3pl':'彼ら,彼女ら,それら'}
            if pn in subj_ja:
                noms.append(subj_ja[pn])

        if noms:
            nom_case_ja = 'が'
            if self.is_sum and not self.subordinate:
                nom_case_ja = 'は'
            joined = '='.join(noms)
            if joined.endswith(nom_case_ja):
                nom_case_ja = ''  # 訳語に助詞まで入っているもの (何が)
            tr.append(joined + nom_case_ja)

        for clause in self.subordinates:
            if getattr(clause, 'adverbial', False):
                tr.append(clause.translate()[0])

        for case, objs in list(case_slot.items()):
            if case in ('Nom', 'Nom/Acc', 'Acc', 'Inf'): continue
            if not objs: continue
            if isinstance(case, tuple):
                # prep-clause
                case_ja = '' # case.encode('utf-8')
            else:
                case_ja = cases_ja[case]
            trs = []
            for obj in objs:
                t, neg = obj.translate()
                if neg: negated = True  # neque ... neque ... は主語以外の枠にも現れる
                trs.append(t)
            tr.append('='.join(trs) + case_ja)

        # Accusative
        if 'Acc' in case_slot:
            acc_objs = case_slot['Acc']
            case_slot['Acc'] = []
            accs = []
            for obj in acc_objs:
                t, neg = obj.translate()
                if neg: negated = True
                accs.append(t)
            accs = [acc[:-1] if acc[-1:] == 'が' else acc for acc in accs]
            tr.append('='.join(accs) + 'を') #[acc for acc in accs]))

        # 不定詞句 ({少年が 遊ぶ}と / {本を 読む}ことが)
        for clause in case_slot.get('Inf', []):
            tr.append(clause.translate()[0])

        # adverb
        for adv in self.modifiers:
            if is_negation(adv):
                negated = True
                continue
            ja = adv.items[0].ja
            if ja.endswith(('〜ない', '〜しない')):
                # 否定の副詞 (nūllō pactō「決して〜ない」, nusquam「どこにも〜ない」): 述語を否定形にする
                negated = True
                ja = ja.split('〜')[0]
            tr.append(ja)

        jas = verb.ja.split(',')

        # flags
        if verb.attrib('mood') == 'imperative':
            flag = Verb.IMPERATIVE
        else:
        # elif verb.attrib('mood') == 'indicative':
            # とりあえず直説法で出しておく
            flag = Verb.INDICATIVE

        if verb.attrib('voice') == 'passive':
            flag |= Verb.PASSIVE

        tense = verb.attrib('tense')
        if tense == 'imperfect':
            flag |= Verb.PAST | Verb.ING
        elif tense == 'perfect':
            flag |= Verb.PERFECT
        elif tense == 'future':
            flag |= Verb.FUTURE

#        if advs != []:
#            print "{", ', '.join(advs), "}",
        if verb.attrib('gloss_lang') == 'en':
            # 英語の訳語 (Wiktionary 由来) は活用させず、時制などを添える
            verb_tr = jas[0] + english_verb_label(verb, negated and not self.is_sum)
        else:
            verb_tr = ','.join([JaVerb(ja).form(flag, negated and not self.is_sum) for ja in jas])
        if self.is_sum and sum_complement:
            verb_tr = '='.join(copula_translation(obj, copula_tense(tense), negated) for obj in sum_complement)
        elif negated and self.is_sum:
            verb_tr = '¬'+ verb_tr  # 補語の無い sum (〜である) は否定の形を作れない

        if case_slot.get('Inf'):
            verb_tr = verb_tr.lstrip('〜～')  # {本を 読む}ことが できる (possum の訳語は「〜できる」)
        tr.append(verb_tr)

#        tr.append(self.first_item.ja )

        return (' / '.join(tr), False)


def is_negation(word):
    return isinstance(word, Word) and language.current().is_negation(word.surface)


def copula_tense(tense):
    if tense in ('imperfect', 'perfect', 'past-perfect'):
        return 'past'
    if tense in ('future', 'future-perfect'):
        return 'future'
    return 'present'


def _is_adjective(obj):
    if isinstance(obj, AndOr):
        return obj.pos == 'adj'
    return isinstance(obj, Word) and bool(obj.items) and obj.items[0].pos in ('adj', 'participle')


def copula_translation(obj, tense, negated):
    """sum の補語を述語の形に (大きい / 幸福であった / 農夫ではない)。並列した形容詞は 長くて広い"""
    if isinstance(obj, AndOr) and obj.pos == 'adj':
        heads = [words[0] for words in obj.words_slots]
        first = [copula_conjunctive(w.translate()[0], True, negated) for w in heads[:-1]]
        return ''.join(first) + copula_predicate(heads[-1].translate()[0], True, tense, negated, also=True)
    gloss = obj.translate()[0]
    # 修飾語 ({美しい}少女 / {人生の}満ちた) はそのまま前に置き、後ろの語だけを述語の形にする
    modifier, head = '', gloss
    if '}' in gloss:
        cut = gloss.rindex('}') + 1
        modifier, head = gloss[:cut], gloss[cut:]
    if not head:
        return gloss + 'である'
    return modifier + copula_predicate(head, _is_adjective(obj), tense, negated)
