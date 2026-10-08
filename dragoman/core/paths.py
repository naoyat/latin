#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# データの置き場所 (辞書・コーパス・評価用のツリーバンクなど。リポジトリには入れない)
#
#   $DRAGOMAN_DATA があればそこ、無ければ ~/.local/share/dragoman-data。
#   旧名の $LATIN_DATA と ~/.local/share/latin-data も読む (改名前の環境のため)
#
import os

# リポジトリの最上位 (例文 samples/ の置き場所) と、ラテン語の手作りの辞書・テキストの置き場所 (latin/words/, latin/texts/)
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LATIN_DIR = os.path.join(REPO_ROOT, 'latin')
HOME_DATA = os.path.expanduser('~/.local/share/dragoman-data')
OLD_HOME_DATA = os.path.expanduser('~/.local/share/latin-data')


def _data_dir():
    for name in ('DRAGOMAN_DATA', 'LATIN_DATA'):
        if os.environ.get(name):
            return os.environ[name]
    if not os.path.exists(HOME_DATA) and os.path.exists(OLD_HOME_DATA):
        return OLD_HOME_DATA
    return HOME_DATA


DATA_DIR = _data_dir()


def data(*parts):
    """データの置き場所の下のパス"""
    return os.path.join(DATA_DIR, *parts)
