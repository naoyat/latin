#!/usr/bin/env python
# -*- coding: utf-8 -*-

import latin

# <56> 等位接続詞
latin_conjs_1 = [
    # (1) 連結
    (u'et', '〜と〜,そして〜,〜も'), # and
    (u'-que', '〜と(他の語と1語をなす。etよりも2項の結合が密接)'),
    (u'atque', '〜および〜(第2項に重点がある)'), # and also
    (u'ac', '〜および〜(第2項に重点がある)'), # and also
    (u'et ... et', '〜も〜も'),
    (u'neque', 'そして〜ない'), # and not
    (u'nec', 'そして〜ない'),
    (u'neque ... neque', '〜もない〜もない'),
    (u'nec ... nec', '〜もない〜もない'),
    (u'cum ... tum', '〜も,また〜も'),
    (u'nōn sūlum ... sed etiam', '〜のみならずまた〜'),
    (u'nōn modo ... sed etiam', '〜のみならずまた〜'),

    # (2) 選択
    (u'aut', '〜かあるいは〜'),
    (u'vel', '〜または〜'),
    (u'-ve', '〜または〜(他の語と1語をなす)'),
    (u'sīve', '〜あるいは〜'), # or
    (u'seu', '〜あるいは〜'), # or
    (u'aut ... aut', '〜か〜か'),
    (u'vel ... vel', '〜か〜か'),
    (u'sīve ... sīve', '〜か〜か'),
    (u'seu ... seu', '〜か〜か'),

    # (3) 相反
    (u'sed', 'しかし,[〜ではなく]て'),
    (u'vērum', 'しかし'),
    (u'autem', 'ところで'), # しかし,さらに,一方'})
    (u'vēro', 'しかし'),
    (u'at', 'これに反して'),
    (u'atquī', 'しかしそれでも'),
    (u'tamen', 'しかしながら,それでも'), # cependant

    # (4) 因由（原因・理由）
    (u'nam', 'というのは,すなわち'),
    (u'namque', 'というのは,すなわち'),
    (u'enim', 'というのは,すなわち'),
    (u'etenim', 'というのは,すなわち'),

    # (5) 結果
    (u'itaque', 'こうして,だから,それ故に'), # et ainsi, et de cette maniere; donc, aussi, ainsi donc, 従って,だから
    (u'igitur', 'そこで,だから,こうして'), # dans ces circonstances, alors
    (u'ergō', 'それ故に,従って'), # a cause de ; donc, ainsi donc, par consequent
    (u'ideō', 'それゆえ'), # pour cela, pour cette raison, a cause de cela
    (u'quamobrem', 'なぜ,だから'), # pourquoi, c'est pourquoi
    (u'quārē', 'どうやって,なぜ'), # par quoi, par quel moyen ? ; pourquoi,
    ]

# <57> 従属接続詞
latin_conjs_2 = [
    # (1) 時間関係
    (u'postquam', '〜したのち'),
    (u'posteāquam', '〜したのち'),
    (u'ubi', '〜するとき,〜するやいなや,〜するたびに'),
    (u'ubī', '〜するとき,〜するやいなや,〜するたびに'),
    (u'antequam', '〜するまえに'),
    (u'priusquam', '〜するまえに'),
    (u'dum', '〜するあいだ,〜するかぎり,〜するまで'),
    (u'cum', '〜したとき,〜するたびに,〜する一方,〜して以来'),
    (u'cum prīmum', '〜するやいなや'),
    (u'simul atque', '〜するやいなや'),
    (u'simul ac', '〜するやいなや'),

    # (2) 目的
    (u'ut', '〜するように,〜するために'),
    (u'uti', '〜するように,〜するために'),
    (u'utī', '〜するように,〜するために'),
    (u'nē', '〜しないように,〜しないことを'),
    (u'quō', '(+比較級)さらに〜するように'),
    (u'nēve', 'また〜しないように'),
    (u'neu', 'また〜しないように'),

    # (3) 仮定
    (u'sī', 'もし'),
    (u'nisi', 'もしなければ'),
    (u'nī', 'もしなければ'),
    (u'quodsī', 'しかしもし'),
    (u'quod sī', 'しかしもし'),
    (u'quasī', 'あたかも〜するごとく'),
    (u'velut sī', 'あたかも〜するごとく'),
    (u'tamquam sī', 'あたかも〜するごとく'),
    (u'ac sī', 'あたかも〜するごとく'),
    (u'dum', '〜しさえすれば'),
    (u'modo', '〜しさえすれば'),
    (u'dummodo', '〜しさえすれば'),

    # (4) 因由
    (u'quod', '〜するゆえに'),
    (u'quia', '〜するゆえに'),
    (u'quoniam', '〜するので,〜したのち'),
    (u'ut', '〜するゆえに'),
    (u'quandō', '〜するゆえに'),
    (u'cum', '〜するゆえに'),

    # (5) 結果
    (u'ut', '〜するほど,〜なので'),
    (u'quīn', '〜しないほど'),
    (u'quōminus', '〜しないほど'),

    # (6) 認容（譲歩）
    (u'tametsī', '〜するけれども,〜するとしても'),
    (u'etsī', '〜するけれども,〜するとしても'),
    (u'etiamsī', '〜するけれども,〜するとしても'),
    (u'quamvīs', '〜するとしても'),
    (u'cum', '〜するけれども'),
    (u'quamquam', '〜するけれども'),
    (u'ut', '〜するとしても'),

    # (7) quod
    (u'quod', '〜すること[を]'), # (英:that)
    ]

def load():
    for word, ja in latin_conjs_1:
        latin.latindic_register(word, {'pos':'conj', 'surface':word, 'ja':ja})

    for word, ja in latin_conjs_2:
        latin.latindic_register(word, {'pos':'conj', 'surface':word, 'ja':ja})
