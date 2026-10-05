#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 合成音声の聞き取りやすさ評価
#   Whisper にラテン語として書き起こさせ、元テキストとの WER / CER を出す
#   mlx-whisper (Apple Silicon の GPU) があれば使い、なければ faster-whisper (CPU)
#
#   python3 tools/tts_eval.py -t sample.txt a.wav b.wav ...
#
import sys
import re
import getopt
import unicodedata


def normalize(text):
    # マクロン除去・小文字化
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn').lower()
    # 綴りの揺れを吸収 (j/i, v/u, ae/oe/e, y/i)
    text = text.replace('j', 'i').replace('v', 'u')
    text = text.replace('ae', 'e').replace('oe', 'e').replace('y', 'i')
    return re.sub(r'[^a-z ]', ' ', text).split()


def edit_distance(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j-1] + 1, prev + (r != h))
    return d[-1]


def wer(ref_words, hyp_words):
    return edit_distance(ref_words, hyp_words) / max(1, len(ref_words))


def cer(ref_words, hyp_words):
    ref, hyp = ' '.join(ref_words), ' '.join(hyp_words)
    return edit_distance(ref, hyp) / max(1, len(ref))


MLX_MODELS = {'large-v3': 'mlx-community/whisper-large-v3-mlx',
              'large-v3-turbo': 'mlx-community/whisper-large-v3-turbo'}


def make_transcriber(model_name):
    # 前の窓の出力に引きずられないよう condition_on_previous_text=False にしている
    # (よく勧められる設定。手元の比較では結果に差は出なかった)
    try:
        import mlx_whisper
        repo = MLX_MODELS.get(model_name, model_name)

        def transcribe(wav_file):
            result = mlx_whisper.transcribe(wav_file, path_or_hf_repo=repo, language='la',
                                            condition_on_previous_text=False)
            return result['text'].strip()
        return transcribe, 'mlx-whisper ' + repo
    except ImportError:
        from faster_whisper import WhisperModel
        model = WhisperModel(model_name, device='cpu', compute_type='int8')

        def transcribe(wav_file):
            segments, _info = model.transcribe(wav_file, language='la', beam_size=5,
                                               condition_on_previous_text=False)
            return ' '.join(seg.text.strip() for seg in segments)
        return transcribe, 'faster-whisper ' + model_name


def usage():
    print("Usage: python %s -t TEXT_FILE [-m MODEL] [-v] WAV_FILE..." % sys.argv[0])
    print("  -t, --text=FILE    reference text")
    print("  -m, --model=NAME   Whisper model (default: large-v3)")
    print("  -v, --verbose      show transcriptions")


def main():
    opts, wav_files = getopt.getopt(sys.argv[1:], 't:m:vh', ['text=', 'model=', 'verbose', 'help'])
    text_file, model_name, verbose = None, 'large-v3', False
    for option, arg in opts:
        if option in ('-t', '--text'):
            text_file = arg
        elif option in ('-m', '--model'):
            model_name = arg
        elif option in ('-v', '--verbose'):
            verbose = True
        elif option in ('-h', '--help'):
            usage()
            sys.exit()
    if text_file is None or not wav_files:
        usage()
        sys.exit(1)

    transcribe, engine = make_transcriber(model_name)
    print('# ' + engine, flush=True)

    with open(text_file) as fp:
        ref_words = normalize(fp.read())

    width = max(len(f) for f in wav_files)
    print('%-*s  %6s  %6s' % (width, 'file', 'WER', 'CER'), flush=True)
    for wav_file in wav_files:
        hyp_text = transcribe(wav_file)
        hyp_words = normalize(hyp_text)
        print('%-*s  %5.1f%%  %5.1f%%' % (width, wav_file,
                                          100 * wer(ref_words, hyp_words),
                                          100 * cer(ref_words, hyp_words)), flush=True)
        if verbose:
            print('  ' + hyp_text, flush=True)


if __name__ == '__main__':
    main()
