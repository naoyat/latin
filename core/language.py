#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析器 (core/analyzer.py) と訳 (core/Predicate.py など) の、言語ごとの設定
#
# 解析の骨組み (並列・係り先・格の枠・日本語訳) は言語に依存しないように書き、言語ごとに違う語 (接続詞・繋辞・
# 否定・呼びかけ) と、格 → 助詞の既定の対応をここに置く。解析中の言語は using() で切り替える
#
#   with language.using(GREEK):
#       analysis = analyzer.analyze_words(words)
#
# 各言語の設定は latin/profile.py (LATIN), greek/analyzer.py (GREEK), sanskrit/analyzer.py (SANSKRIT)。
# using() の外での既定はラテン語 (latin パッケージを読み込むと set_default される)
#
import contextlib
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Language:
    name: str
    and_words: tuple = ()          # 並列の「と」(A et B, et A et B)。最初のものを並列句の名前に使う
    nor_words: tuple = ()          # 否定の並列 (neque A neque B)
    or_words: tuple = ()           # 選択の並列 (aut A aut B)
    copulas: frozenset = frozenset()     # 繋辞の見出し語 (直説法現在1人称単数)
    negations: frozenset = frozenset()   # 否定の副詞 (小文字)
    vocative_particles: frozenset = frozenset()  # 呼びかけの間投詞 (ō)
    case_particles: dict = field(default_factory=dict)  # 格 → 既定の助詞
    absolute_case: str = 'Abl'     # 独立奪格の格 (ギリシア語は属格独立の 'Gen')
    absolute_case_verbs: frozenset = frozenset()  # その格を目的語に取る動詞 (主節の動詞がこれなら独立奪格にしない)
    lookup: object = None          # 見出し語から辞書の項目 (dict) を引く関数 (分詞の元の動詞の訳語など)
    particle: object = None        # 格の枠の語の助詞を文脈で決める関数 (case, obj, predicate) → 助詞 / None
    keep_genitive: object = None   # 名詞に掛けずに述語の枠に残す属格を決める関数 (words, ix) → bool
    predicative_adjective: object = None  # 名詞に掛けない述語的位置の形容詞を決める関数 (adj, noun) → bool
    lexicalized_participle: object = None  # 形容詞になった分詞か (base, 比較級の形のリスト) → bool
    dictionary: object = None      # 子孫語・語源を引く辞書 (descendants(lemma), etymology(lemma) を持つモジュール)
    pronoun_subject: bool = False  # 繋辞の文で代名詞も名詞と同じく主語になる (tat tvam asi, Он студент)
    genitive_follows_head: bool = False  # 属格は前の名詞にだけ掛かり、動詞を越えない (ロシア語の книга брата)
    genitive_precedes_head: bool = False  # 属格は後ろの名詞にだけ掛かる (ヒンディー語の लड़के की किताब「少年の本」)
    objects_follow_verb: bool = False  # 目的語が動詞の後ろに来る語順 (ロシア語)。2つの動詞の間の語を前の動詞に
    possessor_cases: tuple = ('Dat',)  # 繋辞の文で所有者を表す格 (mihi est liber「私には本がある」。サンスクリットは属格)

    def is_copula(self, pres1sg):
        return pres1sg in self.copulas

    def is_negation(self, surface):
        return surface.lower() in self.negations

    def is_nor(self, and_or_word):
        return and_or_word in self.nor_words


_current = None


def current():
    return _current


def set_default(language):
    """using() の外で使う言語"""
    global _current
    _current = language


@contextlib.contextmanager
def using(language):
    global _current
    saved = _current
    _current = language
    try:
        yield language
    finally:
        _current = saved
