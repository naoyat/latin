#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の音韻処理: 綴り → 音素 (母音の核と子音)
#
# 音素は MBROLA のラテン語音声 la1 の SAMPA 表記に合わせる (有気音 p_h t_h k_h、[y]、長母音がある)。
# la1 に無い開いた長母音 η [ɛː]・ω [ɔː] は、短い E・O を長く伸ばして読む ('E:', 'O:' と書き、合成のときに読み替える)。
#
# 発音の流儀 (pron):
#   attic     復元アッティカ発音 (前5世紀)。ζ = [zd], η = [ɛː], ει = [eː], ου = [oː], υ = [y]、有気音、
#             気息 [h]、母音の長短、高低アクセント (既定)
#   koine     コイネー (1〜2世紀ごろ)。母音の長短と気息が消え、αι = [ɛ], ει = [i], η = [e], οι = [y], ου = [u]、
#             ζ = [z]。アクセントは強弱
#   erasmian  学校式 (エラスムス式)。η = [ɛː], ει = [ei], ου = [uː], ζ = [dz]、有気音・気息あり。アクセントは強弱
#
# 長短どちらもある α ι υ は、曲アクセント・下書きのイオータ・長音の印 (ᾱ) があれば長く、なければ短く読む
#
import re
import unicodedata
from dataclasses import dataclass, field

ACUTE, GRAVE, CIRCUMFLEX = '́', '̀', '͂'
SMOOTH, ROUGH = '̓', '̔'
IOTA_SUBSCRIPT, DIAERESIS = 'ͅ', '̈'
MACRON, BREVE = '̄', '̆'

VOWELS = set('αεηιουω')
DIPHTHONGS = {'αι', 'αυ', 'ει', 'ευ', 'οι', 'ου', 'υι', 'ηυ', 'ωυ'}
PRONUNCIATIONS = ('attic', 'koine', 'erasmian', 'modern')
ACCENT_STYLE = {'attic': 'pitch', 'koine': 'stress', 'erasmian': 'stress', 'modern': 'stress'}

# 単母音 → (短い音素, 長い音素)。長さの決まっている η ω は常に長い
SIMPLE = {
    'attic':    {'α': ('a', 'a:'), 'ε': ('E', 'E'), 'η': ('E:', 'E:'), 'ι': ('I', 'i:'), 'ο': ('O', 'O'),
                 'υ': ('y', 'y:'), 'ω': ('O:', 'O:')},
    'erasmian': {'α': ('a', 'a:'), 'ε': ('E', 'E'), 'η': ('E:', 'E:'), 'ι': ('I', 'i:'), 'ο': ('O', 'O'),
                 'υ': ('y', 'y:'), 'ω': ('O:', 'O:')},
    'koine':    {'α': ('a', 'a'), 'ε': ('E', 'E'), 'η': ('e', 'e'), 'ι': ('i', 'i'), 'ο': ('O', 'O'),
                 'υ': ('y', 'y'), 'ω': ('O', 'O')},
}
# 二重母音 → 音素の列 (1つなら1音素の長い核、2つなら前半・後半のモーラ)
DIPHTHONG = {
    'attic':    {'αι': ['aE'], 'αυ': ['aU'], 'ει': ['e:'], 'ευ': ['E', 'U'], 'οι': ['OE'], 'ου': ['o:'],
                 'υι': ['y', 'I'], 'ηυ': ['E', 'U'], 'ωυ': ['O', 'U']},
    'erasmian': {'αι': ['aE'], 'αυ': ['aU'], 'ει': ['E', 'I'], 'ευ': ['E', 'U'], 'οι': ['OE'], 'ου': ['u:'],
                 'υι': ['y', 'I'], 'ηυ': ['E', 'U'], 'ωυ': ['O', 'U']},
    'koine':    {'αι': ['E'], 'αυ': ['a', 'U'], 'ει': ['i'], 'ευ': ['E', 'U'], 'οι': ['y'], 'ου': ['u'],
                 'υι': ['y'], 'ηυ': ['e', 'U'], 'ωυ': ['O', 'U']},
}
CONSONANTS = {'β': ['b'], 'γ': ['g'], 'δ': ['d'], 'θ': ['t_h'], 'κ': ['k'], 'λ': ['l'], 'μ': ['m'], 'ν': ['n'],
              'ξ': ['k', 's'], 'π': ['p'], 'ρ': ['r'], 'σ': ['s'], 'ς': ['s'], 'τ': ['t'], 'φ': ['p_h'],
              'χ': ['k_h'], 'ψ': ['p', 's']}
ZETA = {'attic': ['z', 'd'], 'erasmian': ['d', 'z'], 'koine': ['z']}
VELARS = set('γκξχ')
VOICED = set('βγδμ')
# la1 での読み替え (koine の短い i e u は la1 の i: e: u: の音色で、長さは短く)
LA1 = {'E:': 'E', 'O:': 'O', 'i': 'i:', 'e': 'e:', 'u': 'u:'}
LONG_NUCLEI = {'a:', 'i:', 'y:', 'e:', 'o:', 'u:', 'E:', 'O:', 'aE', 'aU', 'OE'}


@dataclass
class Nucleus:
    phonemes: list          # 1つ (長い核・短い核) か 2つ (二重母音の前半・後半)
    long: bool
    accent: str = None      # 'acute' / 'circumflex' / 'grave' / None


@dataclass
class Word:
    surface: str
    segments: list = field(default_factory=list)  # 子音 (str) と母音の核 (Nucleus) の列


def _letters(word):
    """語を (小文字の文字, 記号の集合) の列に"""
    units = []
    for c in unicodedata.normalize('NFD', word):
        if unicodedata.combining(c):
            if units:
                units[-1][1].add(c)
        elif c.isalpha():
            units.append((c.lower(), set()))
    return units


def _accent(marks):
    if CIRCUMFLEX in marks:
        return 'circumflex'
    if ACUTE in marks:
        return 'acute'
    if GRAVE in marks:
        return 'grave'
    return None


def phonemize_word(word, pron='attic'):
    if pron == 'modern':
        return phonemize_modern(word)
    units = _letters(word)
    result = Word(word)
    segments = result.segments
    i = 0
    while i < len(units):
        letter, marks = units[i]
        nxt = units[i + 1] if i + 1 < len(units) else None
        if letter in VOWELS:
            pair = letter + nxt[0] if nxt else ''
            if pair in DIPHTHONGS and DIAERESIS not in nxt[1] and not (marks & {ACUTE, GRAVE, CIRCUMFLEX, DIAERESIS}):
                all_marks = marks | nxt[1]
                phonemes = list(DIPHTHONG[pron][pair])
                long = pron != 'koine'
                i += 2
            else:
                all_marks = marks
                short, long_ph = SIMPLE[pron][letter]
                long = (letter in 'ηω' and pron != 'koine') or \
                    (pron != 'koine' and bool(marks & {CIRCUMFLEX, IOTA_SUBSCRIPT, MACRON}))
                phonemes = [long_ph if long else short]
                i += 1
            if ROUGH in all_marks and not segments and pron != 'koine':
                segments.append('h')  # 語頭の気息
            segments.append(Nucleus(phonemes, long, _accent(all_marks)))
            continue
        if letter == 'ζ':
            segments.extend(ZETA[pron])
        elif letter == 'γ' and nxt and nxt[0] in VELARS:
            segments.append('N')  # γγ, γκ, γξ, γχ の γ は [ŋ]
        elif letter in ('σ', 'ς') and nxt and nxt[0] in VOICED:
            segments.append('z')  # 有声子音の前の σ (κόσμος)
        elif letter in CONSONANTS:
            phonemes = CONSONANTS[letter]
            if pron == 'koine' and letter in 'φθχ':
                phonemes = [phonemes[0]]  # 初期のコイネーでは有気音のまま。ここでは la1 の有気音で読む
            segments.extend(phonemes)
        i += 1
    return result


# 句読点 (· は上の点、; と ; は疑問符)
PAUSES = {',': 'comma', '·': 'comma', '·': 'comma', ':': 'comma', '.': 'period', ';': 'question',
          ';': 'question', '!': 'period'}
# 語 (語末のアポストロフィ = 母音の省略を含む) と句読点
TOKEN = re.compile("[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+[\u2019'\u02bc\u1fbd]?|[,\u00b7\u0387:.;\u037e!]")


def analyze_text(text, pron='attic', lengths=True):
    """[('word', Word) / ('pause', 種類)]。lengths なら、長短どちらもある母音の長さを辞書から知る (greek.length)"""
    marker = None
    if lengths and pron in ('attic', 'erasmian'):
        from . import length
        marker = length.mark
    result = []
    for token in TOKEN.findall(text):
        if token in PAUSES:
            result.append(('pause', PAUSES[token]))
        else:
            result.append(('word', phonemize_word(marker(token) if marker else token, pron)))
    return result


def to_ipa(text, pron='attic', lengths=True):
    """確かめるための IPA 風の表記"""
    ipa = {'a': 'a', 'a:': 'aː', 'E': 'e', 'E:': 'ɛː', 'e:': 'eː', 'e': 'e', 'I': 'i', 'i:': 'iː', 'i': 'i',
           'O': 'o', 'O:': 'ɔː', 'o:': 'oː', 'u:': 'uː', 'u': 'u', 'U': 'u', 'y': 'y', 'y:': 'yː',
           'aE': 'ai̯', 'aU': 'au̯', 'OE': 'oi̯', 'p_h': 'pʰ', 't_h': 'tʰ', 'k_h': 'kʰ', 'N': 'ŋ',
           # 現代ギリシア語式
           'e': 'e', 'o': 'o', 'T': 'θ', 'D': 'ð', 'G': 'ɣ', 'jj': 'ʝ', 'C': 'ç', 'c': 'c', 'gj': 'ɟ', 'x': 'x'}
    marks = {'acute': '́', 'circumflex': '̂', 'grave': '̀'}
    words = []
    for kind, value in analyze_text(text, pron, lengths):
        if kind != 'word':
            continue
        out = ''
        for seg in value.segments:
            if isinstance(seg, Nucleus):
                text_ = ''.join(ipa.get(p, p) for p in seg.phonemes)
                if seg.accent in marks and ACCENT_STYLE[pron] == 'pitch':
                    text_ = text_[0] + marks[seg.accent] + text_[1:]
                elif seg.accent in ('acute', 'circumflex', 'grave'):
                    text_ = 'ˈ' + text_
                out += text_
            else:
                out += ipa.get(seg, seg)
        words.append(out)
    return unicodedata.normalize('NFC', ' '.join(words))


# ----------------------------------------------------------------------
# 現代ギリシア語式 (pron='modern'): 古典の綴りを現代の発音で読む。音素は MBROLA の現代ギリシア語音声
# gr1 / gr2 の SAMPA (a e i o u, p b t d k c g gj, ts dz, f v T D x C G jj, s z m n l r)。
#   η ι υ ει οι υι = [i], αι = [e], ου = [u], ω = [o]、αυ ευ = [av ev] / [af ef] (無声音の前・語末)、
#   β = [v], γ = [ɣ] / [ʝ] (前舌母音の前), δ = [ð], θ = [θ], φ = [f], χ = [x] / [ç]、κ = [k] / [c]、
#   μπ ντ γκ = 語頭 [b d g] / 語中 [mb nd ŋg]、τσ τζ = [ts dz]、気息は読まず、重子音は1つ、アクセントは強弱
MODERN_VOWELS = {'α': 'a', 'ε': 'e', 'η': 'i', 'ι': 'i', 'ο': 'o', 'υ': 'i', 'ω': 'o'}
MODERN_DIPHTHONGS = {'αι': 'e', 'ει': 'i', 'οι': 'i', 'υι': 'i', 'ου': 'u'}
MODERN_CONSONANTS = {'β': 'v', 'δ': 'D', 'ζ': 'z', 'θ': 'T', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'π': 'p', 'ρ': 'r',
                     'σ': 's', 'ς': 's', 'τ': 't', 'φ': 'f'}
MODERN_VOICELESS = set('θκξπστφχψς')
MODERN_VOICED_CONSONANTS = set('βγδζλμνρ')
FRONT = {'e', 'i'}


def _modern_units(word):
    """(文字, 記号) の列から、母音の核 ('V', 音素, アクセント) と子音の文字 ('C', 文字) の列に"""
    units = _letters(word)
    out = []
    i = 0
    while i < len(units):
        letter, marks = units[i]
        nxt = units[i + 1] if i + 1 < len(units) else None
        if letter in VOWELS:
            pair = letter + nxt[0] if nxt else ''
            plain = not (marks & {ACUTE, GRAVE, CIRCUMFLEX, DIAERESIS})
            if nxt and DIAERESIS not in nxt[1] and plain and pair in MODERN_DIPHTHONGS:
                out.append(('V', MODERN_DIPHTHONGS[pair], _accent(marks | nxt[1])))
                i += 2
                continue
            if nxt and DIAERESIS not in nxt[1] and plain and pair in ('αυ', 'ευ', 'ηυ'):
                # αυ ευ ηυ: 次が母音・有声子音なら [v]、無声子音・語末なら [f]
                after = units[i + 2][0] if i + 2 < len(units) else None
                voiced = after is not None and (after in VOWELS or after in MODERN_VOICED_CONSONANTS)
                out.append(('V', MODERN_VOWELS[letter], _accent(marks | nxt[1])))
                out.append(('P', 'v' if voiced else 'f'))
                i += 2
                continue
            out.append(('V', MODERN_VOWELS[letter], _accent(marks)))
        else:
            out.append(('C', letter))
        i += 1
    return out


def phonemize_modern(word):
    units = _modern_units(word)
    result = Word(word)
    segments = result.segments

    def next_vowel(k):
        for u in units[k + 1:]:
            if u[0] == 'V':
                return u[1]
            if u[0] == 'C' and u[1] in VOWELS:
                return None
        return None

    k = 0
    while k < len(units):
        kind, value, *rest = units[k] + (None,) if len(units[k]) == 2 else units[k]
        if kind == 'V':
            segments.append(Nucleus([value], False, units[k][2]))
            k += 1
            continue
        if kind == 'P':
            segments.append(value)
            k += 1
            continue
        letter = value
        nxt = units[k + 1][1] if k + 1 < len(units) and units[k + 1][0] == 'C' else None
        front = next_vowel(k + (1 if nxt in ('γ', 'κ', 'π', 'τ') and letter in ('γ', 'μ', 'ν') else 0)) in FRONT
        initial = not segments
        if letter == 'μ' and nxt == 'π':
            segments.extend(['b'] if initial else ['m', 'b'])
            k += 2
        elif letter == 'ν' and nxt == 'τ':
            segments.extend(['d'] if initial else ['n', 'd'])
            k += 2
        elif letter == 'γ' and nxt in ('γ', 'κ'):
            g = 'gj' if front else 'g'
            segments.extend([g] if initial and nxt == 'κ' else ['n', g])
            k += 2
        elif letter == 'γ' and nxt in ('ξ', 'χ'):
            segments.append('n')  # γξ γχ の γ は [ŋ] (ここでは n)
            k += 1
        elif letter == 'τ' and nxt in ('σ', 'ς'):
            segments.append('ts')
            k += 2
        elif letter == 'τ' and nxt == 'ζ':
            segments.append('dz')
            k += 2
        elif letter == 'γ':
            segments.append('jj' if next_vowel(k) in FRONT else 'G')
            k += 1
        elif letter == 'κ':
            segments.append('c' if next_vowel(k) in FRONT else 'k')
            k += 1
        elif letter == 'χ':
            segments.append('C' if next_vowel(k) in FRONT else 'x')
            k += 1
        elif letter == 'ξ':
            segments.extend(['k', 's'])
            k += 1
        elif letter == 'ψ':
            segments.extend(['p', 's'])
            k += 1
        elif letter in ('σ', 'ς') and nxt in MODERN_VOICED_CONSONANTS:
            segments.append('z')  # κόσμος [kozmos]
            k += 1
        elif letter in MODERN_CONSONANTS:
            ph = MODERN_CONSONANTS[letter]
            if not (segments and segments[-1] == ph):  # 重子音は1つ (ἄλλος [alos])
                segments.append(ph)
            k += 1
        else:
            k += 1
    return result
