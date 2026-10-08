#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の発音 (ラサ方言を土台にした読み): 綴り → IPA (声調つき) と、espeak-ng の音素
#
#   བླ་མ་ལ་ཕྱག་འཚལ་ལོ  →  la˥ ma˩˧ la˩˧ cʰaʔ˥˩ tsʰɛː˥ lo˩˧
#   ལྷ་ས  →  l̥a˥ sa˥
#
# 音節を 前置字・上に乗る字・基字・下に付く字・母音・後置字 (2つまで) に分けて:
#   * 語頭の子音: 前置字と上に乗る字は読まない。下に付く字で変わる (ky / py → c、khy / phy → cʰ、kr / tr / pr → ʈ、
#     khr → ʈʰ、kl / bl / sl / rl → l、zl → t、sr → s、hr → ʂ)、lh → l̥ (無声の l)、db → w (dbang → wang)、dby → j。
#     有声の基字 (g j d b dz) は無声になり、前置字・上に乗る字が無ければ有気 (ga → kʰà)、あれば無気 (dga → kà)。
#   * 声調: 無声の基字・ཨ、前置字か上に乗る字のある鳴音 (rna, sna, dmar, g.yu)、lh は高い調子。有声の基字・前置字の
#     無い鳴音・འ は低い調子。高い調子は、閉じた音節 (-g, -b) と -d / -s の落ちた音節で下がる (˥˩)
#   * 語末: -g → ʔ、-ng → ŋ、-b → p、-m → m、-r → r、-d / -s は読まず、-l は読まずに母音を伸ばす。-d / -s / -l / -n と
#     語末の 'i の前で母音が前寄りになる (a → ɛ、o → ø、u → y)。2つ目の後置字 -s の前 (-gs, -ngs) では変わらない
#   * 2音節目以降の前置字 ' / m は前の音節の鼻音になる (dge 'dun → ken.tyn、bka' 'gyur → kaŋ.cur)
#
# 読み方 (pron): 'lhasa' (既定)、'chant' (読誦式: 語末の母音を変えず -l / -n を読む。'tshal → tsʰal)
#
import re

from . import script

VOICED = {'g', 'j', 'd', 'b', 'dz'}
SONORANTS = {'ng', 'ny', 'n', 'm', 'w', 'y', 'r', 'l', "'", 'N'}
NASAL_MARKS = {'\u0f7e': 'm', '\u0f82': 'ŋ', '\u0f83': 'ŋ'}   # ཾ (anusvāra)、ྂ ྃ (candrabindu)
PREFIXES = {'g', 'd', 'b', 'm', "'"}
SUPERSCRIPTS = {'r', 'l', 's'}
SUFFIXES = {'g', 'ng', 'd', 'n', 'b', 'm', "'", 'r', 'l', 's'}

# 基字 → (無気の音, 有気の音)。有声の基字は前置字の有無で選ぶ。無声の基字は綴りのとおり
INITIALS = {
    'k': 'k', 'kh': 'kʰ', 'g': ('k', 'kʰ'), 'ng': 'ŋ',
    'c': 'tɕ', 'ch': 'tɕʰ', 'j': ('tɕ', 'tɕʰ'), 'ny': 'ɲ',
    't': 't', 'th': 'tʰ', 'd': ('t', 'tʰ'), 'n': 'n',
    'p': 'p', 'ph': 'pʰ', 'b': ('p', 'pʰ'), 'm': 'm',
    'ts': 'ts', 'tsh': 'tsʰ', 'dz': ('ts', 'tsʰ'), 'w': 'w',
    'zh': 'ɕ', 'z': 's', "'": '', 'y': 'j', 'r': 'r', 'l': 'l', 'sh': 'ɕ', 's': 's', 'h': 'h', '': '',
    'T': 'ʈ', 'Th': 'ʈʰ', 'D': ('ʈ', 'ʈʰ'), 'N': 'n', 'Sh': 'ʂ',
}
# 下に付く字 y / r の付いた形 (無気, 有気)
WITH_Y = {'k': 'c', 'kh': 'cʰ', 'g': ('c', 'cʰ'), 'p': 'c', 'ph': 'cʰ', 'b': ('c', 'cʰ'), 'm': 'ɲ'}
WITH_R = {'k': 'ʈ', 't': 'ʈ', 'p': 'ʈ', 'kh': 'ʈʰ', 'th': 'ʈʰ', 'ph': 'ʈʰ', 'g': ('ʈ', 'ʈʰ'), 'd': ('ʈ', 'ʈʰ'),
          'b': ('ʈ', 'ʈʰ'), 's': 's', 'm': 'm', 'h': 'ʂ', 'n': 'n', 'sh': 'ʂ'}
WITH_L = {'k': ('l', 'H'), 'b': ('l', 'H'), 'r': ('l', 'H'), 's': ('l', 'H'), 'g': ('l', 'L'), 'z': ('t', 'L')}
UMLAUT = {'a': 'ɛ', 'o': 'ø', 'u': 'y'}
CODAS = {'g': 'ʔ', 'ng': 'ŋ', 'b': 'p', 'm': 'm', 'r': 'r', 'n': 'n', 'd': '', 's': '', "'": '', 'l': ''}
TONE_LETTERS = {'55': '˥', '51': '˥˩', '35': '˩˧'}

# espeak-ng の中国語 (普通話) 音声 cmn の音素 (有気・無気、そり舌、歯茎硬口蓋の破擦音、声調がある)。ø は無いので e で代用
ESPEAK = {
    'kʰ': 'kh', 'k': 'k', 'cʰ': 'ch', 'c': 'c', 'tɕʰ': 'tS;h', 'tɕ': 'tS;', 'ʈʰ': 'ts.h', 'ʈ': 'ts.',
    'tʰ': 'th', 't': 't', 'pʰ': 'ph', 'p': 'p', 'tsʰ': 'tsh', 'ts': 'ts', 'ŋ': 'N', 'ɲ': 'n^', 'n': 'n', 'm': 'm',
    'w': 'w', 'j': 'j', 'r': 'r', 'l̥': 'l#', 'l': 'l', 'ɕ': 'S;', 's': 's', 'ʂ': 's.', 'h': 'X', '': '',
}
ESPEAK_VOWELS = {'a': 'A', 'i': 'i', 'u': 'u', 'e': 'e', 'o': 'o', 'ɛ': 'E', 'ø': 'e', 'y': 'y'}


def _stacks(syllable):
    """音節 → [[字 (ワイリー式), 下に付く字 …], 母音] のリスト"""
    out = []
    i = 0
    while i < len(syllable):
        c = syllable[i]
        two = syllable[i:i + 2]
        if len(two) == 2 and two in script.CONSONANTS:
            out.append([[script.CONSONANTS[two]], ''])
            i += 2
            continue
        if c in script.CONSONANTS:
            out.append([[script.CONSONANTS[c]], ''])
        elif c in script.SUBJOINED and out:
            out[-1][0].append(script.SUBJOINED[c])
        elif c in script.VOWELS:
            if out:
                out[-1][1] += script.VOWELS[c]
            else:
                out.append([[''], script.VOWELS[c]])
        i += 1
    return out


def parse(syllable):
    """音節 → dict(prefix, superscript, root, subscripts, vowel, suffix, suffix2, final_vowel)。読めなければ None"""
    stacks = _stacks(syllable)
    if not stacks:
        return None
    letters = [[''.join(s[0]), s[1]] for s in stacks]
    root_index = script._roots(letters)[0]
    if root_index > 1:
        return None  # サンスクリットの音節など
    prefix = stacks[0][0][0] if root_index == 1 else ''
    if prefix and (len(stacks[0][0]) > 1 or prefix not in PREFIXES):
        return None
    root_stack, vowel = stacks[root_index]
    superscript = ''
    if len(root_stack) > 1 and root_stack[0] in SUPERSCRIPTS and root_stack[1] not in ('y', 'r', 'l', 'w') or \
            root_stack[:2] == ['l', 'h']:
        superscript, root_stack = root_stack[0], root_stack[1:]
    root, subscripts = root_stack[0], [s for s in root_stack[1:] if s != 'w']
    rest = stacks[root_index + 1:]
    final_vowel = ''
    if rest and rest[-1][0] == ["'"] and rest[-1][1]:
        final_vowel = rest[-1][1]  # 語末の 'i / 'u / 'o
        rest = rest[:-1]
    if any(len(s[0]) > 1 or s[1] for s in rest) or len(rest) > 2:
        return None
    suffix = rest[0][0][0] if rest else ''
    suffix2 = rest[1][0][0] if len(rest) > 1 else ''
    vowel = script.LONG.get(vowel, vowel) if hasattr(script, 'LONG') else vowel
    return {'prefix': prefix, 'superscript': superscript, 'root': root, 'subscripts': subscripts,
            'vowel': vowel or 'a', 'suffix': suffix, 'suffix2': suffix2, 'final_vowel': final_vowel}


def _pick(value, aspirated):
    if isinstance(value, tuple):
        return value[1] if aspirated else value[0]
    return value


def initial(p, word_initial=True):
    """(子音, 調子 'H' / 'L')"""
    root, subs = p['root'], p['subscripts']
    covered = bool(p['prefix'] or p['superscript'])
    aspirated = not covered and word_initial  # 有声の基字: 前置字が無く語頭なら有気
    if p['superscript'] == 'l' and root == 'h':
        return 'l̥', 'H'
    if p['prefix'] == 'd' and root == 'b':
        return ('j' if 'y' in subs else 'w'), 'L'   # dbang → wang、dbyangs → yang
    register = 'L' if root in VOICED or root in ('zh', 'z', "'") else 'H'
    if root in SONORANTS - {"'"}:
        register = 'H' if covered else 'L'
    if 'y' in subs and root in WITH_Y:
        sound = _pick(WITH_Y[root], aspirated)
    elif 'r' in subs and root in WITH_R:
        sound = _pick(WITH_R[root], aspirated)
        if root == 's' or root == 'h':
            register = 'H'
    elif 'l' in subs and root in WITH_L:
        sound, register = WITH_L[root]
    else:
        sound = _pick(INITIALS.get(root, root), aspirated)
    return sound, register


def rhyme(p, pron='lhasa'):
    """(母音, 長さ, 語末の子音, 下がる調子か)"""
    vowel = p['vowel']
    vowel = {'A': 'a', 'I': 'i', 'U': 'u', 'ai': 'ai', 'au': 'au', '-i': 'i', '-I': 'i'}.get(vowel, vowel)
    suffix, suffix2, final_vowel = p['suffix'], p['suffix2'], p['final_vowel']
    long = False
    if pron == 'chant':
        coda = {'g': 'ʔ', 'ng': 'ŋ', 'b': 'p', 'm': 'm', 'r': 'r', 'n': 'n', 'l': 'l'}.get(suffix, '')
        if final_vowel == 'i':
            vowel += 'i'
        return vowel, long, coda, suffix in ('g', 'b', 'd', 's')
    if suffix in ('d', 'n', 'l', 's') and not suffix2 or final_vowel == 'i':
        vowel = UMLAUT.get(vowel, vowel)
    if suffix == 'l' or final_vowel == 'i':
        long = True
    coda = CODAS.get(suffix, '')
    falling = suffix in ('g', 'b', 'd', 's')
    return vowel, long, coda, falling


def syllable_ipa(syllable, word_initial=True, pron='lhasa'):
    """音節 → (子音, 母音, 長さ, 語末の子音, 声調 '55' / '51' / '35')。読めなければ None"""
    mark = next((NASAL_MARKS[c] for c in syllable if c in NASAL_MARKS), '')
    p = parse(syllable)
    if p is None:
        return None
    sound, register = initial(p, word_initial)
    vowel, long, coda, falling = rhyme(p, pron)
    coda = coda or mark  # ཨོཾ → om、ཧཱུྃ → hung
    tone = ('51' if falling else '55') if register == 'H' else '35'
    return {'initial': sound, 'vowel': vowel, 'long': long, 'coda': coda, 'tone': tone, 'parsed': p}


def word_syllables(word, pron='lhasa'):
    """語 (ツェクで区切った音節) → 音節ごとの読み。2音節目以降の前置字 ' / m は前の音節の鼻音に"""
    out = []
    for k, syl in enumerate(s for s in re.split('[་ ]+', word) if s):
        r = syllable_ipa(syl, word_initial=(k == 0), pron=pron)
        if r is None:
            r = {'initial': '', 'vowel': script.translit(syl), 'long': False, 'coda': '', 'tone': '55', 'parsed': None}
        if k > 0 and r['parsed'] and r['parsed']['prefix'] in ("'", 'm') and out and not out[-1]['coda']:
            first = r['initial'][:1]
            out[-1]['coda'] = 'm' if first == 'p' else 'ŋ' if first in ('k', 'c') else 'n'
        out.append(r)
    return out


def _tone_letter(tone):
    return TONE_LETTERS[tone]


def ipa(text, pron='lhasa', words=None):
    """文 → IPA (語は空白、音節は . で区切る)。words を渡せば語の区切りに使う (無ければ音節ごと)"""
    units = words if words is not None else [s for s in re.split('[་ །༎༏༐༑༔]+', text) if s]
    out = []
    for w in units:
        syls = word_syllables(w, pron)
        out.append('.'.join(s['initial'] + s['vowel'] + ('ː' if s['long'] else '') + s['coda'] +
                            _tone_letter(s['tone']) for s in syls))
    return ' '.join(out)


def espeak_phonemes(text, pron='lhasa', words=None):
    """文 → espeak-ng (-v cmn) に渡す音素の列 ([[...]])"""
    units = words if words is not None else [s for s in re.split('[་ ]+|(?=[།༎༏༐༑༔])', text) if s]
    out = []
    for w in units:
        if re.fullmatch('[།༎༏༐༑༔ ]+', w):
            if out and out[-1] == '_:':
                continue
            out.append('_:')  # 区切りで間を置く
            continue
        for s in word_syllables(re.sub('[།༎༏༐༑༔]', '', w), pron):
            vowel = ''.join(ESPEAK_VOWELS.get(c, c) for c in s['vowel'])
            coda = {'ʔ': '?', 'ŋ': 'N', 'p': 'p', 'm': 'm', 'r': 'r', 'n': 'n', 'l': 'l', '': ''}.get(s['coda'], '')
            out.append(ESPEAK.get(s['initial'], s['initial']) + "'" + vowel + (':' if s['long'] else '') +
                       s['tone'] + coda)
    return '[[' + ' '.join(out) + ']]'
