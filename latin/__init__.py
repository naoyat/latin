# ラテン語 (辞書、変化形の生成、マクロンの推定、品詞タガー、発音、ラテン語の解析の前処理)。
# 共通の解析器 (core/) を using() の外で使うときの既定の言語をラテン語にする
from core import language as _language
from .profile import LATIN as _LATIN

_language.set_default(_LATIN)
