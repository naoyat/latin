#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語の語形の解析: OSHB の語形の符号 (HC/Td/Ncbsa, HVqw3ms) を、切れ目 (接頭辞・本体・人称接尾辞) ごとの
# 解析器 (core/) の項目 (dict) にする
#
#   וְהָאָרֶץ   → ו 接続詞「そして」 + ה 定冠詞 + אֶרֶץ 名詞 女性(両性)単数
#   וַיֹּאמֶר  → ו 接続詞 + אָמַר 動詞 カル態・連続未完了 (wayyiqtol: 物語の過去)・3人称男性単数「言った」
#
# 格の無い言語なので、名詞類は「主格か対格」の両方に読めるものにし (('Nom', 数, 性), ('Acc', 数, 性))、
# 目的語の標識 אֵת の後ろは対格、前置詞の後ろは前置詞句、連語形 (construct) の後ろの名詞は属格に、
# 文の解析 (hebrew/analyzer.py) で絞る
#
from . import dictionary, script

NUMBERS = {'s': 'sg', 'p': 'pl', 'd': 'du'}
GENDERS = {'m': ('m',), 'f': ('f',), 'b': ('m', 'f'), 'c': ('m', 'f')}
PERSONS = {'1': 1, '2': 2, '3': 3}
STATES = {'a': 'absolute', 'c': 'construct', 'd': 'determined'}
# 態の型 (binyan)。受動のもの
STEMS = {'q': 'qal', 'N': 'niphal', 'p': 'piel', 'P': 'pual', 'h': 'hiphil', 'H': 'hophal', 't': 'hithpael',
         'o': 'polel', 'O': 'polal', 'r': 'hithpolel', 'm': 'poel', 'M': 'poal', 'k': 'palel', 'K': 'pulal',
         'Q': 'qal passive', 'l': 'pilpel', 'L': 'polpal', 'f': 'hithpalpel', 'D': 'nithpael', 'j': 'pealal',
         'i': 'pilel', 'u': 'hothpaal', 'c': 'tiphil', 'v': 'hishtaphel', 'w': 'nithpalel', 'y': 'nithpoel',
         'z': 'hithpoel'}
PASSIVE_STEMS = {'N', 'P', 'H', 'Q', 'M', 'K', 'L', 'O'}
# 動詞の型 → (tense, mood)。wayyiqtol (連続未完了) は物語の過去、weqatal (連続完了) は未来・命令の続き
VERB_TYPES = {'p': ('perfect', 'indicative', 'qatal'), 'q': ('future', 'indicative', 'weqatal'),
              'i': ('present', 'indicative', 'yiqtol'), 'w': ('perfect', 'indicative', 'wayyiqtol'),
              'h': ('present', 'imperative', 'cohortative'), 'j': ('present', 'imperative', 'jussive'),
              'v': ('present', 'imperative', 'imperative'), 'a': ('present', 'infinitive', 'infinitive absolute'),
              'c': ('present', 'infinitive', 'infinitive construct')}
# 接頭辞・前置詞の訳 (OSHB の lemma の文字、または独立した前置詞の見出し語の番号)
PREFIXES = {'c': ('conj', 'そして,〜と'), 'd': ('article', ''), 'i': ('adv', '〜か (疑問)'),
            's': ('conj', '〜するところの')}
PREPOSITIONS = {'b': '〜で,〜の中で,〜によって', 'l': '〜に,〜のために', 'k': '〜のように', 'm': '〜から',
                '413': '〜へ', '5921a': '〜の上に,〜について', '5973a': '〜とともに', '854': '〜とともに',
                '996': '〜の間に', '5704': '〜まで', '8478a': '〜の下に', '310': '〜の後に', '4480': '〜から',
                '3644': '〜のように', '5048': '〜の前に'}
PARTICLES = {'a': ('adv', '実に'), 'e': ('adv', 'どうか'), 'i': ('adv', '〜か (疑問)'), 'j': ('adv', '見よ'),
             'm': ('adv', '〜'), 'n': ('adv', '〜ない'), 'o': ('object', ''), 'r': ('conj', '〜するところの')}
PERSONAL = {(1, 'sg'): '私', (2, 'sg'): 'あなた', (3, 'sg'): '彼', (1, 'pl'): '私たち', (2, 'pl'): 'あなたたち',
            (3, 'pl'): '彼ら'}
NOMINAL_CASES = ('Nom', 'Acc')


def _cngs(gender, number, cases=NOMINAL_CASES):
    number = NUMBERS.get(number, 'sg')
    return [(case, number, g) for case in cases for g in GENDERS.get(gender, ('m', 'f'))]


# 訳語を手で決める見出し語 (神の名は伝統に従って「主」)
GLOSSES = {'3068': '主 (ヤハウェ)', '3069': '主 (ヤハウェ)', '136': '主 (アドナイ)'}


def _lemma(aug):
    entry = dict(dictionary.lexicon(aug) or {})
    if aug in GLOSSES:
        entry.update(ja=GLOSSES[aug], gloss_lang='ja')
    return entry.get('word') or aug, entry.get('ja') or aug, entry.get('gloss_lang', 'en'), entry.get('xlit', '')


def _personal(code):
    """人称・性・数 (3ms) → (人称, 性, 数)"""
    person = PERSONS.get(code[0:1])
    return person, code[1:2], code[2:3]


def segment_item(code, lemma, surface):
    """切れ目1つの符号 (Ncbsa, Vqw3ms, R, Td, Sp3ms) と見出し語 → 項目 (dict)"""
    kind = code[:1]
    item = {'surface': surface, 'source': 'oshb', 'morph': code}
    if lemma in PREFIXES and kind in 'CT' and code[:2] != 'To':
        pos, ja = PREFIXES[lemma]
        return dict(item, pos=pos, base=surface, ja=ja, gloss_lang='ja')
    if kind == 'R':
        ja = PREPOSITIONS.get(lemma) or _lemma(lemma)[1]
        word = surface if lemma in PREPOSITIONS and len(lemma) == 1 else _lemma(lemma)[0]
        return dict(item, pos='preposition', base=word, dominates='Acc', ja=ja, gloss_lang='ja')
    if kind == 'C':
        return dict(item, pos='conj', base=surface, ja='そして,〜と' if lemma == 'c' else _lemma(lemma)[1],
                    gloss_lang='ja' if lemma == 'c' else _lemma(lemma)[2])
    if kind == 'T':
        pos, ja = PARTICLES.get(code[1:2], ('adv', ''))
        if code[1:2] == 'd':
            return dict(item, pos='article', base=surface, ja='', gloss_lang='ja')
        if code[1:2] == 'o':
            # 目的語の標識 אֵת: 後ろの名詞を対格にして、冠詞と同じく名詞に付け、訳には出さない
            return dict(item, pos='article', base='אֵת', ja='', gloss_lang='ja', desc='目的語の標識')
        word, gloss, lang, _ = _lemma(lemma)
        return dict(item, pos=pos, base=word, ja=ja or gloss, gloss_lang='ja' if ja else lang)
    if kind == 'D':
        word, gloss, lang, _ = _lemma(lemma)
        return dict(item, pos='adv', base=word, ja=gloss, gloss_lang=lang)
    if kind == 'S':
        if code[1:2] == 'p':
            person, gender, number = _personal(code[2:])
            ja = PERSONAL.get((person, NUMBERS.get(number, 'sg')), '彼')
            if person == 3 and gender == 'f':
                ja = '彼女' if number == 's' else '彼女ら'
            return dict(item, pos='pronoun', base=surface, ja=ja, gloss_lang='ja', suffix=True,
                        person=person, _=_cngs(gender, number, ('Gen', 'Acc')))
        return dict(item, pos='adv', base=surface, ja='〜の方へ' if code[1:2] == 'd' else '', gloss_lang='ja')
    word, gloss, lang, xlit = _lemma(lemma)
    # 見出し語は転写を添えて表示する (ʾāmar אָמַר)
    item.update(base='%s %s' % (xlit, script.isolate(word)) if xlit else word, ja=gloss, gloss_lang=lang,
                xlit=xlit, lemma=lemma, word=word)
    if kind == 'N':
        gender, number, state = (code[2:3], code[3:4], code[4:5]) if code[1:2] != 'p' else ('', '', '')
        item.update(pos='noun', state=STATES.get(state, 'absolute'), _=_cngs(gender, number))
        if lemma == '430' and number == 'p':
            item['_'] += _cngs(gender, 's')  # אֱלֹהִים「神」は形が複数でも単数の動詞を取る (尊厳の複数)
        if code[1:2] == 'p':
            item['proper'] = True
        return item
    if kind == 'A':
        gender, number, state = code[2:3], code[3:4], code[4:5]
        item.update(pos='adj', state=STATES.get(state, 'absolute'), _=_cngs(gender, number))
        if code[1:2] in 'co':
            item['desc'] = '数詞'
        return item
    if kind == 'P':
        sub = code[1:2]
        if sub == 'p':
            person, gender, number = _personal(code[2:])
            ja = PERSONAL.get((person, NUMBERS.get(number, 'sg')), gloss)
            return dict(item, pos='pronoun', ja=ja, gloss_lang='ja', person=person, _=_cngs(gender, number))
        if sub == 'd':
            gender, number = code[2:3], code[3:4]
            return dict(item, pos='adj', desc='指示代名詞', _=_cngs(gender, number))
        if sub == 'r':
            return dict(item, pos='conj', ja='〜するところの', gloss_lang='ja')
        return dict(item, pos='pronoun', _=_cngs('', ''))
    if kind == 'V':
        stem, vtype = code[1:2], code[2:3]
        voice = 'passive' if stem in PASSIVE_STEMS else 'active'
        item.update(pres1sg=word, stem=STEMS.get(stem, stem), voice=voice)
        if vtype in 'rs':
            gender, number, state = code[3:4], code[4:5], code[5:6]
            item.update(pos='participle', tense='present', voice='passive' if vtype == 's' else voice,
                        state=STATES.get(state, 'absolute'), _=_cngs(gender, number))
            return item
        tense, mood, form = VERB_TYPES.get(vtype, ('present', 'indicative', vtype))
        item.update(pos='verb', tense=tense, mood=mood, form=form)
        if word == 'הָיָה':
            item['existential'] = True  # 主語だけなら存在 (יְהִי אוֹר「光あれ」)
        if mood not in ('infinitive',):
            person, gender, number = _personal(code[3:])
            item.update(person=person or 2, gender=GENDERS.get(gender, ('m', 'f'))[0] if gender in 'mf' else None,
                        number=NUMBERS.get(number, 'sg'))
        return item
    return dict(item, pos='adv', base=surface, ja=gloss, gloss_lang=lang)


def analyses(word):
    """語 (母音記号付き、朗唱記号はあってもよい) → OSHB の解析の候補 [{segments, lemmas, morph, count}]。
    ヘブライ語 (H) をアラム語 (A) より先に、多いものから"""
    found = dictionary.forms(word)
    return sorted(found, key=lambda f: (not f['morph'].startswith('H'), -f['count']))


def segments(analysis):
    """解析1つ → [(切れ目の表記, 項目)]"""
    morph = analysis['morph'][1:]  # 先頭の言語 (H / A) を除く
    codes = morph.split('/')
    out = []
    for surface, lemma, code in zip(analysis['segments'], analysis['lemmas'] + [None] * 4, codes):
        out.append((surface, segment_item(code, lemma, surface)))
    # 人称接尾辞は lemma の列に無い (本体と同じ見出し語の後ろ)
    for surface, code in zip(analysis['segments'][len(out):], codes[len(out):]):
        out.append((surface, segment_item(code, None, surface)))
    return out
