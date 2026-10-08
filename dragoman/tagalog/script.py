#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語の表記: 照合用の形 (小文字・アクセント記号なし) と、動詞の見出しの形からの態 (焦点) の判定
#
import re
import unicodedata

ACCENTS = {'̀', '́', '̂'}  # 重アクセント・鋭アクセント・曲アクセント (bilí, batà, hindî)
CONSONANTS = 'bcdfghjklmnpqrstvwxyzñ'


def key(word):
    """照合用の形: 小文字、アクセント記号を除く (ñ は残す)"""
    nfd = unicodedata.normalize('NFD', word.lower().strip())
    return unicodedata.normalize('NFC', ''.join(c for c in nfd if c not in ACCENTS))


def has_um_infix(word):
    """-um- の入った形 (bumili, kumain、母音で始まる語根は um-: umalis)"""
    return word.startswith('um') or (len(word) > 4 and word[0] in CONSONANTS and word[1:3] == 'um')


def verb_voice(word, english=''):
    """動詞の見出し (不定形) → 態 (焦点): actor (行為者)、object (対象)、locative (場所・受け手)、conveyance (移動物・
    道具・受益者: i-)、causative。分からなければ None"""
    w = key(word)
    if re.match(r'^(be |get |happen to |be able to )', english or '') and w.startswith(('ma', 'na')):
        return 'object'         # makita「(偶然) 見る」、marinig: 見られる・聞かれるものが焦点
    if w.startswith(('magpa', 'nagpa', 'pa')) and w.endswith(('in', 'hin')) is False and w.startswith(('magpa', 'nagpa')):
        return 'actor'          # magpa- (使役の行為者焦点)
    if w.startswith(('makipag', 'maki', 'mag', 'nag', 'mang', 'nang', 'maka', 'naka')):
        return 'actor'
    if w.startswith(('man', 'mam')) and len(w) > 5:
        return 'actor'          # manood, mamili
    if w.startswith(('ipag', 'ipang', 'ipa', 'isa', 'ika')) or (w.startswith('i') and len(w) > 3 and w[1] in CONSONANTS):
        return 'conveyance'     # i-: isulat (書く: 書かれる物が焦点)、ibili (買ってあげる: 受益者)
    if has_um_infix(w):
        return 'actor'
    if w.endswith(('an', 'han', 'nan')) and len(w) > 4:
        return 'locative'
    if w.endswith(('in', 'hin', 'nin')) and len(w) > 4:
        return 'object'
    if w.startswith(('ma', 'na')):
        # ma- の状態・可能の動詞: 語義が受動 (to be seen) なら対象焦点、そうでなければ行為者焦点 (matulog「眠る」)
        return 'object' if re.match(r'^(be |get |happen to |be able to )', english or '') else 'actor'
    return None
