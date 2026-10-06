#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 辞書に無い叙事詩 (ホメロス)・イオニア方言の語形を、辞書にあるアッティカ方言の形に読み替える
#
#   ἀγορήν → ἀγοράν, Ἥρη → Ἥρα            イオニア方言の η (アッティカ方言の ᾱ)
#   ἑτάροισι → ἑτάροις, κονίῃσι → κονίαις  叙事詩の複数与格 -οισι(ν) -ῃσι(ν) -εσσι(ν)
#   Οὐλύμποιο → Οὐλύμπου, Ἀτρεΐδαο → -ου  叙事詩の単数属格 -οιο -αο -εω
#   μέσσον → μέσον, Ἀχιλεύς → Ἀχιλλεύς    重子音の揺れ
#   πρόσθε → πρόσθεν, νηυσί → ναυσί
#
# 候補はアクセント・気息記号を除いた形で作り、辞書の「記号を除いた形」の照合で引く
#
from . import dictionary, orthography

# 語尾の置き換え (記号を除いた形)。上から順に試す
ENDINGS = [
    ('οισιν', 'οισ'), ('οισι', 'οισ'), ('ησιν', 'αισ'), ('ησι', 'αισ'), ('ησιν', 'ησι'),
    ('εσσιν', 'σι'), ('εσσι', 'σι'), ('εσσιν', 'εσι'), ('εσσι', 'εσι'), ('σιν', 'σι'),
    ('οιο', 'ου'), ('αο', 'ου'), ('εω', 'ου'), ('αων', 'ων'), ('εων', 'ων'),
    ('ηοσ', 'εωσ'), ('ηοσ', 'εοσ'), ('ηα', 'εα'), ('ηι', 'ει'), ('ηεσ', 'εισ'),
    ('η', 'α'), ('ην', 'αν'), ('ησ', 'ασ'), ('ηι', 'αι'),
    ('θε', 'θεν'),
]
STEMS = [('σσ', 'σ'), ('λλ', 'λ'), ('λ', 'λλ'), ('ππ', 'π'), ('ττ', 'τ'), ('νη', 'να'), ('νη', 'νε')]


def _candidates(flat):
    seen = set()

    def add(c):
        if c and c != flat and c not in seen:
            seen.add(c)
            yield c

    for old, new in ENDINGS:
        if flat.endswith(old):
            yield from add(flat[:-len(old)] + new)
    for old, new in STEMS:
        if old in flat:
            replaced = flat.replace(old, new, 1)
            yield from add(replaced)
            for e_old, e_new in ENDINGS:  # 語幹と語尾の両方 (Ἀχιλῆος → Ἀχιλλέως)
                if replaced.endswith(e_old):
                    yield from add(replaced[:-len(e_old)] + e_new)


def attic(word):
    """辞書に無い語の、辞書にある読み替え (記号を除いた形)。見つからなければ None"""
    if not dictionary.available():
        return None
    for candidate in _candidates(orthography.flat(word)):
        if dictionary.lookup(candidate):
            return candidate
    return None
