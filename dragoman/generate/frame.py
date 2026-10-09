#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析の結果 (Predicate と格の枠) から、言語に依らない「文の枠」を取り出す
#
#   Puella rosam pulchram in hortō videt.
#     → Clause(verb=videō [現在・直説法・能動・3sg],
#              args=[subject: puella sg f, object: rosa sg f + pulcher, in + Abl: hortus sg m])
#
# 格は「役割」に置き換える (主格 → subject、対格 → object、与格 → recipient …)。元の格も残す (元の言語に戻すときに使う)。
# 語は見出し語 (lemma) と品詞・数・性で持つ。訳語 (日本語) は解析のものをそのまま。
#
from dataclasses import dataclass, field

from dragoman.core.Word import Word
from dragoman.core.AndOr import AndOr
from dragoman.core.PrepClause import PrepClause
from dragoman.core.Infinitive import InfinitiveClause
from dragoman.core.Predicate import is_negation
from dragoman.core.Participle import ParticiplePhrase, participle_kind, participle_item
from dragoman.core.Absolute import AblativeAbsolute
from . import connectives as conn

# 格 → 役割 (前置詞の無い格)
ROLES = {'Nom': 'subject', 'Acc': 'object', 'Dat': 'recipient', 'Abl': 'means', 'Gen': 'possessor',
         'Loc': 'place', 'Voc': 'address', 'Nom/Acc': 'object'}
ROLE_JA = {'unknown': '辞書に無い語', 'subject': '主語', 'object': '目的語', 'recipient': '受け手', 'means': '手段・道具', 'possessor': '所有者',
           'place': '場所', 'address': '呼びかけ', 'complement': '補語', 'prep': '前置詞句', 'infinitive': '不定詞句',
           'adverb': '副詞'}


@dataclass
class Lex:
    """語: 見出し語・品詞・訳語"""
    lemma: str
    pos: str
    ja: str = ''
    proper: bool = False   # 固有名詞 (英語で冠詞を付けない)
    degree: str = ''       # 形容詞の比較: '+' 比較級、'++' 最上級
    en: str = ''           # 辞書が英語で持っている訳語 (Wiktionary 由来の語。分詞の singing, having spoken …)
    desc: str = ''         # 代名詞の種類 (人称代名詞・指示代名詞 …)
    verb: str = ''         # 分詞のもとの動詞 (直説法現在1人称単数)
    verb_ja: str = ''      # 分詞のもとの動詞の日本語の訳語 (訳語を選ぶのに使う)
    surface: str = ''      # 文中の形 (変化しない語 (副詞) は元の言語に戻すときこの形で)


@dataclass
class NP:
    """名詞句 (名詞・代名詞・形容詞の名詞的用法、並列、前置詞句)"""
    head: Lex = None
    case: str = ''          # 元の言語の格
    number: str = 'sg'
    gender: str = ''
    cases: list = field(default_factory=list)       # 解析で残った格の候補 (Dat/Abl のような曖昧さを見せる)
    modifiers: list = field(default_factory=list)   # 形容詞 (Lex)
    genitives: list = field(default_factory=list)   # 属格の名詞句 (NP)
    conj: str = ''           # 並列なら接続詞 (et, aut, que …)
    correlative: bool = False   # 接続詞を各要素の前に置く並列 (et … et …「…も…も」)
    members: list = field(default_factory=list)     # 並列の要素 (NP)
    participles: list = field(default_factory=list)  # 名詞に係る分詞句 (Participial。hostem fugientem)
    prep: Lex = None         # 前置詞句なら前置詞
    surface: str = ''


@dataclass
class Clause:
    """節: 述語と、役割ごとの名詞句"""
    verb: Lex
    tense: str = 'present'
    mood: str = 'indicative'
    voice: str = 'active'
    person: int = 3
    number: str = 'sg'
    negated: bool = False
    copula: bool = False
    args: list = field(default_factory=list)       # (役割, NP) の列 (元の語順)
    adverbs: list = field(default_factory=list)    # Lex
    infinitives: list = field(default_factory=list)  # 不定詞句 (Clause。mood='infinitive')
    infinitive_kind: str = ''   # 不定詞句なら、支配する動詞の種類 (saying / perception / command / complement)
    adjuncts: list = field(default_factory=list)   # 独立奪格・述語的な分詞句 (Participial)
    connectives: list = field(default_factory=list)  # 文をつなぐ語 (et, autem, igitur, tum …。connectives.py の見出し)
    subordinator: str = ''   # 従属節の接続詞 (ubi, postquam, dum …)。あれば従属節
    after_main: bool = False   # 従属節が主節の後ろにある (ubi「〜するところの」と読む)
    surface: str = ''

    def role(self, name):
        return [np for r, np in self.args if r == name]


@dataclass
class Participial:
    """分詞句: 独立奪格 (mortuō rēge「王が死んで」) と述語的な分詞 (carpēns flōrēs「花を摘みながら」)"""
    verb: Lex                 # 分詞 (見出しは分詞の主格単数男性、verb にもとの動詞)
    kind: str = 'absolute'    # absolute / adverbial / attributive
    tense: str = 'present'    # present / past / future
    voice: str = 'active'     # 完了分詞の能動 (形式受動態動詞 locūtus) / 受動 (cognitus)
    case: str = 'Nom'         # 分詞の格・数・性 (一致する名詞と同じ)
    number: str = 'sg'
    gender: str = ''
    subject: NP = None        # 独立奪格の主語
    args: list = field(default_factory=list)   # (役割, NP)
    surface: str = ''


def _first_tag(item, case=None):
    """格・数・性の候補の最初のもの。case があればその格のもの (nūntiī: 属格なら Gen sg、主格なら Nom pl)"""
    tags = item._ or []
    if case is not None:
        tags = [t for t in tags if t[0] == case] or tags
    return tags[0] if tags else (None, 'sg', '')


LEMMA_HOOKS = []   # 見出しの無い項目 (ラテン語の代名詞) の見出しを決める関数 (言語ごとに登録)
VERB_GLOSS_HOOKS = []   # 動詞の見出し → 日本語の訳語 (分詞のもとの動詞の訳語を引く。言語ごとに登録)


def lex_of(word, item=None):
    item = item or word.items[0]
    lemma = item.attrib('base') or item.attrib('pres1sg')
    for hook in LEMMA_HOOKS:
        lemma = lemma or hook(item.item)
    lemma = lemma or item.surface
    return Lex(lemma, item.pos, item.ja, proper=lemma[:1].isupper() and item.pos in ('noun', 'unknown'),
               degree=item.attrib('rank') or '', en=item.attrib('ja_en') or '', desc=item.attrib('desc') or '',
               verb=item.attrib('pres1sg') or '' if item.pos == 'participle' else '',
               verb_ja=next((ja for ja in (hook(item.attrib('pres1sg')) for hook in VERB_GLOSS_HOOKS) if ja), '')
               if item.pos == 'participle' and item.attrib('pres1sg') else '',
               surface=word.surface if word is not None else item.surface)


def np_of(node, case=None):
    """Word / AndOr / PrepClause → NP。case は名詞句の格が決まっているとき (属格・前置詞の支配する格)"""
    if isinstance(node, PrepClause):
        prep = Lex(node.item.surface, 'preposition', node.item.ja)
        inner = [w for w in node.words if isinstance(w, (Word, AndOr)) and (not isinstance(w, Word) or w.items)]
        np = np_of(inner[0], node.dominated_case) if inner else NP(Lex('?', 'noun'))
        np.prep = prep
        np.case = node.dominated_case
        np.surface = node.surface
        return np
    if isinstance(node, AndOr):
        member_case = case or (node.cases[0] if node.cases else None)   # 要素は並列句の格で (puerī: 属格単数でなく主格複数)
        members = [np_of(words[0], member_case) for words in node.words_slots if words]
        conj = node.and_or_word
        last = node.words_slots[-1][0] if node.words_slots and node.words_slots[-1] else None
        if isinstance(last, Word) and last.surface.endswith('que') and conj == 'et' and \
                not (last.items and (last.items[0].attrib('base') or '').endswith('que')):
            conj = 'que'   # puerī puellaeque (並列句の名前は et になっている)
        return NP(conj=conj, members=members, number='pl', case=(node.cases or [''])[0],
                  cases=list(node.cases or []), surface=node.surface,
                  correlative=_led_by_conjunction(node, _sentence_words))
    if not isinstance(node, Word) or not node.items:
        return NP(Lex(node.surface, 'unknown'), surface=node.surface)
    item = node.items[0]
    case, number, gender = _first_tag(item, case)
    np = NP(lex_of(node), case=case or '', number=number or 'sg', gender=gender or '',
            cases=list(dict.fromkeys(t[0] for t in item._ or [])), surface=node.surface)
    for mod in node.modifiers:
        if isinstance(mod, Word) and mod.items and mod.items[0].pos != 'article':
            np.modifiers.append(lex_of(mod))
        elif isinstance(mod, AndOr):
            np.modifiers.append(np_of(mod))   # 並列した形容詞 (bonus et fortis vir)
        elif isinstance(mod, ParticiplePhrase):
            np.participles.append(participial_of(mod))
    for gen in node.genitives:
        np.genitives.append(np_of(gen, 'Gen'))
    return np


_sentence_words = []   # 解析中の文の語 (Word の列。並列の接続詞が先頭の要素の前にもあるかを見る)


def _led_by_conjunction(node, words):
    """et dominus et servus のように、最初の要素の前にも接続詞があるか"""
    first = node.words_slots[0][0] if node.words_slots and node.words_slots[0] else None
    index = getattr(first, 'index', None)
    if index is None or not words or index == 0 or index > len(words):
        return False
    return words[index - 1].surface.lower() == node.and_or_word


def clause_of(predicate, lang=None):
    """Predicate → Clause"""
    verb_item = predicate.first_item
    clause = Clause(lex_of(predicate.verb),
                    tense=verb_item.attrib('tense') or 'present', mood=verb_item.attrib('mood') or 'indicative',
                    voice=verb_item.attrib('voice') or 'active', person=verb_item.attrib('person') or 3,
                    number=verb_item.attrib('number') or 'sg', copula=predicate.is_sum, surface=predicate.surface)
    if predicate.conjunction is not None and is_negation(predicate.conjunction, predicate.language):
        clause.negated = True
    elif predicate.conjunction is not None and conn.is_connective(predicate.conjunction.surface):
        if conn.lookup(predicate.conjunction.surface)[0] == 'adv' and predicate.conjunction.items:
            clause.adverbs.append(lex_of(predicate.conjunction))   # tum, tandem, statim …
        else:
            _add_connective(clause, predicate.conjunction.surface)
    elif isinstance(predicate.conjunction, Word) and predicate.conjunction.items:
        clause.adverbs.append(lex_of(predicate.conjunction))   # 文頭の副詞 (解析では conjunction に入る: māgnopere)
    nominatives = []
    for case, objs in predicate.case_slot.items():
        for obj in objs:
            if isinstance(obj, InfinitiveClause):
                inner = clause_of(obj.predicate)
                inner.mood = 'infinitive'
                inner.infinitive_kind = obj.kind or 'complement'
                clause.infinitives.append(inner)
                continue
            if isinstance(obj, ParticiplePhrase) or isinstance(obj, AblativeAbsolute):
                clause.adjuncts.append(participial_of(obj))
                continue
            if isinstance(obj, PrepClause) and not obj.words:
                # 中身の無い前置詞句: 接続詞 (cum ita essent の cum) か、副詞として使った前置詞 (paulō post の post)
                if conn.is_connective(obj.prep):
                    _add_connective(clause, obj.prep)
                else:
                    clause.adverbs.append(Lex(obj.prep, 'adv', obj.item.ja, surface=obj.prep))
                continue
            np = np_of(obj, case if case in ('Nom', 'Acc', 'Dat', 'Abl', 'Gen', 'Loc', 'Voc') else None)
            if isinstance(case, tuple):
                clause.args.append(('prep', np))
            elif case == 'Nom':
                nominatives.append(np)
                clause.args.append(('subject', np))
            else:
                if not np.case:
                    np.case = case
                clause.args.append((ROLES.get(case, case), np))
    if clause.voice == 'passive' and not nominatives:
        # 受動の文で主語が無ければ、主格にも読める目的語を主語に (omnia parāta sunt、Haec nārrantur)
        for k, (role, np) in enumerate(clause.args):
            if role == 'object' and 'Nom' in (np.cases or [np.case]):
                np.case = 'Nom'
                clause.args[k] = ('subject', np)
                nominatives.append(np)
                break
    for inner in clause.infinitives:
        # 補足の不定詞 (cōnstituit līberāre) の主語は主節の主語 (解析で不定詞句に入ることがある: Herculēs)
        inner_subjects = inner.role('subject')
        if inner.infinitive_kind in ('complement', '') and inner_subjects and not nominatives and \
                'Nom' in (inner_subjects[0].cases or [inner_subjects[0].case]):
            np = inner_subjects[0]
            np.case = 'Nom'
            inner.args = [(r, x) for r, x in inner.args if x is not np]
            clause.args.insert(0, ('subject', np))
            nominatives.append(np)
    if predicate.is_sum and len(nominatives) >= 2:
        # 繋辞の文: 名詞を主語に、ほか (形容詞・2つめの名詞) を補語に
        subject = next((np for np in nominatives if np.head and np.head.pos in ('noun', 'pronoun')), nominatives[0])
        clause.args = [('complement', np) if any(np is n for n in nominatives) and np is not subject else (r, np)
                       for r, np in clause.args]
    for adv in predicate.modifiers:
        if is_negation(adv, predicate.language):
            clause.negated = True
        elif isinstance(adv, Word) and conn.lookup(adv.surface) and conn.lookup(adv.surface)[0] != 'adv':
            _add_connective(clause, adv.surface)
        elif isinstance(adv, Word) and adv.items:
            clause.adverbs.append(lex_of(adv))
    for sub in predicate.subordinates:
        if isinstance(sub, (ParticiplePhrase, AblativeAbsolute)):
            clause.adjuncts.append(participial_of(sub))
    return clause


def _first_index(np):
    words = [w for w in _sentence_words if w.surface == (np.surface.split(' ')[0] if np.surface else '')]
    return words[0].index if words else None


def _add_connective(clause, surface):
    key = conn.key(surface)
    if conn.CONNECTIVES[key][0] == 'sub':
        if clause.subordinator == 'simul' and key in ('atque', 'ac'):
            return   # simul atque「〜するとすぐに」
        clause.subordinator = key
    elif key in ('atque', 'ac') and clause.subordinator == 'simul':
        return
    elif key not in clause.connectives:
        clause.connectives.append(key)


def participial_of(phrase):
    """ParticiplePhrase / AblativeAbsolute → Participial"""
    item = participle_item(phrase.verb)
    kind = participle_kind(phrase.verb)
    tense = {'present': 'present', 'future': 'future'}.get(kind, 'past')
    case, number, gender = _first_tag(item)
    p = Participial(lex_of(phrase.verb, item), tense=tense, voice='passive' if kind == 'passive' else 'active',
                    case=case or 'Nom', number=number or 'sg', gender=gender or '', surface=phrase.surface)
    if isinstance(phrase, AblativeAbsolute):
        p.kind = 'absolute'
        p.subject = np_of(phrase.subject)
        p.case, p.number, p.gender = 'Abl', p.subject.number, p.subject.gender or p.gender
    else:
        p.kind = 'adverbial' if phrase.adverbial else 'attributive'
        if isinstance(phrase.head, Word) and phrase.head.items:
            case, number, gender = _first_tag(phrase.head.items[0])   # 名詞句にはしない (名詞の分詞句と循環するので)
            p.case, p.number, p.gender = case or p.case, number or p.number, gender or p.gender
    objects = phrase.case_slot.get('Acc', [])
    for c in phrase.complements:
        np = np_of(c)
        if any(c is o for o in objects):
            p.args.append(('object', np))
        elif isinstance(c, PrepClause):
            p.args.append(('prep', np))
        elif isinstance(c, Word) and c.items and c.items[0].pos == 'adv':
            p.args.append(('adverb', np))
        else:
            p.args.append((ROLES.get(np.case, 'means'), np))
    return p


def frames(analysis):
    """SentenceAnalysis → Clause の列"""
    _sentence_words[:] = analysis.words
    clauses = []
    for c in analysis.clauses:
        clause = clause_of(c.predicate)
        for word in c.not_solved:   # 述語に結びつかなかった接続詞 (et postquam … の postquam)、副詞 (aegrē)
            if isinstance(word, Word) and conn.is_connective(word.surface):
                _add_connective(clause, word.surface)
            elif isinstance(word, Word) and word.items and any(item.pos == 'adv' for item in word.items):
                clause.adverbs.append(lex_of(word, next(item for item in word.items if item.pos == 'adv')))
            elif isinstance(word, Word) and word.items and word.items[0].pos in ('indecl', 'num') and \
                    word.index is not None:
                # 結びつかなかった数詞 (duo frātrēs の duo): すぐ後ろの語の名詞句に付ける
                following = next((np for _, np in clause.args if np.head is not None and
                                  _first_index(np) == word.index + 1), None)
                if following is not None:
                    following.modifiers.insert(0, lex_of(word))
        clause.after_main = bool(clauses) and clause.subordinator in conn.AFTER_MAIN and not clause.connectives
        clauses.append(clause)
    _add_unknown_words(analysis, clauses)
    return clauses


ACCUSATIVE_ENDINGS = ('am', 'em', 'um', 'ēn', 'ān', 'ān', 'ōn')


def _add_unknown_words(analysis, clauses):
    """辞書に無い語 (多くはギリシア系の固有名詞: Zētēs, Peliam) は解析の構造に入らないので、文の中の位置で
    後ろの最も近い述語の節に 'unknown' として入れる (元の言語には綴りのまま戻し、ほかの言語では名前として)"""
    if not clauses:
        return
    verb_positions = []
    for c, clause in zip(analysis.clauses, clauses):
        index = getattr(c.predicate.verb, 'index', None)
        verb_positions.append(index if index is not None else 10 ** 6)
    nodes = analysis.nodes
    words = analysis.words
    skip = set()
    for n, node in enumerate(nodes):
        if n in skip or not (isinstance(node, Word) and node.items == [] and node.surface[:1].isalpha()):
            continue
        index = node.index if node.index is not None else 0
        after = [k for k, pos in enumerate(verb_positions) if pos >= index]
        k = after[0] if after else len(clauses) - 1
        if k > 0 and any(conn.lookup(w.surface) and conn.lookup(w.surface)[0] == 'sub'
                         for w in words[index + 1:verb_positions[k]] if isinstance(w, Word)):
            k -= 1   # 間に従属節の接続詞があれば前の節の語 (Monuit Peliam ut … cavēret の Peliam)
        clause = clauses[k]
        # 辞書に無い名前どうしの並列 (Zētēs et Calais): et は文のつなぎではなく名前の並列
        if n + 2 < len(nodes) and isinstance(nodes[n + 1], Word) and nodes[n + 1].surface in ('et', 'ac', 'atque') \
                and isinstance(nodes[n + 2], Word) and nodes[n + 2].items == [] and nodes[n + 2].surface[:1].isupper():
            other = nodes[n + 2]
            members = [NP(Lex(w.surface, 'noun', '', proper=True, surface=w.surface), surface=w.surface)
                       for w in (node, other)]
            np = NP(conj=nodes[n + 1].surface, members=members, number='pl', surface=node.surface + ' et ' + other.surface)
            skip.add(n + 2)
            if nodes[n + 1].surface in clause.connectives:
                clause.connectives.remove(nodes[n + 1].surface)
            role = 'subject' if not clause.role('subject') else 'unknown'
            np.case = 'Nom' if role == 'subject' else ''
            clause.args.append((role, np))
            continue
        if True:
            proper = node.surface[:1].isupper()
            np = NP(Lex(node.surface, 'noun' if proper else 'unknown', '', proper=proper, surface=node.surface),
                    surface=node.surface)
            role = 'unknown'
            if proper and node.surface.endswith(ACCUSATIVE_ENDINGS):
                role, np.case = 'object', 'Acc'   # Peliam, Aeētem, Glaucēn
            elif proper and not clause.role('subject') and (not after or index < verb_positions[after[0]]):
                role, np.case = 'subject', 'Nom'   # 述語より前で、節に主語が無ければ主語 (Zētēs … sublevāvērunt)
            clause.args.append((role, np))


def describe(clause, indent='  '):
    """文の枠を読める形に (確認用)"""
    labels = {'present': '現在', 'imperfect': '未完了', 'future': '未来', 'perfect': '完了',
              'past-perfect': '過去完了', 'future-perfect': '未来完了', 'indicative': '直説法',
              'subjunctive': '接続法', 'imperative': '命令法', 'infinitive': '不定法', 'active': '能動',
              'passive': '受動'}
    head = '%s述語: %s [%s %s%s %s %s%s]' % (indent, clause.verb.lemma, labels.get(clause.tense, clause.tense),
                                          clause.person, clause.number, labels.get(clause.mood, clause.mood),
                                          labels.get(clause.voice, clause.voice), ' 否定' if clause.negated else '')
    lines = [head]
    if clause.subordinator or clause.connectives:
        lines.append('%s  つなぎ: %s' % (indent, ' '.join(
            ([clause.subordinator + (' (後置: 〜するところの)' if clause.after_main else ' (従属節)')]
             if clause.subordinator else []) + clause.connectives)))
    for role, np in clause.args:
        name = ROLE_JA.get(role, role)
        if np.prep is not None:
            name += ' (%s + %s)' % (np.prep.lemma, np.case)
        else:
            name += ' (%s)' % '/'.join(np.cases or [np.case])
        lines.append('%s  %s: %s' % (indent, name, describe_np(np)))
    for adv in clause.adverbs:
        lines.append('%s  副詞: %s' % (indent, adv.lemma))
    for inner in clause.infinitives:
        lines.append('%s  不定詞句 (%s):' % (indent, inner.infinitive_kind))
        lines.extend(describe(inner, indent + '    ').splitlines())
    for p in clause.adjuncts:
        lines.append(describe_participial(p, indent + '  '))
    return '\n'.join(lines)


PARTICIPIAL_JA = {'absolute': '独立奪格', 'adverbial': '分詞句', 'attributive': '分詞 (修飾)'}


def describe_participial(p, indent):
    tense = {'present': '現在分詞', 'past': '完了分詞', 'future': '未来分詞'}[p.tense]
    lines = ['%s%s: %s (%s、%s%s %s %s%s)' % (indent, PARTICIPIAL_JA[p.kind], p.verb.lemma, p.verb.verb, tense,
                                           '・受動' if p.voice == 'passive' else '', p.case, p.number,
                                           (' ' + p.gender) if p.gender else '')]
    if p.subject is not None:
        lines.append('%s  主語 (Abl): %s' % (indent, describe_np(p.subject)))
    for role, np in p.args:
        lines.append('%s  %s (%s): %s' % (indent, ROLE_JA.get(role, role), np.case, describe_np(np)))
    return '\n'.join(lines)


def describe_np(np):
    if np.members:
        return (' %s ' % np.conj).join(describe_np(m) for m in np.members)
    if np.head.pos in ('adj', 'participle') and not np.number:
        return np.head.lemma
    text = '%s%s %s%s' % (np.head.lemma, np.head.degree, np.number, (' ' + np.gender) if np.gender else '')
    if np.modifiers:
        text += ' + ' + ', '.join(describe_np(m) if isinstance(m, NP) else m.lemma + m.degree
                                  for m in np.modifiers)
    for gen in np.genitives:
        text += ' ← 属格 ' + describe_np(gen)
    for p in np.participles:
        text += ' ← ' + describe_participial(p, '').strip()
    return text
