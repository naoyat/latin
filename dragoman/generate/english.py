#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) から英語の文を作る
#
#   語順は 主語 - 動詞 - 目的語 - 受け手 (to …) - 前置詞句・手段 (with …) - 副詞
#   名詞は the + (形容詞) + 名詞 (+ of + 属格)。複数は -s。固有名詞・代名詞には冠詞を付けない
#   動詞は時制・態・人称で形を変える (sees / saw / was seeing / will see / has seen / is seen …)、否定は do を補う
#
# 訳語はラテン語なら Wiktionary の表 ($DRAGOMAN_DATA/la-en.tsv。tools/build_latin_english.py) から。
# 無ければ日本語の訳語を [ ] で出す。
#
import csv
import functools
import os
import re
import unicodedata

from dragoman.core import paths, en_ja

# 不規則動詞: 原形 → (過去形, 過去分詞)
IRREGULAR = {
    'be': ('was', 'been'), 'have': ('had', 'had'), 'do': ('did', 'done'), 'go': ('went', 'gone'),
    'come': ('came', 'come'), 'see': ('saw', 'seen'), 'give': ('gave', 'given'), 'take': ('took', 'taken'),
    'make': ('made', 'made'), 'say': ('said', 'said'), 'tell': ('told', 'told'), 'get': ('got', 'got'),
    'know': ('knew', 'known'), 'think': ('thought', 'thought'), 'find': ('found', 'found'),
    'leave': ('left', 'left'), 'hear': ('heard', 'heard'), 'write': ('wrote', 'written'), 'read': ('read', 'read'),
    'run': ('ran', 'run'), 'sing': ('sang', 'sung'), 'fight': ('fought', 'fought'), 'bring': ('brought', 'brought'),
    'buy': ('bought', 'bought'), 'teach': ('taught', 'taught'), 'seek': ('sought', 'sought'),
    'catch': ('caught', 'caught'), 'fall': ('fell', 'fallen'), 'eat': ('ate', 'eaten'), 'drink': ('drank', 'drunk'),
    'speak': ('spoke', 'spoken'), 'stand': ('stood', 'stood'), 'sit': ('sat', 'sat'), 'lead': ('led', 'led'),
    'send': ('sent', 'sent'), 'build': ('built', 'built'), 'hold': ('held', 'held'), 'keep': ('kept', 'kept'),
    'sleep': ('slept', 'slept'), 'feel': ('felt', 'felt'), 'meet': ('met', 'met'), 'put': ('put', 'put'),
    'set': ('set', 'set'), 'let': ('let', 'let'), 'begin': ('began', 'begun'), 'break': ('broke', 'broken'),
    'choose': ('chose', 'chosen'), 'drive': ('drove', 'driven'), 'fly': ('flew', 'flown'),
    'forget': ('forgot', 'forgotten'), 'grow': ('grew', 'grown'), 'lie': ('lay', 'lain'), 'lose': ('lost', 'lost'),
    'rise': ('rose', 'risen'), 'shine': ('shone', 'shone'), 'show': ('showed', 'shown'), 'win': ('won', 'won'),
    'throw': ('threw', 'thrown'), 'wear': ('wore', 'worn'), 'understand': ('understood', 'understood'),
    'flee': ('fled', 'fled'), 'swim': ('swam', 'swum'), 'conquer': ('conquered', 'conquered'),
    'weep': ('wept', 'wept'), 'laugh': ('laughed', 'laughed'), 'flee': ('fled', 'fled'),
    'can': ('could', 'could'), 'live': ('lived', 'lived'), 'love': ('loved', 'loved'), 'kill': ('killed', 'killed'),
    'praise': ('praised', 'praised'), 'call': ('called', 'called'), 'carry': ('carried', 'carried'),
}
IRREGULAR_PLURAL = {'man': 'men', 'woman': 'women', 'child': 'children', 'foot': 'feet', 'tooth': 'teeth',
                    'mouse': 'mice', 'person': 'people', 'ox': 'oxen', 'sheep': 'sheep', 'fish': 'fish',
                    'deer': 'deer', 'god': 'gods', 'wife': 'wives', 'life': 'lives', 'wolf': 'wolves',
                    'leaf': 'leaves', 'knife': 'knives', 'half': 'halves', 'farmer': 'farmers'}
PRONOUNS = {(1, 'sg'): 'I', (2, 'sg'): 'you', (3, 'sg'): 'he', (1, 'pl'): 'we', (2, 'pl'): 'you',
            (3, 'pl'): 'they'}
OBJECT_PRONOUNS = {'I': 'me', 'he': 'him', 'she': 'her', 'we': 'us', 'they': 'them', 'who': 'whom'}
CONJUNCTIONS = {'et': 'and', 'atque': 'and', 'ac': 'and', 'que': 'and', '-que': 'and', 'aut': 'or', 'vel': 'or',
                'neque': 'nor', 'nec': 'nor', 'sed': 'but'}
CORRELATIVES = {'and': 'both', 'or': 'either', 'nor': 'neither'}   # et … et「…も…も」→ both … and
# ラテン語の代名詞 (見出し) → 英語: (単数, 複数)。指示代名詞は名詞に係れば限定詞 (haec puella「この少女」)
LATIN_PRONOUNS = {'ego': ('I', 'we'), 'tū': ('you', 'you'), 'sē': ('himself', 'themselves'),
                  'is': ('he', 'they'), 'hīc': ('this', 'these'), 'hic': ('this', 'these'),
                  'ille': ('that', 'those'), 'ipse': ('himself', 'themselves'), 'īdem': ('the same', 'the same'),
                  'quī': ('who', 'who'), 'quis': ('who', 'who')}
GENDERED = {('is', 'f'): ('she', 'they'), ('is', 'n'): ('it', 'they'), ('sē', 'f'): ('herself', 'themselves'),
            ('ipse', 'f'): ('herself', 'themselves'), ('ipse', 'n'): ('itself', 'themselves')}
# 所有形容詞 → 限定詞 (dominum suum「自分の主人」→ his own master)
POSSESSIVES = {'meus': 'my', 'tuus': 'your', 'noster': 'our', 'vester': 'your', 'suus': 'his own'}
# ラテン語の前置詞 (+ 格) → 英語。Wiktionary の訳語より、格で分けたほうが分かりやすいもの
LATIN_PREPS = {('in', 'Abl'): 'in', ('in', 'Acc'): 'into', ('ab', 'Abl'): 'from', ('ā', 'Abl'): 'from',
               ('ē', 'Abl'): 'out of', ('ex', 'Abl'): 'out of', ('dē', 'Abl'): 'about', ('cum', 'Abl'): 'with',
               ('sine', 'Abl'): 'without', ('prō', 'Abl'): 'for', ('sub', 'Abl'): 'under', ('sub', 'Acc'): 'under',
               ('ad', 'Acc'): 'to', ('per', 'Acc'): 'through', ('post', 'Acc'): 'after', ('ante', 'Acc'): 'before',
               ('apud', 'Acc'): 'among', ('inter', 'Acc'): 'among', ('trāns', 'Acc'): 'across',
               ('circum', 'Acc'): 'around', ('prope', 'Acc'): 'near', ('propter', 'Acc'): 'because of',
               ('contrā', 'Acc'): 'against', ('super', 'Acc'): 'over', ('ob', 'Acc'): 'because of'}
# 前置詞の無い格の役割 → 英語の前置詞
ROLE_PREPS = {'recipient': 'to', 'means': 'with', 'place': 'in', 'address': 'O'}


def _flat(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


@functools.lru_cache(maxsize=1)
def _table():
    """(見出し語, 品詞) → [英語]。マクロンを外した形でも引けるように"""
    table, flat = {}, {}
    path = paths.data('la-en.tsv')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for lemma, pos, en in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                glosses = [g for g in en.split(',') if g and not g.startswith('[')]
                if glosses:
                    table[(lemma, pos)] = glosses
                    flat.setdefault((_flat(lemma).lower(), pos), glosses)
    return table, flat


def candidates(lex):
    """語 → 英語の訳語の候補 (解析の日本語の訳語に合うものを先頭に)。無ければ []"""
    table, flat = _table()
    pos = {'participle': 'verb'}.get(lex.pos, lex.pos)
    found = table.get((lex.lemma, pos)) or flat.get((_flat(lex.lemma).lower(), pos))
    if found is None and pos in ('pronoun', 'adj'):
        found = table.get((lex.lemma, 'pronoun' if pos == 'adj' else 'adj'))
    synonyms = [m.group(1) for m in (SYNONYM.match(en) for en in found or []) if m]
    found = [en for en in found or [] if not DESCRIPTION.search(en)]
    for other in synonyms:   # cantō: synonym of canō → canō の訳語 (sing) も候補に
        found += table.get((other, pos)) or flat.get((_flat(other).lower(), pos)) or []
    found = list(dict.fromkeys(en for en in found if not DESCRIPTION.search(en)))
    if not found:
        return []
    best = _matching(tuple(found), lex.ja, pos)
    return [best] + [en for en in found if en != best]


def gloss(lex):
    """語 → 英語の訳語 (無ければ None)。候補のうち、英語 → 日本語の表で解析の日本語の訳語に合うものを選ぶ
    (ambulō: traverse, walk, … → 日本語が「歩く」なので walk)"""
    found = candidates(lex)
    return found[0] if found else None


SYNONYM = re.compile(r'^(?:synonym|alternative form|alternative spelling) of (\S+)$')
# 訳語でない説明 (synonym of canō, alternative form of epistola, masculine praenomen)
DESCRIPTION = re.compile(r'\b(synonym|alternative form|alternative spelling|form) of\b|praenomen|cognomen|nomen\b')


@functools.lru_cache(maxsize=20000)
def _matching(candidates, ja, pos):
    wanted = [j.strip() for j in (ja or '').split(',') if j.strip()]
    for j in wanted:   # 日本語の訳語の順 (よく使う訳語が先) に、それに合う英語を探す
        for en in candidates:
            if j in en_ja.lookup(en, pos):
                return en
    return candidates[0]


def word(lex):
    if lex.proper:
        return _flat(lex.lemma)   # 固有名詞は綴りのまま (Wiktionary の説明 Roman cognomen … は使わない)
    en = gloss(lex)
    if en is None and lex.en:
        en = lex.en.split(',')[0]   # 辞書の英語の訳語 (Wiktionary 由来の分詞: singing, dead)
    if en is None:
        if lex.proper:
            return lex.lemma
        return '[%s]' % lex.ja.split(',')[0]
    if lex.degree == '+':
        return comparative(en)
    if lex.degree == '++':
        return superlative(en)
    return en


def comparative(adj):
    if len(adj) <= 5 and ' ' not in adj:
        return (adj[:-1] if adj.endswith('e') else adj[:-1] + 'i' if re.search('[^aeiou]y$', adj) else adj) + 'er'
    return 'more ' + adj


def superlative(adj):
    if len(adj) <= 5 and ' ' not in adj:
        return (adj[:-1] if adj.endswith('e') else adj[:-1] + 'i' if re.search('[^aeiou]y$', adj) else adj) + 'est'
    return 'most ' + adj


# ----------------------------------------------------------------------
# 語形

def plural(noun):
    words = noun.split(' ')
    head = words[-1]
    if head in IRREGULAR_PLURAL:
        head = IRREGULAR_PLURAL[head]
    elif re.search('(s|x|z|ch|sh)$', head):
        head += 'es'
    elif re.search('[^aeiou]y$', head):
        head = head[:-1] + 'ies'
    else:
        head += 's'
    return ' '.join(words[:-1] + [head])


def _split_verb(verb):
    """'be fond of' → ('be', ' fond of')"""
    head, _, rest = verb.partition(' ')
    return head, (' ' + rest if rest else '')


def third_singular(verb):
    head, rest = _split_verb(verb)
    if head == 'be':
        return 'is' + rest
    if head == 'have':
        return 'has' + rest
    if re.search('(s|x|z|ch|sh|o)$', head):
        return head + 'es' + rest
    if re.search('[^aeiou]y$', head):
        return head[:-1] + 'ies' + rest
    return head + 's' + rest


def past(verb):
    head, rest = _split_verb(verb)
    if head in IRREGULAR:
        return IRREGULAR[head][0] + rest
    return _regular_ed(head) + rest


def past_participle(verb):
    head, rest = _split_verb(verb)
    if head in IRREGULAR:
        return IRREGULAR[head][1] + rest
    return _regular_ed(head) + rest


def present_participle(verb):
    head, rest = _split_verb(verb)
    if head.endswith('ie'):
        stem = head[:-2] + 'y'
    elif head.endswith('e') and head not in ('be', 'see', 'flee'):
        stem = head[:-1]
    elif re.search('[^aeiou][aeiou][bdgmnprt]$', head) and len(head) <= 4:
        stem = head + head[-1]
    else:
        stem = head
    return stem + 'ing' + rest


def _regular_ed(head):
    if head.endswith('e'):
        return head + 'd'
    if re.search('[^aeiou]y$', head):
        return head[:-1] + 'ied'
    if re.search('[^aeiou][aeiou][bdgmnprt]$', head) and len(head) <= 4:
        return head + head[-1] + 'ed'
    return head + 'ed'


def _be(tense, person, number):
    if tense == 'past':
        return 'was' if number == 'sg' and person != 2 else 'were'
    return {(1, 'sg'): 'am', (3, 'sg'): 'is'}.get((person, number), 'are')


def verb_phrase(verb, clause, subject_person, subject_number):
    """動詞の形 (助動詞を含む語の列)。否定は not を入れる"""
    tense, voice, mood = clause.tense, clause.voice, clause.mood
    sg3 = subject_person == 3 and subject_number == 'sg'
    neg = clause.negated
    if mood == 'imperative':
        return (['do not'] if neg else []) + [verb]
    if mood == 'infinitive':
        return (['not'] if neg else []) + ['to', verb if voice != 'passive' else 'be ' + past_participle(verb)]
    if voice == 'passive':
        main = past_participle(verb)
        if tense in ('perfect', 'imperfect'):
            aux = [_be('past', subject_person, subject_number)]
        elif tense == 'past-perfect':
            aux = ['had', 'been']
        elif tense == 'future':
            aux = ['will', 'be']
        elif tense == 'future-perfect':
            aux = ['will', 'have', 'been']
        else:
            aux = [_be('present', subject_person, subject_number)]
        if mood == 'subjunctive':
            aux = ['may', 'be'] if tense == 'present' else ['might', 'be']
        if neg:
            aux = aux[:1] + ['not'] + aux[1:]
        return aux + [main]
    if mood == 'subjunctive':
        aux = 'may' if tense in ('present', 'perfect') else 'might'
        return [aux] + (['not'] if neg else []) + ([verb] if tense in ('present', 'imperfect')
                                                   else ['have', past_participle(verb)])
    head, rest = _split_verb(verb)
    if head == 'be':
        form = _be('past' if tense in ('perfect', 'imperfect') else 'present', subject_person, subject_number)
        if tense == 'future':
            return ['will'] + (['not'] if neg else []) + ['be' + rest]
        return [form] + (['not'] if neg else []) + ([rest.strip()] if rest else [])
    if tense == 'imperfect':
        return [_be('past', subject_person, subject_number)] + (['not'] if neg else []) + \
            [present_participle(verb)]
    if tense == 'future':
        return ['will'] + (['not'] if neg else []) + [verb]
    if tense == 'past-perfect':
        return ['had'] + (['not'] if neg else []) + [past_participle(verb)]
    if tense == 'future-perfect':
        return ['will'] + (['not'] if neg else []) + ['have', past_participle(verb)]
    if tense == 'perfect':
        return ['did', 'not', verb] if neg else [past(verb)]
    if neg:
        return ['does' if sg3 else 'do', 'not', verb]
    return [third_singular(verb) if sg3 else verb]


# ----------------------------------------------------------------------
# 名詞句

def coordinate(parts, conj, correlative=False):
    text = ', '.join(parts[:-1]) + ' ' + conj + ' ' + parts[-1] if len(parts) > 1 else parts[0]
    if correlative or conj == 'nor':
        text = CORRELATIVES.get(conj, '') + ' ' + text
    return text


def pronoun(lex, number, gender, objective=False):
    forms = GENDERED.get((lex.lemma, gender)) or LATIN_PRONOUNS.get(lex.lemma) or \
        LATIN_PRONOUNS.get(_flat(lex.lemma))
    en = (forms[1] if number == 'pl' else forms[0]) if forms else word(lex)
    return OBJECT_PRONOUNS.get(en, en) if objective else en


def modifier(mod):
    if hasattr(mod, 'members'):   # 並列した形容詞 (good and brave)
        return coordinate([word(m.head) for m in mod.members], CONJUNCTIONS.get(mod.conj, 'and'), mod.correlative)
    return word(mod)


def noun_phrase(np, objective=False, passive=False):
    if np.members:
        parts = [noun_phrase(m, objective) for m in np.members]
        text = coordinate(parts, CONJUNCTIONS.get(np.conj, 'and'), np.correlative)
    else:
        head = np.head
        if head.pos == 'pronoun' and not np.modifiers:
            text = pronoun(head, np.number, np.gender, objective)
        else:
            en = word(head)
            noun = plural(en) if np.number == 'pl' and head.pos == 'noun' and gloss(head) else en
            if head.pos in ('adj', 'participle', 'pronoun') and not np.modifiers:
                noun = en + (' ones' if np.number == 'pl' else ' one')  # 形容詞の名詞的用法 (bonī「良い人たち」)
            determiner = 'the'
            adjectives = []
            for m in np.modifiers:
                if getattr(m, 'pos', '') == 'pronoun' and getattr(m, 'desc', '') == '指示代名詞':
                    determiner = pronoun(m, np.number, np.gender)   # this girl / that boy
                elif getattr(m, 'lemma', '') in POSSESSIVES:
                    determiner = POSSESSIVES[m.lemma]
                else:
                    adjectives.append(modifier(m))
            text = ' '.join(adjectives + [noun])
            if not head.proper:
                text = determiner + ' ' + text
        for gen in np.genitives:
            text += ' of ' + noun_phrase(gen, True)
        for p in np.participles:
            text += ' ' + participial(p)   # the enemy fleeing
    if np.prep is not None:
        prep = LATIN_PREPS.get((np.prep.lemma, np.case)) or gloss(np.prep) or '[%s]' % np.prep.ja
        if passive and np.prep.lemma in ('ā', 'ab', 'abs'):
            prep = 'by'   # 受動の動作主 (ā duce laudantur「指揮官によって褒められる」)
        text = prep + ' ' + text
    return text


def _subject_features(np, clause):
    if np is None:
        return clause.person, clause.number
    if np.members:
        return 3, 'pl'
    if np.head.pos == 'pronoun':
        return clause.person, clause.number
    return 3, np.number


def participial(p):
    """分詞句: 独立奪格は「主語 + 分詞」(the king dead, these things having been learned)、
    述語的な分詞は「分詞 + 補語」(plucking the flowers, having said these things)"""
    en = p.verb.en.split(',') if p.verb.en else []
    verb = word(frame_lex(p.verb.verb, 'verb', '')) if p.verb.verb else None
    if p.tense == 'present':
        form = en[0] if en else present_participle(verb) if verb and not verb.startswith('[') else word(p.verb)
    elif p.voice == 'active':   # 形式受動態動詞の完了分詞 (locūtus「話して」)
        having = [e for e in en if e.startswith('having ')]
        form = having[0] if having else 'having ' + past_participle(verb) if verb else word(p.verb)
    elif p.kind == 'absolute':
        form = en[0] if en else past_participle(verb) if verb else word(p.verb)
    else:
        form = past_participle(verb) if verb and not verb.startswith('[') else (en[0] if en else word(p.verb))
    words = []
    if p.subject is not None:
        words.append(noun_phrase(p.subject, objective=True))
    words.append(form)
    for role, np in p.args:
        if role == 'adverb':
            words.append(word(np.head))
        elif role == 'object':
            words.append(noun_phrase(np, objective=True))
        elif role == 'prep':
            words.append(noun_phrase(np, objective=True, passive=p.voice == 'passive'))
        else:
            words.append(('by ' if p.voice == 'passive' and role == 'means' else ROLE_PREPS.get(role, '') + ' ') +
                         noun_phrase(np, objective=True))
    if p.kind == 'absolute' and words[1:2] and words[1].startswith('having') is False and p.voice == 'passive' \
            and not en:
        words[1] = 'having been ' + words[1]
    return ' '.join(w.strip() for w in words if w.strip())


def frame_lex(lemma, pos, ja):
    from .frame import Lex
    return Lex(lemma, pos, ja)


def infinitive_phrase(inner, main_subject=None):
    """不定詞句: 言う・思う → that 節、見る・聞く → 目的語 + 原形、命じる → 目的語 + to 不定詞、補足 → to 不定詞"""
    kind = inner.infinitive_kind
    subjects = inner.role('subject')
    if kind == 'saying' and subjects:
        finite = _replace(inner, mood='indicative', infinitive_kind='')
        if subjects[0].head is not None and subjects[0].head.lemma in ('sē',):
            # 再帰代名詞は主節の主語を指す (Puella sē … dīcit「少女は自分が…と言う」→ she)
            ref = main_subject if main_subject is not None and not main_subject.members else subjects[0]
            finite.args = [('subject', _pronoun_np('is', ref))] + \
                [(r, np) for r, np in finite.args if np is not subjects[0]]
        return 'that ' + realize(finite, capitalize=False)
    rest = realize(_replace(inner, args=[(r, np) for r, np in inner.args if r != 'subject']), capitalize=False)
    subject = noun_phrase(subjects[0], objective=True) + ' ' if subjects and kind in ('perception', 'command') else ''
    if kind == 'perception':
        rest = rest[3:] if rest.startswith('to ') else rest   # I see the girl sing
    return subject + rest


def _replace(clause, **changes):
    import dataclasses
    return dataclasses.replace(clause, **changes)


def _pronoun_np(lemma, np):
    from .frame import NP, Lex
    return NP(Lex(lemma, 'pronoun'), number=np.number, gender=np.gender)


def realize(clause, capitalize=True):
    """Clause → 英語の文"""
    subjects = clause.role('subject')
    subject = subjects[0] if subjects else None
    person, number = _subject_features(subject, clause)
    verb = word(clause.verb) if not clause.copula else 'be'
    if clause.infinitives:
        verb = re.sub(' to$', '', verb)   # be able to + to read → be able to read
    out = []
    possessors = [np for np in clause.role('recipient') if clause.copula and not clause.role('complement')]
    if possessors and subject is not None:
        # 所有の与格 (Mihi est liber「私には本がある」) → I have a book
        owner = possessors[0]
        p_person, p_number = _subject_features(owner, clause)
        if owner.head is not None and owner.head.pos == 'pronoun':
            p_person = {'ego': 1, 'tū': 2}.get(owner.head.lemma, 3)
        have = _replace(clause, verb=frame_lex('habeō', 'verb', ''), copula=False,
                        args=[('subject', owner), ('object', subject)])
        text = noun_phrase(owner) + ' ' + ' '.join(verb_phrase('have', have, p_person, owner.number)) + ' ' + \
            noun_phrase(subject, objective=True).replace('the ', 'a ' if subject.number == 'sg' else '', 1)
        return text[:1].upper() + text[1:] if capitalize else text
    if clause.copula and subject is not None and len(clause.args) == 1 and not clause.infinitives \
            and clause.mood == 'indicative':
        # 補語も場所も無い繋辞は存在 (Vir magnus est「偉大な人がいる」→ There is a great man)
        there = _replace(clause, args=[])
        be = verb_phrase('be', there, 3, subject.number)
        text = 'there ' + ' '.join(be) + ' ' + \
            noun_phrase(subject).replace('the ', 'a ' if subject.number == 'sg' else '', 1)
        return text[:1].upper() + text[1:] if capitalize else text
    for p in clause.adjuncts:
        if p.kind == 'absolute':
            out.append(participial(p) + ',')
    if clause.mood not in ('imperative', 'infinitive'):
        out.append(noun_phrase(subject) if subject is not None else PRONOUNS.get((person, number), 'it'))
        for other in subjects[1:]:
            out[-1] += ', ' + noun_phrase(other) + ','   # 主語が2つ (並列でない): 同格として (this, the slave,)
    for p in clause.adjuncts:
        if p.kind != 'absolute':
            out.append(', ' + participial(p) + ',')
    out += verb_phrase(verb, clause, person, number)
    for np in clause.role('complement'):
        if not np.members and np.head.pos in ('adj', 'participle') and not np.modifiers:
            out.append(word(np.head))   # 補語の形容詞には冠詞を付けない (is happy)
        elif np.members and all(m.head is not None and m.head.pos in ('adj', 'participle') for m in np.members):
            out.append(modifier(np))     # is both long and broad
        else:
            out.append(noun_phrase(np).replace('the ', 'a ' if np.number == 'sg' else '', 1))
    for np in clause.role('object'):
        out.append(noun_phrase(np, objective=True))
    for inner in clause.infinitives:
        out.append(infinitive_phrase(inner, subject))
    for role, np in clause.args:
        if role in ('subject', 'object', 'complement'):
            continue
        if role == 'prep':
            out.append(noun_phrase(np, objective=True, passive=clause.voice == 'passive'))
        elif role == 'possessor':
            out.append('of ' + noun_phrase(np, objective=True))
        else:
            out.append(ROLE_PREPS.get(role, '') + ' ' + noun_phrase(np, objective=True))
    out += [word(adv) for adv in clause.adverbs]
    text = ' '.join(w.strip() for w in out if w.strip()).replace(' ,', ',').replace(',,', ',')
    if capitalize:
        text = text[:1].upper() + text[1:]
    return text


def sentence(clauses):
    """節の列 → 英語の文 (節は ; でつなぐ)"""
    if not clauses:
        return ''
    return '; '.join(realize(c, capitalize=(i == 0)) for i, c in enumerate(clauses)) + '.'
