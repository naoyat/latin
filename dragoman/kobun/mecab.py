#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古文 (平安の和文) の形態素解析: MeCab + 中古和文UniDic (国立国語研究所、CC BY-NC-SA 4.0。
# $DRAGOMAN_DATA/ojp/unidic-chuko に置く。リポジトリには入れない)
#
#   いふ → Token(surface='いふ', pos='動詞', ctype='文語四段-ハ行', cform='連体形-一般', lemma='言う',
#                 kana='いう' (現代仮名遣い), base_orth='いふ')
#
import functools
import os
from dataclasses import dataclass

from dragoman.core import paths

DIC_DIR = paths.data('ojp', 'unidic-chuko')


@dataclass
class Token:
    surface: str
    pos: str          # 品詞 (名詞, 動詞, 形容詞, 形状詞, 助動詞, 助詞 …)
    pos2: str         # 品詞の細分類 (係助詞, 格助詞, 非自立可能 …)
    pos3: str         # さらに細かい分類 (副詞可能 …)
    ctype: str        # 活用の種類 (文語四段-ハ行, 文語助動詞-ケリ …)
    cform: str        # 活用形 (連体形-一般 …)
    lemma: str        # 語彙素 (現代の形: 言う, 有る, 白い。助動詞は けり, たり-完了 など)
    reading: str      # 語彙素の読み (カタカナ)
    base_orth: str    # 書字形の基本形 (古文の綴り: いふ, 白し)
    kana: str         # この形の現代仮名遣いの読み (ひらがな)
    chosen: str = ''  # 文脈で選んだ助動詞の意味 (受身・意志 …)
    obsolete: str = ''  # 現代語に無い語: 'table' (廃語の表で訳した) / 'unknown' (表に無く、形だけ現代語にした)

    @property
    def form(self):
        """活用形の名前 (連体形)"""
        return self.cform.split('-')[0] if self.cform not in ('*', '') else ''


def available():
    return os.path.exists(os.path.join(DIC_DIR, 'sys.dic'))


@functools.lru_cache(maxsize=1)
def _tagger():
    import MeCab
    return MeCab.Tagger('-d %s -r %s' % (DIC_DIR, os.path.join(DIC_DIR, 'dicrc')))


def hiragana(katakana):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in katakana)


def parse(text):
    """文 → [Token]"""
    out = []
    for line in _tagger().parse(text).splitlines():
        if line == 'EOS' or '\t' not in line:
            continue
        surface, feature = line.split('\t', 1)
        f = next(__import__('csv').reader([feature]))
        f += ['*'] * (24 - len(f))
        kana = f[22] if f[22] not in ('*', '') else f[9]
        out.append(Token(surface=surface, pos=f[0], pos2=f[1], pos3=f[2], ctype=f[4], cform=f[5], lemma=f[7],
                         reading=f[6], base_orth=f[10], kana=hiragana(kana) if kana != '*' else surface))
    return out
