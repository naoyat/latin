#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# チベット文字 → ワイリー式 (EWTS) の転写
#
#   བསྒྲུབས → bsgrubs、དགའ → dga'、གཡོ → g.yo、བཅོམ་ལྡན་འདས → bcom ldan 'das
#
# 音節 (ツェク ་ で区切る) ごとに、基字 (母音記号の付く字。重ね字なら重ねたもの全体) を決めて、母音記号が無ければ
# 基字の後ろに a を補う。基字が分からない3字の音節 (དགས: dgas / dags) は、辞書にある方を選べるように候補を返す。
#
import re

CONSONANTS = {
    'ཀ': 'k', 'ཁ': 'kh', 'ག': 'g', 'གྷ': 'gh', 'ང': 'ng', 'ཅ': 'c', 'ཆ': 'ch', 'ཇ': 'j', 'ཉ': 'ny',
    'ཊ': 'T', 'ཋ': 'Th', 'ཌ': 'D', 'ཌྷ': 'Dh', 'ཎ': 'N', 'ཏ': 't', 'ཐ': 'th', 'ད': 'd', 'དྷ': 'dh', 'ན': 'n',
    'པ': 'p', 'ཕ': 'ph', 'བ': 'b', 'བྷ': 'bh', 'མ': 'm', 'ཙ': 'ts', 'ཚ': 'tsh', 'ཛ': 'dz', 'ཛྷ': 'dzh', 'ཝ': 'w',
    'ཞ': 'zh', 'ཟ': 'z', 'འ': "'", 'ཡ': 'y', 'ར': 'r', 'ལ': 'l', 'ཤ': 'sh', 'ཥ': 'Sh', 'ས': 's', 'ཧ': 'h',
    'ཨ': '', 'ཀྵ': 'kSh', 'ཪ': 'r',
}
# 下に付く字 (U+0F90〜U+0FBC は基本の字 + 0x50)
SUBJOINED = {chr(ord(c) + 0x50): w for c, w in CONSONANTS.items() if len(c) == 1 and c not in 'ཨཪ'}
SUBJOINED.update({'ྭ': 'w', 'ྱ': 'y', 'ྲ': 'r', 'ྺ': 'w', 'ྻ': 'y', 'ྼ': 'r',
                  'ྸ': 'a'})
VOWELS = {'ཱ': 'A', 'ི': 'i', 'ཱི': 'I', 'ུ': 'u', 'ཱུ': 'U', 'ེ': 'e', 'ཻ': 'ai',
          'ོ': 'o', 'ཽ': 'au', 'ྀ': '-i', 'ཱྀ': '-I'}
MARKS = {'ཾ': 'M', 'ཿ': 'H', 'ྂ': '~M`', 'ྃ': '~M', '྄': '?', '༷': '', '༵': ''}
PUNCT = {'་': ' ', '༌': ' ', '།': '/', '༎': '//', '༏': ';', '༐': ';', '༑': '|', '༔': '!', '༄': '@', '༅': '#',
         '༈': '!', '༼': '(', '༽': ')', '༴': '=', '༸': ''}
DIGITS = {chr(0x0f20 + i): str(i) for i in range(10)}

PREFIXES = {
    'g': {'c', 'ny', 't', 'd', 'n', 'ts', 'zh', 'z', 'y', 'sh', 's'},
    'd': {'k', 'g', 'ng', 'p', 'b', 'm'},
    'b': {'k', 'g', 'c', 't', 'd', 'ts', 'zh', 'z', 'sh', 's'},
    'm': {'kh', 'g', 'ng', 'ch', 'j', 'ny', 'th', 'd', 'n', 'tsh', 'dz'},
    "'": {'kh', 'g', 'ch', 'j', 'th', 'd', 'ph', 'b', 'tsh', 'dz'},
}

TIBETAN = re.compile('[ༀ-࿿]')


def is_tibetan(text):
    return bool(TIBETAN.search(text))


def _letters(syllable):
    """音節 → 字のリスト [[基本の字と下に付く字の転写], 母音] と、記号 (ཾ ཿ)"""
    letters, marks = [], ''
    i = 0
    while i < len(syllable):
        c = syllable[i]
        two = syllable[i:i + 2]
        if len(two) == 2 and two in CONSONANTS:
            letters.append([CONSONANTS[two], ''])
            i += 2
            continue
        if c in CONSONANTS:
            letters.append([CONSONANTS[c], ''])
        elif c in SUBJOINED and letters:
            letters[-1][0] += SUBJOINED[c]
        elif c in VOWELS:
            if letters:
                letters[-1][1] += VOWELS[c]
            else:
                letters.append(['', VOWELS[c]])
        elif c in MARKS:
            if letters and i + 1 < len(syllable) and syllable[i + 1] in CONSONANTS:
                letters[-1][1] += MARKS[c]  # 音節の途中の ཾ (སཾག → saMga): その字に付ける
            else:
                marks += MARKS[c]
        i += 1
    return letters, marks


def _stacked(syllable_letters):
    return [k for k, (text, _) in enumerate(syllable_letters) if text not in CONSONANTS.values()]


def _roots(letters):
    """基字の位置の候補 (最初がふつうの読み)。母音の付いた字があればそれ (ただし語末の འི འུ འོ は除く)"""
    plain = [t for t, _ in letters]
    voweled = [k for k, (t, v) in enumerate(letters) if v and not (k > 0 and t == "'")]
    if voweled:
        return [voweled[0]]
    # 語末の འི / འུ (པའི pa'i): 母音の付いた འ より前で決める
    n = len(letters)
    while n > 1 and plain[n - 1] == "'" and letters[n - 1][1]:
        n -= 1
    stacked = [k for k in _stacked(letters[:n])]
    if stacked:
        return [stacked[0]]
    if n <= 2:
        return [0]
    prefixed = plain[0] in PREFIXES and plain[1] in PREFIXES[plain[0]]
    if n == 3 and plain[2] == 's' and plain[1] in ('g', 'ng', 'b', 'm'):
        return [0, 1] if prefixed else [0]   # མངས mangs / དགས dgas
    return [1, 0] if prefixed else [0]       # དབང dbang、དགའ dga'、བདགས bdags


LONG = {'Au': 'U', 'Ai': 'I', 'A-i': '-I'}


def _join(letters, root):
    out = []
    for k, (text, vowel) in enumerate(letters):
        vowel = LONG.get(vowel, vowel)
        if k < root and not (k == root - 1 and text in PREFIXES) and not vowel:
            vowel = 'a'  # サンスクリットの字の連なり (པདྨེ padme): 前置字でない字には a
        elif k > root and not vowel and (text not in CONSONANTS.values() or
                                         letters[k - 1][1][-1:] in ('M', 'H')):
            vowel = 'a'  # 基字の後ろの重ね字 (ཤཱཀྱ shAkya)、ཾ の後ろの字 (སཾག saMga)
        if vowel[:1] in ('M', 'H', '~'):
            vowel = 'a' + vowel  # 母音記号の無い字に付いた ཾ ཿ
        if k == root:
            if k == 1 and letters[0][0] == 'g' and text == 'y':
                out.append('.')  # གཡ (g + y) と གྱ (gy) を分ける
            out.append(text + (vowel or 'a'))
        else:
            out.append(text + vowel)
    return ''.join(out)


def syllable_candidates(syllable):
    """音節 → 転写の候補 (最初がふつうの読み)"""
    letters, marks = _letters(syllable)
    if not letters:
        return [marks]
    return [_join(letters, r) + marks for r in _roots(letters)]


def translit_syllable(syllable, known=None):
    candidates = syllable_candidates(syllable)
    if known is not None:
        for c in candidates:
            if c in known:
                return c
    return candidates[0]


def translit(text, known=None):
    """チベット文字の文 → ワイリー式。known (転写の集合) があれば、読みの分かれる音節はそこにある方を選ぶ"""
    out = []
    syllable = ''
    for c in text + ' ':
        if c in PUNCT or c in DIGITS or not TIBETAN.match(c):
            if syllable:
                out.append(translit_syllable(syllable, known))
                syllable = ''
            if c in PUNCT:
                out.append(PUNCT[c])
            elif c in DIGITS:
                out.append(DIGITS[c])
            else:
                out.append(c)
        else:
            syllable += c
    text = ''.join(out)[:-1]
    text = re.sub(' +/', ' /', text)
    return re.sub(' {2,}', ' ', text).strip()


def word_translit(word, known=None):
    """語 (音節をツェクで区切ったもの) → ワイリー式 (語末のツェク・区切りは除く)"""
    return translit(word.strip('་།༑ '), known)


IAST = [('tsh', 'ch'), ('ts', 'c'), ('dz', 'j'), ('kSh', 'kṣ'), ('Sh', 'ṣ'), ('sh', 'ś'), ('ny', 'ñ'), ('Th', 'ṭh'),
        ('Dh', 'ḍh'), ('T', 'ṭ'), ('D', 'ḍ'), ('N', 'ṇ'), ('A', 'ā'), ('I', 'ī'), ('U', 'ū'), ('-i', 'ṛ'), ('-I', 'ṝ'),
        ('~M', 'ṃ'), ('M', 'ṃ'), ('H', 'ḥ'), ('w', 'v'), ("'", '')]


def iast(wylie):
    """チベット文字で書いたサンスクリットのワイリー式 → IAST (bha ga ba tI → bhagabatī、ts → c、w → v)。
    音節はつなげる (チベットでは va を ba と書くことが多いので b はそのまま)"""
    out = wylie.replace(' ', '')
    for a, b in IAST:
        out = out.replace(a, b)
    return out
