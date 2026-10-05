#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary (kaikki.org の wiktextract 抽出データ) の項目を、この辞書の形式に変換する
#
#   convert_entry(entry, ja_glosses) → (lemma_info, [(surface, features), ...]) or None
#
# lemma_info は語に共通の情報 (pos, base/pres1sg, ja, gloss_lang ...)、
# features は変化形ごとの情報 ('_' の格・数・性のリスト、または法・態・時制・人称・数)。
# 両者を合わせると latin_noun 等が作るのと同じ形の dict になる。
#
import re
import unicodedata

from . import orthography

CASES = {'nominative': 'Nom', 'vocative': 'Voc', 'accusative': 'Acc', 'genitive': 'Gen',
         'dative': 'Dat', 'ablative': 'Abl', 'locative': 'Loc'}
NUMBERS = {'singular': 'sg', 'plural': 'pl'}
GENDERS = {'masculine': 'm', 'feminine': 'f', 'neuter': 'n'}
PERSONS = {'first-person': 1, 'second-person': 2, 'third-person': 3}
MOODS = ('indicative', 'subjunctive', 'imperative', 'infinitive')
VOICES = ('active', 'passive')
PARTICIPLE_TENSES = {'present': 'present', 'perfect': 'past', 'future': 'future'}

# 変化表の中で、変化形ではないもの・扱わないもの
SKIP_FORM_TAGS = {'canonical', 'table-tags', 'inflection-template', 'romanization', 'alternative',
                  'comparative', 'superlative', 'adverb', 'participle', 'gerund', 'supine',
                  'class', 'declension', 'pronominal', 'obsolete', 'archaic', 'Old-Latin',
                  'potential', 'sigmatic', 'aorist', 'noun-from-verb'}

# Wiktionary の品詞 → この辞書の品詞
NOMINAL_POS = {'noun': 'noun', 'name': 'noun', 'adj': 'adj', 'det': 'adj', 'num': 'adj',
               'pron': 'pronoun'}
INDECLINABLE_POS = {'adv': 'adv', 'conj': 'conj', 'intj': 'indecl', 'particle': 'indecl',
                    'num': 'indecl', 'det': 'indecl', 'pron': 'indecl', 'adj': 'indecl'}

# 日本語版 Wiktionary との突き合わせに使う品詞のまとまり
POS_GROUP = {'noun': 'noun', 'name': 'noun', 'verb': 'verb', 'adj': 'adj', 'det': 'adj',
             'num': 'adj', 'pron': 'pron', 'adv': 'adv', 'prep': 'prep', 'conj': 'conj',
             'intj': 'intj', 'particle': 'intj'}


def flatten(text):
    """突き合わせ用のキー: マクロン除去・小文字化・j→i"""
    return orthography.flat(text)


def _is_form_of(entry):
    """すべての語義が他の語の変化形・異形を指している項目"""
    senses = entry.get('senses', [])
    return bool(senses) and all('form_of' in s or 'alt_of' in s for s in senses)


def _participle_tense(tags, base):
    for tag in ('future', 'perfect', 'present'):
        if tag in tags:
            return PARTICIPLE_TENSES[tag]
    # 時制のタグが無いものは語尾で判定する (動形容詞 -ndus は未来)
    if base.endswith(('ndus', 'ūrus')):
        return 'future'
    if base.endswith(('ns', 'ēns', 'āns')):
        return 'present'
    return 'past'


# 見出し語として立っている分詞 (mortuus など) は form_of が無く、語源欄に元の動詞が書いてある
ETYMOLOGY_PARTICIPLE = re.compile(r'\bparticiple of (\w+)')


def _participle_verbs(entry):
    verbs = [f['word'] for s in entry.get('senses', []) for f in s.get('form_of', [])]
    if not verbs:
        m = ETYMOLOGY_PARTICIPLE.search(entry.get('etymology_text') or '')
        if m:
            verbs = [m.group(1)]
    return verbs


def _sense_tags(entry):
    return set(t for s in entry.get('senses', []) for t in s.get('tags', []))


def canonical(entry):
    for form in entry.get('forms', []):
        if 'canonical' in form.get('tags', []):
            return form['form']
    for head in entry.get('head_templates', []):
        expansion = head.get('expansion', '')
        if expansion:
            return expansion.split()[0]
    return entry['word']


def english_glosses(entry, senses=None, limit=3):
    """語義の頭から最大 limit 個の語句を取り出す: 'to love, be fond of' → 'love,be fond of'"""
    glosses = []
    for sense in senses if senses is not None else entry.get('senses', []):
        for gloss in sense.get('glosses', [])[:1]:
            gloss = re.sub(r'\s*\(.*?\)', '', gloss)
            for chunk in re.split(r'[;,]', gloss):
                chunk = re.sub(r'^(to|a|an|the) ', '', chunk.strip().rstrip('.:'), flags=re.I).strip()
                if chunk and chunk not in glosses:
                    glosses.append(chunk)
                if len(glosses) >= limit:
                    return ','.join(glosses)
    return ','.join(glosses)


# 日本語版で「〜の変化形」を説明している語義 (訳語ではない)
FORM_DESCRIPTION = re.compile(r'の[^。]{0,40}(形|分詞|不定法|命令法|接続法|直説法)$')


def japanese_gloss(entry, limit=4):
    """日本語版 Wiktionary の項目から訳語を取り出す: '道、道路、通路。' → '道,道路,通路'"""
    glosses = []
    for sense in entry.get('senses', []):
        for gloss in sense.get('glosses', [])[:1]:
            for sentence in re.split(r'[。．]\s*', gloss.strip()):
                sentence = re.sub(r'^[（(][^）)]*[）)]\s*', '', sentence.strip())  # 先頭の注記
                if not sentence or FORM_DESCRIPTION.search(sentence) or '"' in sentence:
                    continue
                for g in re.split(r'[、,，;；]', sentence):
                    g = g.strip()
                    if g and g not in glosses:
                        glosses.append(g)
        if len(glosses) >= limit:
            break
    return ','.join(glosses[:limit])


def ja_key(entry):
    return (flatten(entry['word']), POS_GROUP.get(entry.get('pos')))


def _table_forms(entry):
    for form in entry.get('forms', []):
        tags = set(form.get('tags', []))
        surface = form['form'].strip()
        if not surface or tags & SKIP_FORM_TAGS or surface in ('-', '—'):
            continue
        if len(surface.split()) > 2:  # 3語以上の複合形は辞書引きできないので除く
            continue
        yield surface, tags


def _lemma_genders(entry):
    tags = _sense_tags(entry)
    for form in entry.get('forms', []):
        if 'canonical' in form.get('tags', []):
            tags |= set(form['tags'])
    genders = [g for tag, g in GENDERS.items() if tag in tags]
    if not genders:
        for head in entry.get('head_templates', []):
            m = re.match(r'\S+ ((?:[mfn](?: or |, | ))*[mfn])\b', head.get('expansion', ''))
            if m:
                genders = re.findall(r'[mfn]', m.group(1))
    return genders or ['m']


def _nominal_features(entry, default_genders):
    """変化表から {表層形: [(格, 数, 性), ...]} を作る"""
    table = {}
    for surface, tags in _table_forms(entry):
        cases = [c for tag, c in CASES.items() if tag in tags]
        numbers = [n for tag, n in NUMBERS.items() if tag in tags]
        if not cases or not numbers:
            continue
        genders = [g for tag, g in GENDERS.items() if tag in tags] or default_genders
        cng = table.setdefault(surface, [])
        for case in cases:
            for number in numbers:
                for gender in genders:
                    if (case, number, gender) not in cng:
                        cng.append((case, number, gender))
    return table


def _tense(tags):
    # 未来完了は 'future' と 'perfect' の2つのタグで表される
    if 'pluperfect' in tags:
        return 'past-perfect'
    if 'perfect' in tags:
        return 'future-perfect' if 'future' in tags else 'perfect'
    for tense in ('future', 'imperfect', 'present'):
        if tense in tags:
            return tense
    return None


# 完了受動は「完了受動分詞 + sum」の説明文で書かれているので、sum の変化形と組み合わせて作る
SUM_FORMS = {
    ('indicative', 'perfect'): ['sum', 'es', 'est', 'sumus', 'estis', 'sunt'],
    ('indicative', 'past-perfect'): ['eram', 'erās', 'erat', 'erāmus', 'erātis', 'erant'],
    ('indicative', 'future-perfect'): ['erō', 'eris', 'erit', 'erimus', 'eritis', 'erunt'],
    ('subjunctive', 'perfect'): ['sim', 'sīs', 'sit', 'sīmus', 'sītis', 'sint'],
    ('subjunctive', 'past-perfect'): ['essem', 'essēs', 'esset', 'essēmus', 'essētis', 'essent'],
}
PARTICIPLE_ENDINGS = {'sg': {'m': 'us', 'f': 'a', 'n': 'um'}, 'pl': {'m': 'ī', 'f': 'ae', 'n': 'a'}}


def _perfect_passive_forms(participle):
    if not participle.endswith('us'):
        return []
    stem = participle[:-2]
    result = []
    for (mood, tense), sum_forms in SUM_FORMS.items():
        for k, sum_form in enumerate(sum_forms):
            number = 'sg' if k < 3 else 'pl'
            for gender, ending in PARTICIPLE_ENDINGS[number].items():
                result.append(('%s%s %s' % (stem, ending, sum_form),
                               {'mood': mood, 'tense': tense, 'voice': 'passive',
                                'person': k % 3 + 1, 'number': number, 'gender': gender}))
    return result


def _verb_features(entry):
    result = []
    for form in entry.get('forms', []):
        tags = set(form.get('tags', []))
        if {'participle', 'passive', 'perfect'} <= tags and form['form'] != '-' and \
           not tags & {'future', 'potential'}:
            result += _perfect_passive_forms(form['form'])
    for surface, tags in _table_forms(entry):
        moods = [m for m in MOODS if m in tags]
        tense = _tense(tags)
        if not moods or not tense:
            continue
        feature = {'mood': moods[0], 'tense': tense,
                   'voice': 'passive' if 'passive' in tags else 'active'}
        if moods[0] != 'infinitive':
            persons = [p for tag, p in PERSONS.items() if tag in tags]
            numbers = [n for tag, n in NUMBERS.items() if tag in tags]
            if not persons or not numbers:
                continue
            feature['person'] = persons[0]
            feature['number'] = numbers[0]
        result.append((surface, feature))
    return result


def _infinitive(entry):
    for form in entry.get('forms', []):
        tags = set(form.get('tags', []))
        if {'infinitive', 'present'} <= tags and 'passive' not in tags:
            return form['form']
    return None


def _gloss(entry, ja_glosses, senses=None):
    if ja_glosses:
        keys = [ja_key(entry)]
        if entry.get('pos') == 'verb' and _infinitive(entry):
            # 日本語版のラテン語動詞は、見出しが1人称単数のものと不定詞のものがある
            keys.append((flatten(_infinitive(entry)), 'verb'))
        for key in keys:
            if ja_glosses.get(key):
                return ja_glosses[key], 'ja'
    limit = 1 if entry.get('pos') == 'name' else 3  # 固有名詞の語義は説明文が続くことが多い
    return english_glosses(entry, senses, limit), 'en'


def convert_entry(entry, ja_glosses=None, participle_gloss=None):
    """Wiktionary の1項目を (lemma_info, [(表層形, features)]) に変換する。扱わない項目は None"""
    if entry.get('lang_code') != 'la':
        return None
    pos = entry.get('pos')
    tags = _sense_tags(entry)
    base = canonical(entry)

    # 分詞 (wiktextract では動詞の変化形の項目として入っている)
    if 'participle' in tags and pos in ('verb', 'adj'):
        verbs = _participle_verbs(entry)
        tense = _participle_tense(tags, base)
        table = _nominal_features(entry, ['m', 'f', 'n'])
        if not table:
            return None
        ja, lang = None, None
        if participle_gloss and verbs:
            ja = participle_gloss(verbs[0], tense)
            lang = 'ja' if ja else None
        if not ja:
            ja, lang = english_glosses(entry), 'en'
        info = {'pos': 'participle', 'base': base, 'pres1sg': verbs[0] if verbs else None,
                'tense': tense, 'ja': ja, 'gloss_lang': lang}
        return info, [(s, {'_': cng}) for s, cng in table.items()]

    # 比較級・最上級 (wiktextract では原級の変化形の項目として入っている)
    if ('comparative' in tags or 'superlative' in tags) and pos in ('adj', 'adv'):
        positives = [f['word'] for s in entry.get('senses', []) for f in s.get('form_of', [])]
        superlative = 'superlative' in tags
        ja, lang = None, None
        if ja_glosses and positives:
            positive_ja = ja_glosses.get((flatten(positives[0]), POS_GROUP[pos]))
            if positive_ja:
                ja = ('最も' if superlative else 'より') + positive_ja.split(',')[0]
                lang = 'ja'
        if not ja:
            label = '最上級' if superlative else '比較級'
            ja, lang = ('%s(%s)' % (positives[0], label) if positives else english_glosses(entry)), 'en'
        if pos == 'adv':
            return {'pos': 'adv', 'ja': ja, 'gloss_lang': lang}, [(base, {})]
        table = _nominal_features(entry, ['m', 'f', 'n'])
        if not table:
            return None
        info = {'pos': 'adj', 'base': base, 'rank': '++' if superlative else '+', 'ja': ja, 'gloss_lang': lang}
        return info, [(s, {'_': cng}) for s, cng in table.items()]

    if _is_form_of(entry):
        return None

    if pos == 'verb':
        forms = _verb_features(entry)
        if not forms:
            return None
        ja, lang = _gloss(entry, ja_glosses)
        return {'pos': 'verb', 'pres1sg': base, 'ja': ja, 'gloss_lang': lang}, forms

    if pos == 'prep':
        forms = []
        dominated = []
        for sense in entry.get('senses', []):
            for tag, case in (('with-accusative', 'Acc'), ('with-ablative', 'Abl'), ('with-genitive', 'Gen')):
                if tag in sense.get('tags', []) and case not in dominated:
                    dominated.append(case)
        if not dominated:
            return None
        ja, lang = _gloss(entry, ja_glosses)
        info = {'pos': 'preposition', 'base': base, 'ja': ja, 'gloss_lang': lang}
        forms = []
        for case, tag in zip(('Acc', 'Abl', 'Gen'), ('with-accusative', 'with-ablative', 'with-genitive')):
            if case not in dominated:
                continue
            feature = {'dominates': case}
            if lang == 'en':  # 英語の訳語は支配する格ごとの語義から作る
                feature['ja'] = english_glosses(entry, [s for s in entry['senses'] if tag in s.get('tags', [])])
            forms.append((base, feature))
        return info, forms

    if pos in NOMINAL_POS:
        genders = _lemma_genders(entry) if pos in ('noun', 'name') else ['m', 'f', 'n']
        table = _nominal_features(entry, genders)
        if table:
            ja, lang = _gloss(entry, ja_glosses)
            info = {'pos': NOMINAL_POS[pos], 'base': base, 'ja': ja, 'gloss_lang': lang}
            if pos in ('noun', 'name'):
                gen_sg = [s for s, cng in table.items() if any(c == 'Gen' and n == 'sg' for c, n, g in cng)]
                if gen_sg:
                    info['gen_sg'] = gen_sg[0]
            return info, [(s, {'_': cng}) for s, cng in table.items()]

    if pos in INDECLINABLE_POS:
        ja, lang = _gloss(entry, ja_glosses)
        return {'pos': INDECLINABLE_POS[pos], 'ja': ja, 'gloss_lang': lang}, [(base, {})]

    return None


def make_item(surface, info, features):
    """lemma_info と features から辞書の項目 (dict) を作る"""
    item = dict(info)
    item.update(features)
    item['surface'] = surface
    if '_' in item:
        item['_'] = [tuple(x) for x in item['_']]
    item['source'] = 'wiktionary'
    return item


# ----------------------------------------------------------------------
# 子孫語 (英語・ロマンス諸語に残った語)
#
# Wiktionary の descendants は木の形: {lang_code, word, raw_tags, descendants: [...]}。
# 借用は raw_tags の borrowed / learned borrowing、または「Borrowings」のまとまりの下に置かれる。
# 経由した語 (古フランス語 agu → 中期フランス語 aigu → フランス語 aigu) も残す

DESCENDANT_LANGS = ('en', 'fr', 'it', 'es')
MAX_DESCENDANTS_PER_LANG = 5
# ラテン語から語を継承しうる言語 (ロマンス諸語とその古い形)。ほかの言語 (英語など) に印の無いまま
# 載っている語は、書物からの借用とみなす
ROMANCE_CODES = {'fr', 'fro', 'frm', 'xno', 'it', 'it-old', 'es', 'osp', 'pt', 'roa-opt', 'gl', 'ca', 'oc',
                 'pro', 'ro', 'rup', 'sc', 'co', 'fur', 'rm', 'lld', 'dlm', 'ist', 'ast', 'an', 'lmo', 'lmo-old',
                 'pms', 'egl', 'lij', 'vec', 'nap', 'scn', 'frp', 'wa', 'pcd', 'nrf', 'la-vul', 'la-lat', 'la-med'}


def _descendant_kind(node):
    tags = set(node.get('raw_tags', [])) | set(node.get('tags', []))
    if any('semi-learned' in t for t in tags):
        return 'semi-learned'
    if any('borrow' in t for t in tags) or node.get('lang') == 'Borrowings':
        return 'borrowed'
    if 'calque' in tags:
        return 'calque'
    return None


def descendants_summary(entry):
    """[{lang, word, kind (inherited/borrowed/semi-learned/calque), via: [[lang_code, word], ...]}]"""
    found = []

    def walk(nodes, path, kind):
        for node in nodes:
            node_kind = _descendant_kind(node) or kind
            word = node.get('word')
            code = node.get('lang_code')
            if node_kind is None and code not in ROMANCE_CODES and code != 'unknown':
                node_kind = 'borrowed'
            step = [[code, word]] if word and code and code != 'unknown' else []
            if word and code in DESCENDANT_LANGS and not word.startswith('-') and not word.endswith('-'):
                found.append({'lang': code, 'word': word, 'kind': node_kind or 'inherited', 'via': path})
            walk(node.get('descendants', []), path + step, node_kind)

    walk(entry.get('descendants', []), [], None)
    # 言語ごとに、1語のもの (in medias res のような句でないもの) を先に、重複を除いて数を絞る
    result, seen = [], set()
    for lang in DESCENDANT_LANGS:
        items = [d for d in found if d['lang'] == lang]
        if any(' ' not in d['word'] for d in items):
            items = [d for d in items if ' ' not in d['word']]  # 1語のものがあれば句 (ad rem) は除く
        items.sort(key=lambda d: len(d['via']))
        n = 0
        for d in items:
            key = (lang, d['word'])
            if key in seen or n >= MAX_DESCENDANTS_PER_LANG:
                continue
            seen.add(key)
            result.append(d)
            n += 1
    return result
