#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Wiktionary 由来の辞書 (lemmas.info, forms.features の形) の逆引き: 見出し語 → 語形をすべて
#
#   見出し語 (名詞・形容詞は base、動詞は pres1sg) → lemmas.id の表を最初に一度だけ作り、forms は lemma_id で引く。
#   forms に lemma_id の索引が無い古い辞書には索引を足す (tools/build_wiktionary_dic.py, build_greek_dic.py で作る索引)
#
import json
import sqlite3


class Reverse:
    def __init__(self, db):
        self.db = db
        self._ids = None
        try:
            db.execute('CREATE INDEX IF NOT EXISTS forms_lemma ON forms (lemma_id)')
            db.commit()
        except sqlite3.OperationalError:
            pass   # 書き込めない辞書: 索引なしで引く (遅い)

    def ids(self, key, lemma):
        if self._ids is None:
            self._ids = {}
            for i, base, pres in self.db.execute("SELECT id, json_extract(info, '$.base'), "
                                                 "json_extract(info, '$.pres1sg') FROM lemmas"):
                if base:
                    self._ids.setdefault(('base', base), []).append(i)
                if pres:
                    self._ids.setdefault(('pres1sg', pres), []).append(i)
        return self._ids.get((key, lemma), [])

    def forms(self, lemma, pos):
        """[(語形, 項目)]。項目は lemmas.info と forms.features を合わせた辞書"""
        ids = self.ids('pres1sg' if pos == 'verb' else 'base', lemma)
        if not ids:
            return []
        rows = self.db.execute('SELECT f.surface, l.info, f.features FROM forms f JOIN lemmas l ON l.id = f.lemma_id '
                               'WHERE f.lemma_id IN (%s) ORDER BY f.rowid' % ','.join('?' * len(ids)), ids).fetchall()
        return [(surface, dict(json.loads(info), **json.loads(features))) for surface, info, features in rows]
