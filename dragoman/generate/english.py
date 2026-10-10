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
from .frame import Lex

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
# 名詞的に使う形容詞・代名詞的な形容詞 (単数, 複数)
SUBSTANTIVES = {'omnis': ('everything', 'all'), 'multus': ('much', 'many'), 'alius': ('another', 'others'),
                'cēterus': ('the rest', 'the others'), 'paucus': ('few', 'few'), 'nūllus': ('none', 'none'),
                'tōtus': ('the whole', 'all')}
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
    """(見出し語, 品詞) → [[英語]] (同綴の語ごと)。マクロンを外した形でも引けるように"""
    table, flat = {}, {}
    path = paths.data('la-en.tsv')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            for row in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                lemma, pos, en = row[:3]
                glosses = Glosses(g for g in en.split(',') if g and not g.startswith('['))
                glosses.parts = row[3].split() if len(row) > 3 else []
                if glosses:
                    table.setdefault((lemma, pos), []).append(glosses)
                    flat.setdefault((_flat(lemma).lower(), pos), table[(lemma, pos)])   # 同じリスト (後の同綴の語も入る)
    return table, flat


def _entries(lemma, pos):
    table, flat = _table()
    return table.get((lemma, pos)) or flat.get((_flat(lemma).lower(), pos)) or []


class Glosses(list):
    """英語の訳語のリスト。parts に動詞の基本形 (volāre volāvī volātum)"""
    parts = ()


def _homograph(entries, ja, pos, surface=''):
    """同綴の語のうち、解析の日本語の訳語に合う英語の訳語を持つもの (volō「飛ぶ」→ fly の項目)。
    日本語で決まらなければ、文中の形が基本形の語幹と長く一致するもの (appellābātur → appellāre の項目)"""
    if len(entries) <= 1:
        return entries[0] if entries else []
    wanted = [j.strip() for j in (ja or '').split(',') if j.strip()]
    for j in wanted:
        for glosses in entries:
            if any(j == x or j in x for en in glosses for x in en_ja.lookup(en, pos)):
                return glosses
    if surface:
        return max(entries, key=lambda glosses: _stem_match(glosses.parts, surface))
    return entries[0]


def _stem_match(parts, surface):
    """基本形の語幹 (volāre → volā、volāvī → volāv、volātum → volāt) と文中の形の一致の長さ"""
    surface = surface.lower()
    stems = []
    for part in parts:
        for ending in ('āre', 'ēre', 'ere', 'īre', 'ī', 'um', 'us', 'se'):
            if part.endswith(ending):
                stems.append(part[:-len(ending)] + ('ā' if ending == 'āre' else 'ē' if ending == 'ēre' else
                                                    'ī' if ending == 'īre' else ''))
                break
    return max((len(stem) for stem in stems if stem and surface.startswith(stem)), default=0)


def substantive(lex):
    """名詞的に使った形容詞が、その形で名詞として辞書にあれば名詞の Lex (tālāria ← tālāris)"""
    if lex.pos != 'adj' or not lex.surface:
        return None
    noun = Lex(lex.surface.lower(), 'noun', lex.ja, surface=lex.surface)
    return noun if _entries(noun.lemma, 'noun') else None


# 品詞が辞書と違うときに引く品詞 (trēs: 解析では形容詞、辞書では数詞。modo: 接続詞 / 副詞)
POS_FALLBACK = {'adj': ('num', 'pronoun'), 'pronoun': ('adj',), 'conj': ('adv',), 'adv': ('conj',), 'num': ('adj',)}
# 最上級の形 → 原級 (Wiktionary 由来の項目は最上級の形が見出し: difficillimus → difficilis)
SUPERLATIVES = (('illimus', 'ilis'), ('errimus', 'er'), ('issimus', 'us'), ('issimus', 'is'),
                ('illimē', 'ilis'), ('errimē', 'er'), ('issimē', 'us'), ('issimē', 'is'))
DEGREE_OF = re.compile(r'^(comparative|superlative) degree of (\S+)$', re.I)


def verb_bases(english):
    """分詞の英語の訳語から動詞の原形の候補: 'which is to be approached' → approach、'having risen' → rise、
    'followed' → follow"""
    out = []
    for en in english.split(','):
        en = re.sub(r'^(which is to be|which is to|to be|having been|having|being)\s+', '', en.strip())
        head, _, rest = en.partition(' ')
        rest = (' ' + rest) if rest else ''
        bases = [base for base, (past_form, pp) in IRREGULAR.items() if head in (past_form, pp)]
        if head.endswith('ing'):
            bases += [head[:-3], head[:-3] + 'e']
        elif head.endswith('ied'):
            bases.append(head[:-3] + 'y')
        elif head.endswith('ed'):
            bases += [head[:-2], head[:-1], head[:-3]]   # approached → approach / approache / approac (doubled: stopped → stop)
        bases.append(head)
        out += [b + rest for b in bases if b]
    return list(dict.fromkeys(out))


def candidates(lex):
    """語 → 英語の訳語の候補 (解析の日本語の訳語に合うものを先頭に)。無ければ []"""
    pos = {'participle': 'verb'}.get(lex.pos, lex.pos)
    if lex.lang and lex.lang != 'la':
        # ロシア語・サンスクリットの語: その言語の英語の訳語の表と、辞書の英語の訳語 (ja_en)
        from . import transfer
        found = transfer.english_glosses(lex.lang, lex.lemma, pos) + \
            [g.strip() for g in (lex.en or '').split(',') if g.strip()]
        # 辞書の英語の訳語の並びのまま。ただし一番の日本語の訳語に合う英語があれば先頭に (pustaka「本」→ book)
        # (二番目以降の日本語の訳語では並べ替えない: видеть「見える,会う」を meet にしないように)
        found = list(dict.fromkeys(g for g in found if not DESCRIPTION.search(g)))
        if lex.lemma in transfer.FIRST_GLOSSES.get(lex.lang, {}):
            return found   # 先に使う訳語の決まっている語 (βασιλεύς: 日本語の訳語「長」より king)
        first = (lex.ja or '').split(',')[0].strip()
        match = next((g for g in found if first and first in en_ja.lookup(g, pos)), None) if lex.ja and \
            not lex.ja.isascii() else None
        return ([match] + [g for g in found if g != match]) if match else found
    entries = _entries(lex.lemma, pos)
    for other in POS_FALLBACK.get(pos, ()):
        entries = entries or _entries(lex.lemma, other)
    if not entries:
        positive = _positive(lex)
        if positive is not None:   # 最上級の見出し → 原級の訳語を最上級に (difficillimus → most difficult)
            return [superlative(en) if pos != 'adv' else 'most ' + _adverb(en) for en in candidates(positive)]
    found = list(_homograph(entries, lex.ja, pos, lex.surface))
    synonyms = [m.group(1) for m in (SYNONYM.match(en) for en in found) if m]
    degrees = [m.groups() for m in (DEGREE_OF.match(en) for en in found) if m]
    found = [DEGREE.sub('', en) for en in found]   # Superlative degree of magnus: greatest → greatest
    found = [en for en in found if not DESCRIPTION.search(en)]
    for other in synonyms:   # cantō: synonym of canō → canō の訳語 (sing) も候補に
        found += _homograph(_entries(other, pos), lex.ja, pos, lex.surface)
    for degree, other in degrees:   # superior: comparative degree of superus → superus の訳語の比較級
        inflect = comparative if degree.lower() == 'comparative' else superlative
        base = [en for en in _homograph(_entries(other, pos), lex.ja, pos, lex.surface) if not DESCRIPTION.search(en)]
        ready = [en for en in base if en.endswith('er' if inflect is comparative else 'est') and ' ' not in en]
        found += ready or [inflect(en) for en in base]   # 原級の訳語に比較級があればそれを (superus: upper)
    found = list(dict.fromkeys(en for en in found if not DESCRIPTION.search(en)))
    if not found:
        return []
    best = _matching(tuple(found), lex.ja, pos)
    return [best] + [en for en in found if en != best]


def _positive(lex):
    for ending, base in SUPERLATIVES:
        if lex.lemma.endswith(ending):
            stem = lex.lemma[:-len(ending)] + base
            if _entries(stem, 'adj'):
                return Lex(stem, 'adj', '')
    return None


IRREGULAR_ADVERBS = {'fast': 'fast', 'good': 'well', 'hard': 'hard', 'early': 'early', 'late': 'late'}


def _adverb(adjective):
    """形容詞 → 副詞 (quick → quickly)"""
    if adjective in IRREGULAR_ADVERBS:
        return IRREGULAR_ADVERBS[adjective]
    if adjective.endswith('ly') or ' ' in adjective:
        return adjective
    if adjective.endswith('y'):
        return adjective[:-1] + 'ily'
    if adjective.endswith('le'):
        return adjective[:-1] + 'y'
    return adjective + 'ly'


def gloss(lex):
    """語 → 英語の訳語 (無ければ None)。候補のうち、英語 → 日本語の表で解析の日本語の訳語に合うものを選ぶ
    (ambulō: traverse, walk, … → 日本語が「歩く」なので walk)"""
    found = candidates(lex)
    return found[0] if found else None


DEGREE = re.compile(r'^.*\b(?:comparative|superlative) degree of \S+: ', re.I)
SYNONYM = re.compile(r'^(?:synonym|alternative form|alternative spelling) of (\S+)$')
# 訳語でない説明 (synonym of canō, alternative form of epistola, masculine praenomen)
DESCRIPTION = re.compile(r'\b(synonym|alternative form|alternative spelling|form) of\b|praenomen|cognomen|nomen\b|'
                         r'^of or pertaining to\b|degree of\b', re.I)


@functools.lru_cache(maxsize=20000)
def _matching(candidates, ja, pos):
    wanted = [j.strip() for j in (ja or '').split(',') if j.strip()]
    for j in wanted:   # 日本語の訳語の順 (よく使う訳語が先) に、それに合う英語を探す
        for en in candidates:
            if j in en_ja.lookup(en, pos):
                return en
    return candidates[0]


NUMERALS = {'ūnus': 'one', 'duo': 'two', 'trēs': 'three', 'quattuor': 'four', 'quīnque': 'five', 'sex': 'six',
            'septem': 'seven', 'octō': 'eight', 'novem': 'nine', 'decem': 'ten', 'ūndecim': 'eleven',
            'duodecim': 'twelve', 'vīgintī': 'twenty', 'centum': 'a hundred', 'mīlle': 'a thousand'}


def word(lex):
    if lex.lemma in NUMERALS:
        return NUMERALS[lex.lemma]
    if lex.proper:
        return _flat(lex.lemma)   # 固有名詞は綴りのまま (Wiktionary の説明 Roman cognomen … は使わない)
    en = gloss(lex)
    if en is None and lex.en:
        en = lex.en.split(',')[0]   # 辞書の英語の訳語 (Wiktionary 由来の分詞: singing, dead)
    if en is None:
        if lex.proper:
            return lex.lemma
        return '[%s]' % lex.ja.split(',')[0]
    if ' or ' in en and lex.pos in ('verb', 'participle'):
        en = en.split(' or ')[0]   # drive or move to → drive
    if _positive(lex) is not None and not lex.degree:
        return en   # 最上級の見出し (difficillimus) は candidates で最上級にしてある
    already = en.startswith(('more ', 'most ')) or en.endswith(('er', 'est')) and lex.lemma[-2:] != en[-2:]
    if lex.degree == '+' and not already:
        return comparative(en)
    if lex.degree == '++' and not (en.startswith('most ') or en.endswith('est')):
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
        if head.pos == 'pronoun' and not np.modifiers and np.relatives and head.lemma in CORRELATIVE_HEADS:
            # 関係節の付いた指示代名詞: 人なら he who … / those who …、物なら what … (ea quae dīxistī → what you said)
            relative = np.relatives[0]
            if not np.animate:
                return ((np.prep and (LATIN_PREPS.get((np.prep.lemma, np.case)) or np.prep.lemma) + ' ') or '') + \
                    'what ' + realize(_replace(relative, mood='indicative'), capitalize=False)
            text = pronoun(Lex('is', 'pronoun'), np.number, np.gender, objective) if np.number == 'sg' else \
                ('them' if objective else 'those')
        elif head.pos == 'pronoun' and not np.modifiers:
            # 単独の ille (「彼」の意味で語りに多い) は人称代名詞に
            lemma = 'is' if head.lemma == 'ille' else head.lemma
            text = pronoun(Lex(lemma, 'pronoun', head.ja, desc=head.desc), np.number, np.gender, objective)
        else:
            en = word(head)
            noun = plural(en) if np.number == 'pl' and head.pos == 'noun' and gloss(head) else en
            noun_lex = substantive(head)
            if head.lemma in SUBSTANTIVES and not np.modifiers:
                noun = SUBSTANTIVES[head.lemma][1 if np.number == 'pl' else 0]   # omnium「すべての人の」→ of all
            elif noun_lex is not None:
                noun = gloss(noun_lex)   # 名詞として辞書にある形 (tālāria「翼のあるサンダル」← tālāris)
            elif head.pos in ('adj', 'participle', 'pronoun') and not np.modifiers:
                noun = en + (' ones' if np.number == 'pl' else ' one')  # 形容詞の名詞的用法 (bonī「良い人たち」)
            determiner = 'the'
            adjectives = []
            for m in np.modifiers:
                if getattr(m, 'pos', '') == 'pronoun' and getattr(m, 'desc', '') == '指示代名詞':
                    determiner = pronoun(m, np.number, np.gender)   # this girl / that boy
                    if m.lemma == 'is':
                        determiner = 'those' if np.number == 'pl' else 'that'   # eum locum「その場所」
                elif getattr(m, 'lemma', '') in POSSESSIVES:
                    determiner = POSSESSIVES[m.lemma]
                else:
                    adjectives.append(modifier(m))
            text = ' '.join(adjectives + [noun])
            if not head.proper and not (head.lemma in SUBSTANTIVES and not np.modifiers):
                text = determiner + ' ' + text
        for gen in np.genitives:
            text += ' of ' + noun_phrase(gen, True)
        for p in np.participles:
            text += ' ' + participial(p)   # the enemy fleeing
        for r in np.relatives:
            text += ' ' + relative_clause(r, np)
    if np.prep is not None:
        prep = LATIN_PREPS.get((np.prep.lemma, np.case)) or gloss(np.prep) or '[%s]' % np.prep.ja
        if passive and np.prep.lemma in ('ā', 'ab', 'abs'):
            prep = 'by'   # 受動の動作主 (ā duce laudantur「指揮官によって褒められる」)
        text = prep + ' ' + text
    return text


def _subject_features(np, clause):
    if np is None:
        return clause.person, clause.number
    if np.relatives and not np.animate and np.head is not None and np.head.lemma in CORRELATIVE_HEADS:
        return 3, 'sg'   # what you said is true
    if np.members:
        return 3, 'pl'
    if np.head.pos == 'pronoun':
        return clause.person, clause.number
    return 3, np.number


def adverb(lex):
    from . import connectives
    entry = connectives.lookup(lex.surface or lex.lemma) or connectives.lookup(lex.lemma)
    return entry[1] if entry else word(lex)


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


def relative_clause(r, np):
    """関係節: who / whom / which (人・動物かどうか)、where (ubi)、前置詞 + which (in which)、whose"""
    person = np.animate
    if r.gap == 'place':
        word = 'where'
    elif r.gap == 'prep':
        prep, case = r.gap_prep
        word = (LATIN_PREPS.get((prep.lemma, case)) or gloss(prep) or prep.lemma) + ' ' + ('whom' if person else 'which')
    elif r.gap == 'subject':
        word = 'who' if person else 'which'
    elif r.gap == 'possessor':
        word = 'whose'
    elif r.gap == 'recipient':
        word = 'to whom' if person else 'to which'
    elif r.gap == 'means':
        word = 'by whom' if person else 'with which'
    else:
        word = 'whom' if person else 'which'
    finite = _replace(r, mood='indicative') if r.mood == 'subjunctive' else r
    return word + ' ' + realize(finite, capitalize=False)


CORRELATIVE_HEADS = {'is', 'ille', 'hic', 'hīc', 'iste', 'īdem'}
WHO = {'quis', 'quem', 'cui', 'cūius', 'cuius', 'quibus'}   # 人を問う形 (ほかの quae, quid, quod … は what)


def question_phrase(inner):
    """間接疑問: 疑問詞を頭に、動詞は直説法で (asked why the boy was weeping、showed what he wanted to happen)。
    疑問代名詞が節の主語なら主語の位置のまま (who had come)"""
    from .frame import interrogative_np, without_interrogative, NP
    from . import connectives
    from .frame import question_idiom
    finite = _replace(inner, mood='indicative', question_word='')
    idiom, stripped = question_idiom(inner)
    stripped = _replace(stripped, mood='indicative', question_word='')
    if idiom:   # quō in locō → where、quam ob causam → why
        return idiom + ' ' + realize(stripped, capitalize=False)
    owner, role, wh = interrogative_np(inner)
    if wh is None:
        entry = connectives.interrogative(inner.question_word)
        return (entry[0] if entry else inner.question_word) + ' ' + realize(finite, capitalize=False)
    word = 'who' if inner.question_word in WHO else 'what'   # quae causa esset → what
    if owner is inner and role == 'subject':
        return realize(without_interrogative(finite, NP(Lex(word, 'noun', proper=True))), capitalize=False)
    return word + ' ' + realize(without_interrogative(finite), capitalize=False)


def realize(clause, capitalize=True):
    from .frame import periphrastic, lexical_negation
    clause = lexical_negation(periphrastic(clause))   # prōgressus est → 完了の能動 (advanced / продвинулся)
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
    if clause.mood not in ('imperative', 'infinitive') and not (subject is None and clause.gap == 'subject'):
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
    for inner in clause.questions:
        out.append(question_phrase(inner))
    for role, np in clause.args:
        if role in ('subject', 'object', 'complement'):
            continue
        if role == 'prep':
            out.append(noun_phrase(np, objective=True, passive=clause.voice == 'passive'))
        elif role == 'possessor':
            out.append('of ' + noun_phrase(np, objective=True))
        elif role == 'recipient' and verb.split(' ')[-1] in ('into', 'to', 'at', 'on', 'with', 'upon'):
            out.append(noun_phrase(np, objective=True))   # run into + 与格: 前置詞を重ねない
        else:
            out.append(ROLE_PREPS.get(role, '') + ' ' + noun_phrase(np, objective=True))
    out += [adverb(adv) for adv in clause.adverbs]
    text = ' '.join(w.strip() for w in out if w.strip()).replace(' ,', ',').replace(',,', ',')
    if capitalize:
        text = text[:1].upper() + text[1:]
    return text


def sentence(clauses):
    """節の列 → 英語の文 (節は ; でつなぐ)"""
    if not clauses:
        return ''
    from . import connectives
    text = connectives.join(clauses, [realize(c, capitalize=False) for c in clauses], 'en')
    return text[:1].upper() + text[1:] + '.'
