#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# なんちゃってラテン語スピーチ
# by naoya_t
#
# バックエンド:
#   mbrola : 自前の音韻処理 (latin_phonology / latin_prosody) で作った .pho を
#            MBROLA の古典ラテン語音声 la1 で合成する（既定。高低アクセント）
#   espeak : espeak-ng のラテン語音声 (-v la) にテキストをそのまま渡す
#            （MBROLA が使えない場合の代替）
#   piper  : 自前の音韻処理で作った IPA を、Piper のイタリア語/スペイン語モデルで合成する
#
# 古典ギリシア語 (set_language('grc', pron)) は、mbrola では greek/prosody.py の .pho を同じ la1 音声で
# (有気音・[y]・長母音があるので)、espeak では espeak-ng の古典ギリシア語音声 (-v grc) で読む
#
# サンスクリット (set_language('sa')) は、mbrola では sanskrit/prosody.py の .pho を MBROLA のヒンディー語音声 in1
# (-v in2 で女声) で、espeak では espeak-ng のヒンディー語音声 (-v hi) にデーヴァナーガリーで渡して読む
#
# (2013年版は macOS の音声合成に自前の音素列 (TUNE形式) を渡していたが、
#  現行の macOS では音素入力が解釈されないため削除した。git の履歴を参照)
#
import os
import re
import sys
import shutil
import tempfile
from subprocess import Popen, PIPE, DEVNULL, run

from latin import latin_prosody
from latin import latin_phonology

MBROLA_HOME = os.environ.get('MBROLA_HOME', os.path.expanduser('~/.local/share/mbrola'))
PIPER_VOICES = os.environ.get('PIPER_VOICES', os.path.expanduser('~/.local/share/piper/voices'))
PIPER_LENGTH_SCALE = 1.15   # 1より大きいとゆっくり
PIPER_SENTENCE_PAUSE = 0.35  # 秒

BACKENDS = {
    'espeak': {'command': 'espeak-ng', 'voice': 'la'},
    'mbrola': {'command': os.path.join(MBROLA_HOME, 'bin', 'mbrola'),
               'voice': os.path.join(MBROLA_HOME, 'voices', 'la1', 'la1')},
    'piper':  {'command': None, 'voice': 'it_IT-paola-medium'},
}
DEFAULT_BACKEND = 'mbrola'
FALLBACK_BACKEND = 'espeak'
ESPEAK_SPEED = 140  # words per minute (espeak-ng の既定は175)

backend = None
voice = None
proc = None
language = 'la'          # 'la' / 'grc' / 'sa'
pronunciation = 'attic'  # ギリシア語の発音の流儀 (attic / koine / erasmian)
ESPEAK_VOICES = {'la': 'la', 'grc': 'grc', 'sa': 'hi'}
# サンスクリットを読む MBROLA のヒンディー語音声 (in1 男声 / in2 女声)
SANSKRIT_VOICE = os.path.join(MBROLA_HOME, 'voices', 'in1', 'in1')
# 現代ギリシア語式 (--pron=modern) で読む MBROLA の現代ギリシア語音声 (gr1 / gr2)
MODERN_GREEK_VOICE = os.path.join(MBROLA_HOME, 'voices', 'gr2', 'gr2')
# 声ごとの、収録されていないダイフォン (合成時に mbrola の警告から自動的に追加される)
MISSING_BY_VOICE = {}


def missing_diphones():
    if voice not in MISSING_BY_VOICE:
        MISSING_BY_VOICE[voice] = latin_prosody.MISSING_DIPHONES if voice.endswith('la1') else set()
    return MISSING_BY_VOICE[voice]


def _default_voice(backend_name):
    if backend_name == 'espeak':
        return ESPEAK_VOICES.get(language, BACKENDS['espeak']['voice'])
    if backend_name == 'mbrola' and language == 'grc' and pronunciation == 'modern':
        return MODERN_GREEK_VOICE
    if backend_name == 'mbrola' and language == 'sa':
        return SANSKRIT_VOICE
    return BACKENDS[backend_name]['voice']


def set_language(lang, pron=None):
    """読む言語 ('la' / 'grc') と、ギリシア語の発音の流儀"""
    global language, pronunciation
    language = lang
    if pron:
        pronunciation = pron
    if backend == 'espeak':
        global voice
        voice = ESPEAK_VOICES.get(lang, voice)


def make_pho(text):
    """いまの言語の .pho"""
    if language == 'grc':
        from greek import prosody as greek_prosody
        return greek_prosody.to_pho(text, pron=pronunciation, missing=missing_diphones(),
                                    phone_set='gr2' if voice.endswith('gr2') else 'gr1')
    if language == 'sa':
        from sanskrit import prosody as sanskrit_prosody
        return sanskrit_prosody.to_pho(text, missing=missing_diphones(),
                                       base_pitch=200 if voice.endswith('in2') else sanskrit_prosody.BASE_PITCH)
    return latin_prosody.to_pho(text, accent=accent, missing=missing_diphones())
ACCENTS = ('pitch', 'stress')
accent = 'pitch'  # mbrola: 'pitch' (高低アクセント) / 'stress' (強勢アクセント)


def set_accent(accent_name):
    global accent
    if accent_name not in ACCENTS:
        print("Unknown accent: %s (choose from %s)" % (accent_name, ', '.join(ACCENTS)))
        return None
    accent = accent_name
    return accent


def init_synth(backend_name=None, voice_name=None):
    """backend_name を省略すると DEFAULT_BACKEND、使えなければ FALLBACK_BACKEND"""
    if backend_name is None:
        return _init_synth(DEFAULT_BACKEND, voice_name) or _init_synth(FALLBACK_BACKEND, voice_name)
    return _init_synth(backend_name, voice_name)


def _init_synth(backend_name, voice_name=None):
    global backend, voice
    if backend_name not in BACKENDS:
        print("Unknown speech backend: %s (choose from %s)" % (backend_name, ', '.join(BACKENDS)))
        return None
    conf = BACKENDS[backend_name]
    if conf['command'] and shutil.which(conf['command']) is None:
        print("Speech Synthesizer (%s) is not available" % conf['command'])
        return None
    if backend_name == 'mbrola' and voice_name and not os.path.exists(voice_name):
        voice_name = os.path.join(MBROLA_HOME, 'voices', voice_name, voice_name)  # -v gr1 のような名前だけ
    voice = voice_name or _default_voice(backend_name)
    if backend_name == 'mbrola' and not os.path.exists(voice):
        print("MBROLA voice is not available: %s" % voice)
        return None
    if backend_name == 'piper':
        try:
            _load_piper_voice(voice)
        except Exception as e:
            print("Piper voice is not available: %s (%s)" % (voice, e))
            return None
    backend = backend_name
    return backend


def pause_while_speaking():
    if proc is None: return
    proc.wait()


def _spawn(args, text, pause=False):
    global proc
    pause_while_speaking()  # 前の発話が終わるのを待つ
    proc = Popen(args, stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
    proc.stdin.write(text.encode('utf-8'))
    proc.stdin.close()
    if pause:
        pause_while_speaking()


def espeak(text, pause=False, wav_file=None, show_phonemes=False):
    if language == 'sa':
        from sanskrit import script
        text = script.devanagari(script.to_slp1(text))  # espeak-ng のヒンディー語はデーヴァナーガリーで
    if backend != 'espeak': return None
    args = ['espeak-ng', '-v', voice, '-s', str(ESPEAK_SPEED), '--stdin']
    if wav_file:
        args += ['-w', wav_file]
    if show_phonemes:
        args += ['--ipa']
        print(text)
    _spawn(args, text, pause=pause)


def synthesize_mbrola(text, wav_file, max_retry=3):
    """MBROLA で WAV を作る。未収録のダイフォンは警告から学習して作り直す"""
    command = BACKENDS['mbrola']['command']
    with tempfile.NamedTemporaryFile('w', suffix='.pho', delete=False) as fp:
        pho_file = fp.name
    try:
        for _ in range(max_retry):
            with open(pho_file, 'w') as fp:
                fp.write(make_pho(text))
            result = run([command, '-e', voice, pho_file, wav_file],
                         capture_output=True, text=True)
            missing = {(a, b) for a, b in re.findall(r'Warning: (\S+?)-(\S+) unknown', result.stderr)}
            new = missing - missing_diphones()
            if not new:
                break
            missing_diphones().update(new)
    finally:
        os.unlink(pho_file)


def mbrola(text, pause=False, wav_file=None):
    if backend != 'mbrola': return None
    _synthesize_and_play(synthesize_mbrola, text, pause=pause, wav_file=wav_file)


def piper(text, pause=False, wav_file=None):
    if backend != 'piper': return None
    _synthesize_and_play(synthesize_piper, text, pause=pause, wav_file=wav_file)


_piper_voices = {}

def _load_piper_voice(name):
    if name not in _piper_voices:
        from piper import PiperVoice
        _piper_voices[name] = PiperVoice.load(os.path.join(PIPER_VOICES, name + '.onnx'))
    return _piper_voices[name]


def synthesize_piper(text, wav_file):
    import wave
    import numpy as np
    from piper import SynthesisConfig

    piper_voice = _load_piper_voice(voice)
    lang = os.path.basename(voice)[:2]  # it_IT-paola-medium → it
    rate = piper_voice.config.sample_rate
    config = SynthesisConfig(length_scale=PIPER_LENGTH_SCALE)
    silence = np.zeros(int(rate * PIPER_SENTENCE_PAUSE), dtype=np.float32)

    chunks = []
    for sentence in latin_phonology.to_target_ipa(text, lang):
        ids = piper_voice.phonemes_to_ids(list(sentence))
        chunks += [piper_voice.phoneme_ids_to_audio(ids, config), silence]
    audio = np.concatenate(chunks) if chunks else silence
    audio = audio / max(1e-6, float(np.abs(audio).max())) * 0.9

    with wave.open(wav_file, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())


def _synthesize_and_play(synthesize, text, pause=False, wav_file=None):
    global proc
    if wav_file:
        synthesize(text, wav_file)
        return
    pause_while_speaking()
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False).name
    synthesize(text, tmp)
    proc = Popen(['afplay', tmp])
    if pause:
        pause_while_speaking()


def say_latin(text_uc, debug_mode=False, pause=False, wav_file=None):
    if backend == 'espeak':
        espeak(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'mbrola':
        if debug_mode:
            if language == 'grc':
                from greek import phonology as greek_phonology
                print(greek_phonology.to_ipa(text_uc, pronunciation))
            elif language == 'sa':
                from sanskrit import phonology as sanskrit_phonology
                print(sanskrit_phonology.to_ipa(text_uc))
            print(make_pho(text_uc))
        mbrola(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'piper':
        if language in ('grc', 'sa'):
            print('piper does not support this language (use mbrola or espeak)')
            return
        if debug_mode:
            print('\n'.join(latin_phonology.to_target_ipa(text_uc, os.path.basename(voice)[:2])))
        piper(text_uc, pause=pause, wav_file=wav_file)


def main(argv=None):
    """コマンドラインから音読する (tools/speak.py)"""
    import getopt
    import select
    argv = sys.argv[1:] if argv is None else argv
    opts, args = getopt.getopt(argv, 'b:v:w:a:d', ['backend=', 'voice=', 'wav=', 'accent=', 'debug',
                                                    'lang=', 'pron='])
    opts = dict(opts)
    set_accent(opts.get('-a', opts.get('--accent', accent)))
    set_language(opts.get('--lang', 'la'), opts.get('--pron'))
    init_synth(opts.get('-b', opts.get('--backend')),
               opts.get('-v', opts.get('--voice')))
    text = ' '.join(args)
    if not text and select.select([sys.stdin], [], [], 0.0)[0]:
        text = ' '.join(line.rstrip() for line in sys.stdin)
    if language == 'grc':
        text = text or 'μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος οὐλομένην.'
    if language == 'sa':
        text = text or 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।'
    text = text or 'Arma virumque canō, Trōiae quī prīmus ab ōrīs Ītaliam, fātō profugus, Lāvīniaque vēnit lītora.'
    debug_mode = '-d' in opts or '--debug' in opts
    say_latin(text, debug_mode=debug_mode, pause=True, wav_file=opts.get('-w', opts.get('--wav')))


if __name__ == '__main__':
    main()
