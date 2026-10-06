#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の抽出データ) の古典ギリシア語の項目を、辞書の項目に変換する
#
# 項目の形はラテン語の辞書 (latin/wiktionary_import.py) と同じ: lemma_info (pos, base/pres1sg, ja, gloss_lang …)
# と、表層形ごとの features (名詞類は '_': [(格, 数, 性)]、動詞は mood/voice/tense/person/number)。
# ギリシア語にだけあるもの: 双数 (du)、中動態 (middle)、アオリスト (aorist)、希求法 (optative)、
# 方言 (dialect: Epic, Ionic, Attic, Koine …)、冠詞 (pos 'article')
#

from latin.wiktionary_import import english_glosses, japanese_gloss, descendants_summary, etymology_summary
from . import orthography

CASES = {'nominative': 'Nom', 'genitive': 'Gen', 'dative': 'Dat', 'accusative': 'Acc', 'vocative': 'Voc'}
NUMBERS = {'singular': 'sg', 'dual': 'du', 'plural': 'pl'}
GENDERS = {'masculine': 'm', 'feminine': 'f', 'neuter': 'n'}
PERSONS = {'first-person': 1, 'second-person': 2, 'third-person': 3}
MOODS = ('indicative', 'subjunctive', 'optative', 'imperative', 'infinitive', 'participle')
# 表の見出し (「Epic aorist」「contracted present」) の中の時制。長いものから照合する
# (imperfect は perfect より先に: 'perfect' は 'imperfect' の中にもある)
TENSES = [('future perfect', 'future-perfect'), ('pluperfect', 'past-perfect'), ('imperfect', 'imperfect'),
          ('perfect', 'perfect'), ('aorist', 'aorist'), ('future', 'future'), ('present', 'present')]
DIALECTS = ('Epic', 'Ionic', 'Attic', 'Doric', 'Aeolic', 'Koine', 'Laconian', 'Boeotian', 'Arcadocypriot')

NOMINAL_POS = {'noun': 'noun', 'name': 'noun', 'adj': 'adj', 'num': 'adj', 'det': 'adj', 'pron': 'pronoun',
               'article': 'article'}
INDECLINABLE_POS = {'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'intj': 'indecl'}
PREP_CASES = {'gen': 'Gen', 'dat': 'Dat', 'acc': 'Acc'}
# 子孫語として集める言語 (ラテン語への借用も) と、古典ギリシア語から語を継承しうる言語 (中世・現代ギリシア語)
DESCENDANT_LANGS = ('la', 'en', 'fr', 'it', 'es')
INHERITING = {'grc-koi', 'gkm', 'el', 'grc'}
SKIP_FORM_TAGS = {'canonical', 'table-tags', 'inflection-template', 'romanization', 'class', 'alternative'}


def _senses_tags(entry):
    return set(t for s in entry.get('senses', []) for t in s.get('tags', []))


def _is_form_of(entry):
    senses = entry.get('senses', [])
    return bool(senses) and all('form_of' in s or 'alt_of' in s for s in senses)


def canonical(entry):
    for form in entry.get('forms', []):
        if 'canonical' in form.get('tags', []):
            return orthography.key(form['form'].split(' •')[0].strip())
    return orthography.key(entry['word'])


def _surface(form):
    """表の形から辞書の表層形を: 冠詞付き (ἡ ῐ̔́ππος) なら最後の語、長短の印などは除く"""
    word = form.strip().split()[-1] if form.strip() else ''
    return orthography.key(word)


ARTICLE_GENDERS = {'ὁ': 'm', 'ἡ': 'f', 'τό': 'n'}
# 冠詞の形 (形容詞などの変化表には冠詞の欄が単独の形として入っているので、それを除く)
ARTICLE_FORMS = {'ὁ', 'ἡ', 'τό', 'τοῦ', 'τῆς', 'τῷ', 'τῇ', 'τόν', 'τήν', 'τώ', 'τοῖν', 'ταῖν', 'οἱ', 'αἱ', 'τά',
                 'τῶν', 'τοῖς', 'ταῖς', 'τούς', 'τάς', 'ὦ'}


def _lemma_genders(entry):
    """見出し語の性: 見出しの形のタグ、見出しのテンプレートの引数 (grc-noun の 'm')、
    変化表の冠詞付きの主格 (ὁ λόγος, ἡ ὁδός, τὸ ἔργον) の順に"""
    genders = [g for tag, g in GENDERS.items()
               for form in entry.get('forms', []) if 'canonical' in form.get('tags', []) and tag in form.get('tags', [])]
    if not genders:
        for head in entry.get('head_templates', []):
            if head.get('name') in ('grc-noun', 'grc-proper noun', 'grc-noun-con'):
                for value in head.get('args', {}).values():
                    for g in str(value).split('-'):
                        if g in ('m', 'f', 'n') and g not in genders:
                            genders.append(g)
    if not genders:
        for form in entry.get('forms', []):
            tags = form.get('tags', [])
            words = form.get('form', '').split()
            if len(words) == 2 and 'nominative' in tags and 'singular' in tags:
                g = ARTICLE_GENDERS.get(orthography.key(words[0]))
                if g and g not in genders:
                    genders.append(g)
    return list(dict.fromkeys(genders)) or [None]


def _nominal_features(entry, default_genders):
    """変化表から {表層形: {'_': [(格, 数, 性)], 'dialect': …}}"""
    article = entry.get('pos') in ('article', 'det', 'pron')
    table = {}
    dialect = None
    for form in entry.get('forms', []):
        tags = form.get('tags', [])
        if 'table-tags' in tags:
            dialect = next((d for d in DIALECTS if d in form['form']), None)
            continue
        if SKIP_FORM_TAGS & set(tags):
            continue
        cases = [c for tag, c in CASES.items() if tag in tags]
        numbers = [n for tag, n in NUMBERS.items() if tag in tags]
        if not cases or not numbers:
            continue
        genders = [g for tag, g in GENDERS.items() if tag in tags] or default_genders
        surface = _surface(form['form'])
        if not surface or surface == '-' or (surface in ARTICLE_FORMS and not article):
            continue
        features = table.setdefault(surface, {'_': []})
        if dialect and 'dialect' not in features:
            features['dialect'] = dialect
        for case in cases:
            for number in numbers:
                for gender in genders:
                    if (case, number, gender) not in features['_']:
                        features['_'].append((case, number, gender))
    return table


def _verb_forms(entry):
    """活用表から [(表層形, features)]。時制は直前の表の見出し (table-tags) から"""
    result = []
    tense, dialect = 'present', None
    for form in entry.get('forms', []):
        tags = form.get('tags', [])
        if 'table-tags' in tags:
            label = form['form']
            tense = next((t for name, t in TENSES if name in label), tense)
            dialect = next((d for d in DIALECTS if d in label), None)
            continue
        if SKIP_FORM_TAGS & set(tags):
            continue
        surface = _surface(form['form'])
        if not surface or surface == '-':
            continue
        mood = next((m for m in MOODS if m in tags), None)
        if mood is None:
            continue
        voices = [v for v in ('active', 'middle', 'passive') if v in tags]
        features = {'mood': mood, 'tense': tense,
                    # 中動・受動が同じ形のときは 'middle-passive'
                    'voice': 'middle-passive' if voices == ['middle', 'passive'] else (voices[0] if voices else 'active')}
        if mood == 'participle':
            genders = [g for tag, g in GENDERS.items() if tag in tags] or [None]
            features['_'] = [('Nom', 'sg', g) for g in genders]
        else:
            person = next((p for tag, p in PERSONS.items() if tag in tags), None)
            number = next((n for tag, n in NUMBERS.items() if tag in tags), None)
            if person:
                features['person'] = person
            if number:
                features['number'] = number
        if dialect:
            features['dialect'] = dialect
        result.append((surface, features))
    return result


def _prep_cases(entry):
    """前置詞が支配する格と、格ごとの訳語の語義"""
    cases = []
    for head in entry.get('head_templates', []):
        for k in sorted(k for k in head.get('args', {}) if k.isdigit()):
            case = PREP_CASES.get(head['args'][k])
            if case and case not in cases:
                cases.append(case)
    by_case = {}
    for s in entry.get('senses', []):
        tagged = [CASES[t[len('with-'):]] for t in s.get('tags', []) if t.startswith('with-') and t[len('with-'):] in CASES]
        for case in tagged or cases[:1]:
            by_case.setdefault(case, []).append(s)
    return cases, by_case


JA_GLOSS_MAX = 12  # これより長い日本語の訳語は説明文 (ほかに訳語があれば落とす)


def _gloss(entry, ja_glosses, senses=None):
    if ja_glosses:
        ja = ja_glosses.get(ja_key(entry))
        if ja:
            glosses = ja.split(',')
            short = [g for g in glosses if len(g) <= JA_GLOSS_MAX]
            return ','.join(short or glosses[:1]), 'ja'
    return english_glosses(entry, senses), 'en'


def ja_key(entry):
    # アクセント・気息記号まで含めて照合する (εἰμί「ある」と εἶμι「行く」を混ぜない)
    return (orthography.key(entry.get('word', '')), NOMINAL_POS.get(entry.get('pos'), entry.get('pos')))


def _is_participle_entry(entry):
    """分詞の項目 (λυθείς): すべての語義が分詞"""
    senses = entry.get('senses', [])
    return entry.get('pos') == 'verb' and bool(senses) and all('participle' in s.get('tags', []) for s in senses)


def _participle_verb(entry):
    return next((orthography.key(f['word']) for s in entry.get('senses', []) for f in s.get('form_of', [])), None)


def _participle_tense(entry):
    tags = _senses_tags(entry)
    return next((t for name, t in TENSES if name in tags), None)


INDECLINABLE_CNG = [(case, 'sg', None) for case in CASES.values()]


def convert_entry(entry, ja_glosses=None):
    """Wiktionary の1項目を [(lemma_info, [(表層形, features)])] に (前置詞は格ごとに分けるので複数)。扱わなければ []"""
    if entry.get('lang_code') != 'grc':
        return []
    pos = entry.get('pos')
    base = canonical(entry)

    # 分詞の項目 (変化形の項目として書かれているが、変化表を持つ)
    if _is_participle_entry(entry):
        table = _nominal_features(entry, [None])
        if not table:
            return []
        ja, lang = _gloss(entry, ja_glosses)
        voices = _senses_tags(entry) & {'active', 'middle', 'passive'}
        info = {'pos': 'participle', 'base': base, 'pres1sg': _participle_verb(entry),
                'tense': _participle_tense(entry) or 'present', 'ja': ja, 'gloss_lang': lang,
                'voice': 'middle-passive' if voices == {'middle', 'passive'} else (voices.pop() if voices else 'active')}
        return [(info, list(table.items()))]
    if _is_form_of(entry):
        return []

    if pos == 'verb':
        ja, lang = _gloss(entry, ja_glosses)
        info = {'pos': 'verb', 'pres1sg': base, 'ja': ja, 'gloss_lang': lang}
        return [(info, _verb_forms(entry))]

    if pos == 'prep':
        cases, by_case = _prep_cases(entry)
        result = []
        for case in cases or ['Gen']:
            ja, lang = _gloss(entry, ja_glosses, by_case.get(case))
            result.append(({'pos': 'preposition', 'dominates': case, 'base': base, 'ja': ja, 'gloss_lang': lang},
                           [(base, {})]))
        return result

    if pos in NOMINAL_POS:
        group = NOMINAL_POS[pos]
        table = _nominal_features(entry, _lemma_genders(entry))
        if not table:
            if pos not in ('noun', 'name'):
                return []
            # 変化表の無い名詞 (不変化の固有名詞 Ἰσραήλ, Δαβίδ や文字の名前): どの格にもなりうる
            genders = _lemma_genders(entry)
            table = {base: {'_': [(c, n, g) for c, n, _ in INDECLINABLE_CNG for g in genders]}}
        ja, lang = _gloss(entry, ja_glosses)
        info = {'pos': group, 'base': base, 'ja': ja, 'gloss_lang': lang}
        return [(info, list(table.items()))]

    if pos in INDECLINABLE_POS:
        ja, lang = _gloss(entry, ja_glosses)
        return [({'pos': INDECLINABLE_POS[pos], 'base': base, 'ja': ja, 'gloss_lang': lang}, [(base, {})])]
    return []


def lemma_key(entry):
    """子孫語・語源の表の見出し語のキー (アクセント・気息記号を保つ: ὁ と文字の Ο を混ぜない)"""
    return orthography.key(entry.get('word', ''))


__all__ = ['convert_entry', 'descendants_summary', 'etymology_summary', 'japanese_gloss', 'ja_key', 'lemma_key']
