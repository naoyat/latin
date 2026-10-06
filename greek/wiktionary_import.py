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

import re
import unicodedata

from latin.wiktionary_import import english_glosses, japanese_gloss, descendants_summary, etymology_summary
from . import orthography, participles

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


def _surfaces(form):
    """表の形から辞書の表層形 (のリスト) を: 冠詞付き (ἡ ῐ̔́ππος) なら最後の語、長短の印などは除く。
    括弧の付いた文字は付けた形と付けない形の両方 (ἐστῐ́(ν) → ἐστί, ἐστίν。ν の付加)"""
    word = form.strip().split()[-1] if form.strip() else ''
    m = re.search(r'\(([^)]*)\)', word)
    if m:
        return [orthography.key(word[:m.start()] + word[m.end():]),
                orthography.key(word[:m.start()] + m.group(1) + word[m.end():])]
    return [orthography.key(word)]


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
        for surface in _surfaces(form['form']):
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
        surfaces = [s for s in _surfaces(form['form']) if s and s != '-']
        if not surfaces:
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
        result.extend((surface, dict(features)) for surface in surfaces)
    return result


CASE_MARKER = re.compile(r'^[\[(]with (genitive|dative|accusative)[^\])]*[\])]\s*', re.I)
CASE_NAMES = {'genitive': 'Gen', 'dative': 'Dat', 'accusative': 'Acc'}


def _sense_case(sense, umbrellas=()):
    """前置詞の語義が支配する格と、その意味の訳語 (無ければ None)。
    語義の書き出しの [with genitive] / (with dative) を優先し、無ければタグ (対格 > 与格 > 属格の順。
    属格のタグは誤って付いていることが多いので最後に)。訳語が複数あるとき、最初が全体の要約
    (πρός の「on the side of, from, at, to …」) なら最後のものを使う"""
    glosses = [g for g in sense.get('glosses', []) if g.strip()]
    if not glosses:
        return None, None
    m = CASE_MARKER.match(glosses[0])
    if m:
        rest = glosses[0][m.end():].strip()
        meaning = rest or (glosses[1] if len(glosses) > 1 else '')
        return CASE_NAMES[m.group(1).lower()], meaning or None
    # 最初の訳語がほかの語義と共通の要約なら、残りを使う
    meaning = ', '.join(glosses[1:]) if glosses[0] in umbrellas and len(glosses) > 1 else glosses[-1]
    tags = sense.get('tags', [])
    for tag, case in (('with-accusative', 'Acc'), ('with-dative', 'Dat'), ('with-genitive', 'Gen')):
        if tag in tags:
            return case, meaning
    return None, meaning


def _clean_prep_gloss(texts, limit=3):
    words = []
    for text in texts:
        text = re.sub(r'\([^)]*\)', '', text.split('\n')[0])
        for part in re.split(r'[;,]', text):
            part = part.strip().rstrip('.')
            # 例文 (εἰς τὴν πόλιν) とそのローマ字表記 (eis tḕn pólin) は除く
            if any(orthography.is_greek(c) or '\u1e00' <= c <= '\u1eff' or unicodedata.combining(c) for c in part):
                continue
            if part and part not in words:
                words.append(part)
    return ','.join(words[:limit])


def _prep_cases(entry):
    """前置詞が支配する格 (見出しのテンプレートの順) と、格ごとの英語の訳語"""
    cases = []
    for head in entry.get('head_templates', []):
        for k in sorted(k for k in head.get('args', {}) if k.isdigit()):
            case = PREP_CASES.get(head['args'][k])
            if case and case not in cases:
                cases.append(case)
    firsts = [s['glosses'][0] for s in entry.get('senses', []) if s.get('glosses')]
    umbrellas = {g for g in firsts if firsts.count(g) >= 2 and not CASE_MARKER.match(g)}
    by_case = {}
    for sense in entry.get('senses', []):
        case, meaning = _sense_case(sense, umbrellas)
        case = case or (cases[0] if cases else None)
        if case and meaning:
            by_case.setdefault(case, []).append(meaning)
    for case in by_case:
        if case not in cases:
            cases.append(case)
    return cases, {case: _clean_prep_gloss(texts) for case, texts in by_case.items()}


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


def _generated_participles(verb, forms, ja, lang):
    """活用表の男性単数主格の分詞から、変化形を作った分詞の項目 (greek/participles.py)"""
    result, seen = [], set()
    for surface, features in forms:
        if features.get('mood') != 'participle' or ('Nom', 'sg', 'm') not in features.get('_', []):
            continue
        key = (surface, features['tense'], features['voice'])
        if key in seen:
            continue
        seen.add(key)
        table = participles.declension(surface)
        if not table:
            continue
        info = {'pos': 'participle', 'base': surface, 'pres1sg': verb, 'tense': features['tense'],
                'voice': features['voice'], 'ja': ja, 'gloss_lang': lang, 'generated': True}
        result.append((info, [(form, {'_': cng}) for form, cng in table.items()]))
    return result


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
        forms = _verb_forms(entry)
        return [(info, forms)] + _generated_participles(base, forms, ja, lang)

    if pos == 'prep':
        cases, glosses = _prep_cases(entry)
        result = []
        for i, case in enumerate(cases or ['Gen']):
            # 日本語の訳語は主な格 (最初の格) にだけ使う (ほかの格は意味が違う: παρά + 属格「〜から」/ 与格「〜のそばで」)
            ja, lang = _gloss(entry, ja_glosses if i == 0 else None)
            if lang == 'en' and glosses.get(case):
                ja = glosses[case]
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
