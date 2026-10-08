#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の文の解析
#
# 辞書引き (greek.dictionary) と冠詞の処理だけをここで行い、並列・係り先・格の枠・日本語訳は
# ラテン語と共通の解析器 (latin.analyzer.analyze_words) を、ギリシア語の設定 (GREEK) で使う
#
import re

from core import analyzer as common
from core import language
from core.Word import Word
from . import dictionary, orthography, government, elision, dialect, morpheus

GREEK = language.Language(
    name='grc',
    and_words=('καί',),
    nor_words=('οὐδέ', 'μηδέ', 'οὔτε', 'μήτε'),
    or_words=('ἤ',),
    copulas=frozenset({'εἰμί'}),
    negations=frozenset({'οὐ', 'οὐκ', 'οὐχ', 'μή'}),
    vocative_particles=frozenset({'ὦ'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の', 'Dat': 'に', 'Voc': 'よ'},
    absolute_case='Gen',  # 属格独立
    # 属格を目的語に取る動詞 (知覚・接触・支配・記憶・欲求など)。主節の動詞がこれなら属格独立にしない
    absolute_case_verbs=frozenset({'ἀκούω', 'ἀκροάομαι', 'αἰσθάνομαι', 'ἅπτω', 'ἅπτομαι', 'ἄρχω', 'κρατέω',
                                   'βασιλεύω', 'ἡγέομαι', 'ἐπιθυμέω', 'ἐράω', 'μιμνῄσκω', 'μιμνήσκω', 'μνημονεύω',
                                   'ἐπιλανθάνομαι', 'τυγχάνω', 'φείδομαι', 'γεύομαι', 'μετέχω', 'δέομαι', 'πειράω',
                                   'κατηγορέω', 'ἀμελέω', 'φροντίζω', 'ἐπιμελέομαι', 'ἀντιλαμβάνω'}),
    lookup=dictionary.lookup,
    particle=government.particle,
    keep_genitive=government.keep_genitive,
    predicative_adjective=government.predicative_adjective,
)

# 語 (ギリシア文字と結合文字、語末のアポストロフィ) と句読点 (· は上の点、; は疑問符)
TOKEN = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+(?:[’'ʼ᾽][Ͱ-Ͽἀ-῿̀-ͯ]*)?"
                   r"|[.,·;·;:!]")
PUNCTUATION = set('.,·;·;:!')
SENTENCE_END = re.compile(r'(?<=[.;;··])\s+')

USE_MORPHEUS = True  # 辞書に無い語を Morpheus で解析する ($DRAGOMAN_DATA/grc/morpheus にビルドしてあれば)
ARTICLE_WINDOW = 4  # 冠詞と名詞の間に入りうる語の数 (ὁ ἀγαθὸς ἀνήρ, ὁ τοῦ βασιλέως υἱός)


def tokens(text):
    return TOKEN.findall(text)


def sentences(text):
    """テキストを文に分け、各文の語の列を返す"""
    for sentence in SENTENCE_END.split(text.strip()):
        if orthography.is_greek(sentence):
            yield tokens(sentence)


def _word(surface, next_surface=None):
    if surface in PUNCTUATION:
        return Word(surface, None)
    restored = elision.restore(surface, next_surface)
    if not restored and not dictionary.lookup(surface):
        # 辞書に無い語: 異形 (ἐξ → ἐκ)、Morpheus の解析 (叙事詩・方言の語形、加音の無い過去形)、
        # 規則による読み替え (ἀγορήν → ἀγοράν。greek/dialect.py。Morpheus が無いときの予備) の順
        restored = elision.variant(surface)
        if not restored:
            items = morpheus.analyze(surface) if USE_MORPHEUS else []
            if items:
                return Word(orthography.key(surface), items)
            restored = dialect.attic(surface)
    if restored:
        # 母音の省略 (ἀλλ’ → ἀλλά, ἐφ’ ἡμῖν → ἐπί): 元の形で引き、解析も元の形で
        surface = restored
    key = orthography.key(surface)
    if key.lower() in GREEK.negations:
        # 否定 (οὐ, οὐκ, οὐχ, μή): 述語を否定形にする副詞として (οὐκ, οὐχ は辞書に無い)
        return Word(key, [{'surface': key, 'pos': 'adv', 'ja': '〜ない', 'base': key}])
    items = dictionary.lookup(surface)
    for item in items:
        if item['pos'] == 'particle':
            item['pos'] = 'conj'  # δέ, γάρ, οὖν などの後置の小辞は接続詞と同じに扱う
    return Word(key, items)


def lookup_all(surfaces):
    # 母音の融合 (κἀγώ = καὶ ἐγώ) は元の2語に分ける
    expanded = []
    for s in surfaces:
        expanded.extend(elision.split_crasis(s) or (s,))
    if USE_MORPHEUS:
        # 辞書に無い語は Morpheus でまとめて解析しておく (1文につき1回の呼び出し)
        morpheus.analyze_many([s for s in expanded if s not in PUNCTUATION and not elision.is_elided(s)
                               and not dictionary.lookup(s)])
    words = [_word(s, expanded[i + 1] if i + 1 < len(expanded) else None) for i, s in enumerate(expanded)]
    for i, word in enumerate(words):
        word.index = i
    return words


def _cng(word, pos):
    return [cng for item in (word.items or []) if item.pos in pos for cng in (item._ or [])]


def _agree(a, b):
    return [x for x in a for y in b if x[0] == y[0] and x[1] == y[1] and (x[2] == y[2] or None in (x[2], y[2]))]


def attach_articles(words, trace):
    """冠詞を、後ろの一致する名詞 (無ければ名詞として使われた形容詞・分詞) の修飾語にする。
    冠詞は訳に出さず、付けた語の格の候補を冠詞と一致するものに絞る"""
    for i, word in enumerate(words):
        article = _cng(word, ('article',))
        if not article:
            continue
        head = None
        for j in range(i + 1, min(len(words), i + 1 + ARTICLE_WINDOW)):
            w = words[j]
            if w.items is None:
                break  # 句読点は越えない
            if w.items and w.items[0].pos == 'verb' and \
                    not any(item.pos == 'participle' or item.attrib('mood') in ('participle', 'infinitive')
                            for item in w.items):
                break  # 定動詞は越えない (分詞・不定詞とも読める語は越える: τῶν ἐχόντων)
            if _agree(article, _cng(w, ('noun', 'pronoun'))):
                head = w
                break
            if head is None and _agree(article, _cng(w, ('adj', 'participle'))):
                head = w  # 名詞が無ければこれ (οἱ ἀγαθοί「善い人々」)。後ろに名詞があればそちら
        if head is None:
            continue
        cng = _agree(_cng(head, ('noun', 'pronoun', 'adj', 'participle')), article)
        word.items = [item for item in word.items if item.pos == 'article']
        head.restrict_cases(list(dict.fromkeys(c for c, _, _ in cng)))
        head.add_modifier(word)
        trace.append('// ART#%d (%s) -> #%d (%s)' % (i, word.surface, head.index, head.surface))


FINITE_MOODS = ('indicative', 'imperative', 'optative', 'subjunctive')


def _finite(item):
    return item.pos == 'verb' and item.attrib('mood', 'indicative') in FINITE_MOODS


def choose_verb(words):
    """動詞の読みだけを持つ語が無い文では、定動詞の読みが一番の語のうち最後のものを動詞に絞る
    (πιστεύουσιν: 定動詞「信じる」3人称複数と、分詞 πιστεύων の与格複数)"""
    if any(w.items and all(item.pos == 'verb' for item in w.items) for w in words):
        return
    candidates = [w for w in words if w.items and _finite(w.items[0])]
    if candidates:
        candidates[-1].items = [item for item in candidates[-1].items if _finite(item)]


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    trace = []
    attach_articles(words, trace)
    choose_verb(words)
    with language.using(GREEK):
        return common.analyze_words(surfaces, words, word_details, trace)


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
