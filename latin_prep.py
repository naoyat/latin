#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin

latin_prepositions = [
    ## Acc/Abl
    (u'in', 'Acc', '〜の中へ,〜の上へ,〜に向かって,〜に対して'),
    (u'sub', 'Acc', '〜の下へ,〜のもとへ'),
    (u'in', 'Abl', '〜の中で,〜の上で'),
    (u'sub', 'Abl', '〜の下で,〜のもとで'),

    ## Acc
    (u'ad', 'Acc', '〜の方へ,〜のところまで'),
    (u'ante', 'Acc', '〜の前に,〜以前に'),
    (u'apud', 'Acc', '〜の家で,〜のもとで'),
    (u'circum', 'Acc', '〜のまわりに'),
    (u'circā', 'Acc', '〜のまわりに'),
    (u'contrā', 'Acc', '〜に対抗して,〜に反して'),
    (u'extrā', 'Acc', '〜の外側で,〜の外へ'),
    (u'praeter', 'Acc', '〜の傍らをすぎて,〜に反して'),
    (u'prope', 'Acc', '〜の近くで'),
    (u'propter', 'Acc', '〜の近くで,〜のゆえに'),
    (u'īnfrā', 'Acc', '〜の下方へ,〜に劣って'),
    (u'inter', 'Acc', '〜の間に'),
    (u'intrā', 'Acc', '〜の内側で,〜の中へ'),
    (u'ob', 'Acc', '〜の前へ,〜ゆえに,〜の代わりに'),
    (u'per', 'Acc', '〜を通って,〜を通じて,〜により'),
    (u'post', 'Acc', '〜のうしろで,〜以後'),
    (u'suprā', 'Acc', '〜の上方に,〜をこえて'),
    (u'trāns', 'Acc', '〜をこえて,〜を通過して'),
    (u'ultrā', 'Acc', '〜の向こうに,〜をこえて'),

    ## Abl
    (u'ā', 'Abl', '〜から(離れて),〜によって'), # ā 子音 / ab 母音
    (u'ab', 'Abl', '〜から(離れて),〜によって'),
    (u'cum', 'Abl', '〜とともに,〜をもって'),
    (u'dē', 'Abl', '〜から(離れて)下へ,〜について'),
    (u'ē', 'Abl', '〜(の中)から外へ'),
    (u'ex', 'Abl', '〜(の中)から外へ'),
    (u'prae', 'Abl', '〜の前に,〜のあまり,〜に比して'),
    (u'prō', 'Abl', '〜の前に,〜のために,〜の代わりに'),
    (u'sine', 'Abl', '〜なしに'),
]

def load():
    for word, dom, ja in latin_prepositions:
        latin.latindic_register(word, {'pos':'preposition', 'surface':word, 'base':word, 'domines':dom, 'ja':ja})
