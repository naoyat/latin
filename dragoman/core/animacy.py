#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 生き物 (人・動物・神) を表す名詞か: 存在の文の「いる / ある」(森にはライオンがいる、部屋には机がある) を決めるのに使う
#
# 辞書の情報があればそれ (ロシア語は pymorphy3 の活動体)、無ければ訳語の最初のいくつかの語で推定する
# (日本語の訳語: 人, 王, 神, 息子, 少女, ライオン…、英語の訳語: man, king, god, son, lion…)
#
import re

# 末尾が合えばよい語 (商人, 女神, 少女, 歩兵) と、全体が合うときだけの1字の語 (子: 小冊子・椅子は除く)
JAPANESE_SUFFIXES = ('人', '者', '王', '神', '少年', '少女', '兵', '民', '主人', '奴隷', '農夫', '水夫', '息子', '動物',
                     '獣', '鳥', 'ライオン', '狼', '熊', '犬', '猫', '馬', '牛', '羊', '山羊', '象', '蛇', '竜')
JAPANESE_WORDS = ('子', '娘', '父', '母', '兄', '弟', '姉', '妹', '夫', '妻', '男', '女', '友', '敵', '客', '魚', '虫',
                  '鹿', '豚', '兄弟', '姉妹', '学生', '医者', '医師', '先生', '友人')
ENGLISH = {'man', 'men', 'woman', 'women', 'person', 'people', 'human', 'boy', 'girl', 'child', 'children', 'son',
           'daughter', 'father', 'mother', 'brother', 'sister', 'husband', 'wife', 'king', 'queen', 'prince',
           'princess', 'lord', 'master', 'servant', 'slave', 'soldier', 'warrior', 'farmer', 'sailor', 'poet',
           'teacher', 'student', 'friend', 'enemy', 'guest', 'citizen', 'god', 'goddess', 'deity', 'demon',
           'animal', 'beast', 'bird', 'fish', 'insect', 'horse', 'cow', 'ox', 'bull', 'sheep', 'goat', 'dog', 'cat',
           'lion', 'tiger', 'wolf', 'bear', 'deer', 'pig', 'elephant', 'snake', 'serpent', 'dragon', 'monkey',
           'youth', 'merchant', 'priest', 'sage', 'hero', 'chief', 'leader', 'ruler'}
PERSONAL_PRONOUNS = ('私', 'あなた', '彼', '彼女', '我々', '私たち', 'あなたたち', 'あなた方', '彼ら', '自分', '誰')
WORD = re.compile(r'[a-z]+')


def is_animate(item):
    """項目 (core.Item) が生き物を表すか"""
    if item.attrib('animate') is not None:
        return bool(item.attrib('animate'))
    glosses = [g.strip() for g in (item.ja or '').split(',')][:2]
    if item.pos == 'pronoun':
        return any(g in PERSONAL_PRONOUNS for g in glosses)
    if item.pos not in ('noun', 'name'):
        return False
    for gloss in glosses:
        if gloss.endswith(JAPANESE_SUFFIXES) or gloss in JAPANESE_WORDS:
            return True
        words = WORD.findall(gloss.lower())
        if words and (words[0] in ENGLISH or (len(words) > 1 and words[-1] in ENGLISH and words[0] in ('a', 'an', 'the'))):
            return True
    return False
