#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) からラテン語の文を作る
#
#   語形は解析に使う辞書を逆に引いて作る: (見出し語, 格, 数, 性) → 語形、(見出し語, 人称, 数, 時制, 法, 態) → 語形。
#   手作りの辞書 (latin/words/) を先に、無ければ Wiktionary 由来の補助辞書 (wiktionary.sqlite) を見出し語で引く。
#   語順は 主語 - 受け手 - 目的語 - 前置詞句・手段 - 副詞 - (否定) - 動詞 (ラテン語の散文のふつうの順)。
#   形容詞は名詞の後ろ、属格は名詞の後ろ。主語が代名詞だけなら省く (動詞の人称で分かる)
#
import json
import functools

from dragoman.latin import latindic, wiktionary
from . import frame

CONJUNCTIONS = {'et': 'et', 'atque': 'atque', 'ac': 'ac', 'aut': 'aut', 'vel': 'vel', 'neque': 'neque',
                'nec': 'nec', 'que': 'que', '-que': 'que', 'sed': 'sed'}
PERSONAL = ('ego', 'tū', 'nōs', 'vōs')


@functools.lru_cache(maxsize=1)
def _pronoun_groups():
    """見出しの無い代名詞 (手作りの辞書の ego・hic・ille …): (種類, 訳語, 人称) → 最初に登録された語形 (主格単数男性)"""
    if not latindic.LatinDic.dic:
        latindic.load()
    groups = {}
    for surface, items in latindic.LatinDic.dic.items():
        for item in items:
            if item.get('pos') == 'pronoun' and not item.get('base'):
                groups.setdefault((item.get('desc'), item.get('ja'), item.get('person')), surface)
    return groups


def pronoun_lemma(item):
    if item.get('pos') != 'pronoun' or item.get('base'):
        return None
    return _pronoun_groups().get((item.get('desc'), item.get('ja'), item.get('person')))


frame.LEMMA_HOOKS.append(pronoun_lemma)


@functools.lru_cache(maxsize=5000)
def verb_gloss(pres1sg):
    """動詞の見出し (直説法現在1人称単数) → 日本語の訳語 (分詞 cantāns のもとの cantō「歌う」)"""
    for item in latindic.lookup(pres1sg) or []:
        if item.get('pos') == 'verb' and item.get('pres1sg') == pres1sg:
            return item.get('ja') if item.get('gloss_lang', 'ja') == 'ja' else None
    return None


frame.VERB_GLOSS_HOOKS.append(verb_gloss)


def _lemma(item):
    return item.get('base') or item.get('pres1sg') or pronoun_lemma(item)


@functools.lru_cache(maxsize=1)
def _hand_index():
    """手作りの辞書の逆引き: 見出し語 → [(語形, 項目)]"""
    if not latindic.LatinDic.dic:
        latindic.load()
    index = {}
    for surface, items in latindic.LatinDic.dic.items():
        for item in items:
            lemma = _lemma(item)
            if lemma:
                index.setdefault(lemma, []).append((surface, item))
    return index


@functools.lru_cache(maxsize=2000)
def _wiktionary_forms(lemma, pos):
    """Wiktionary 由来の辞書の逆引き: 見出し語の語形をすべて [(語形, 項目)]"""
    db = wiktionary._connect()
    if db is None:
        return []
    key = '$.pres1sg' if pos == 'verb' else '$.base'
    rows = db.execute('SELECT f.surface, l.info, f.features FROM lemmas l JOIN forms f ON f.lemma_id = l.id '
                      'WHERE json_extract(l.info, ?) = ?', (key, lemma)).fetchall()
    out = []
    for surface, info, features in rows:
        item = dict(json.loads(info), **json.loads(features))
        if item.get('pos') == pos:
            out.append((surface, item))
    return out


def _forms(lemma, pos):
    """手作りの辞書の語形を先に、Wiktionary 由来の語形を後に"""
    hand = [(s, it) for s, it in _hand_index().get(lemma, []) if it.get('pos') == pos]
    return hand + _wiktionary_forms(lemma, pos)


def decline(lex, case, number, gender='', prefer=None):
    """名詞・代名詞・形容詞・分詞の語形。見つからなければ見出し語に * を付けて返す。
    同じ働きの形が複数あれば、手作りの辞書の形 → prefer (語形を受けて真偽を返す関数) に合う形 → Wiktionary にもある形"""
    pos = lex.pos
    candidates = []
    for order, (surface, item) in enumerate(_forms(lex.lemma, pos)):
        if (item.get('rank') or '') != lex.degree:
            continue   # 比較級・最上級は、元の語と同じ度合いの形だけ
        for tag in item.get('_') or []:
            c, n, g = (list(tag) + [None, None, None])[:3]
            if c == case and n == number:
                candidates.append((0 if not gender or g in (gender, 'c') else 1,
                                   0 if prefer is None or prefer(surface) else 1, order, surface))
    if not candidates:
        return '*' + lex.lemma
    return min(candidates)[3]


def _attested(surfaces):
    """同じ働きの語形が複数あれば、Wiktionary にもある形を選ぶ (possum: potest と、手作りの表の posest)"""
    if len(surfaces) > 1:
        for surface in surfaces:
            if wiktionary.lookup(surface):
                return surface
    return surfaces[0]


def conjugate(lex, person, number, tense, mood, voice):
    found = [surface for surface, item in _forms(lex.lemma, 'verb')
             if item.get('person') == person and item.get('number') == number and
             (item.get('tense') or 'present') == tense and (item.get('mood') or 'indicative') == mood and
             (item.get('voice') or 'active') == voice]
    return _attested(list(dict.fromkeys(found))) if found else '*' + lex.lemma


def infinitive(lex, tense, voice):
    found = [surface for surface, item in _forms(lex.lemma, 'verb')
             if item.get('mood') == 'infinitive' and (item.get('tense') or 'present') == tense and
             (item.get('voice') or 'active') == voice]
    return _attested(list(dict.fromkeys(found))) if found else '*' + lex.lemma


def participle(p):
    """分詞を、一致する名詞の格・数・性で。独立奪格の現在分詞の奪格単数は -e (cantante。形容詞的な -ī ではなく)"""
    prefer = (lambda surface: surface.endswith('e')) if p.kind == 'absolute' and p.tense == 'present' else None
    return decline(p.verb, p.case, p.number, p.gender, prefer)


def participial(p):
    """分詞句: 独立奪格は 主語 - 補語 - 分詞、分詞句は 補語 - 分詞"""
    words = []
    if p.subject is not None:
        words.append(noun_phrase(p.subject, 'Abl'))
    for role, np in p.args:
        words.append(np.head.lemma if role == 'adverb' else noun_phrase(np))
    words.append(participle(p))
    return ' '.join(words)


def noun_phrase(np, case=None):
    case = case or np.case
    if np.members:
        conj = CONJUNCTIONS.get(np.conj, np.conj)
        parts = [noun_phrase(m, case) for m in np.members]
        if conj == 'que':
            text = ' '.join(parts[:-1] + [parts[-1] + 'que'])   # puerī puellaeque
        elif conj in ('neque', 'nec') or np.correlative:
            text = ' '.join(conj + ' ' + p for p in parts)     # et dominus et servus
        else:
            text = (' %s ' % conj).join(parts)
    else:
        words = [decline(np.head, case, np.number, np.gender)]
        for mod in np.modifiers:
            words.append(agree(mod, case, np.number, np.gender))  # 形容詞は名詞の格・数・性に一致させる
        for gen in np.genitives:
            words.append(noun_phrase(gen, 'Gen'))
        for p in np.participles:
            p.case, p.number, p.gender = case, np.number, np.gender
            words.append(participial(p))
        if any(m.desc == '指示代名詞' for m in np.modifiers if isinstance(m, frame.Lex)):
            words = words[1:2] + words[:1] + words[2:]   # 指示代名詞は名詞の前 (haec puella)
        text = ' '.join(words)
    if np.prep is not None:
        text = np.prep.lemma + ' ' + text
    return text


def agree(mod, case, number, gender):
    """修飾語 (形容詞、並列した形容詞) を名詞に一致させる"""
    if isinstance(mod, frame.NP):
        np = frame.NP(conj=mod.conj, correlative=mod.correlative,
                      members=[frame.NP(m.head, number=number, gender=gender) for m in mod.members])
        return noun_phrase(np, case)
    return decline(mod, case, number, gender)


def realize(clause, capitalize=True):
    out = [participial(p) for p in clause.adjuncts if p.kind == 'absolute']
    subjects = clause.role('subject')
    # 不定詞句の主語は対格 (dīcit puerōs lūdere)。補足の不定詞 (legere potest) は主語を持たない
    subject_case = 'Acc' if clause.mood == 'infinitive' else 'Nom'
    for np in subjects:
        if not (np.head is not None and np.head.pos == 'pronoun' and not np.modifiers and
                np.head.lemma in PERSONAL and clause.mood != 'infinitive'):
            out.append(noun_phrase(np, subject_case))
    out += [participial(p) for p in clause.adjuncts if p.kind != 'absolute']
    for role in ('recipient', 'object', 'complement'):
        for np in clause.role(role):
            if role == 'complement' and subjects and not np.members and np.head.pos in ('adj', 'participle'):
                # 補語の形容詞は主語の数・性に一致させる (Vīta brevis est)
                subject = subjects[0]
                out.append(decline(np.head, subject_case, subject.number, subject.gender))
                continue
            out.append(noun_phrase(np))
    for inner in clause.infinitives:
        out.append(realize(inner, capitalize=False))
    for role, np in clause.args:
        if role not in ('subject', 'recipient', 'object', 'complement'):
            out.append(noun_phrase(np))
    out += [adv.lemma for adv in clause.adverbs]
    if clause.negated:
        out.append('nōn')
    if clause.mood == 'infinitive':
        out.append(infinitive(clause.verb, clause.tense, clause.voice))
    else:
        out.append(conjugate(clause.verb, clause.person, clause.number, clause.tense, clause.mood, clause.voice))
    text = ' '.join(out)
    if capitalize:
        text = text[:1].upper() + text[1:]
    return text


def sentence(clauses):
    if not clauses:
        return ''
    return ', '.join(realize(c, capitalize=(i == 0)) for i, c in enumerate(clauses)) + '.'
