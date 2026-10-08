#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヒンディー語の語形の解析: Wiktionary の変化表から作った語形の辞書 (hindi/dictionary.py) の読みを、
# 解析器 (core/) の項目 (dict) にする
#
#   लड़के   → noun लड़का「少年」 直格複数 / 斜格単数 / 呼格単数
#   पढ़ता   → verb पढ़ना「読む」 未完了分詞 (習慣) 男性単数
#   मैंने   → pronoun मैं「私」 能格 (ने の付いた形)
#
# 格は、直格 (主語・目的語) を ('Nom', 'Acc')、斜格 (後置詞の前) を 'Obl' とし、後置詞の働きは文の解析
# (hindi/analyzer.py) で決める (ने → 主語、को → 目的語・与格、का/की/के → 属格、में など → 後置詞句)
#
import functools
import re

from . import dictionary, script

NUMBERS = {'singular': 'sg', 'plural': 'pl'}
PERSONS = {'first-person': 1, 'second-person': 2, 'third-person': 3}

# 後置詞 (1語のもの): 書かれた形 → (転写, 訳)。का/की/के (属格) と ने・को は文の解析で特別に扱う
POSTPOSITIONS = {'ने': ('ne', '※能格の ne: 完了形の他動詞の主語'), 'को': ('ko', '〜を,〜に'), 'से': ('se', '〜から,〜で,〜より'),
                 'में': ('mẽ', '〜で,〜の中で'), 'पर': ('par', '〜の上で,〜に'), 'तक': ('tak', '〜まで'),
                 'का': ('kā', '※属格の kā「〜の」(後ろの男性単数の名詞に一致)'),
                 'की': ('kī', '※属格の kī「〜の」(後ろの女性名詞に一致)'),
                 'के': ('ke', '※属格の ke「〜の」(後ろの男性複数・斜格の名詞に一致)'),
                 'द्वारा': ('dvārā', '〜によって'), 'बिना': ('binā', '〜なしで')}
# 複合後置詞 (के / की / से + 語): 語の並び → (転写, 訳)
COMPOUND_POSTPOSITIONS = {
    ('के', 'लिए'): ('ke lie', '〜のために'), ('के', 'लिये'): ('ke liye', '〜のために'),
    ('के', 'बाद'): ('ke bād', '〜の後で'), ('के', 'साथ'): ('ke sāth', '〜とともに'),
    ('के', 'पास'): ('ke pās', '〜のそばに,〜のところに'), ('के', 'बारे', 'में'): ('ke bāre mẽ', '〜について'),
    ('की', 'ओर'): ('kī or', '〜の方へ'), ('की', 'तरह'): ('kī tarah', '〜のように'),
    ('के', 'अंदर'): ('ke andar', '〜の中に'), ('के', 'ऊपर'): ('ke ūpar', '〜の上に'),
    ('के', 'नीचे'): ('ke nīce', '〜の下に'), ('के', 'बीच'): ('ke bīc', '〜の間に'),
    ('के', 'सामने'): ('ke sāmne', '〜の前に'), ('के', 'पीछे'): ('ke pīche', '〜の後ろに'),
    ('के', 'कारण'): ('ke kāraṇ', '〜のせいで'), ('के', 'द्वारा'): ('ke dvārā', '〜によって'),
    ('से', 'पहले'): ('se pahle', '〜の前に'), ('के', 'पहले'): ('ke pahle', '〜の前に'),
    ('के', 'बिना'): ('ke binā', '〜なしで'), ('के', 'अनुसार'): ('ke anusār', '〜によれば'),
    ('के', 'खिलाफ़'): ('ke xilāf', '〜に反して'), ('के', 'ख़िलाफ़'): ('ke xilāf', '〜に反して'),
    ('के', 'दौरान'): ('ke daurān', '〜の間に'), ('की', 'वजह', 'से'): ('kī vajah se', '〜のせいで'),
}
FUNCTION_WORDS = {
    'और': ('conj', 'aur', 'そして,〜と'), 'या': ('conj', 'yā', 'または'), 'लेकिन': ('conj', 'lekin', 'しかし'),
    'मगर': ('conj', 'magar', 'しかし'), 'परंतु': ('conj', 'parantu', 'しかし'), 'कि': ('conj', 'ki', '〜ということ'),
    'क्योंकि': ('conj', 'kyõki', 'なぜなら'), 'अगर': ('conj', 'agar', 'もし'), 'यदि': ('conj', 'yadi', 'もし'),
    'तो': ('conj', 'to', 'それなら,〜は'), 'जब': ('conj', 'jab', '〜するとき'), 'तब': ('adv', 'tab', 'そのとき'),
    'जो': ('conj', 'jo', '〜するところの'), 'तथा': ('conj', 'tathā', 'そして,〜と'), 'एवं': ('conj', 'evam', 'そして,〜と'),
    'नहीं': ('adv', 'nahī̃', '〜ない'), 'न': ('adv', 'na', '〜ない'), 'मत': ('adv', 'mat', '〜するな'),
    'भी': ('adv', 'bhī', '〜も'), 'ही': ('adv', 'hī', '〜こそ,〜だけ'), 'तो': ('adv', 'to', '〜は'),
    'बहुत': ('adv', 'bahut', 'とても'), 'आज': ('adv', 'āj', '今日'), 'कल': ('adv', 'kal', '昨日,明日'),
    'अब': ('adv', 'ab', '今'), 'यहाँ': ('adv', 'yahā̃', 'ここに'), 'वहाँ': ('adv', 'vahā̃', 'そこに'),
    'कहाँ': ('adv', 'kahā̃', 'どこに'), 'क्यों': ('adv', 'kyõ', 'なぜ'), 'कैसे': ('adv', 'kaise', 'どのように'),
    'क्या': ('adv', 'kyā', '〜か (疑問),何'), 'हाँ': ('adv', 'hā̃', 'はい'), 'जी': ('adv', 'jī', '(丁寧)'),
    'फिर': ('adv', 'phir', 'また,それから'), 'सिर्फ़': ('adv', 'sirf', '〜だけ'), 'केवल': ('adv', 'keval', '〜だけ'),
}
NEGATIONS = {'नहीं', 'न', 'मत'}
# 代名詞: 形 → (見出し語, 転写, 人称, 数, 格の種類)。格の種類: direct / oblique / ergative (ने 込み) / dative (को 込み)
PRONOUNS = {
    'मैं': ('मैं', 'ma͠i', 1, 'sg', 'direct'), 'मुझ': ('मैं', 'mujh', 1, 'sg', 'oblique'),
    'मैंने': ('मैं', 'ma͠ine', 1, 'sg', 'ergative'), 'मुझे': ('मैं', 'mujhe', 1, 'sg', 'dative'),
    'तू': ('तू', 'tū', 2, 'sg', 'direct'), 'तुझ': ('तू', 'tujh', 2, 'sg', 'oblique'), 'तूने': ('तू', 'tūne', 2, 'sg', 'ergative'),
    'तुझे': ('तू', 'tujhe', 2, 'sg', 'dative'),
    'हम': ('हम', 'ham', 1, 'pl', 'direct'), 'हमने': ('हम', 'hamne', 1, 'pl', 'ergative'),
    'हमें': ('हम', 'hamẽ', 1, 'pl', 'dative'),
    'तुम': ('तुम', 'tum', 2, 'pl', 'direct'), 'तुमने': ('तुम', 'tumne', 2, 'pl', 'ergative'),
    'तुम्हें': ('तुम', 'tumhẽ', 2, 'pl', 'dative'),
    'आप': ('आप', 'āp', 2, 'pl', 'direct'), 'आपने': ('आप', 'āpne', 2, 'pl', 'ergative'),
    'वह': ('वह', 'vah', 3, 'sg', 'direct'), 'वो': ('वह', 'vo', 3, 'sg', 'direct'), 'उस': ('वह', 'us', 3, 'sg', 'oblique'),
    'उसने': ('वह', 'usne', 3, 'sg', 'ergative'), 'उसे': ('वह', 'use', 3, 'sg', 'dative'),
    'यह': ('यह', 'yah', 3, 'sg', 'direct'), 'ये': ('यह', 'ye', 3, 'pl', 'direct'), 'इस': ('यह', 'is', 3, 'sg', 'oblique'),
    'इसने': ('यह', 'isne', 3, 'sg', 'ergative'), 'इसे': ('यह', 'ise', 3, 'sg', 'dative'),
    'वे': ('वह', 've', 3, 'pl', 'direct'), 'उन': ('वह', 'un', 3, 'pl', 'oblique'),
    'उन्होंने': ('वह', 'unhõne', 3, 'pl', 'ergative'), 'उन्हें': ('वह', 'unhẽ', 3, 'pl', 'dative'),
    'इन': ('यह', 'in', 3, 'pl', 'oblique'), 'इन्होंने': ('यह', 'inhõne', 3, 'pl', 'ergative'),
    'इन्हें': ('यह', 'inhẽ', 3, 'pl', 'dative'),
    'कौन': ('कौन', 'kaun', 3, 'sg', 'direct'), 'किस': ('कौन', 'kis', 3, 'sg', 'oblique'),
    'किसने': ('कौन', 'kisne', 3, 'sg', 'ergative'), 'किसे': ('कौन', 'kise', 3, 'sg', 'dative'),
    'कोई': ('कोई', 'koī', 3, 'sg', 'direct'), 'किसी': ('कोई', 'kisī', 3, 'sg', 'oblique'),
    'कुछ': ('कुछ', 'kuch', 3, 'sg', 'direct'), 'सब': ('सब', 'sab', 3, 'pl', 'direct'),
    'अपना': ('अपना', 'apnā', 3, 'sg', 'direct'),
}
PRONOUN_GLOSSES = {'मैं': '私', 'तू': 'お前', 'हम': '私たち', 'तुम': '君', 'आप': 'あなた', 'वह': '彼,彼女,それ',
                   'यह': 'これ,彼,彼女', 'कौन': '誰', 'कोई': '誰か', 'कुछ': '何か,いくらか', 'सब': 'すべて,みな'}
# 所有の形容詞 (属格の代名詞): 語幹 → (転写の語幹, 訳)。-ā / -ī / -e で後ろの名詞に一致
POSSESSIVES = {'मेर': ('mer', '私の'), 'तेर': ('ter', 'お前の'), 'हमार': ('hamār', '私たちの'), 'तुम्हार': ('tumhār', '君の'),
               'आपक': ('āpk', 'あなたの'), 'उसक': ('usk', '彼の,彼女の,その'), 'इसक': ('isk', 'この,これの'),
               'उनक': ('unk', '彼らの'), 'इनक': ('ink', 'これらの'), 'किसक': ('kisk', '誰の'), 'अपन': ('apn', '自分の')}
# 訳語を手で決める見出し語 (Wiktionary の英語の訳語の先頭が良くないもの)
GLOSSES = {'होना': 'ある,いる,〜である', 'करना': 'する', 'जाना': '行く', 'आना': '来る', 'देना': '与える',
           'लेना': '取る', 'पढ़ना': '読む,学ぶ', 'लिखना': '書く', 'देखना': '見る', 'खाना': '食べる',
           'पीना': '飲む', 'बोलना': '話す', 'कहना': '言う', 'सुनना': '聞く', 'रहना': '住む,とどまる', 'सोना': '眠る',
           'चलना': '歩く,進む', 'बैठना': '座る', 'मिलना': '会う,得られる', 'समझना': '理解する', 'जानना': '知る',
           'लड़का': '少年,息子', 'लड़की': '少女,娘', 'किताब': '本', 'घर': '家', 'पानी': '水', 'आदमी': '男,人',
           'औरत': '女', 'स्कूल': '学校', 'शहर': '町,都市', 'दोस्त': '友人', 'काम': '仕事', 'अच्छा': '良い',
           'बड़ा': '大きい', 'छोटा': '小さい', 'नया': '新しい', 'पुराना': '古い', 'सुंदर': '美しい', 'भारत': 'インド',
           'हिंदी': 'ヒンディー語', 'दिल्ली': 'デリー', 'पिता': '父', 'माता': '母', 'माँ': '母', 'भाई': '兄弟',
           'बहन': '姉妹', 'बच्चा': '子ども', 'गाड़ी': '車', 'खाना_noun': '食べ物', 'चाय': '茶', 'दूध': '牛乳',
           'फल': '果物', 'आम': 'マンゴー', 'पेड़': '木', 'फूल': '花', 'दिन': '日', 'रात': '夜', 'साल': '年',
           'सकना': '〜できる', 'चाहना': '望む', 'खेलना': '遊ぶ', 'एक': 'ある,一つの', 'बगीचा': '庭', 'बग़ीचा': '庭',
           'पत्र': '手紙', 'राम': 'ラーマ', 'सीता': 'シーター'}


def available():
    return dictionary.available()


def _gloss(lemma, pos, entry):
    if pos == 'noun' and lemma + '_noun' in GLOSSES:
        return GLOSSES[lemma + '_noun'], 'ja'
    if lemma in GLOSSES and not (pos == 'noun' and lemma == 'खाना'):
        return GLOSSES[lemma], 'ja'
    if entry:
        ja = entry['ja']
        m = re.match(r'(?:nuqtaless form of|alternative form of|alternative spelling of) (\S+)', ja)
        if m:  # बगीचा は「ヌクタの無い綴り」: 元の語 बग़ीचा の訳語を
            target = _entry(script.key(m.group(1)), pos)
            if target and target['ja'] != ja:
                return _gloss(script.key(m.group(1)), pos, target)
        if pos == 'name' or entry.get('pos') == 'name':
            roman = entry.get('roman') or script.translit(lemma)
            return roman[:1].upper() + roman[1:], 'en'  # 固有名詞は転写 (Wiktionary の英語の説明は使わない)
        return ja, entry['gloss_lang']
    return lemma, 'en'


@functools.lru_cache(maxsize=50000)
def _entry(lemma, pos):
    found = [e for e in dictionary.lemmas(lemma) if e['pos'] == pos]
    return max(found, key=lambda e: e['senses'] or 0) if found else None


def _base(entry, lemma):
    roman = (entry or {}).get('roman') or script.translit(lemma)
    return '%s %s' % (roman, lemma)


def _cases(tags):
    out = []
    if 'direct' in tags:
        out += ['Nom', 'Acc']
    if 'oblique' in tags:
        out.append('Obl')
    if 'vocative' in tags:
        out.append('Voc')
    return out


def _numbers(tags):
    return [n for t, n in NUMBERS.items() if t in tags] or ['sg', 'pl']


def _genders(tags, default):
    out = [g for t, g in (('masculine', 'm'), ('feminine', 'f')) if t in tags]
    return out or ([default] if default else ['m', 'f'])


def _nominal_items(word, readings):
    """名詞・形容詞の読み (同じ見出し語の読みをまとめて1項目に)"""
    out = {}
    for lemma, pos, tags in readings:
        if pos not in ('noun', 'name', 'adj', 'num', 'det', 'pronoun'):
            continue
        entry = _entry(lemma, pos)
        # 同じ綴りの名詞の性をすべて (साल「年」は男性、「サラノキ」は女性)
        genders = {e.get('gender') for e in dictionary.lemmas(lemma) if e['pos'] == pos and e.get('gender')}
        default_gender = next(iter(genders)) if len(genders) == 1 else None
        key = (lemma, pos)
        item = out.get(key)
        if item is None:
            ja, gloss_lang = _gloss(lemma, pos, entry)
            item = {'surface': word, 'pos': 'adj' if pos in ('adj', 'num', 'det') else 'noun', 'lemma': lemma,
                    'base': _base(entry, lemma), 'ja': ja, 'gloss_lang': gloss_lang,
                    'roman': script.translit_known(word, lemma, (entry or {}).get('roman')), 'compact': True, '_': []}
            if pos == 'name':
                item['proper'] = True
            out[key] = item
        if tags == {'lemma'}:
            cases, numbers, genders = ['Nom', 'Acc', 'Obl'], ['sg'], _genders(set(), default_gender)
            if pos in ('adj', 'num', 'det'):
                numbers, genders = ['sg', 'pl'], ['m', 'f']
        else:
            cases, numbers, genders = _cases(tags) or ['Nom', 'Acc', 'Obl'], _numbers(tags), \
                _genders(tags, default_gender)
        for c in cases:
            for n in numbers:
                for g in genders:
                    if (c, n, g) not in item['_']:
                        item['_'].append((c, n, g))
    return list(out.values())


def _verb_items(word, readings):
    """動詞の読み: 形の種類ごとに1項目"""
    out = []
    seen = set()
    for lemma, pos, tags in readings:
        if pos != 'verb':
            continue
        entry = _entry(lemma, 'verb')
        if 'stem' in tags:
            kind = 'stem'
        elif 'conjunctive' in tags:
            kind = 'conjunctive'
        elif 'infinitive' in tags:
            kind = 'infinitive'
        elif 'habitual' in tags:
            kind = 'habitual'
        elif 'perfective' in tags or 'perfect' in tags:
            kind = 'perfective'
        elif 'future' in tags and 'subjunctive' not in tags:
            kind = 'future'
        elif 'subjunctive' in tags:
            kind = 'subjunctive'
        elif 'imperative' in tags:
            kind = 'imperative'
        elif 'present' in tags:
            kind = 'present'
        elif 'imperfect' in tags:
            kind = 'past'
        elif 'counterfactual' in tags:
            continue  # 反実仮想 (पढ़ता「読んだなら」) は未完了分詞と同じ形なので分詞の読みに任せる
        elif tags == {'lemma'}:
            kind = 'infinitive'
        else:
            continue
        persons = [p for t, p in PERSONS.items() if t in tags]
        numbers = [n for t, n in NUMBERS.items() if t in tags]
        genders = [g for t, g in (('masculine', 'm'), ('feminine', 'f')) if t in tags]
        sig = (lemma, kind, tuple(persons), tuple(numbers), tuple(genders))
        if sig in seen:
            continue
        seen.add(sig)
        ja, gloss_lang = _gloss(lemma, 'verb', entry)
        item = {'surface': word, 'pos': 'verb', 'lemma': lemma, 'pres1sg': lemma, 'base': _base(entry, lemma),
                'ja': ja, 'gloss_lang': gloss_lang, 'roman': script.translit_known(word, lemma, (entry or {}).get('roman')),
                'compact': True,
                'form': kind, 'voice': 'active', 'mood': 'indicative', 'tense': 'present',
                'person': persons[-1] if persons else 3, 'number': numbers[0] if numbers else 'sg',
                'gender': genders[0] if len(genders) == 1 else None, 'persons': persons}
        if kind == 'imperative':
            item.update(mood='imperative', person=2)
        elif kind == 'future':
            item['tense'] = 'future'
        elif kind == 'perfective':
            item['tense'] = 'perfect'
        elif kind == 'past':
            item['tense'] = 'imperfect' if lemma != 'होना' else 'past'
        elif kind in ('stem', 'conjunctive', 'infinitive'):
            item['mood'] = 'infinitive' if kind == 'infinitive' else 'participle'
        if lemma == 'होना':
            item['existential'] = True
        out.append(item)
    return out


@functools.lru_cache(maxsize=50000)
def analyses(token):
    """語 → 項目 (dict) のリスト (先のものほど確からしい)"""
    word = script.key(token)
    out = []
    if word in POSTPOSITIONS:
        roman, ja = POSTPOSITIONS[word]
        out.append({'surface': word, 'pos': 'postposition', 'base': roman, 'ja': ja, 'gloss_lang': 'ja',
                    'roman': roman, 'compact': True, 'postposition': word})
    if word in FUNCTION_WORDS:
        pos, roman, ja = FUNCTION_WORDS[word]
        out.append({'surface': word, 'pos': pos, 'base': roman, 'ja': ja, 'gloss_lang': 'ja', 'roman': roman,
                    'compact': True})
    if word in PRONOUNS:
        lemma, roman, person, number, kind = PRONOUNS[word]
        cases = {'direct': ['Nom', 'Acc'], 'oblique': ['Obl'], 'ergative': ['Nom'], 'dative': ['Dat', 'Acc']}[kind]
        out.append({'surface': word, 'pos': 'pronoun', 'lemma': lemma, 'base': roman, 'roman': roman, 'compact': True,
                    'ja': PRONOUN_GLOSSES.get(lemma, lemma), 'gloss_lang': 'ja', 'person': person,
                    'pronoun_case': kind, '_': [(c, number, g) for c in cases for g in ('m', 'f')]})
    for stem, (roman, ja) in POSSESSIVES.items():
        for ending, gender, numbers, cases in (('ा', 'm', ['sg'], ['Nom', 'Acc']), ('ी', 'f', ['sg', 'pl'], ['Nom', 'Acc', 'Obl']),
                                                ('े', 'm', ['sg', 'pl'], ['Nom', 'Acc', 'Obl'])):
            if word == script.key(stem + ending):
                cngs = [(c, n, gender) for c in cases for n in numbers]
                if ending == 'े':
                    cngs = [c for c in cngs if not (c[0] in ('Nom', 'Acc') and c[1] == 'sg')]
                out.append({'surface': word, 'pos': 'adj', 'lemma': stem + 'ा', 'base': roman + 'ā', 'ja': ja,
                            'gloss_lang': 'ja', 'roman': script.translit(word), 'compact': True, 'possessive': True,
                            '_': cngs})
    readings = dictionary.forms(word)
    if not any(i['pos'] == 'pronoun' or i.get('possessive') for i in out):
        out += _verb_items(word, readings)
        out += _nominal_items(word, readings)
    if not out:
        out.append({'surface': word, 'pos': 'noun', 'lemma': word, 'base': script.translit(word),
                    'ja': script.translit(word), 'gloss_lang': 'en', 'roman': script.translit(word), 'compact': True,
                    'unknown': True, '_': [(c, n, g) for c in ('Nom', 'Acc', 'Obl') for n in ('sg',) for g in ('m', 'f')]})
    return out
