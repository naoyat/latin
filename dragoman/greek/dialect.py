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
#   Οὐλύμποιο → Ὀλύμπου, ξεῖνος → ξένος   韻律のための長音化 (ου, ει) を戻す
#   πτόλεμος → πόλεμος, τεύχεα → τεύχη      語幹の違い・縮約しない語尾
#   φάτο → ἔφατο, βῆ → ἔβη, ἄγε → ἦγε      加音 (ἐ-、母音の延長) の無い過去形。複合動詞は前置詞の後に (καταβῆ → κατέβη)
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
    ('εα', 'η'), ('εοσ', 'ουσ'), ('εε', 'ει'), ('εεσ', 'εισ'),  # 縮約しない語尾 (τεύχεα → τεύχη)
]
STEMS = [('σσ', 'σ'), ('λλ', 'λ'), ('λ', 'λλ'), ('ππ', 'π'), ('ττ', 'τ'), ('νη', 'να'), ('νη', 'νε'),
         # 語幹の違う叙事詩形
         ('πτολ', 'πολ'), ('ουλ', 'ολ'), ('ξειν', 'ξεν'), ('μουν', 'μον'), ('κουρ', 'κορ'), ('γουν', 'γον'),
         ('δουρ', 'δορ'), ('ουρε', 'ορε'), ('ειν', 'εν'), ('εταρ', 'εταιρ'), ('ηελι', 'ηλι'), ('ηω', 'εω')]
# 韻律のための長音化 (ου → ο, ει → ε)。当たりすぎる (κεῖνος → κενός) ので最後に試す
LENGTHENING = [('ου', 'ο'), ('ει', 'ε')]
PAST_TENSES = {'imperfect', 'aorist', 'past-perfect'}

# 加音 (過去形の ἐ- と、語頭の母音の延長)
AUGMENT_VOWELS = [('αι', 'ηι'), ('οι', 'ωι'), ('αυ', 'ηυ'), ('ευ', 'ηυ'), ('ει', 'ηι'),
                  ('α', 'η'), ('ε', 'η'), ('ο', 'ω')]
# 複合動詞の前置詞 (加音はその後に入る)。(前置詞, 加音の前の形)
PREFIXES = [('ανα', 'αν'), ('απο', 'απ'), ('δια', 'δι'), ('επι', 'επ'), ('κατα', 'κατ'), ('μετα', 'μετ'),
            ('παρα', 'παρ'), ('αμφι', 'αμφ'), ('αντι', 'αντ'), ('υπο', 'υπ'), ('υπερ', 'υπερ'), ('περι', 'περι'),
            ('προσ', 'προσ'), ('προ', 'προ'), ('εκ', 'εξ'), ('εξ', 'εξ'), ('εν', 'εν'), ('εμ', 'εν'),
            ('συν', 'συν'), ('συμ', 'συν'), ('εισ', 'εισ')]
VOWEL_LETTERS = 'αεηιουω'


def _augmented(flat):
    """加音を補った形の候補"""
    def augment(stem):
        if not stem:
            return []
        if stem[0] not in VOWEL_LETTERS:
            return ['ε' + stem] + (['ερ' + stem] if stem[0] == 'ρ' else [])
        return [new + stem[len(old):] for old, new in AUGMENT_VOWELS if stem.startswith(old)]
    result = augment(flat)
    for prefix, before in PREFIXES:
        if flat.startswith(prefix) and len(flat) > len(prefix) + 1:
            rest = flat[len(prefix):]
            for a in augment(rest):
                # κατα + βη → κατ + εβη、ἐκ + βη → ἐξ + εβη
                result.append((before if a[0] in VOWEL_LETTERS else prefix) + a)
    return result


def _candidates(flat, stems=STEMS):
    seen = set()

    def add(c):
        if c and c != flat and c not in seen:
            seen.add(c)
            yield c

    for old, new in ENDINGS:
        if flat.endswith(old):
            yield from add(flat[:-len(old)] + new)
    for old, new in stems:
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
    flat = orthography.flat(word)
    for stems in (STEMS, LENGTHENING):
        candidates = list(_candidates(flat, stems))
        for candidate in candidates:
            if dictionary.lookup(candidate):
                return candidate
        # 加音の無い過去形 (元の形と、読み替えた形のそれぞれに加音を補う)。過去形の動詞として引けたものだけ
        for c in [flat] + candidates:
            for candidate in _augmented(c):
                if any(item.get('pos') == 'verb' and item.get('tense') in PAST_TENSES
                       for item in dictionary.lookup(candidate)):
                    return candidate
    return None
