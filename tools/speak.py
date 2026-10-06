#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語を音読する
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
#   --pron=NAME          ギリシア語の発音: attic (既定、復元アッティカ発音・高低アクセント) / koine / erasmian
#
#   python3 tools/speak.py --lang=grc "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"
#
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import speech

if __name__ == '__main__':
    speech.main()
