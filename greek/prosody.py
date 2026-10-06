#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の韻律付け: 音素 (greek.phonology) → MBROLA の .pho (ラテン語音声 la1 で読む)
#
# 高低アクセント (attic) は綴りのアクセント記号どおりに:
#   鋭アクセント  短い母音ならその母音で上がる。長い母音・二重母音なら後半のモーラで上がる
#   曲アクセント  長い母音・二重母音の前半で高く、後半で下がる
#   重アクセント  上がらない
# 強弱アクセント (koine, erasmian) は、アクセントのある母音を長めにし、少しだけ上げる
#
from latin.latin_prosody import DURATION, PAUSE, BASE_PITCH, DECLINATION, GAP, MISSING_DIPHONES, \
    STRESS_ACCENT_RISE, STRESS_LENGTHEN
from .phonology import analyze_text, Nucleus, LA1, LONG_NUCLEI, ACCENT_STYLE

RISE = 30  # 高低アクセントの上がり幅 (Hz)


def _phrases(analysis):
    phrases, words = [], []
    for kind, value in analysis:
        if kind == 'pause':
            if words:
                phrases.append((words, value))
            words = []
        else:
            words.append(value)
    if words:
        phrases.append((words, 'period'))
    return phrases


def _sequence(words):
    """フレーズ内の音素を [(音素, 核, 核の中の位置 0/1, 核の音素数)] に平らにし、重子音をまとめる (λλ → l:)"""
    seq = []
    for word in words:
        for seg in word.segments:
            if isinstance(seg, Nucleus):
                for k, ph in enumerate(seg.phonemes):
                    seq.append([ph, seg, k, len(seg.phonemes)])
            elif seq and seq[-1][1] is None and seq[-1][0] == seg:
                seq[-1][0] = seg + ':'
            else:
                seq.append([seg, None, 0, 1])
    return seq


def _pitch_targets(nucleus, k, n, pitch, style):
    """核の音素 (n 個のうち k 番目) のピッチの目標 [(位置%, Hz)]"""
    accent = nucleus.accent
    if style == 'stress':
        if accent in ('acute', 'circumflex', 'grave'):
            return [(30, pitch + STRESS_ACCENT_RISE), (100, pitch)]
        return [(50, pitch)]
    if accent == 'acute':
        if not nucleus.long:
            return [(0, pitch), (60, pitch + RISE), (100, pitch + RISE * 0.7)]
        if n == 1:
            return [(0, pitch), (50, pitch + RISE * 0.3), (100, pitch + RISE)]  # 後半のモーラで上がる
        return [(50, pitch + RISE * 0.2)] if k == 0 else [(0, pitch + RISE * 0.3), (100, pitch + RISE)]
    if accent == 'circumflex':
        if n == 1:
            return [(0, pitch + RISE * 0.5), (30, pitch + RISE), (100, pitch - RISE * 0.2)]  # 上がって下がる
        return [(0, pitch + RISE * 0.6), (70, pitch + RISE)] if k == 0 else [(100, pitch - RISE * 0.1)]
    return [(50, pitch)]


def to_pho(text, pron='attic', speed=1.0, missing=MISSING_DIPHONES):
    style = ACCENT_STYLE[pron]
    lines = ['_ %d' % PAUSE['edge']]
    prev = '_'

    def emit(ph, line):
        nonlocal prev
        if (prev, ph) in missing and prev != '_' and ph != '_':
            lines.append('_ %d' % GAP)  # la1 に無いダイフォンは短い無音を挟む
        lines.append(line)
        prev = ph

    for words, boundary in _phrases(analyze_text(text, pron)):
        seq = _sequence(words)
        n = len(seq)
        for i, (ph, nucleus, k, size) in enumerate(seq):
            progress = i / max(1, n - 1)
            pitch = BASE_PITCH * (1 + DECLINATION / 2 - DECLINATION * progress)
            if nucleus is not None:
                long = nucleus.long
                if size == 2:
                    dur = DURATION['long_vowel'] / 2 if long else DURATION['short_vowel'] / 2
                else:
                    dur = DURATION['long_vowel' if long or ph in LONG_NUCLEI and style == 'pitch' else 'short_vowel']
                if style == 'stress' and nucleus.accent:
                    dur *= STRESS_LENGTHEN
                targets = _pitch_targets(nucleus, k, size, pitch, style)
            else:
                dur = DURATION['geminate'] if ph.endswith(':') else DURATION['consonant']
                targets = [(50, pitch)]
            # フレーズ末の抑揚
            if i == n - 1 or (nucleus is not None and not any(s[1] is not None for s in seq[i + 1:])):
                if boundary == 'question':
                    targets = targets + [(100, pitch * 1.25)]
                elif boundary == 'period':
                    targets = targets + [(100, pitch * 0.8)]
            name = LA1.get(ph, ph)
            emit(name, '%s %d %s' % (name, dur / speed, ' '.join('%d %d' % t for t in targets)))
        emit('_', '_ %d' % PAUSE.get(boundary, PAUSE['comma']))
    lines.append('_ %d' % PAUSE['edge'])
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    import sys
    print(to_pho(' '.join(sys.argv[1:]) or 'μῆνιν ἄειδε θεά.'))
