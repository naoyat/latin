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
    voice = voice_name or conf['voice']
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
                fp.write(latin_prosody.to_pho(text, accent=accent))
            result = run([command, '-e', voice, pho_file, wav_file],
                         capture_output=True, text=True)
            missing = {(a, b) for a, b in re.findall(r'Warning: (\S+?)-(\S+) unknown', result.stderr)}
            new = missing - latin_prosody.MISSING_DIPHONES
            if not new:
                break
            latin_prosody.MISSING_DIPHONES.update(new)
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
            print(latin_prosody.to_pho(text_uc, accent=accent))
        mbrola(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'piper':
        if debug_mode:
            print('\n'.join(latin_phonology.to_target_ipa(text_uc, os.path.basename(voice)[:2])))
        piper(text_uc, pause=pause, wav_file=wav_file)


def main(argv=None):
    """コマンドラインから音読する (tools/speak.py)"""
    import getopt
    import select
    argv = sys.argv[1:] if argv is None else argv
    opts, args = getopt.getopt(argv, 'b:v:w:a:d', ['backend=', 'voice=', 'wav=', 'accent=', 'debug'])
    opts = dict(opts)
    set_accent(opts.get('-a', opts.get('--accent', accent)))
    init_synth(opts.get('-b', opts.get('--backend')),
               opts.get('-v', opts.get('--voice')))
    text = ' '.join(args)
    if not text and select.select([sys.stdin], [], [], 0.0)[0]:
        text = ' '.join(line.rstrip() for line in sys.stdin)
    text = text or 'Arma virumque canō, Trōiae quī prīmus ab ōrīs Ītaliam, fātō profugus, Lāvīniaque vēnit lītora.'
    debug_mode = '-d' in opts or '--debug' in opts
    say_latin(text, debug_mode=debug_mode, pause=True, wav_file=opts.get('-w', opts.get('--wav')))


if __name__ == '__main__':
    main()
