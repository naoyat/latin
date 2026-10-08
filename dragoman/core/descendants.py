#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 子孫語 (英語・フランス語などに残った語) の表示
#
#   acūtus   仏 aigu (継承: 古仏 agu → 中仏 aigu) / 英 acute (借用: 中英 acute)
#   fragilis 仏 frêle (継承: 古仏 fraile), fragile (借用) / 英 frail (借用: 古仏 fraile), fragile (借用)
#
from . import language
from .languages import lang_name

KIND_NAMES = {'inherited': '継承', 'borrowed': '借用', 'semi-learned': '半借用', 'calque': '翻訳借用'}
DEFAULT_LANGS = ('fr', 'en')
FALLBACK_LANGS = ('it', 'es')  # 仏・英が載っていない語 (cantō → 伊 cantare, 西 cantar)


def lemma_of(item):
    """項目の見出し語 (名詞・形容詞・分詞は base、動詞は直説法現在1人称単数)"""
    return item.attrib('pres1sg') if item.pos == 'verb' else (item.attrib('base') or item.attrib('surface'))


def describe(lemma, langs=DEFAULT_LANGS, source=None, fallback=FALLBACK_LANGS):
    """見出し語の子孫語を1行で。langs の言語が無ければ fallback の言語を。どれも無ければ None。
    source は子孫語を引く辞書 (descendants(lemma) を持つモジュール。既定はラテン語の Wiktionary 辞書)"""
    found = (source or language.current().dictionary).descendants(lemma)
    if fallback and not any(d['lang'] in langs for d in found):
        langs = fallback
    by_lang = {}
    for d in found:
        if d['lang'] in langs:
            via = [v for v in d['via'] if not (v[0] == d['lang'] and v[1] == d['word'])]
            route = ' → '.join('%s %s' % (lang_name(code), word) for code, word in via)
            note = KIND_NAMES.get(d['kind'], d['kind']) + (': ' + route if route else '')
            by_lang.setdefault(d['lang'], []).append('%s (%s)' % (d['word'], note))
    parts = ['%s %s' % (lang_name(lang), ', '.join(by_lang[lang])) for lang in langs if lang in by_lang]
    return ' / '.join(parts) if parts else None


def describe_word(word, langs=DEFAULT_LANGS, source=None, fallback=FALLBACK_LANGS):
    """語 (Word) の候補の見出し語ごとの子孫語。[(見出し語, 説明)]"""
    result, seen = [], set()
    for item in word.items or []:
        lemmas = [lemma_of(item)]
        if item.pos == 'participle':
            lemmas.append(item.attrib('pres1sg'))  # 分詞に無ければ元の動詞 (carpēns → carpō)
        for lemma in lemmas:
            if not lemma or lemma in seen:
                continue
            seen.add(lemma)
            text = describe(lemma, langs, source, fallback)
            if text:
                result.append((lemma, text))
                break
    return result
