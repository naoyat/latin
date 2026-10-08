#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ラテン語の音韻処理
#   綴り → 音素列 → 音節 → アクセント位置
#
# 音素は MBROLA la1 音声の SAMPA 表記で持つ
#   短母音: a E I O U y   長母音: a: e: i: o: u: y:   二重母音: aE aU OE
#   子音:   p b t d k g p_h t_h k_h f s h z m n N l r w j
#   重子音: 末尾に ':' (t:, l:, j: ...)
#
import re
import unicodedata

from . import latin_char as char

SHORT_VOWELS = {'a': 'a', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'U', 'y': 'y'}
LONG_VOWELS = {'ā': 'a:', 'ē': 'e:', 'ī': 'i:', 'ō': 'o:', 'ū': 'u:', 'ȳ': 'y:'}
DIPHTHONGS = {'ae': 'aE', 'au': 'aU', 'oe': 'OE'}

VOWEL_PHONEMES = set(SHORT_VOWELS.values()) | set(LONG_VOWELS.values()) | set(DIPHTHONGS.values())
LONG_NUCLEI = set(LONG_VOWELS.values()) | set(DIPHTHONGS.values())

SIMPLE_CONSONANTS = {
    'p': 'p', 'b': 'b', 't': 't', 'd': 'd', 'c': 'k', 'k': 'k', 'g': 'g',
    'f': 'f', 's': 's', 'h': 'h', 'z': 'z',
    'm': 'm', 'n': 'n', 'l': 'l', 'r': 'r', 'v': 'w', 'j': 'j',
}
ASPIRATES = {'ph': 'p_h', 'th': 't_h', 'ch': 'k_h', 'rh': 'r'}

# 閉鎖音/f + 流音 は次の音節の頭子音になる (muta cum liquida)
MUTA = {'p', 'b', 't', 'd', 'k', 'g', 'f', 'p_h', 't_h', 'k_h'}
LIQUIDA = {'l', 'r'}

# -que 等が付いていても語彙化しているもの（アクセント移動しない）
LEXICALIZED_QUE = {'neque', 'itaque', 'atque', 'quoque', 'usque', 'quisque',
                   'quaeque', 'quodque', 'undique', 'ubique', 'utique', 'dēnique', 'plērumque'}
ENCLITICS = ('que', 'ne', 've')


def is_vowel_phoneme(ph):
    return ph in VOWEL_PHONEMES


def is_long_nucleus(ph):
    return ph in LONG_NUCLEI


def _letters(word):
    word = unicodedata.normalize('NFC', word)
    return char.tolower(word)


def phonemize_word(word):
    """綴りを音素列に変換する"""
    w = _letters(word)
    w = re.sub(r'[^a-zāēīōūȳ]', '', w)
    phonemes = []
    i = 0
    n = len(w)

    def prev_is_vowel():
        return phonemes and is_vowel_phoneme(phonemes[-1])

    def next_is_vowel(k):
        return k < n and (w[k] in SHORT_VOWELS or w[k] in LONG_VOWELS)

    while i < n:
        c = w[i]
        two = w[i:i+2]

        # qu / ngu+母音 → k w / g w
        if two == 'qu':
            phonemes += ['k', 'w']
            i += 2
            continue
        if two == 'gu' and phonemes and phonemes[-1] == 'N' and next_is_vowel(i+2):
            phonemes += ['g', 'w']
            i += 2
            continue
        # 有気音 (ギリシア語由来)
        if two in ASPIRATES:
            phonemes.append(ASPIRATES[two])
            i += 2
            continue
        # 二重母音
        if two in DIPHTHONGS:
            phonemes.append(DIPHTHONGS[two])
            i += 2
            continue
        # 母音
        if c in LONG_VOWELS:
            phonemes.append(LONG_VOWELS[c])
            i += 1
            continue
        if c in SHORT_VOWELS:
            # 語頭の i + 母音 (iam, Iuppiter) は子音 j
            if c == 'i' and i == 0 and next_is_vowel(i+1):
                phonemes.append('j')
            # 語頭の u + 母音 (uoco) は w
            elif c == 'u' and i == 0 and next_is_vowel(i+1):
                phonemes.append('w')
            else:
                phonemes.append(SHORT_VOWELS[c])
            i += 1
            continue
        # x = k s
        if c == 'x':
            phonemes += ['k', 's']
            i += 1
            continue
        # gn = N n (magnus)
        if two == 'gn':
            phonemes += ['N', 'n']
            i += 2
            continue
        # n + 軟口蓋音 = N
        if c == 'n' and i+1 < n and w[i+1] in ('c', 'g', 'k', 'q', 'x'):
            phonemes.append('N')
            i += 1
            continue
        # 母音間の j は重子音 (Trōja = Trōj-ja)
        if c == 'j' and prev_is_vowel() and next_is_vowel(i+1):
            phonemes.append('j:')
            i += 1
            continue
        # b + 無声音 = p (urbs, obtineo)
        if c == 'b' and i+1 < n and w[i+1] in ('s', 't'):
            phonemes.append('p')
            i += 1
            continue
        if c in SIMPLE_CONSONANTS:
            ph = SIMPLE_CONSONANTS[c]
            # 重子音 (tt, ll, ss ...)
            if i+1 < n and w[i+1] == c:
                phonemes.append(ph + ':')
                i += 2
            else:
                phonemes.append(ph)
                i += 1
            continue
        i += 1  # 未知の文字は無視

    return phonemes


def _split_cluster(cluster):
    """母音間の子音連続を (前の音節の末尾, 次の音節の頭) に分ける"""
    if not cluster:
        return [], []
    # 重子音は前後に分ける
    if cluster[0].endswith(':'):
        base = cluster[0][:-1]
        return [base], [base] + cluster[1:]
    if len(cluster) == 1:
        return [], cluster
    # qu / gu (k w, g w) は1つの子音として扱い分けない
    if cluster[-2:] in (['k', 'w'], ['g', 'w']):
        return cluster[:-2], cluster[-2:]
    if len(cluster) == 2 and cluster[0] in MUTA and cluster[1] in LIQUIDA:
        return [], cluster
    if len(cluster) >= 2 and cluster[-2] in MUTA and cluster[-1] in LIQUIDA:
        return cluster[:-2], cluster[-2:]
    return cluster[:1], cluster[1:]


def syllabify(phonemes):
    """音素列を音節 (音素のリスト) のリストにする"""
    nuclei = [k for k, ph in enumerate(phonemes) if is_vowel_phoneme(ph)]
    if not nuclei:
        return [phonemes] if phonemes else []

    syllables = []
    onset = phonemes[:nuclei[0]]
    for idx, k in enumerate(nuclei):
        syl = onset + [phonemes[k]]
        if idx + 1 < len(nuclei):
            cluster = phonemes[k+1:nuclei[idx+1]]
            coda, onset = _split_cluster(cluster)
            syl += coda
        else:
            syl += phonemes[k+1:]
        syllables.append(syl)
    return syllables


def is_heavy(syllable):
    nucleus = next(ph for ph in syllable if is_vowel_phoneme(ph))
    coda = syllable[syllable.index(nucleus)+1:]
    return is_long_nucleus(nucleus) or len(coda) > 0


def locate_accent(syllables, word=None):
    """アクセントのある音節の位置 (後ろから2番目が重ければそこ、軽ければ3番目)"""
    vocalic = [k for k, syl in enumerate(syllables) if any(is_vowel_phoneme(ph) for ph in syl)]
    if not vocalic:
        return None
    if len(vocalic) <= 2:
        accent = vocalic[0]
    elif is_heavy(syllables[vocalic[-2]]):
        accent = vocalic[-2]
    else:
        accent = vocalic[-3]

    # 前接語 -que/-ne/-ve の直前の音節にアクセント (virúmque)
    if word is not None and len(vocalic) >= 2:
        lw = _letters(word)
        if lw not in LEXICALIZED_QUE and any(lw.endswith(e) and len(lw) > len(e) + 1 for e in ENCLITICS):
            accent = vocalic[-2]
    return accent


class Syllable:
    def __init__(self, phonemes, accented=False):
        self.phonemes = phonemes
        self.accented = accented

    def __repr__(self):
        return ('ˈ' if self.accented else '') + ''.join(self.phonemes)


def analyze_word(word):
    phonemes = phonemize_word(word)
    syllables = syllabify(phonemes)
    accent = locate_accent(syllables, word)
    return [Syllable(syl, k == accent) for k, syl in enumerate(syllables)]


#
# 文単位の処理
#
PAUSES = {',': 'comma', ';': 'comma', ':': 'comma', '.': 'period', '!': 'period', '?': 'question'}

def tokenize(text):
    """テキストを語と区切り記号の列にする"""
    return re.findall(r"[A-Za-zĀĒĪŌŪȲāēīōūȳ]+|[,;:.!?]", text)


def analyze_text(text):
    """[('word', 語, [Syllable...]) | ('pause', 種類, None)] のリスト"""
    result = []
    for token in tokenize(text):
        if token in PAUSES:
            result.append(('pause', PAUSES[token], None))
        else:
            result.append(('word', token, analyze_word(token)))
    return result


#
# IPA 表記 (Piper などの IPA 入力 TTS 用)
#
SAMPA_TO_IPA = {
    'a': 'a', 'E': 'ɛ', 'I': 'ɪ', 'O': 'ɔ', 'U': 'ʊ', 'y': 'y',
    'a:': 'aː', 'e:': 'eː', 'i:': 'iː', 'o:': 'oː', 'u:': 'uː', 'y:': 'yː',
    'aE': 'ae̯', 'aU': 'au̯', 'OE': 'oe̯',
    'p_h': 'pʰ', 't_h': 'tʰ', 'k_h': 'kʰ', 'N': 'ŋ',
}

def sampa_to_ipa(ph):
    if ph in SAMPA_TO_IPA:
        return SAMPA_TO_IPA[ph]
    if ph.endswith(':'):
        return sampa_to_ipa(ph[:-1]) * 2
    return ph


def to_ipa(text, diphthong_marks=True):
    out = []
    for kind, token, syllables in analyze_text(text):
        if kind == 'pause':
            out.append({'comma': ',', 'period': '.', 'question': '?'}[token])
            continue
        ipa = ''
        for syl in syllables:
            s = ''.join(sampa_to_ipa(ph) for ph in syl.phonemes)
            if not diphthong_marks:
                s = s.replace('\u032f', '')
            ipa += ('ˈ' if syl.accented and len(syllables) > 1 else '') + s
        out.append(' ' + ipa)
    return ''.join(out).strip()


#
# 他言語の TTS モデル向けの IPA
#   Piper (espeak-ng 音素で学習) のモデルが知っている記号・表記に寄せる
#   - 強勢記号は強勢母音の直前に置く (kavˈallo)
#   - 重子音は記号を重ねる
#
TARGET_IPA = {
    # イタリア語: ɛ ɔ ɪ はある。y・有気音・二重母音記号はない
    'it': {'a': 'a', 'E': 'ɛ', 'I': 'ɪ', 'O': 'ɔ', 'U': 'u', 'y': 'i',
           'a:': 'aː', 'e:': 'eː', 'i:': 'iː', 'o:': 'oː', 'u:': 'uː', 'y:': 'iː',
           'aE': 'ae', 'aU': 'aʊ', 'OE': 'oe',
           'p_h': 'p', 't_h': 't', 'k_h': 'k', 'N': 'ŋ', 'g': 'ɡ', 'r': 'ɾ', 'r:': 'rr'},
    # スペイン語: 5母音のみ、長短の区別なし
    'es': {'a': 'a', 'E': 'e', 'I': 'i', 'O': 'o', 'U': 'u', 'y': 'i',
           'a:': 'a', 'e:': 'e', 'i:': 'i', 'o:': 'o', 'u:': 'u', 'y:': 'i',
           'aE': 'ae', 'aU': 'aʊ', 'OE': 'oe',
           'p_h': 'p', 't_h': 't', 'k_h': 'k', 'N': 'ŋ', 'g': 'ɡ', 'r': 'ɾ', 'r:': 'r'},
}


def _target_phoneme(ph, table):
    if ph in table:
        return table[ph]
    if ph.endswith(':'):
        return _target_phoneme(ph[:-1], table) * 2
    return sampa_to_ipa(ph)


def to_target_ipa(text, lang):
    """lang ('it', 'es') の TTS モデル向け IPA を文ごとのリストで返す"""
    table = TARGET_IPA[lang]
    sentences = []
    words = []
    for kind, token, syllables in analyze_text(text):
        if kind == 'pause':
            mark = {'comma': ',', 'period': '.', 'question': '?'}[token]
            if words:
                words[-1] += mark
            if token != 'comma':
                sentences.append(' '.join(words))
                words = []
            continue
        ipa = ''
        for syl in syllables:
            for ph in syl.phonemes:
                if syl.accented and is_vowel_phoneme(ph) and len(syllables) > 1:
                    ipa += 'ˈ'
                ipa += _target_phoneme(ph, table)
        words.append(ipa)
    if words:
        sentences.append(' '.join(words) + '.')
    return sentences


if __name__ == '__main__':
    import sys
    text = ' '.join(sys.argv[1:]) or 'Arma virumque canō, Trōjae quī prīmus ab ōrīs'
    for kind, token, syllables in analyze_text(text):
        if kind == 'word':
            print('%-16s %s' % (token, '.'.join(map(repr, syllables))))
    print(to_ipa(text))
