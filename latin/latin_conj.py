#!/usr/bin/env python
# -*- coding: utf-8 -*-

# <56> 等位接続詞
latin_conjs_1 = [
    # (1) 連結
    ('et', '〜と〜,そして〜,〜も'), # and
    ('-que', '〜と(他の語と1語をなす。etよりも2項の結合が密接)'),
    ('atque', '〜および〜(第2項に重点がある)'), # and also
    ('ac', '〜および〜(第2項に重点がある)'), # and also
    ('et ... et', '〜も〜も'),
    ('neque', 'そして〜ない'), # and not
    ('nec', 'そして〜ない'),
    ('neque ... neque', '〜もない〜もない'),
    ('nec ... nec', '〜もない〜もない'),
    ('cum ... tum', '〜も,また〜も'),
    ('nōn sūlum ... sed etiam', '〜のみならずまた〜'),
    ('nōn modo ... sed etiam', '〜のみならずまた〜'),

    # (2) 選択
    ('aut', '〜かあるいは〜'),
    ('vel', '〜または〜'),
    ('-ve', '〜または〜(他の語と1語をなす)'),
    ('sīve', '〜あるいは〜'), # or
    ('seu', '〜あるいは〜'), # or
    ('aut ... aut', '〜か〜か'),
    ('vel ... vel', '〜か〜か'),
    ('sīve ... sīve', '〜か〜か'),
    ('seu ... seu', '〜か〜か'),

    # (3) 相反
    ('sed', 'しかし,[〜ではなく]て'),
    ('vērum', 'しかし'),
    ('autem', 'ところで'), # しかし,さらに,一方'})
    ('vēro', 'しかし'),
    ('at', 'これに反して'),
    ('atquī', 'しかしそれでも'),
    ('tamen', 'しかしながら,それでも'), # cependant

    # (4) 因由（原因・理由）
    ('nam', 'というのは,すなわち'),
    ('namque', 'というのは,すなわち'),
    ('enim', 'というのは,すなわち'),
    ('etenim', 'というのは,すなわち'),

    # (5) 結果
    ('itaque', 'こうして,だから,それ故に'), # et ainsi, et de cette maniere; donc, aussi, ainsi donc, 従って,だから
    ('igitur', 'そこで,だから,こうして'), # dans ces circonstances, alors
    ('ergō', 'それ故に,従って'), # a cause de ; donc, ainsi donc, par consequent
    ('ideō', 'それゆえ'), # pour cela, pour cette raison, a cause de cela
    ('quamobrem', 'なぜ,だから'), # pourquoi, c'est pourquoi
    ('quārē', 'どうやって,なぜ'), # par quoi, par quel moyen ? ; pourquoi,
    ]

# <57> 従属接続詞
latin_conjs_2 = [
    # (1) 時間関係
    ('postquam', '〜したのち'),
    ('posteāquam', '〜したのち'),
#    (u'ubi', '〜するとき,〜するやいなや,〜するたびに'),
#    (u'ubī', '〜するとき,〜するやいなや,〜するたびに'),
    ('antequam', '〜するまえに'),
    ('priusquam', '〜するまえに'),
    ('dum', '〜するあいだ,〜するかぎり,〜するまで'),
#    (u'cum', '〜したとき,〜するたびに,〜する一方,〜して以来,〜するゆえに,〜するけれども'),

    ('cum prīmum', '〜するやいなや'),
    ('simul atque', '〜するやいなや'),
    ('simul ac', '〜するやいなや'),

    # (2) 目的
    ('ut', '〜するように,〜するために'),
    ('uti', '〜するように,〜するために'),
    ('utī', '〜するように,〜するために'),
    ('nē', '〜しないように,〜しないことを'),
    ('quō', '(+比較級)さらに〜するように'),
    ('nēve', 'また〜しないように'),
    ('neu', 'また〜しないように'),

    # (3) 仮定
    ('sī', 'もし'),
    ('nisi', 'もしなければ'),
    ('nī', 'もしなければ'),
    ('quodsī', 'しかしもし'),
    ('quod sī', 'しかしもし'),
    ('quasī', 'あたかも〜するごとく'),
    ('velut sī', 'あたかも〜するごとく'),
    ('tamquam sī', 'あたかも〜するごとく'),
    ('ac sī', 'あたかも〜するごとく'),
    ('dum', '〜しさえすれば'),
    ('modo', '〜しさえすれば'),
    ('dummodo', '〜しさえすれば'),

    # (4) 因由
    ('quod', '〜するゆえに'),
    ('quia', '〜するゆえに'),
    ('quoniam', '〜するので,〜したのち'),
    ('ut', '〜するゆえに'),
    ('quandō', '〜するゆえに'),
#    (u'cum', '〜するゆえに'),

    # (5) 結果
    ('ut', '〜するほど,〜なので'),
    ('quīn', '〜しないほど'),
    ('quōminus', '〜しないほど'),

    # (6) 認容（譲歩）
    ('tametsī', '〜するけれども,〜するとしても'),
    ('etsī', '〜するけれども,〜するとしても'),
    ('etiamsī', '〜するけれども,〜するとしても'),
    ('quamvīs', '〜するとしても'),
#    (u'cum', '〜するけれども'),
    ('quamquam', '〜するけれども'),
    ('ut', '〜するとしても'),

    # (7) quod
    ('quod', '〜すること[を]'), # (英:that)
    ]


def load():
    items = []

    for word, ja in latin_conjs_1:
        items.append({'pos':'conj', 'surface':word, 'ja':ja})

    for word, ja in latin_conjs_2:
        items.append({'pos':'conj', 'surface':word, 'ja':ja})

    return items
