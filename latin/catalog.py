#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# テキストの目録 (texts/catalog.json)
#
# テキストごとに「どう使ってよいか」を記録する:
#   - マクロン推定の知識 (頻度・隠れた長音) に使えるか
#   - マクロン推定の評価データに使えるか、評価するときに知識から除くべきテキスト (同じ family)
# 目録に無いテキストは「読む対象のみ」(知識にも評価にも使わない)
#
# 権利関係が不明なテキストはリポジトリに入れず、$DRAGOMAN_DATA/private-texts/ に
# 同じ書式の目録 (catalog.json) と一緒に置く。両方の目録を合わせて使う
#
import os
import json
from core import paths

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTS_DIR = os.path.join(ROOT, 'texts')
CATALOG_PATH = os.environ.get('LATIN_CATALOG', os.path.join(TEXTS_DIR, 'catalog.json'))
DATA_DIR = paths.DATA_DIR
PRIVATE_TEXTS_DIR = os.path.join(DATA_DIR, 'private-texts')


class Entry:
    def __init__(self, path, info, base_dir=TEXTS_DIR):
        self.path = path  # 絶対パス
        self.info = info
        self.base_dir = base_dir

    @property
    def name(self):
        return os.path.relpath(self.path, self.base_dir)

    @property
    def private(self):
        return self.base_dir != TEXTS_DIR

    @property
    def macrons(self):
        return self.info.get('macrons', 'none')

    @property
    def hidden(self):
        return self.info.get('hidden', 'mixed')

    @property
    def family(self):
        return self.info.get('family', self.name)

    @property
    def used_for_dictionary(self):
        return bool(self.info.get('used_for_dictionary', False))

    @property
    def knowledge(self):
        return self.info.get('knowledge', self.macrons == 'full')

    @property
    def evaluation(self):
        return self.info.get('evaluation', self.macrons == 'full' and not self.used_for_dictionary)


class Catalog:
    def __init__(self, path=CATALOG_PATH, texts_dir=TEXTS_DIR, extra=()):
        """extra: 追加で読む (目録のパス, テキストのフォルダ) の組"""
        self.texts_dir = texts_dir
        self.entries = {}
        self.dictionary = {}
        for catalog_path, base_dir in [(path, texts_dir)] + list(extra):
            if not os.path.exists(catalog_path):
                continue
            with open(catalog_path, encoding='utf-8') as fp:
                data = json.load(fp)
            if 'dictionary' in data:
                self.dictionary = data['dictionary']
            for name, info in data.get('texts', {}).items():
                full = os.path.abspath(os.path.join(base_dir, name))
                self.entries[full] = Entry(full, info, base_dir)

    def get(self, path):
        return self.entries.get(os.path.abspath(path))

    def existing(self):
        return [e for e in self.entries.values() if os.path.exists(e.path)]

    def knowledge_files(self):
        """マクロン推定の頻度に使うテキスト (マクロンが信頼できるもの)"""
        return sorted(e.path for e in self.existing() if e.knowledge)

    def hidden_mark_files(self):
        """隠れた長音の「印を付ける」流儀の知識に使うテキスト"""
        return sorted(e.path for e in self.existing() if e.knowledge and e.hidden == 'mark')

    def evaluation_files(self):
        return sorted(e.path for e in self.existing() if e.evaluation)

    def family_of(self, path):
        """評価するときに知識から除くテキスト (同じ family。目録に無ければそのファイルだけ)"""
        entry = self.get(path)
        if entry is None:
            return {os.path.abspath(path)}
        return {e.path for e in self.entries.values() if e.family == entry.family}


_catalog = None


def default():
    """リポジトリの目録と、リポジトリ外 (private-texts) の目録を合わせたもの"""
    global _catalog
    if _catalog is None:
        _catalog = Catalog(extra=[(os.path.join(PRIVATE_TEXTS_DIR, 'catalog.json'), PRIVATE_TEXTS_DIR)])
    return _catalog
