#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの発音: SLP1 の文字列 → 音 (音素・長短・音節)
#
#   rāmo vanaṃ gacchati → rɑː.mo.ʋɐ.nɐŋ.gɐt.tʃʰɐ.ti (IPA)
#
# 母音の長短 (短 1 モーラ、長 2 モーラ。e ai o au は長い)、有気音、そり舌音、反舌の ṣ、
# 音節頭に立つ ṛ (母音)、ḥ (visarga: 前の母音を短く添えて rāmaḥ → rāmaha と読む伝統の読み方)、
# ṃ (anusvāra: 後ろの子音と同じ位置の鼻音) を扱う。
# 強勢は、現代のインドの読み方に近い「重い次末音節、無ければ前」の規則で置く (古典期の文に元の高低アクセントは書かれない)
#
from . import script

VOWELS = {'a': ('ɐ', 1), 'A': ('ɑː', 2), 'i': ('i', 1), 'I': ('iː', 2), 'u': ('u', 1), 'U': ('uː', 2),
          'f': ('r̩', 1), 'F': ('r̩ː', 2), 'x': ('l̩', 1), 'X': ('l̩ː', 2),
          'e': ('eː', 2), 'E': ('ɐi', 2), 'o': ('oː', 2), 'O': ('ɐu', 2)}
CONSONANTS = {
    'k': 'k', 'K': 'kʰ', 'g': 'g', 'G': 'gʱ', 'N': 'ŋ',
    'c': 'tʃ', 'C': 'tʃʰ', 'j': 'dʒ', 'J': 'dʒʱ', 'Y': 'ɲ',
    'w': 'ʈ', 'W': 'ʈʰ', 'q': 'ɖ', 'Q': 'ɖʱ', 'R': 'ɳ',
    't': 't̪', 'T': 't̪ʰ', 'd': 'd̪', 'D': 'd̪ʱ', 'n': 'n',
    'p': 'p', 'P': 'pʰ', 'b': 'b', 'B': 'bʱ', 'm': 'm',
    'y': 'j', 'r': 'r', 'l': 'l', 'v': 'ʋ', 'S': 'ʃ', 'z': 'ʂ', 's': 's', 'h': 'ɦ',
}
# ṃ の後ろの子音 → 同じ位置の鼻音
NASAL_OF = {}
for group, nasal in (('kKgGN', 'ŋ'), ('cCjJY', 'ɲ'), ('wWqQR', 'ɳ'), ('tTdDn', 'n'), ('pPbBm', 'm')):
    for c in group:
        NASAL_OF[c] = nasal


class Segment:
    """音素1つ。vowel なら mora (1/2)"""

    def __init__(self, ipa, slp1, vowel=False, mora=0):
        self.ipa = ipa
        self.slp1 = slp1
        self.vowel = vowel
        self.mora = mora

    def __repr__(self):
        return self.ipa


def segments(slp1, following=''):
    """語 (SLP1) → Segment のリスト。following は次の語 (語末の ṃ を次の語の頭の子音に合わせる)"""
    out = []
    word = slp1.replace("'", 'a')  # 語頭の a の省略 (ऽ) は a を戻して読む
    for i, c in enumerate(word):
        nxt = word[i + 1] if i + 1 < len(word) else following[:1]
        if c in VOWELS:
            ipa, mora = VOWELS[c]
            out.append(Segment(ipa, c, vowel=True, mora=mora))
        elif c in CONSONANTS:
            out.append(Segment(CONSONANTS[c], c))
        elif c == 'M':  # anusvāra
            out.append(Segment(NASAL_OF.get(nxt, 'm' if not nxt else 'ŋ'), c))
        elif c == 'H':  # visarga: h と前の母音の短い響き
            prev = next((s for s in reversed(out) if s.vowel), None)
            out.append(Segment('h', c))
            if i + 1 == len(word):
                echo = {'ɑː': 'ɐ', 'iː': 'i', 'uː': 'u', 'eː': 'e', 'oː': 'o', 'ɐi': 'i', 'ɐu': 'u'}
                ipa = echo.get(prev.ipa, prev.ipa) if prev else 'ɐ'
                out.append(Segment(ipa, 'echo', vowel=True, mora=0.5))
    return out


def syllabify(segs):
    """音節のリスト (各音節は Segment のリスト)"""
    vowel_ix = [i for i, s in enumerate(segs) if s.vowel]
    if not vowel_ix:
        return [segs] if segs else []
    sylls = []
    start = 0
    for n, v in enumerate(vowel_ix):
        if n + 1 < len(vowel_ix):
            nxt = vowel_ix[n + 1]
            cluster = nxt - v - 1
            end = v + 1 + max(0, cluster - 1)  # 子音1つは次の音節の頭、残りはこの音節の終わり
        else:
            end = len(segs)
        sylls.append(segs[start:end])
        start = end
    return sylls


def heavy(syll):
    """重い音節: 長母音 (2モーラ) か、子音で終わる"""
    vowel = next(s for s in syll if s.vowel)
    return vowel.mora >= 2 or not syll[-1].vowel


def stress_index(sylls):
    """強勢の位置: 次末音節が重ければそこ、そうでなければ前の重い音節 (4つ前まで)、無ければ最初"""
    n = len([s for s in sylls if any(x.vowel and x.mora >= 1 for x in s)])
    if n <= 1:
        return 0
    if heavy(sylls[n - 2]):
        return n - 2
    for k in range(n - 3, max(-1, n - 6), -1):
        if heavy(sylls[k]):
            return k
    return 0 if n < 4 else n - 4


def words(text):
    """テキスト → [(語の SLP1, 区切り)]。区切りは 'period' / 'comma' / None"""
    from .analyzer import tokens, PUNCTUATION
    out = []
    for token in tokens(text):
        if token in PUNCTUATION:
            if out:
                out[-1] = (out[-1][0], PUNCTUATION[token])
            continue
        out.append((script.to_slp1(token), None))
    return out


def to_ipa(text):
    lines, current = [], []
    ws = words(text)
    for n, (word, boundary) in enumerate(ws):
        following = ws[n + 1][0] if n + 1 < len(ws) and not boundary else ''
        sylls = syllabify(segments(word, following))
        k = stress_index(sylls)
        current.append('.'.join(("ˈ" if i == k and len(sylls) > 1 else '') + ''.join(s.ipa for s in syll)
                                for i, syll in enumerate(sylls)))
        if boundary:
            lines.append(' '.join(current) + (' |' if boundary == 'comma' else ' ‖'))
            current = []
    if current:
        lines.append(' '.join(current))
    return '\n'.join(lines)
