#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Latin Dependency Treebank (LDT) 形式の品詞タグ
#
#   9文字: 品詞 人称 数 時制 法 態 性 格 比較   (使わない位置は '-')
#   例: n-s---fb-  名詞・単数・女性・奪格
#       v3sria---  動詞・3人称・単数・完了・直説法・能動
#
# Morpheus の解析結果 (Latin Macronizer の macrons.txt) と RFTagger の出力がこの形式
#
POS = {'n': 'noun', 'v': 'verb', 'a': 'adj', 'p': 'pronoun', 'd': 'adv', 'c': 'conj',
       'r': 'preposition', 'm': 'adj', 'i': 'indecl', 'e': 'indecl', 'u': 'punct', 'g': 'indecl',
       't': 'participle'}
NUMBERS = {'s': 'sg', 'p': 'pl'}
TENSES = {'p': 'present', 'i': 'imperfect', 'r': 'perfect', 'l': 'past-perfect',
          't': 'future-perfect', 'f': 'future'}
MOODS = {'i': 'indicative', 's': 'subjunctive', 'n': 'infinitive', 'm': 'imperative',
         'p': 'participle', 'd': 'gerund', 'g': 'gerundive', 'u': 'supine'}
VOICES = {'a': 'active', 'p': 'passive'}
GENDERS = {'m': 'm', 'f': 'f', 'n': 'n'}
CASES = {'n': 'Nom', 'g': 'Gen', 'd': 'Dat', 'a': 'Acc', 'b': 'Abl', 'v': 'Voc', 'l': 'Loc'}


def parse(tag):
    """タグを特徴の dict にする。不明な位置は含めない"""
    tag = tag.replace('.', '')
    if len(tag) < 9:
        tag = tag.ljust(9, '-')
    features = {}
    for key, table, ch in (('pos', POS, tag[0]), ('number', NUMBERS, tag[2]), ('tense', TENSES, tag[3]),
                           ('mood', MOODS, tag[4]), ('voice', VOICES, tag[5]), ('gender', GENDERS, tag[6]),
                           ('case', CASES, tag[7])):
        if ch in table:
            features[key] = table[ch]
    if tag[1] in '123':
        features['person'] = int(tag[1])
    # 分詞・動形容詞は格変化する語として扱う
    if features.get('pos') == 'verb' and features.get('mood') in ('participle', 'gerundive'):
        features['pos'] = 'participle'
    return features


def to_item(tag, lemma, surface):
    """タグからこの辞書の形式の項目を作る (訳語は無い)"""
    f = parse(tag)
    pos = f.get('pos', 'indecl')
    item = {'surface': surface, 'pos': pos, 'ja': lemma, 'gloss_lang': 'lemma', 'ldt': tag}
    if pos in ('noun', 'adj', 'pronoun', 'participle'):
        item['base'] = lemma
        if 'case' in f and 'number' in f:
            item['_'] = [(f['case'], f['number'], f.get('gender', 'm'))]
    elif pos == 'verb':
        item['pres1sg'] = lemma
        for key in ('mood', 'tense', 'voice', 'person', 'number'):
            if key in f:
                item[key] = f[key]
    return item


def item_matches(item, features):
    """辞書の項目がタグの特徴と矛盾しないか (タグが決めている格・数・時制などが合うか)
    性は資料によって扱いが違う (同じ語を中性とする辞書と、男性形の見出しで学習したタガーなど) ので見ない"""
    pos = features.get('pos')
    if pos in ('noun', 'adj', 'pronoun', 'participle'):
        case, number = features.get('case'), features.get('number')
        if not case:
            return False
        return any(c == case and (not number or n == number) for c, n, g in (item.get('_') or []))
    if pos == 'verb':
        if item.get('pos') != 'verb':
            return False
        return all(item.get(key) == features[key]
                   for key in ('tense', 'mood', 'person', 'number') if key in features and item.get(key) is not None)
    if pos in ('adv', 'conj'):
        # 語形変化しない小辞は資料によって副詞・接続詞の分類が揺れる (tamen, itaque など)
        return item.get('pos') in ('adv', 'conj')
    if pos == 'preposition':
        return item.get('pos') == pos
    return False
