#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Morpheus (Perseus の語形解析器。perseids-tools/morpheus を $DRAGOMAN_DATA/grc/morpheus でビルドしたもの) で、
# 辞書に無い語形 (叙事詩・方言の形、加音の無い過去形など) を解析する
#
#   ἑτάροισι → ἑταῖρος 男性複数与格 (epic ionic aeolic)
#   φάτο     → φημί アオリスト中動3人称単数 (epic)
#
# 解析は Morpheus の見出し語と語形の情報。品詞 (名詞・形容詞など) と訳語は、見出し語を Wiktionary の辞書で引いて決める。
# Morpheus が無ければ何もしない (規則による読み替え greek/dialect.py だけを使う)
#
import os
import re
import subprocess
import unicodedata

from . import dictionary, orthography

HOME = os.path.join(dictionary.DATA_DIR, 'morpheus')
CRUNCHER = os.path.join(HOME, 'bin', 'cruncher')
STEMLIB = os.path.join(HOME, 'stemlib')

# ----------------------------------------------------------------------
# ベータコード

LETTERS = {'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'h', 'θ': 'q', 'ι': 'i', 'κ': 'k',
           'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'c', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
           'υ': 'u', 'φ': 'f', 'χ': 'x', 'ψ': 'y', 'ω': 'w', 'ϝ': 'v'}
MARKS = {'̓': ')', '̔': '(', '́': '/', '̀': '\\', '͂': '=', 'ͅ': '|', '̈': '+'}
BETA_LETTERS = {v: k for k, v in LETTERS.items() if k != 'ς'}
BETA_MARKS = {v: k for k, v in MARKS.items()}
BETA_MARKS.update({'_': '̄', '^': '̆'})


def to_betacode(word):
    """ギリシア文字の語をベータコードに (大文字は *、記号は文字の後ろ。大文字では文字の前)"""
    out = []
    for c in unicodedata.normalize('NFD', orthography.key(word)):
        if c in MARKS:
            if out and out[-1].startswith('*'):
                out[-1] = out[-1][:-1] + MARKS[c] + out[-1][-1]  # 大文字の記号は文字の前 (*)a)
            elif out:
                out[-1] += MARKS[c]
        elif c.lower() in LETTERS:
            letter = LETTERS[c.lower()]
            out.append('*' + letter if c.isupper() else letter)
    return ''.join(out)


def from_betacode(beta):
    """ベータコードをギリシア文字に (語末の σ は ς。同綴異義の番号は除く)"""
    beta = re.sub(r'\d+$', '', beta)
    out, pending, capital = [], [], False
    for c in beta:
        if c == '*':
            capital = True
        elif c in BETA_MARKS:
            if capital and not out[-1:] or capital:
                pending.append(BETA_MARKS[c])
            elif out:
                out[-1] += BETA_MARKS[c]
        elif c in BETA_LETTERS:
            letter = BETA_LETTERS[c]
            out.append((letter.upper() if capital else letter) + ''.join(pending))
            pending, capital = [], False
    text = ''.join(out)
    if text.endswith('σ'):
        text = text[:-1] + 'ς'
    return unicodedata.normalize('NFC', text)


# ----------------------------------------------------------------------
# 解析

CASES = {'nom': 'Nom', 'gen': 'Gen', 'dat': 'Dat', 'acc': 'Acc', 'voc': 'Voc'}
NUMBERS = {'sg': 'sg', 'dual': 'du', 'pl': 'pl'}
GENDERS = {'masc': 'm', 'fem': 'f', 'neut': 'n'}
TENSES = {'pres': 'present', 'imperf': 'imperfect', 'fut': 'future', 'aor': 'aorist', 'perf': 'perfect',
          'plupf': 'past-perfect', 'futperf': 'future-perfect'}
MOODS = {'ind': 'indicative', 'subj': 'subjunctive', 'opt': 'optative', 'imperat': 'imperative',
         'inf': 'infinitive', 'part': 'participle'}
VOICES = {'act': 'active', 'mid': 'middle', 'pass': 'passive', 'mp': 'middle-passive'}
PERSONS = {'1st': 1, '2nd': 2, '3rd': 3}
INDECLINABLE = {'adverb': 'adv', 'conj': 'conj', 'prep': 'preposition', 'particle': 'conj', 'article': 'article'}
DIALECTS = ('epic', 'homeric', 'ionic', 'aeolic', 'doric', 'attic')
NL = re.compile(r'<NL>(.*?)</NL>')

_cache = {}


def available():
    return os.path.exists(CRUNCHER) and os.path.isdir(STEMLIB)


def _cng(features):
    cases = [CASES[f] for f in features if f in CASES]
    numbers = [NUMBERS[f] for f in features if f in NUMBERS] or ['sg']
    genders = [GENDERS[g] for f in features for g in f.split('/') if g in GENDERS] or [None]
    return [(c, n, g) for c in cases for n in numbers for g in genders]


def _lemma_info(lemma):
    """見出し語の品詞と訳語 (Wiktionary の辞書から)。無ければ (None, 見出し語そのもの, 'en')"""
    for item in dictionary.lookup(lemma):
        if orthography.key(item.get('base') or item.get('pres1sg') or '') == orthography.key(lemma):
            return item.get('pos'), item.get('ja'), item.get('gloss_lang', 'en')
    return None, lemma, 'en'


def _parse(surface, line):
    """<NL> の1行 (品詞 見出し語  語形の情報 \\t 方言 \\t 注記 \\t 語幹の型) → 辞書の項目 (dict)。扱わなければ None"""
    fields = line.split('\t')
    head = fields[0].split()
    if len(head) < 2:
        return None
    kind, lemma_beta, features = head[0], head[1].split(',')[-1], head[2:]
    dialect = ' '.join(f for f in (fields[1].split() if len(fields) > 1 else []) if f in DIALECTS) or None
    lemma = from_betacode(lemma_beta)
    pos, ja, gloss_lang = _lemma_info(lemma)
    item = {'surface': orthography.key(surface), 'ja': ja, 'gloss_lang': gloss_lang, 'source': 'morpheus'}
    if dialect:
        item['dialect'] = dialect
    if kind == 'V':
        mood = next((MOODS[f] for f in features if f in MOODS), 'indicative')
        item.update({'tense': next((TENSES[f] for f in features if f in TENSES), 'present'),
                     'voice': next((VOICES[f] for f in features if f in VOICES), 'active')})
        if mood == 'participle':
            item.update({'pos': 'participle', 'base': lemma, 'pres1sg': lemma, '_': _cng(features)})
        else:
            item.update({'pos': 'verb', 'pres1sg': lemma, 'mood': mood})
            person = next((PERSONS[f] for f in features if f in PERSONS), None)
            number = next((NUMBERS[f] for f in features if f in NUMBERS), None)
            if person:
                item['person'] = person
            if number:
                item['number'] = number
        return item
    if 'indeclform' in features:
        stemtype = fields[-1].strip() if fields else ''
        pos = INDECLINABLE.get(stemtype, pos or 'adv')
        item.update({'pos': pos, 'base': lemma})
        if pos == 'preposition':
            return None  # 前置詞は Wiktionary の辞書にある (支配する格はそちらで)
        return item
    cng = _cng(features)
    if not cng:
        return None
    item.update({'pos': pos if pos in ('noun', 'adj', 'pronoun', 'article', 'participle') else 'noun',
                 'base': lemma, '_': cng})
    return item


def analyze_many(words):
    """語のリストを1回の Morpheus の呼び出しで解析し、キャッシュに入れる"""
    todo = [w for w in dict.fromkeys(words) if w not in _cache]
    if not todo or not available():
        for w in todo:
            _cache[w] = []
        return
    betas = [to_betacode(w) for w in todo]
    env = dict(os.environ, MORPHLIB=STEMLIB)
    try:
        out = subprocess.run([CRUNCHER, '-S'], input='\n'.join(betas) + '\n', capture_output=True, text=True,
                             env=env, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        out = ''
    # 出力は「入力の語」「解析 (<NL>…</NL> の並び。無ければ空)」の行の繰り返し
    lines = out.split('\n')
    results = {}
    i = 0
    for word, beta in zip(todo, betas):
        while i < len(lines) and lines[i].strip() != beta:
            i += 1
        if i >= len(lines):
            break
        analysis = lines[i + 1] if i + 1 < len(lines) and '<NL>' in lines[i + 1] else ''
        results[word] = [item for item in (_parse(word, nl) for nl in NL.findall(analysis)) if item]
        i += 1
    for w in todo:
        _cache[w] = results.get(w, [])


def analyze(word):
    """語の解析 (辞書の項目のリスト)"""
    if word not in _cache:
        analyze_many([word])
    return _cache[word]
