#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの音読: sanskrit/phonology.py の音を、MBROLA のヒンディー語音声 in1 / in2 の .pho にする
#
# in1 の音素: 母音 a aa ii uu e ai o au (短い i u は無いので ii uu を短く)、子音 k kh g gh c ch j jh T Th D Dh N
# t th d dh n p ph b bh m y r l v sh s h ks (क्ष)。ṛ は r + 短い i、ṅ ñ は n、ṣ は sh で代用する。
# 長さは短母音 1 : 長母音 2。強勢のある音節の母音を少し高くし、文末で下げる
#
from . import phonology

IN1 = {'ɐ': 'a', 'ɑː': 'aa', 'i': 'ii', 'iː': 'ii', 'u': 'uu', 'uː': 'uu', 'eː': 'e', 'e': 'e', 'ɐi': 'ai',
       'oː': 'o', 'o': 'o', 'ɐu': 'au',
       'k': 'k', 'kʰ': 'kh', 'g': 'g', 'gʱ': 'gh', 'ŋ': 'n',
       'tʃ': 'c', 'tʃʰ': 'ch', 'dʒ': 'j', 'dʒʱ': 'jh', 'ɲ': 'n',
       'ʈ': 'T', 'ʈʰ': 'Th', 'ɖ': 'D', 'ɖʱ': 'Dh', 'ɳ': 'N',
       't̪': 't', 't̪ʰ': 'th', 'd̪': 'd', 'd̪ʱ': 'dh', 'n': 'n',
       'p': 'p', 'pʰ': 'ph', 'b': 'b', 'bʱ': 'bh', 'm': 'm',
       'j': 'y', 'r': 'r', 'l': 'l', 'ʋ': 'v', 'ʃ': 'sh', 'ʂ': 'sh', 's': 's', 'ɦ': 'h', 'h': 'h'}
SYLLABIC = {'r̩': ('r', 'ii'), 'r̩ː': ('r', 'ii'), 'l̩': ('l', 'ii'), 'l̩ː': ('l', 'ii')}

BASE_PITCH = 115       # Hz (in1 は男声。in2 なら 200 くらい)
STRESS_RAISE = 0.12
DECLINATION = 0.15
MORA = 90              # 短母音の長さ (ms)
DURATION = {'consonant': 70, 'aspirate': 85, 'echo': 45}
PAUSE = {'edge': 200, 'comma': 300, 'period': 550, 'word': 0}


def _phones(text):
    """[(in1 の音素, 長さ, 強勢, 区切り)] の列。区切りは語・句の終わりの印"""
    out = []
    ws = phonology.words(text)
    for n, (word, boundary) in enumerate(ws):
        following = ws[n + 1][0] if n + 1 < len(ws) and not boundary else ''
        sylls = phonology.syllabify(phonology.segments(word, following))
        k = phonology.stress_index(sylls)
        segs = [(seg, i == k and len(sylls) > 1) for i, syll in enumerate(sylls) for seg in syll]
        j = 0
        while j < len(segs):
            seg, stressed = segs[j]
            nxt = segs[j + 1][0] if j + 1 < len(segs) else None
            if seg.vowel:
                dur = DURATION['echo'] if seg.mora < 1 else MORA * seg.mora
                if seg.ipa in SYLLABIC:
                    cons, vowel = SYLLABIC[seg.ipa]
                    out.append((cons, DURATION['consonant'] * 0.6, False, None))
                    out.append((vowel, dur * 0.8, stressed, None))
                else:
                    out.append((IN1[seg.ipa], dur, stressed, None))
            elif seg.ipa == 'k' and nxt is not None and nxt.ipa == 'ʂ':
                out.append(('ks', DURATION['consonant'] * 1.6, False, None))  # क्ष
                j += 1
            else:
                aspirate = seg.ipa.endswith(('ʰ', 'ʱ'))
                out.append((IN1[seg.ipa], DURATION['aspirate' if aspirate else 'consonant'], False, None))
            j += 1
        if out:
            out[-1] = out[-1][:3] + (boundary or 'word',)
    return out


VOWEL_PHONES = {'a', 'aa', 'ii', 'uu', 'e', 'ai', 'o', 'au'}
CLUSTER_GAP = 15  # in1 には子音どうしのダイフォンがほとんど無いので、子音の間に短い無音を挟む (in1 の README の k a c _ r aa)


def to_pho(text, speed=1.0, base_pitch=BASE_PITCH, missing=frozenset()):
    lines = ['_ %d' % PAUSE['edge']]
    prev = '_'
    phrase = []

    def flush(boundary):
        nonlocal prev
        n = len(phrase)
        if not n:
            return
        for i, (ph, dur, stressed) in enumerate(phrase):
            pitch = base_pitch * (1 + DECLINATION / 2 - DECLINATION * i / max(1, n - 1))
            if stressed:
                pitch *= 1 + STRESS_RAISE
            targets = [(50, pitch)]
            if i == n - 1 and boundary == 'period':
                targets.append((100, pitch * 0.8))
            if prev not in VOWEL_PHONES and prev != '_' and ph not in VOWEL_PHONES or (prev, ph) in missing:
                lines.append('_ %d' % CLUSTER_GAP)
            lines.append('%s %d %s' % (ph, dur / speed, ' '.join('%d %d' % t for t in targets)))
            prev = ph
        if boundary in ('comma', 'period', 'question'):
            lines.append('_ %d' % PAUSE.get(boundary, PAUSE['comma']))
            prev = '_'
        phrase.clear()

    for ph, dur, stressed, boundary in _phones(text):
        phrase.append((ph, dur, stressed))
        if boundary and boundary != 'word':
            flush(boundary)
    flush('period')
    lines.append('_ %d' % PAUSE['edge'])
    return '\n'.join(lines) + '\n'

