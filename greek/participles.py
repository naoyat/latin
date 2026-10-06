#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の分詞の変化形を、男性単数主格の形から作る
#
# Wiktionary の動詞の活用表には分詞の主格しか無い (変化表のある分詞の項目は一部だけ) ので、規則的な変化で補う。
# アクセントは変化で位置が動くので作らず、記号を除いた形 (orthography.flat) で返す。辞書引きは
# アクセントの一致する形が無ければ記号を除いた形で照合するので、それで見つかる
#
#   -ων / -ουσα / -ον     (現在能動 λύων、第2アオリスト能動 ἐλθών、未来能動)   属格 -οντος
#   -ῶν                   (縮約動詞 ποιῶν, τιμῶν)                          属格 -οῦντος / -ῶντος
#   -ας / -ασα / -αν      (アオリスト能動 λύσας)                            属格 -αντος
#   -είς / -εῖσα / -έν    (アオリスト受動 λυθείς)                           属格 -έντος
#   -ώς / -υῖα / -ός      (完了能動 λελυκώς)                                属格 -ότος
#   -μενος / -μένη / -μενον (中動・受動 λυόμενος)                           属格 -μένου
#
from . import orthography

CASES5 = ('Nom', 'Gen', 'Dat', 'Acc')

# 第3変化の分詞 (男性・中性の語幹 + 語尾、女性は -σα 型の第1変化)
THIRD_M = {('Nom', 'pl'): 'εσ', ('Gen', 'sg'): 'οσ', ('Dat', 'sg'): 'ι', ('Acc', 'sg'): 'α',
           ('Gen', 'pl'): 'ων', ('Acc', 'pl'): 'ασ'}
THIRD_N = {('Nom', 'pl'): 'α', ('Acc', 'pl'): 'α', ('Gen', 'sg'): 'οσ', ('Dat', 'sg'): 'ι', ('Gen', 'pl'): 'ων'}
FIRST_F = {('Nom', 'sg'): '', ('Gen', 'sg'): 'σ', ('Dat', 'sg'): '', ('Acc', 'sg'): 'ν',
           ('Nom', 'pl'): 'ι', ('Gen', 'pl'): 'ων', ('Dat', 'pl'): 'ισ', ('Acc', 'pl'): 'σ'}


def _first_declension_feminine(nom):
    """-ουσα, -ασα, -εισα (女性。単数属格 -ης)。nom は記号を除いた形"""
    stem = nom[:-1]  # 末尾の α を除く
    return {('Nom', 'sg'): nom, ('Gen', 'sg'): stem + 'ησ', ('Dat', 'sg'): stem + 'η', ('Acc', 'sg'): nom + 'ν',
            ('Nom', 'pl'): stem + 'αι', ('Gen', 'pl'): stem + 'ων', ('Dat', 'pl'): stem + 'αισ',
            ('Acc', 'pl'): stem + 'ασ'}


def _third(stem, dat_pl, nom_m, nom_n, nom_f, fem_table=None):
    """第3変化の分詞: stem は斜格の語幹 (λυοντ)、dat_pl は複数与格 (λυουσι)"""
    forms = {}

    def add(form, case, number, gender):
        forms.setdefault(form, []).append((case, number, gender))

    add(nom_m, 'Nom', 'sg', 'm')
    for (case, number), ending in THIRD_M.items():
        add(stem + ending, case, number, 'm')
    for form in (dat_pl, dat_pl + 'ν'):
        add(form, 'Dat', 'pl', 'm')
        add(form, 'Dat', 'pl', 'n')
    add(nom_n, 'Nom', 'sg', 'n')
    add(nom_n, 'Acc', 'sg', 'n')
    for (case, number), ending in THIRD_N.items():
        add(stem + ending, case, number, 'n')
    for (case, number), form in (fem_table or _first_declension_feminine(nom_f)).items():
        add(form, case, number, 'f')
    return forms


def _second(nom_m):
    """-μενος / -μένη / -μενον"""
    stem = nom_m[:-2]
    m = {('Nom', 'sg'): 'οσ', ('Gen', 'sg'): 'ου', ('Dat', 'sg'): 'ω', ('Acc', 'sg'): 'ον',
         ('Nom', 'pl'): 'οι', ('Gen', 'pl'): 'ων', ('Dat', 'pl'): 'οισ', ('Acc', 'pl'): 'ουσ'}
    f = {('Nom', 'sg'): 'η', ('Gen', 'sg'): 'ησ', ('Dat', 'sg'): 'η', ('Acc', 'sg'): 'ην',
         ('Nom', 'pl'): 'αι', ('Gen', 'pl'): 'ων', ('Dat', 'pl'): 'αισ', ('Acc', 'pl'): 'ασ'}
    n = {('Nom', 'sg'): 'ον', ('Acc', 'sg'): 'ον', ('Gen', 'sg'): 'ου', ('Dat', 'sg'): 'ω',
         ('Nom', 'pl'): 'α', ('Acc', 'pl'): 'α', ('Gen', 'pl'): 'ων', ('Dat', 'pl'): 'οισ'}
    forms = {}
    for gender, table in (('m', m), ('f', f), ('n', n)):
        for (case, number), ending in table.items():
            forms.setdefault(stem + ending, []).append((case, number, gender))
    return forms


def declension(nominative):
    """男性単数主格 (アクセント付き) から {記号を除いた形: [(格, 数, 性)]}。型が分からなければ {}"""
    nom = orthography.flat(nominative)
    if nom.endswith('μενοσ'):
        return _second(nom)
    if nom.endswith('ων'):
        base = nom[:-2]
        if orthography.key(nominative).endswith('ῶν'):
            # 縮約動詞: ποιῶν → ποιοῦντος (-εω, -οω)。τιμῶν → τιμῶντος (-αω) は語幹からは分からないので両方
            forms = _third(base + 'ουντ', base + 'ουσι', nom, base + 'ουν', base + 'ουσα')
            for form, cng in _third(base + 'ωντ', base + 'ωσι', nom, base + 'ων', base + 'ωσα').items():
                forms.setdefault(form, []).extend(c for c in cng if c not in forms.get(form, []))
            return forms
        return _third(base + 'οντ', base + 'ουσι', nom, base + 'ον', base + 'ουσα')
    if nom.endswith('εισ'):
        base = nom[:-3]
        return _third(base + 'εντ', base + 'εισι', nom, base + 'εν', base + 'εισα')
    if nom.endswith('ασ'):
        base = nom[:-2]
        return _third(base + 'αντ', base + 'ασι', nom, base + 'αν', base + 'ασα')
    if nom.endswith('ωσ'):
        base = nom[:-2]
        fem = {('Nom', 'sg'): base + 'υια', ('Gen', 'sg'): base + 'υιασ', ('Dat', 'sg'): base + 'υια',
               ('Acc', 'sg'): base + 'υιαν', ('Nom', 'pl'): base + 'υιαι', ('Gen', 'pl'): base + 'υιων',
               ('Dat', 'pl'): base + 'υιαισ', ('Acc', 'pl'): base + 'υιασ'}
        return _third(base + 'οτ', base + 'οσι', nom, base + 'οσ', None, fem)
    return {}
