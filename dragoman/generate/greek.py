#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) から古典ギリシア語 (アッティカ方言) の文を作る
#
#   語形はラテン語と同じく、解析に使う辞書 (grc/wiktionary.sqlite) を逆に引いて作る
#   冠詞: 普通名詞に ὁ ἡ τό を付ける (元がギリシア語なら元の冠詞の有無、ほかの言語からは付ける)
#   時制: ラテン語の完了 → アオリスト (語りの過去)、過去完了 → 過去完了、未来 → 未来。受動・中動 (Clause.middle)
#   格: 主語 主格、目的語 対格、受け手 与格、手段 与格 (道具の与格)、所有者 属格。前置詞は表で (in + 奪格 → ἐν + 与格 …)
#   語順: 主語 - 受け手 - 目的語 - そのほか - 副詞 - (οὐ) - 動詞。形容詞は冠詞と名詞の間 (ἡ καλὴ κόρη)
#   節: 関係代名詞 ὅς ἥ ὅ (先行詞の性・数、空所の格)、不定詞句は対格 + 不定詞、独立奪格は属格独立
#
import functools
import json
import os
import unicodedata

from dragoman.core import paths
from . import transfer, english
from .frame import Lex, NP

DB_PATH = paths.data('grc', 'wiktionary.sqlite')

ARTICLE = {('Nom', 'sg', 'm'): 'ὁ', ('Gen', 'sg', 'm'): 'τοῦ', ('Dat', 'sg', 'm'): 'τῷ', ('Acc', 'sg', 'm'): 'τὸν',
           ('Nom', 'sg', 'f'): 'ἡ', ('Gen', 'sg', 'f'): 'τῆς', ('Dat', 'sg', 'f'): 'τῇ', ('Acc', 'sg', 'f'): 'τὴν',
           ('Nom', 'sg', 'n'): 'τὸ', ('Gen', 'sg', 'n'): 'τοῦ', ('Dat', 'sg', 'n'): 'τῷ', ('Acc', 'sg', 'n'): 'τὸ',
           ('Nom', 'pl', 'm'): 'οἱ', ('Gen', 'pl', 'm'): 'τῶν', ('Dat', 'pl', 'm'): 'τοῖς', ('Acc', 'pl', 'm'): 'τοὺς',
           ('Nom', 'pl', 'f'): 'αἱ', ('Gen', 'pl', 'f'): 'τῶν', ('Dat', 'pl', 'f'): 'ταῖς', ('Acc', 'pl', 'f'): 'τὰς',
           ('Nom', 'pl', 'n'): 'τὰ', ('Gen', 'pl', 'n'): 'τῶν', ('Dat', 'pl', 'n'): 'τοῖς', ('Acc', 'pl', 'n'): 'τὰ'}
ROLE_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Dat', 'possessor': 'Gen',
              'complement': 'Nom', 'place': 'Dat', 'source': 'Gen'}
# ラテン語の前置詞 + 格 → (ギリシア語の前置詞, 格)
PREPOSITIONS = {('in', 'Abl'): ('ἐν', 'Dat'), ('in', 'Acc'): ('εἰς', 'Acc'), ('ad', 'Acc'): ('πρός', 'Acc'),
                ('ex', 'Abl'): ('ἐκ', 'Gen'), ('ē', 'Abl'): ('ἐκ', 'Gen'), ('ab', 'Abl'): ('ἀπό', 'Gen'),
                ('ā', 'Abl'): ('ἀπό', 'Gen'), ('cum', 'Abl'): ('μετά', 'Gen'), ('dē', 'Abl'): ('περί', 'Gen'),
                ('sine', 'Abl'): ('ἄνευ', 'Gen'), ('per', 'Acc'): ('διά', 'Gen'), ('post', 'Acc'): ('μετά', 'Acc'),
                ('ante', 'Acc'): ('πρό', 'Gen'), ('sub', 'Abl'): ('ὑπό', 'Dat'), ('super', 'Acc'): ('ὑπέρ', 'Gen'),
                ('prō', 'Abl'): ('ὑπέρ', 'Gen'), ('apud', 'Acc'): ('παρά', 'Dat'), ('propter', 'Acc'): ('διά', 'Acc'),
                ('ob', 'Acc'): ('διά', 'Acc'), ('contrā', 'Acc'): ('κατά', 'Gen'), ('inter', 'Acc'): ('μεταξύ', 'Gen'),
                ('trāns', 'Acc'): ('πέραν', 'Gen'), ('circum', 'Acc'): ('περί', 'Acc'), ('prope', 'Acc'): ('ἐγγύς', 'Gen')}
PRONOUNS = {'ego': 'ἐγώ', 'tū': 'σύ', 'is': 'αὐτός', 'hic': 'οὗτος', 'hīc': 'οὗτος', 'ille': 'ἐκεῖνος',
            'quī': 'ὅς', 'quis': 'τίς', 'quid': 'τίς', 'sē': 'ἑαυτοῦ', 'meus': 'ἐμός', 'tuus': 'σός',
            'suus': 'ἑαυτοῦ', 'omnis': 'πᾶς', 'ipse': 'αὐτός'}
PERSONAL_PLURALS = {'ἐγώ': 'ἡμεῖς', 'σύ': 'ὑμεῖς'}
TENSES = {'present': 'present', 'imperfect': 'imperfect', 'perfect': 'aorist', 'past-perfect': 'pluperfect',
          'future': 'future', 'future-perfect': 'future'}
CONNECTIVES = {'et': ('καί', 'front'), 'que': ('τε', 'post'), 'autem': ('δέ', 'post'), 'enim': ('γάρ', 'post'),
               'igitur': ('οὖν', 'post'), 'itaque': ('οὖν', 'post'), 'sed': ('ἀλλά', 'front'),
               'at': ('ἀλλά', 'front'), 'tamen': ('ὅμως', 'front'), 'nam': ('γάρ', 'post'), 'neque': ('οὐδέ', 'front'),
               'ubi': ('ὅτε', 'front'), 'cum': ('ὅτε', 'front'), 'postquam': ('ἐπεί', 'front'), 'dum': ('ἕως', 'front'),
               'quod': ('ὅτι', 'front'), 'quia': ('ὅτι', 'front'), 'sī': ('εἰ', 'front'), 'ut': ('ἵνα', 'front'),
               'nē': ('ἵνα μή', 'front'), 'quamquam': ('καίτοι', 'front'), 'tum': ('τότε', 'front')}
GENDERS = {'m', 'f', 'n'}


def available():
    return os.path.exists(DB_PATH) and transfer.available('grc')


@functools.lru_cache(maxsize=1)
def _db():
    import sqlite3
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@functools.lru_cache(maxsize=4000)
def _forms(lemma, pos):
    key = '$.pres1sg' if pos == 'verb' else '$.base'
    rows = _db().execute('SELECT f.surface, l.info, f.features FROM lemmas l JOIN forms f ON f.lemma_id = l.id '
                         'WHERE json_extract(l.info, ?) = ?', (key, lemma)).fetchall()
    out = []
    for surface, info, features in rows:
        item = dict(json.loads(info), **json.loads(features))
        if item.get('pos') == pos or (pos == 'pronoun' and item.get('pos') in ('pronoun', 'adj')):
            out.append((surface, item))
    return out


def to_greek(lex, pos=None):
    """語 → ギリシア語の語 (Lex, 性)。元がギリシア語ならそのまま"""
    pos = pos or {'participle': 'verb', 'name': 'noun'}.get(lex.pos, lex.pos)
    if lex.pos == 'pronoun' and lex.lemma in PRONOUNS:
        return Lex(PRONOUNS[lex.lemma], 'pronoun'), ''
    if lex.lang == 'grc' or lex.proper:
        return Lex(lex.lemma, pos, lex.ja, proper=lex.proper), ''
    target = transfer.best(lex, 'grc', pos)
    if target is None:
        return None, ''
    return Lex(target.lemma, pos), target.gender


def _gender(lex, gender):
    if gender in GENDERS:
        return gender
    for _, item in _forms(lex.lemma, lex.pos):
        for tag in item.get('_') or []:
            if len(tag) > 2 and tag[2] in GENDERS:
                return tag[2]
    return 'm'


DIPHTHONGS = {'αι', 'ει', 'οι', 'υι', 'αυ', 'ευ', 'ηυ', 'ου', 'ωυ'}


def _hiatus(surface):
    """母音が続く (縮約していない) 形なら 1。方言の印が無いので、ἐπαινέει (イオニア方言) より ἐπαινεῖ を先に"""
    d = unicodedata.normalize('NFD', surface.lower())
    if '\u0308' in d:
        return 0   # 分音符はもともと母音の連続
    base = ''.join(c for c in d if not unicodedata.combining(c))
    return int(any(a in VOWELS and b in VOWELS and a + b not in DIPHTHONGS for a, b in zip(base, base[1:])))


def decline(lex, case, number, gender):
    """名詞・形容詞・代名詞の語形 (縮約形を先に)。作れなければ見出しに *"""
    best = None
    for surface, item in _forms(lex.lemma, lex.pos):
        for tag in item.get('_') or []:
            c, n, g = (list(tag) + [None, None, None])[:3]
            if c == case and n == number:
                score = (0 if g in (gender, None) else 1, _hiatus(surface))
                if best is None or score < best[0]:
                    best = (score, surface)
    if best is None:
        return lex.lemma if lex.proper else '*' + lex.lemma
    return best[1]


def conjugate(lex, person, number, tense, mood, voice):
    tense = TENSES.get(tense, tense)
    candidates = []
    for surface, item in _forms(lex.lemma, 'verb'):
        if item.get('person') == person and item.get('number') == number and item.get('tense') == tense and \
                (item.get('mood') or 'indicative') == mood:
            v = item.get('voice') or 'active'
            score = 0 if v == voice else 1 if voice in v or v in voice else 2 if voice == 'active' else 9   # 形式所相
            if score < 9:
                candidates.append((score, _hiatus(surface), len(candidates), surface))
    if not candidates and tense == 'aorist':
        return conjugate(lex, person, number, 'imperfect', mood, voice)   # アオリストの形が辞書に無い動詞
    return min(candidates)[-1] if candidates else '*' + lex.lemma


def infinitive(lex, tense, voice):
    tense = {'perfect': 'aorist'}.get(tense, 'present')
    for surface, item in _forms(lex.lemma, 'verb'):
        if item.get('mood') == 'infinitive' and item.get('tense') == tense and \
                (item.get('voice') or 'active') in (voice, 'middle-passive' if voice == 'passive' else voice):
            return surface
    return '*' + lex.lemma


def _voice(clause):
    if clause.middle:
        return clause.middle
    if clause.voice == 'passive':
        return 'passive' if TENSES.get(clause.tense) in ('aorist', 'future') else 'middle-passive'
    return 'active'


# ----------------------------------------------------------------------
# 名詞句

def noun_phrase(np, case):
    if np.members:
        parts = [noun_phrase(m, case) for m in np.members]
        conj = 'καί' if np.conj in ('et', 'que', 'atque', 'ac') else 'ἤ' if np.conj in ('aut', 'vel') else 'καί'
        return (' %s ' % conj).join(parts)
    head = np.head
    lex, gender = to_greek(head)
    if lex is None:
        return '[%s]' % english.word(head)
    gender = np.gender if (head.lang == 'grc' and np.gender in GENDERS) else _gender(lex, gender)
    number = np.number
    if lex.pos == 'pronoun' and number == 'pl' and lex.lemma in PERSONAL_PLURALS:
        lex = Lex(PERSONAL_PLURALS[lex.lemma], 'pronoun')
    word = decline(lex, case, number, gender)
    adjectives = []
    demonstrative = None
    for m in np.modifiers:
        if isinstance(m, NP):
            adjectives.append(' καὶ '.join(_adjective(x.head, case, number, gender) for x in m.members))
        elif m.pos == 'pronoun' and m.lemma in ('hic', 'hīc', 'ille', 'is'):
            demonstrative = decline(Lex(PRONOUNS[m.lemma], 'pronoun'), case, number, gender)
        else:
            adjectives.append(_adjective(m, case, number, gender))
    genitives = [noun_phrase(g, 'Gen') for g in np.genitives]
    article = ''
    if lex.pos == 'noun' and not lex.proper and np.definite is not False:
        article = ARTICLE.get((case, number, gender), '')   # 指示代名詞があっても冠詞は付ける (οὗτος ὁ ἀνήρ)
    words = ([demonstrative] if demonstrative else []) + [w for w in [article] if w] + adjectives + [word] + genitives
    for r in np.relatives:
        words.append(relative_clause(r, number, gender))
    return ' '.join(words)


def _adjective(lex, case, number, gender):
    if lex.pos == 'pronoun' and lex.lemma in PRONOUNS:
        return decline(Lex(PRONOUNS[lex.lemma], 'pronoun'), case, number, gender)
    found, _ = to_greek(lex, 'adj')
    if found is None:
        return '[%s]' % english.word(lex)
    return decline(Lex(found.lemma, 'adj'), case, number, gender)


def prepositional(np, passive=False):
    prep, case = PREPOSITIONS.get((np.prep.lemma, np.case), ('ἐν', 'Dat'))
    if np.prep.lang == 'grc' and np.prep.surface and getattr(np, 'source_case', None):
        prep, case = np.prep.surface, np.source_case   # 元がギリシア語なら元の前置詞
    if passive and np.prep.lemma in ('ā', 'ab'):
        prep, case = 'ὑπό', 'Gen'   # 受動の動作主
    import dataclasses
    inner = noun_phrase(dataclasses.replace(np, prep=None), case)
    if prep == 'ἐκ' and inner[:1] in 'αεηιουωἀἐἠἰὀὑὠἁἑἡἱὁὑὡ':
        prep = 'ἐξ'
    return prep + ' ' + inner


GAP_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Dat', 'possessor': 'Gen'}


def relative_clause(r, number, gender):
    """関係節: ὅς ἥ ὅ を先行詞の性・数と空所の格で、前置詞の空所は前置詞 + ὅς"""
    if r.gap == 'place':
        word = 'ὅπου'
    else:
        if r.gap == 'prep':
            prep, case = PREPOSITIONS.get((r.gap_prep[0].lemma, r.gap_prep[1]), ('ἐν', 'Dat'))
        else:
            prep, case = None, GAP_CASES.get(r.gap, 'Nom')
        word = decline(Lex('ὅς', 'pronoun'), case, number, gender)
        if prep:
            word = prep + ' ' + word
    return word + ' ' + realize(r, capitalize=False)


# ----------------------------------------------------------------------
# 節

def _negation(next_word):
    plain = unicodedata.normalize('NFD', next_word or '')
    if plain[:1] and plain[:1] in 'αεηιουω':
        return 'οὐχ' if '̔' in plain[:3] else 'οὐκ'   # 有気 (οὐχ ὁρᾷ) / 無気 (οὐκ ἔστι)
    return 'οὐ'


def realize(clause, capitalize=False):
    subjects = clause.role('subject')
    subject = subjects[0] if subjects else None
    person, number = clause.person, clause.number
    if subject is not None and subject.head is not None and subject.head.pos != 'pronoun':
        person, number = 3, 'pl' if subject.members else subject.number
    out = []
    for p in clause.adjuncts:
        if p.kind == 'absolute' and p.subject is not None:
            out.append(_absolute(p))
    subject_case = 'Acc' if clause.mood == 'infinitive' else 'Nom'
    for np in subjects:
        personal = np.head is not None and np.head.pos == 'pronoun' and np.head.lemma in ('ego', 'tū')
        if not personal or clause.mood == 'infinitive':
            out.append(noun_phrase(np, subject_case))
    for role in ('recipient', 'object'):
        for np in clause.role(role):
            out.append(noun_phrase(np, ROLE_CASES[role]))
    for inner in clause.infinitives:
        out.append(realize(inner))
    for role, np in clause.args:
        if role in ('subject', 'object', 'recipient', 'complement'):
            continue
        out.append(prepositional(np, clause.voice == 'passive') if role == 'prep'
                   else noun_phrase(np, ROLE_CASES.get(role, 'Dat')))
    for np in clause.role('complement'):
        if np.head is not None and np.head.pos in ('adj', 'participle') and not np.members:
            g = subject.gender if subject is not None and subject.gender in GENDERS else 'm'
            out.append(_adjective(np.head, subject_case, number, g))
        else:
            out.append(noun_phrase(np, subject_case))
    for adv in clause.adverbs:
        found, _ = to_greek(adv, 'adv')
        out.append(found.lemma if found else '[%s]' % english.word(adv))
    verb = _verb(clause, person, number)
    if clause.negated:
        if verb in ('ἐστί', 'ἐστίν', 'εἰσί', 'εἰσίν'):
            verb = {'ἐστί': 'ἔστι', 'ἐστίν': 'ἔστιν'}.get(verb, verb)   # οὐκ ἔστι
        out.append(_negation(verb))
    out.append(verb)
    return ' '.join(w for w in out if w)


def _verb(clause, person, number):
    verb = Lex('εἰμί', 'verb') if clause.copula else to_greek(clause.verb, 'verb')[0]
    if verb is None:
        return '[%s]' % english.word(clause.verb)
    if clause.mood == 'infinitive':
        return infinitive(verb, clause.tense, _voice(clause))
    return conjugate(verb, person, number, clause.tense, 'indicative' if clause.mood == 'subjunctive' and
                     not clause.question_word else clause.mood, _voice(clause))


def _absolute(p):
    """属格独立 (独立奪格 urbe captā → τῆς πόλεως ληφθείσης): 主語と分詞を属格に"""
    gender = p.subject.gender if p.subject.gender in GENDERS else 'm'
    number = p.subject.number
    subject = noun_phrase(p.subject, 'Gen')
    form = '[%s]' % english.word(p.verb)
    verb = to_greek(Lex(p.verb.verb, 'verb', p.verb.verb_ja or _latin_ja(p.verb), lang=p.verb.lang), 'verb')[0] \
        if p.verb.verb else None
    if verb is not None:
        tense = 'present' if p.tense == 'present' else 'aorist'
        voice = 'passive' if p.voice == 'passive' and tense == 'aorist' else \
            'middle-passive' if p.voice == 'passive' else 'active'
        for surface, item in _forms(verb.lemma, 'verb'):
            if item.get('mood') == 'participle' and item.get('tense') == tense and item.get('voice') == voice and \
                    ['Nom', 'sg', 'm'] in (item.get('_') or []) and not _hiatus(surface):
                form = _participle_genitive(surface, number, gender) or form
                break
        else:
            if tense == 'present' and voice == 'active' and verb.lemma.endswith('ω') and \
                    not _hiatus(verb.lemma[-2:]) and verb.lemma[-2:-1] not in 'άέό':
                form = _participle_genitive(verb.lemma + 'ν', number, gender) or form   # ᾄδω → ᾄδων (辞書に無い分詞)
    return subject + ' ' + form


def _latin_ja(participle):
    """ラテン語の分詞のもとの動詞の日本語の訳語 (訳語を選ぶ手がかりに)"""
    if participle.lang not in ('', 'la'):
        return ''
    from . import latin
    for _, item in latin._forms(participle.verb, 'verb')[:5]:
        if item.get('ja'):
            return item['ja']
    return ''


# 分詞の主格単数男性の語尾 → (属格単数 男・中, 属格複数 男・中, 属格単数 女, 属格複数 女)。辞書には主格の形しか無い
PARTICIPLE_GENITIVES = [('μενος', ('μένου', 'μένων', 'μένης', 'μένων')),
                        ('είς', ('έντος', 'έντων', 'είσης', 'εισῶν')),
                        ('ών', ('όντος', 'όντων', 'ούσης', 'ουσῶν')),
                        ('ων', ('οντος', 'όντων', 'ούσης', 'ουσῶν')),
                        ('ας', ('αντος', 'άντων', 'άσης', 'ασῶν'))]


def _participle_genitive(nominative, number, gender):
    for ending, forms in PARTICIPLE_GENITIVES:
        if nominative.endswith(ending):
            stem = nominative[:-len(ending)]
            k = (0 if number == 'sg' else 1) + (2 if gender == 'f' else 0)
            if k or ending in ('μενος', 'είς'):   # 語尾にアクセントが移る形は語幹のアクセントを外す
                stem = unicodedata.normalize('NFC', ''.join(
                    c for c in unicodedata.normalize('NFD', stem) if c not in '\u0301\u0342'))
            return stem + forms[k]
    return None


def wrap(text, clause):
    front, second = [], []
    for key in clause.connectives + ([clause.subordinator] if clause.subordinator else []):
        word, kind = CONNECTIVES.get(key, (None, None))
        if word is None:
            continue
        (second if kind == 'post' else front).append(word)
    if front:
        text = ' '.join(front) + ' ' + text
    if second:   # δέ・γάρ・οὖν は節の2語目
        head, _, rest = text.partition(' ')
        text = head + ' ' + ' '.join(second) + (' ' + rest if rest else '')
    return text


ENCLITICS = {'τε', 'ἐστί', 'ἐστίν', 'εἰσί', 'εἰσίν', 'τις', 'τι', 'μου', 'μοι', 'με', 'σου', 'σοι', 'σε'}
VOWELS = set('αεηιουω')


def _grave(text):
    """文中の語末の鋭アクセント → 重アクセント (καλὸν ῥόδον)。句読点・前接語の前と τίς はそのまま"""
    words = text.split(' ')
    out = []
    for i, w in enumerate(words):
        following = words[i + 1] if i + 1 < len(words) else ''
        if following and w[-1:].isalpha() and following not in ENCLITICS and w not in ('τίς', 'τί'):
            d = unicodedata.normalize('NFD', w)
            k = d.rfind('\u0301')
            if k >= 0 and not any(c in VOWELS for c in d[k + 1:]):
                w = unicodedata.normalize('NFC', d[:k] + '\u0300' + d[k + 1:])
        out.append(w)
    return ' '.join(out)


def sentence(clauses):
    if not clauses:
        return ''
    return ', '.join(_grave(wrap(realize(c), c)) for c in clauses) + '.'
