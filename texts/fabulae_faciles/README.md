# Ritchie's Fabulae Faciles

Francis Ritchie, *Fabulae Faciles: A First Latin Reader*, ed. John Copeland Kirtland (1903).
Project Gutenberg eBook [#8997](https://www.gutenberg.org/ebooks/8997)（パブリックドメイン）から
`tools/import_fabulae_faciles.py` で取り込んだもの。

* `perseus.txt`（11章）、`hercules.txt`（45章）、`argonautae.txt`（24章）、`ulixes.txt`（20章）。章の間は空行。
* 原文では長音をアキュート記号で表しているので、マクロンに置き換えた（`á` → `ā`）。
* 英語の導入文・章題・挿絵の注記は除いた。綴りは原文のまま（`Iuppiter`, `iuvenis` のように i を使う）。
