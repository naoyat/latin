#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 英語 → サンスクリットの表を Apte の英梵辞典から作る (文の生成 dragoman/generate の語の置き換えで、
# kaikki 由来の表 sa/en-index.tsv を補う)
#
#   python3 tools/build_sanskrit_apte.py
#
# 見出し語の最初の語義 (2 以下の語義・派生語 [Girl]hood・例文 ‘…’ は除く) から、品詞ごとにサンスクリットの語を取る:
#   名詞 (s.): 主格の形から語幹と性 (pustakaM → pustaka 中性、nfpaH → nfpa 男性、kanyA → kanyA 女性。
#             語幹のまま書いた語は後ろの m. / f. / n. で: rAjan m.)
#   動詞 (v. t. / v. i.): 語根と類 (dfS 1 P → dfS 第1類)。接頭辞つき (vi-saM-ava-…)・使役 (c.) は除く
#   形容詞 (a.)・副詞 (adv.): 語幹のまま
#
# 入力: $DRAGOMAN_DATA/sa/apte-ae/xml/ae.xml
#   (V. S. Apte, The Student's English-Sanskrit Dictionary, 1884。Cologne Digital Sanskrit Dictionaries の電子版
#    https://sanskrit-lexicon.uni-koeln.de/scans/AEScan/2020/web/ 。電子版は CC BY-NC-SA 3.0)
# 出力: $DRAGOMAN_DATA/sa/en-index-apte.tsv (sa/en-index.tsv と同じ列 + 候補の順位。参照だけの見出しは英語の列が
#       chest=box。手元だけで使う (非営利・継承))
#
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths

ENTRY = re.compile(r'<H1><h><key1>([^<]+)</key1>.*?<body>(.*?)</body>', re.S)
POS_MARK = re.compile(r'<i><ab>(s|v\. t|v\. i|a|adv)\.</ab></i>')
POS = {'s': 'noun', 'v. t': 'verb', 'v. i': 'verb', 'a': 'adj', 'adv': 'adv'}
SKT = re.compile(r'<s>([^<]+)</s>((?:\s*\d+)?(?:\s*<ab>[^<]+</ab>)*)')
GENDER = {'m.': 'm', 'f.': 'f', 'n.': 'n'}


def first_sense(body):
    """最初の語義だけ: 2 番目の語義 (<b>2</b>) と派生語 (<b>[Girl]hood</b>) の前まで"""
    cut = re.search(r'<div n="lb"/>\s*<b>(?:\d|\[)', body)
    return body[:cut.start()] if cut else body


def sections(body):
    """品詞の印で区切った (品詞, 本文) の列。例文 (‘…’) の後ろは捨てる"""
    marks = list(POS_MARK.finditer(body))
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(body)
        text = body[m.end():end]
        text = text.split('‘')[0]   # 例文・句の訳より前
        yield POS[m.group(1)], text


def noun_stem(word, gender):
    """主格 → (語幹, 性)"""
    for ending, stem_end, g in (('aM', 'a', 'n'), ('aH', 'a', 'm'), ('iH', 'i', 'm'), ('uH', 'u', 'm'),
                                ('A', 'A', 'f'), ('I', 'I', 'f'), ('UH', 'U', 'f')):
        if word.endswith(ending):
            return word[:-len(ending)] + stem_end, gender or g
    return word, gender


def words(text, pos):
    out = []
    for m in SKT.finditer(text):
        group, after = m.group(1), m.group(2)
        if '°' in group:
            continue
        abbrevs = re.findall(r'<ab>([^<]+)</ab>', after)
        if 'c.' in abbrevs:
            continue   # 使役
        gender = next((GENDER[a] for a in abbrevs if a in GENDER), '')
        gana = (re.findall(r'\d+', after) or [''])[0]
        items = [w.strip() for w in group.split(',') if w.strip()]
        for k, w in enumerate(items):
            if ' ' in w or not re.fullmatch(r'[a-zA-Z]+', w.replace('-', '')):
                continue
            if pos == 'verb':
                if '-' in w or k < len(items) - 1 and not gana or w.endswith('ati'):
                    continue   # 接頭辞の並び (ut-vi-sfj)、類の分からない語根、活用形 (arpayati)
                out.append((w, '', gana if k == len(items) - 1 else ''))
            elif pos == 'noun':
                stem, g = noun_stem(w.replace('-', ''), gender if k == len(items) - 1 else '')
                out.append((stem, g, ''))
            else:
                out.append((w.replace('-', ''), '', ''))
    return out


def main():
    src = paths.data('sa', 'apte-ae', 'xml', 'ae.xml')
    out = paths.data('sa', 'en-index-apte.tsv')
    with open(src, encoding='utf-8') as f:
        xml = f.read()
    rows, refs = {}, {}
    for m in ENTRY.finditer(xml):
        key, body = m.group(1).strip().lower(), first_sense(m.group(2))
        for pos, text in sections(body):
            found = words(text, pos)
            if found:
                rows.setdefault(key, []).extend((pos, w) for w in found)
            else:   # 参照だけの見出し (Chest: See Breast, and Box) は参照先の語で
                refs.setdefault(key, []).extend((pos, r.lower()) for r in re.findall(r'<b>([A-Za-z]+)</b>', text))
    n = 0
    with open(out, 'w', encoding='utf-8') as f:
        for key in list(rows) + [k for k in refs if k not in rows]:
            # 参照先の語は、英語の列を「見出し=参照先」に (chest=box。訳語を選ぶとき参照先の英語で日本語と照らす)
            entries = [(pos, w, key) for pos, w in rows.get(key, [])] or \
                [(pos, w, key + '=' + ref) for pos, ref in refs[key] for p, w in rows.get(ref, []) if p == pos]
            ranks = {}
            for pos, (lemma, gender, gana), english in entries:
                rank = ranks[pos] = ranks.get(pos, -1) + 1
                f.write('\t'.join((lemma, pos, english, gender, gana, '3', str(rank))) + '\n')
                n += 1
    print('%d rows → %s' % (n, out))


if __name__ == '__main__':
    main()
