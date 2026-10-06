#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語 (古典ギリシア語、サンスクリット) を音読する
#
#   python3 tools/speak.py "Arma virumque canō, Trōiae quī prīmus ab ōrīs"
#   echo "..." | python3 tools/speak.py
#
#   -b, --backend=NAME   mbrola (既定) / espeak / piper
#   -v, --voice=NAME     音声 (piper なら it_IT-paola-medium など)
#   -a, --accent=NAME    mbrola のアクセント: pitch (既定、高低) / stress (強弱)
#   -w, --wav=FILE       再生せずに WAV に書き出す
#   -d, --debug          音素列 (.pho / IPA) を表示する
#   --lang=grc           古典ギリシア語を読む (mbrola は la1 音声で、espeak は -v grc で)
#   --pron=NAME          ギリシア語の発音: attic (既定、復元アッティカ発音・高低アクセント) / koine / erasmian /
#                        modern (現代ギリシア語式。MBROLA の現代ギリシア語音声 gr2、-v gr1 で gr1)
#
#   --lang=sa            サンスクリットを読む (mbrola はヒンディー語音声 in1、-v in2 で女声。espeak は -v hi)
#
#   python3 tools/speak.py --lang=grc "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"
#   python3 tools/speak.py --lang=sa -d "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।"
#
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import speech

if __name__ == '__main__':
    speech.main()
