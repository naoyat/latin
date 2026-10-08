#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 音声合成 (ラテン語・古典ギリシア語・サンスクリット)
# by naoya_t
#
# バックエンド:
#   mbrola : 自前の音韻処理 (latin_phonology / latin_prosody) で作った .pho を
#            MBROLA の古典ラテン語音声 la1 で合成する（既定。高低アクセント）
#   espeak : espeak-ng のラテン語音声 (-v la) にテキストをそのまま渡す
#            （MBROLA が使えない場合の代替）
#   piper  : 自前の音韻処理で作った IPA を、Piper のイタリア語/スペイン語モデルで合成する
#   say    : macOS の音声合成にテキストをそのまま渡す (現代語向け。ロシア語は Milena、-b say でサンスクリットは
#            ヒンディー語の Lekha、ギリシア語は現代ギリシア語の Melina)
#
# 古典ギリシア語 (set_language('grc', pron)) は、mbrola では greek/prosody.py の .pho を同じ la1 音声で
# (有気音・[y]・長母音があるので)、espeak では espeak-ng の古典ギリシア語音声 (-v grc) で読む
#
# ロシア語 (set_language('ru')) は espeak-ng のロシア語音声 (-v ru) で読む。
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


MBROLA_HOME = os.environ.get('MBROLA_HOME', os.path.expanduser('~/.local/share/mbrola'))
PIPER_VOICES = os.environ.get('PIPER_VOICES', os.path.expanduser('~/.local/share/piper/voices'))
PIPER_LENGTH_SCALE = 1.15   # 1より大きいとゆっくり
PIPER_SENTENCE_PAUSE = 0.35  # 秒

BACKENDS = {
    'espeak': {'command': 'espeak-ng', 'voice': 'la'},
    'mbrola': {'command': os.path.join(MBROLA_HOME, 'bin', 'mbrola'),
               'voice': os.path.join(MBROLA_HOME, 'voices', 'la1', 'la1')},
    'piper':  {'command': None, 'voice': 'it_IT-paola-medium'},
    'say':    {'command': 'say', 'voice': None},
}
# macOS の say の言語ごとの音声 (現代語の読み方になる)
SAY_VOICES = {'ru': 'Milena', 'sa': 'Lekha', 'grc': 'Melina', 'he': 'Carmit', 'ar': 'Majed', 'hi': 'Lekha'}
# 方式を指定しないときに試す順 (言語ごと。無ければ DEFAULT_BACKEND → FALLBACK_BACKEND)
LANGUAGE_BACKENDS = {'ru': ('say', 'espeak'), 'he': ('say', 'espeak'), 'ar': ('say', 'espeak'), 'fa': ('espeak',),
                     'hi': ('say', 'espeak'), 'ur': ('espeak',)}
DEFAULT_BACKEND = 'mbrola'
FALLBACK_BACKEND = 'espeak'
ESPEAK_SPEED = 140  # words per minute (espeak-ng の既定は175)

backend = None
voice = None
proc = None
language = 'la'          # 'la' / 'grc' / 'sa'
divine_name = 'adonai'   # ヘブライ語の神の名の読み方 (adonai / hashem / literal。hebrew.script.qere)
pronunciation = 'attic'  # ギリシア語の発音の流儀 (attic / koine / erasmian)
ESPEAK_VOICES = {'la': 'la', 'grc': 'grc', 'sa': 'hi', 'ru': 'ru', 'he': 'he', 'ar': 'ar', 'fa': 'fa', 'hi': 'hi', 'ur': 'ur'}
# サンスクリットを読む MBROLA のヒンディー語音声 (in1 男声 / in2 女声)
SANSKRIT_VOICE = os.path.join(MBROLA_HOME, 'voices', 'in1', 'in1')
# 現代ギリシア語式 (--pron=modern) で読む MBROLA の現代ギリシア語音声 (gr1 / gr2)
MODERN_GREEK_VOICE = os.path.join(MBROLA_HOME, 'voices', 'gr2', 'gr2')
# 声ごとの、収録されていないダイフォン (合成時に mbrola の警告から自動的に追加される)
MISSING_BY_VOICE = {}


def missing_diphones():
    if voice not in MISSING_BY_VOICE:
        if voice.endswith('la1'):
            from dragoman.latin import latin_prosody
            MISSING_BY_VOICE[voice] = latin_prosody.MISSING_DIPHONES
        else:
            MISSING_BY_VOICE[voice] = set()
    return MISSING_BY_VOICE[voice]


def _default_voice(backend_name):
    if backend_name == 'say':
        return SAY_VOICES.get(language)
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
        from dragoman.greek import prosody as greek_prosody
        return greek_prosody.to_pho(text, pron=pronunciation, missing=missing_diphones(),
                                    phone_set='gr2' if voice.endswith('gr2') else 'gr1')
    if language == 'sa':
        from dragoman.sanskrit import prosody as sanskrit_prosody
        return sanskrit_prosody.to_pho(text, missing=missing_diphones(),
                                       base_pitch=200 if voice.endswith('in2') else sanskrit_prosody.BASE_PITCH)
    from dragoman.latin import latin_prosody
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
        for name in LANGUAGE_BACKENDS.get(language, (DEFAULT_BACKEND, FALLBACK_BACKEND)):
            if _init_synth(name, voice_name):
                return backend
        return None
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
    if backend_name == 'say' and not _say_voice_available(voice):
        print("say has no voice for this language (%s)" % language if not voice else "say voice is not available: %s" % voice)
        return None
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


def _plain_text(text):
    """テキストをそのまま読む方式 (espeak, say) に渡す形"""
    if language == 'sa':
        from dragoman.sanskrit import script
        return script.devanagari(script.to_slp1(text))  # ヒンディー語の音声にはデーヴァナーガリーで
    if language == 'ru':
        from dragoman.russian import script
        return script.strip_stress(text)  # 強勢記号は読まれない (強勢は音声の辞書に任せる)
    if language == 'he':
        from dragoman.hebrew import script
        # 朗唱記号は除く (母音記号は残す)。神の名 יְהוָה は伝統どおり アドナイ (エロヒム) と読み替える
        return script.qere(script.pointed(text), divine_name)
    if language == 'grc' and backend == 'say':
        return _monotonic(text)  # 現代ギリシア語の音声は多調符 (気息記号・曲アクセント) を読めない
    return text


def _monotonic(text):
    """多調符のギリシア文字を単調符に (ἀρχῇ → αρχή): 気息記号・下書きのイオタ・長短の印を除き、
    重アクセント・曲アクセントを鋭アクセント (トノス) に"""
    import unicodedata
    out = []
    for c in unicodedata.normalize('NFD', text):
        if c in '\u0313\u0314\u0345\u0304\u0306':
            continue
        out.append('\u0301' if c in '\u0300\u0342' else c)
    return unicodedata.normalize('NFC', ''.join(out))


def _say_voice_available(name):
    if not name:
        return False
    try:
        listing = run(['say', '-v', '?'], capture_output=True, text=True).stdout
    except OSError:
        return False
    return any(line.split()[0] == name for line in listing.splitlines() if line.strip())


def say(text, pause=False, wav_file=None):
    """macOS の say で読む"""
    if backend != 'say': return None
    args = ['say', '-v', voice, '-f', '-']
    if wav_file:
        args += ['-o', wav_file, '--file-format=WAVE', '--data-format=LEI16@22050']
    _spawn(args, _plain_text(text), pause=pause or bool(wav_file))


def espeak(text, pause=False, wav_file=None, show_phonemes=False):
    text = _plain_text(text)
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
    from dragoman.latin import latin_phonology
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
    if backend == 'say':
        say(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'espeak':
        espeak(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'mbrola':
        if debug_mode:
            if language == 'grc':
                from dragoman.greek import phonology as greek_phonology
                print(greek_phonology.to_ipa(text_uc, pronunciation))
            elif language == 'sa':
                from dragoman.sanskrit import phonology as sanskrit_phonology
                print(sanskrit_phonology.to_ipa(text_uc))
            print(make_pho(text_uc))
        mbrola(text_uc, pause=pause, wav_file=wav_file)
    elif backend == 'piper':
        if language in ('grc', 'sa'):
            print('piper does not support this language (use mbrola or espeak)')
            return
        if debug_mode:
            from dragoman.latin import latin_phonology
            print('\n'.join(latin_phonology.to_target_ipa(text_uc, os.path.basename(voice)[:2])))
        piper(text_uc, pause=pause, wav_file=wav_file)


def main(argv=None):
    """コマンドラインから音読する (tools/speak.py)"""
    import getopt
    import select
    argv = sys.argv[1:] if argv is None else argv
    opts, args = getopt.getopt(argv, 'b:v:w:a:d', ['backend=', 'voice=', 'wav=', 'accent=', 'debug',
                                                    'lang=', 'pron=', 'divine-name='])
    opts = dict(opts)
    set_accent(opts.get('-a', opts.get('--accent', accent)))
    set_language(opts.get('--lang', 'la'), opts.get('--pron'))
    global divine_name
    divine_name = opts.get('--divine-name', divine_name)
    init_synth(opts.get('-b', opts.get('--backend')),
               opts.get('-v', opts.get('--voice')))
    text = ' '.join(args)
    if not text and select.select([sys.stdin], [], [], 0.0)[0]:
        text = ' '.join(line.rstrip() for line in sys.stdin)
    if language == 'grc':
        text = text or 'μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος οὐλομένην.'
    if language == 'sa':
        text = text or 'धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।'
    if language == 'ru':
        text = text or 'Девочка читала интересную книгу в школе.'
    text = text or 'Arma virumque canō, Trōiae quī prīmus ab ōrīs Ītaliam, fātō profugus, Lāvīniaque vēnit lītora.'
    debug_mode = '-d' in opts or '--debug' in opts
    say_latin(text, debug_mode=debug_mode, pause=True, wav_file=opts.get('-w', opts.get('--wav')))


if __name__ == '__main__':
    main()
