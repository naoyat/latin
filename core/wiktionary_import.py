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

from .keys import flat as key_of

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
    return key_of(text)


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


# 読点で切ったときに残る、訳語でない断片 (都市、特に、古代ギリシアの都市国家 → 「特に」)
GLOSS_FILLERS = {'特に', '主に', '例えば', 'また', 'および', '及び', 'すなわち', '即ち', 'など', '等', 'あるいは',
                 '或いは', 'または', '又は', 'ないし', '転じて', '比喩的に', '一般に'}


def _strip_leading_note(text):
    """先頭の括弧書きの注記を、入れ子の括弧ごと除く: '(女性形 (ἡ θεός) で) 女神' → '女神'"""
    if not text or text[0] not in '（(':
        return text
    depth = 0
    for i, c in enumerate(text):
        if c in '（(':
            depth += 1
        elif c in '）)':
            depth -= 1
            if depth == 0:
                return text[i + 1:].strip()
    return text


def japanese_gloss(entry, limit=4):
    """日本語版 Wiktionary の項目から訳語を取り出す: '道、道路、通路。' → '道,道路,通路'"""
    glosses = []
    for sense in entry.get('senses', []):
        for gloss in sense.get('glosses', [])[:1]:
            for sentence in re.split(r'[。．]\s*', gloss.strip()):
                sentence = _strip_leading_note(sentence.strip())  # 先頭の注記 (入れ子の括弧も)
                if not sentence or FORM_DESCRIPTION.search(sentence) or '"' in sentence:
                    continue
                for g in re.split(r'[、,，;；]', sentence):
                    g = g.strip()
                    if g and g not in glosses and g not in GLOSS_FILLERS:
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


def lemma_key(entry):
    """子孫語・語源の表の見出し語のキー: ページ名 (pater noster のような句は句のまま) のマクロンを除いた形"""
    return key_of(entry.get('word', ''), merge_uv=True)


def descendants_summary(entry, langs=DESCENDANT_LANGS, inheriting=ROMANCE_CODES):
    """[{lang, word, kind (inherited/borrowed/semi-learned/calque), via: [[lang_code, word], ...]}]。
    langs は集める言語、inheriting は元の言語から語を継承しうる言語 (ほかは印が無くても借用とみなす)"""
    found = []

    def walk(nodes, path, kind):
        for node in nodes:
            node_kind = _descendant_kind(node) or kind
            word = node.get('word')
            code = node.get('lang_code')
            if node_kind is None and code not in inheriting and code != 'unknown':
                node_kind = 'borrowed'
            step = [[code, word]] if word and code and code != 'unknown' else []
            if word and code in langs and not word.startswith('-') and not word.endswith('-'):
                found.append({'lang': code, 'word': word, 'kind': node_kind or 'inherited', 'via': path})
            walk(node.get('descendants', []), path + step, node_kind)

    walk(entry.get('descendants', []), [], None)
    # 言語ごとに、1語のもの (in medias res のような句でないもの) を先に、重複を除いて数を絞る
    result, seen = [], set()
    for lang in langs:
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


# ----------------------------------------------------------------------
# 語源 (祖語の系統・同源語・説明文)
#
# etymology_templates の inh (継承) / der (派生) / bor (借用) / root (語根) から系統を、cog から同源語を取る。
# 説明文 (etymology_text) は頭の「Etymology tree」の系統図を除いて、長ければ文の切れ目で切る

ETYMOLOGY_TEXT_LIMIT = 400
NARRATIVE_STARTS = ('From', 'Borrowed', 'Inherited', 'Learned', 'Derived', 'Compound', 'Univerbation', 'Calque',
                    'Back-formation', 'Alteration', 'Perfect', 'Present', 'Future', 'Diminutive', 'Frequentative',
                    'Possibly', 'Probably', 'Perhaps', 'Uncertain', 'Unknown', 'Ultimately', 'Of ', 'Clipping')
# テンプレートの名前 → 系統の種類 (inh+, lbor などの別名もまとめる)
ANCESTOR_TEMPLATES = {'inh': 'inh', 'inh+': 'inh', 'der': 'der', 'der+': 'der', 'bor': 'bor', 'bor+': 'bor',
                      'lbor': 'bor', 'slbor': 'bor', 'obor': 'bor', 'root': 'root'}
MAX_COGNATES = 12


def _template_gloss(args):
    return args.get('t') or args.get('gloss') or args.get('5') or ''


def _etymology_text(text):
    lines = [line.strip() for line in (text or '').split('\n') if line.strip()]
    if lines and lines[0] == 'Etymology tree':
        lines = lines[1:]
        # 系統図の行 (「Proto-Indo-European *ph₂tḗr」「Ancient Greek φιλοσοφία (philosophía)bor.」のような
        # 短い行) を、説明文らしい行 (From …, Borrowed from …) が来るまで飛ばす
        while lines and len(lines[0].split()) <= 6 and not lines[0].startswith(NARRATIVE_STARTS):
            lines = lines[1:]
    text = ' '.join(line for line in lines if line != 'Details')
    if len(text) > ETYMOLOGY_TEXT_LIMIT:
        cut = text.rfind('. ', 0, ETYMOLOGY_TEXT_LIMIT)
        text = text[:cut + 1] if cut > 0 else text[:ETYMOLOGY_TEXT_LIMIT] + '…'
    return text


def _parse_etymon(kind, spec, out):
    """新しい形式のテンプレート (ety, etymon) の '3' の値: 'grc:φιλόσοφος<t:lover of wisdom>' や
    'itc-pro:*genu<ety:inh<ine-pro:*ǵónu>>' (入れ子は1つ前の語の語源) を [種類, 言語, 語, 意味] にして out へ"""
    head, _, rest = spec.partition('<')
    lang, _, term = head.partition(':')
    if not (lang and term):
        return
    gloss = ''
    depth, i, parts, start = 0, 0, [], None
    rest = '<' + rest if rest else ''
    for i, c in enumerate(rest):  # 外側の <…> を1つずつ取り出す
        if c == '<':
            if depth == 0:
                start = i + 1
            depth += 1
        elif c == '>':
            depth -= 1
            if depth == 0 and start is not None:
                parts.append(rest[start:i])
    out.append([ANCESTOR_TEMPLATES.get(kind, kind), lang, term, ''])
    for part in parts:
        key, _, value = part.partition(':')
        if key in ('t', 'gloss'):
            out[-1][3] = value
        elif key == 'ety':
            nested_kind, _, nested = value.partition('<')
            _parse_etymon(nested_kind, nested[:-1] if nested.endswith('>') else nested, out)


def etymology_summary(entry):
    """{ancestors: [[種類, 言語, 語, 意味]], cognates: [[言語, 語, 翻字, 意味]], text}。何も無ければ None"""
    ancestors, cognates = [], []
    for t in entry.get('etymology_templates', []):
        name, args = t.get('name'), t.get('args', {})
        found = []
        if name in ANCESTOR_TEMPLATES and args.get('2') and args.get('3'):
            found = [[ANCESTOR_TEMPLATES[name], args['2'], args['3'], _template_gloss(args)]]
        elif name in ('ety', 'etymon') and args.get('2', '').startswith(':') and args.get('3'):
            _parse_etymon(args['2'][1:], args['3'], found)
        for item in found:
            # 同じ語が古い形式と新しい形式の両方で書かれていることがあるので、言語と語で重複を除く
            if not any(a[1] == item[1] and a[2] == item[2] for a in ancestors):
                ancestors.append(item)
        if name == 'cog' and args.get('1') and args.get('2') and len(cognates) < MAX_COGNATES:
            cognates.append([args['1'], args['2'], args.get('tr', ''), _template_gloss(args)])
    text = _etymology_text(entry.get('etymology_text'))
    if not (ancestors or cognates or text):
        return None
    return {'ancestors': ancestors, 'cognates': cognates, 'text': text}
