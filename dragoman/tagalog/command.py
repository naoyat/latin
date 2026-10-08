#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary, morphology

USAGE = '''
  ./dragoman.py tl -e "Binili ng lalaki ang isda."
  名詞句の標識 (ang / ng / sa) と動詞の焦点 (接辞: -um- / mag- 行為者、-in 対象、-an 場所、i- 移動物) から格を決め、
  焦点の名詞 (ang) を主題「は」にして日本語に訳す。辞書は tools/build_tagalog_dic.py
'''


def explain(word):
    item = word.items[0] if word.items else None
    if item is None:
        return []
    out = []
    if item.pos == 'verb' and item.attrib('focus') in morphology.VOICE_NAMES:
        out.append('%s・%s' % (morphology.VOICE_NAMES[item.attrib('focus')],
                              morphology.ASPECT_NAMES.get(item.attrib('aspect'), '')))
    if getattr(word, 'focus', False):
        out.append('焦点 (ang) →「は」')
    return out


def available():
    return None if dictionary.available() else 'no Tagalog data (python3 tools/build_tagalog_dic.py)'


COMMAND = Command(lang='tl', name='タガログ語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=lambda a, o: ' '.join(a.surfaces), explain=explain,
                  descendant_langs=('en', 'ja'), speech_lang='tl')
