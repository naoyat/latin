#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語の辞書 (SQLite) を Wiktionary (kaikki.org の抽出データ) から作る
#
#   python3 tools/build_tagalog_dic.py
#
# 見出し語 (小文字・アクセント記号なし) ごとの品詞・訳語 (英語の語義。日本語には実行時に core/en_ja.py で直す)、
# 動詞の態 (焦点: actor / object / locative / conveyance / benefactive …。見出しの形から)、語形の表 (語形 → 見出し語、
# アスペクト: completive / progressive / contemplative / infinitive)。語形は次から:
#   - 動詞の見出しの活用形のうち、きれいな印 (completive / progressive / contemplative) の付いたもの
#   - 「complete aspect of bilhin」のような語義 (binili → bilhin の完了)
# 辞書に無い語形は、解析 (tagalog/morphology.py) で接辞と重複を外して引く。
#
# 入力: $DRAGOMAN_DATA/tl/kaikki.org-dictionary-Tagalog.jsonl (https://kaikki.org/dictionary/Tagalog/。CC BY-SA)
# 出力: $DRAGOMAN_DATA/tl/wiktionary.sqlite (データは Wiktionary 由来 (CC BY-SA)。出力ファイルもその条件に従う)
#
import os
import re
import sys
import json
import sqlite3
import time
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.core.wiktionary_import import english_glosses
from dragoman.tagalog.script import key as normalize, verb_voice

POS = {'noun': 'noun', 'name': 'name', 'adj': 'adj', 'num': 'num', 'pron': 'pronoun', 'det': 'det',
       'verb': 'verb', 'adv': 'adv', 'conj': 'conj', 'particle': 'particle', 'prep': 'preposition',
       'intj': 'intj', 'article': 'article'}
ASPECT_LINK = re.compile(r'^(complete|completed|progressive|contemplative|imperfective|perfective) aspect of (\S+)')
ASPECTS = {'complete': 'completive', 'completed': 'completive', 'perfective': 'completive',
           'progressive': 'progressive', 'imperfective': 'progressive', 'contemplative': 'contemplative'}
FORM_OF = re.compile(r'^(?:alternative (?:form|spelling)|plural|superlative|informal spelling|'
                     r'clipping|contraction|abbreviation) of (\S+)', re.I)


def main():
    t0 = time.time()
    path = paths.data('tl', 'kaikki.org-dictionary-Tagalog.jsonl')
    out = paths.data('tl', 'wiktionary.sqlite')
    tmp = out + '.tmp'
    if os.path.exists(tmp):
        os.unlink(tmp)
    db = sqlite3.connect(tmp)
    db.executescript('''
        CREATE TABLE lemmas (key TEXT, pos TEXT, en TEXT, voice TEXT, target TEXT, senses INTEGER, word TEXT);
        CREATE TABLE forms (form TEXT, lemma TEXT, aspect TEXT);
    ''')
    lemmas, forms = [], set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            pos = POS.get(entry.get('pos'))
            word = entry.get('word', '')
            if pos is None or not word:
                continue
            key = normalize(word)
            target = None
            senses = []
            for sense in entry.get('senses', []):
                gloss = (sense.get('glosses') or [''])[0]
                m = ASPECT_LINK.match(gloss)
                if m and pos == 'verb':
                    forms.add((key, normalize(m.group(2)), ASPECTS[m.group(1)]))
                    target = target or normalize(m.group(2))
                    continue
                m = FORM_OF.match(gloss)
                if m:
                    target = target or normalize(m.group(1))
                    continue
                senses.append(sense)
            en = english_glosses(entry, senses=senses) if senses else ''
            voice = verb_voice(key, en) if pos == 'verb' else None
            lemmas.append((key, pos, en, voice, target, len(senses), word))
            if pos == 'verb' and senses:
                for form in entry.get('forms', []):
                    tags = set(form.get('tags') or [])
                    if tags & {'error-unrecognized-form', 'dialectal', 'Baybayin', 'alternative'}:
                        continue
                    if len(tags) == 1 and tags & {'completive', 'progressive', 'contemplative'} and \
                            re.fullmatch("[a-zñ'-]+", normalize(form['form'])):
                        forms.add((normalize(form['form']), key, tags.pop()))
    db.executemany('INSERT INTO lemmas VALUES (?, ?, ?, ?, ?, ?, ?)', lemmas)
    db.executemany('INSERT INTO forms VALUES (?, ?, ?)', sorted(forms))
    db.executescript('CREATE INDEX lemmas_key ON lemmas (key); CREATE INDEX forms_form ON forms (form);')
    db.commit()
    db.close()
    os.replace(tmp, out)
    print('%d entries, %d forms → %s (%.1fs)' % (len(lemmas), len(forms), out, time.time() - t0))


if __name__ == '__main__':
    main()
