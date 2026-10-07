#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語の文の解析
#
# 語を OSHB の解析で切れ目 (接続詞 ו、定冠詞 ה、前置詞 ב ל כ מ、本体、人称接尾辞) ごとの語に分け、
# 格の代わりの手がかりで名詞の「格」を絞ってから、並列・係り先・前置詞句・格の枠・日本語訳を共通の解析器
# (core/analyzer.py) をヘブライ語の設定 (HEBREW) で使う:
#   - 定冠詞 ה と目的語の標識 אֵת は名詞の修飾語として付け、訳に出さない。אֵת の後ろの名詞は対格
#   - 連語形 (construct) の名詞の後ろの名詞・人称接尾辞は属格「〜の」(בֵּית הַמֶּלֶךְ「王の家」、בְּנוֹ「彼の息子」)
#   - 動詞の人称接尾辞は対格「〜を」、前置詞の人称接尾辞は前置詞の目的語
#   - 主語は動詞と性・数が合う名詞 (ヘブライ語の動詞は性も変わる)
#   - 動詞の無い文 (名詞文) には見えない繋辞を補う (יְהוָה רֹעִי「主は私の羊飼い」)
#
import re

from core import analyzer as common
from core import language
from core.Word import Word
from . import dictionary, morphology, script

PUNCTUATION = {script.SOF_PASUQ: 'period', '.': 'period', ',': 'comma', ';': 'comma', ':': 'comma', '?': 'question',
               '!': 'period', '׀': None, '׀': None}
TOKEN = re.compile('[֑-ׂׄ-ׇא-ת͏‌‍]+|[׃.,;:?!]')
AND_WORDS = ('ו', 'וְ', 'וּ', 'וַ', 'וָ', 'וֶ', 'וִ', 'וֵ')


def _root_items(lemma):
    return []


HEBREW = language.Language(
    name='he',
    and_words=AND_WORDS,
    copulas=frozenset({'הָיָה'}),
    negations=frozenset({'לֹא', 'אַל', 'לֹא־', 'אַל־'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の', 'Dat': 'に', 'Voc': 'よ'},
    absolute_case=None,
    lookup=_root_items,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_follows_head=True,
    objects_follow_verb=True,
)


ATNAH = '\u0591'  # 節を前半と後半に分ける朗唱記号 (アトナハ ֑)


def tokens(text):
    """語 (マカフ ־ でつながった語は分ける) と句読点 (ソフ・パスーク ׃)。アトナハのある語の後ろには節の切れ目 (,) を"""
    out = []
    for token in TOKEN.findall(text.replace(script.MAQAF, ' ')):
        out.append(token)
        if ATNAH in token:
            out.append(',')
    return out


def sentences(text):
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


def _words(token, ix):
    """1語 → 切れ目ごとの Word のリスト"""
    if token in PUNCTUATION:
        word = Word(token, None)
        word.token_ix = ix
        return [word]
    found = morphology.analyses(token)
    if not found:
        word = Word(script.pointed(token), [])
        word.token_ix = ix
        return [word]
    out = []
    for k, (surface, item) in enumerate(morphology.segments(found[0])):
        word = Word(surface, [item])
        word.token_ix = ix
        # 同じ綴りで連語形の解析もある名詞 (רוּחַ「霊」は絶対形と連語形が同じ形) は、その項目を持っておく
        construct = _construct_alternative(found, k)
        if construct is not None and item.get('state') == 'absolute':
            word.construct_item = construct
        out.append(word)
    return out


def _construct_alternative(found, k):
    """OSHB の解析の候補のうち、切れ目 k が連語形の名詞で、ほかの切れ目は1つ目の解析と同じもの (の項目)"""
    first = morphology.segments(found[0])
    for analysis in found[1:]:
        segments = morphology.segments(analysis)
        if len(segments) != len(first) or segments[k][1].get('state') != 'construct':
            continue
        if all(a[1]['pos'] == b[1]['pos'] for a, b in zip(first, segments)):
            return segments[k][1]
    return None


def choose_construct(words):
    """連語形とも読める名詞は、すぐ後ろ (冠詞を除く) が名詞なら連語形に (רוּחַ אֱלֹהִים「神の霊」)"""
    for i, word in enumerate(words):
        construct = getattr(word, 'construct_item', None)
        if construct is None:
            continue
        nxt = next((w for w in words[i + 1:] if w.items is not None and
                    not (w.items and w.items[0].pos == 'article')), None)
        if nxt is not None and nxt.items and nxt.items[0].pos == 'noun' and not nxt.items[0].attrib('suffix'):
            word.items = [type(word.items[0])(construct)]


def _nominal(word):
    return bool(word.items) and word.items[0].pos in ('noun', 'pronoun', 'adj', 'participle')


def attach_markers(words):
    """定冠詞 ה と目的語の標識 אֵת を後ろの名詞類の修飾語にする (訳には出さない)。אֵת の後ろは対格"""
    for i, word in enumerate(words):
        if not word.items or word.items[0].pos != 'article':
            continue
        target = next((w for w in words[i + 1:i + 4] if _nominal(w)), None)
        if target is None:
            continue
        if word.items[0].attrib('desc') == '目的語の標識':
            target.restrict_cases(('Acc',))
            # 並列した目的語 (אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ) はそれぞれの אֵת で
        else:
            target.items[0].item['definite'] = True
        target.add_modifier(word)


def mark_construct(words):
    """連語形の名詞の後ろの名詞・人称接尾辞を属格に。動詞の人称接尾辞は対格、前置詞の人称接尾辞は対格 (前置詞の目的語)"""
    for i, word in enumerate(words):
        if not word.items or getattr(word, 'attached_to', None) is not None:
            continue
        item = word.items[0]
        if item.attrib('suffix'):
            prev = next((w for w in reversed(words[:i]) if w.items and getattr(w, 'attached_to', None) is None), None)
            host = prev.items[0].pos if prev is not None else None
            word.restrict_cases(('Gen',) if host in ('noun', 'adj', 'participle') else ('Acc',))
            continue
        if item.pos in ('noun', 'adj', 'participle') and item.attrib('state') == 'construct':
            # すぐ後ろ (冠詞を除く) の名詞類だけ (動詞を越えない)
            nxt = next((w for w in words[i + 1:] if getattr(w, 'attached_to', None) is None), None)
            # 組んでいる相手を書いておく (解説の「連語形」の行に使う)
            if nxt is not None and nxt.items and nxt.items[0].attrib('suffix'):
                item.item['construct_with'] = ('suffix', nxt.surface, nxt.items[0].ja)
            elif nxt is not None and _nominal(nxt):
                item.item['construct_with'] = ('noun', nxt.surface, nxt.items[0].ja.split(',')[0])
            else:
                item.item['construct_with'] = ('none', '', '')
            if nxt is not None and _nominal(nxt) and not nxt.items[0].attrib('suffix'):
                for it in nxt.items:
                    if it._:
                        it._ = [('Gen',) + tuple(c[1:]) for c in it._ if c[0] in ('Nom', 'Acc')] or it._


def _finite(item):
    return item.pos == 'verb' and item.attrib('mood') in ('indicative', 'imperative', 'subjunctive')


def _free_nominals(words):
    """前置詞の目的語・修飾語・人称接尾辞を除いた名詞類の位置"""
    out = []
    after_preposition = False
    for i, word in enumerate(words):
        if not word.items or getattr(word, 'attached_to', None) is not None:
            continue
        item = word.items[0]
        if item.pos == 'preposition':
            after_preposition = True
            continue
        if item.pos in ('noun', 'pronoun') and not item.attrib('suffix'):
            if not after_preposition and item.attrib('state') != 'genitive':
                out.append(i)
            after_preposition = False
        elif item.pos not in ('adj', 'participle'):
            after_preposition = False
    return out


def choose_subject(words):
    """3人称の定動詞の主語を決める: 動詞の後ろ (無ければ前) の、性・数が合い、対格・属格に決まっていない最初の名詞類を
    主格に (וַיֹּאמֶר אֱלֹהִים「神は言った」。ヘブライ語の物語は 動詞-主語-目的語 の順で、目的語は אֵת で示されることが多い)。
    性の合わない名詞は主語にしない"""
    free = _free_nominals(words)
    for i, word in enumerate(words):
        if not word.items or not _finite(word.items[0]) or word.items[0].attrib('person') != 3:
            continue
        verb = word.items[0]
        gender, number = verb.attrib('gender'), verb.attrib('number')

        def agrees(c):
            return c[0] == 'Nom' and c[1] == number and (gender is None or c[2] in (gender, None))
        nxt = next((j for j in range(i + 1, len(words)) if _finite_word(words[j])), len(words))
        prv = next((j for j in range(i - 1, -1, -1) if _finite_word(words[j])), -1)
        candidates = [j for j in free if i < j < nxt] + [j for j in reversed(free) if prv < j < i]
        for j in candidates:
            item = words[j].items[0]
            if any(agrees(c) for c in item._ or []):
                item._ = [c for c in item._ if agrees(c)]
                break


def _finite_word(word):
    return bool(word.items) and _finite(word.items[0])


COPULA = {'pos': 'verb', 'pres1sg': 'הָיָה', 'base': 'הָיָה', 'ja': 'ある,いる', 'gloss_lang': 'ja', 'voice': 'active',
          'mood': 'indicative', 'tense': 'present', 'person': 3, 'number': 'sg', 'desc': '名詞文 (繋辞なし)'}


def supply_copula(words):
    """動詞の無い節 (名詞文) に見えない繋辞を補う: 主格に読める名詞類が2つ以上あれば、最初のものの後ろに。
    節は句読点 (アトナハの切れ目を含む) で区切る"""
    out, clause = [], []
    for word in words:
        if word.items is None:
            out += _supply_copula(clause) + [word]
            clause = []
        else:
            clause.append(word)
    return out + _supply_copula(clause)


def _supply_copula(words):
    """節の、最初の定動詞より前 (定動詞が無ければ全体) に主格に読める名詞類が2つ以上あり、その定動詞が主語を取らない
    (1・2人称の) ときに補う (יְהוָה רֹעִי לֹא אֶחְסָר「主は私の羊飼い、私は乏しくない」)"""
    first = next((i for i, w in enumerate(words) if w.items and w.items[0].pos == 'verb'
                  and w.items[0].attrib('mood') != 'infinitive'), None)
    if first is not None and words[first].items[0].attrib('person') == 3:
        return words
    if first is not None:
        while first > 0 and words[first - 1].items and words[first - 1].items[0].pos == 'adv':
            first -= 1  # 動詞の前の否定・副詞 (לֹא אֶחְסָר) は動詞の側に
    head = words if first is None else words[:first]
    free = [i for i, w in enumerate(head) if _nominal(w) and getattr(w, 'attached_to', None) is None
            and any(c[0] == 'Nom' for c in w.items[0]._ or [])]
    if len(free) < 2:
        return words
    at = free[0] + 1
    while at < len(head) and head[at].items and (head[at].items[0].attrib('suffix') or
                                                 any(c[0] == 'Gen' for c in head[at].items[0]._ or [])):
        at += 1  # 主語に掛かる属格・人称接尾辞の後ろへ
    copula = Word('(הוּא)', [dict(COPULA, surface='(הוּא)')])
    rest = [] if first is None else [Word(',', None)] + words[first:]
    return head[:at] + [copula] + head[at:] + rest


def mark_vocatives(words):
    """命令形 (2人称) の動詞の近くの固有名詞は呼びかけ「〜よ」(שְׁמַע יִשְׂרָאֵל「聞け、イスラエルよ」)"""
    for i, word in enumerate(words):
        if not word.items or word.items[0].pos != 'verb' or word.items[0].attrib('mood') != 'imperative' \
                or word.items[0].attrib('person') != 2:
            continue
        for other in words[max(0, i - 2):i + 3]:
            if other.items and other.items[0].attrib('proper') and getattr(other, 'attached_to', None) is None:
                other.items[0]._ = [('Voc',) + tuple(c[1:]) for c in other.items[0]._ if c[0] == 'Nom']


def lookup_all(surfaces):
    words = [w for ix, s in enumerate(surfaces) for w in _words(s, ix)]
    mark_vocatives(words)
    choose_construct(words)
    attach_markers(words)
    mark_construct(words)
    choose_subject(words)
    words = supply_copula(words)
    for i, word in enumerate(words):
        word.index = i
    return words


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(HEBREW):
        return common.analyze_words([w.surface for w in words], words, word_details, [])


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
