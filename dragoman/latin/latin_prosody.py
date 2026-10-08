#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 韻律付け: 音節列 → MBROLA の .pho (音素 長さms [位置% ピッチHz]...)
#
#   accent='pitch'  : アクセント音節の母音でピッチを上げる (高低アクセント説)
#   accent='stress' : アクセント音節の母音を長めにし、少しだけピッチを上げる (強勢アクセント説)
#
from .latin_phonology import analyze_text, is_vowel_phoneme, is_long_nucleus

DURATION = {
    'short_vowel': 95,
    'long_vowel': 180,
    'consonant': 70,
    'geminate': 140,
}
PAUSE = {'word': 0, 'comma': 220, 'period': 450, 'question': 450, 'edge': 120}

BASE_PITCH = 100      # la1 は男声 (82-117Hz 程度)
PITCH_ACCENT_RISE = 30
STRESS_ACCENT_RISE = 10
STRESS_LENGTHEN = 1.3
DECLINATION = 0.12    # フレーズ内でのピッチ下降率

VOICELESS = {'p', 't', 'k', 's', 'f', 'p_h', 't_h', 'k_h'}
DEVOICE = {'d': 't', 'b': 'p', 'g': 'k'}

# la1 に収録されていないダイフォン
# 合成時に mbrola の警告から自動的に追加される (latin.speech.synthesize_mbrola)
MISSING_DIPHONES = {
    ('a:', 'i:'), ('u:', 'j:'), ('s', 'a:'), ('I', 'h'), ('w', 'r'), ('w', '_'), ('N', 'k:'),
}
GAP = 15


def _phrases(analysis):
    """区切り記号でフレーズに分ける: [([(語, 音節列)...], 末尾の区切り)]"""
    phrases = []
    words = []
    for kind, token, syllables in analysis:
        if kind == 'pause':
            if words:
                phrases.append((words, token))
            words = []
        else:
            words.append((token, syllables))
    if words:
        phrases.append((words, 'period'))
    return phrases


def _flatten(words):
    """フレーズ内の音素を [(音素, アクセント音節か)] に平らにし、重子音をまとめる"""
    seq = []
    for _word, syllables in words:
        for syl in syllables:
            for ph in syl.phonemes:
                seq.append([ph, syl.accented])
    # 有声閉鎖音 + 無声子音 → 無声化 (ad tē → at tē, ab sē → ap sē)
    for k in range(len(seq) - 1):
        if seq[k][0] in DEVOICE and seq[k+1][0] in VOICELESS:
            seq[k][0] = DEVOICE[seq[k][0]]
    merged = []
    for ph, accented in seq:
        # 音節境界・語境界で分かれた重子音 (t + t) を t: に戻す
        if merged and merged[-1][0] == ph and not is_vowel_phoneme(ph):
            merged[-1][0] = ph + ':'
            continue
        # t + t_h → t_h (語境界でのみ生じる。la1 は t_h: の収録が少ない)
        if merged and ph.endswith('_h') and merged[-1][0] == ph[:-2]:
            merged[-1][0] = ph
            continue
        merged.append([ph, accented])
    return merged


def to_pho(text, accent='pitch', speed=1.0, missing=MISSING_DIPHONES):
    lines = ['_ %d' % PAUSE['edge']]
    prev = '_'

    def emit(ph, line):
        nonlocal prev
        if (prev, ph) in missing:
            if ph.endswith(':') and not is_vowel_phoneme(ph) and (prev, ph[:-1]) not in missing:
                # 重子音を単子音にする (u:-j: → u:-j)
                line = ph[:-1] + line[len(ph):]
                ph = ph[:-1]
            elif prev == 'w' and lines[-1].startswith('w '):
                # w を母音 U にする
                lines[-1] = 'U' + lines[-1][1:]
            elif prev != '_' and ph != '_':
                # 短い無音を挟む
                lines.append('_ %d' % GAP)
        lines.append(line)
        prev = ph

    for words, boundary in _phrases(analyze_text(text)):
        seq = _flatten(words)
        n = len(seq)
        for k, (ph, accented) in enumerate(seq):
            progress = k / max(1, n - 1)
            pitch = BASE_PITCH * (1 + DECLINATION / 2 - DECLINATION * progress)

            if is_vowel_phoneme(ph):
                dur = DURATION['long_vowel' if is_long_nucleus(ph) else 'short_vowel']
            elif ph.endswith(':'):
                dur = DURATION['geminate']
            else:
                dur = DURATION['consonant']

            targets = [(50, pitch)]
            if accented and is_vowel_phoneme(ph):
                if accent == 'pitch':
                    targets = [(0, pitch), (60, pitch + PITCH_ACCENT_RISE), (100, pitch + PITCH_ACCENT_RISE * 0.6)]
                else:
                    dur *= STRESS_LENGTHEN
                    targets = [(30, pitch + STRESS_ACCENT_RISE), (100, pitch)]

            # フレーズ末の抑揚
            if k == n - 1 or (k >= n - 3 and is_vowel_phoneme(ph) and
                              not any(is_vowel_phoneme(p) for p, _ in seq[k+1:])):
                if boundary == 'question':
                    targets.append((100, pitch * 1.25))
                elif boundary == 'period':
                    targets.append((100, pitch * 0.8))

            pitch_str = ' '.join('%d %d' % (pos, hz) for pos, hz in targets)
            emit(ph, '%s %d %s' % (ph, dur / speed, pitch_str))
        emit('_', '_ %d' % PAUSE.get(boundary, PAUSE['comma']))
    lines.append('_ %d' % PAUSE['edge'])
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    import sys
    print(to_pho(' '.join(sys.argv[1:]) or 'Arma virumque canō.'))
