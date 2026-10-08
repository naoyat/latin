# D'Ooge, Latin for Beginners の読み物

Benjamin L. D'Ooge, *Latin for Beginners* (1909).
Project Gutenberg eBook [#18251](https://www.gutenberg.org/ebooks/18251)（パブリックドメイン）の巻末の読み物を
`tools/import_dooge.py` で取り込んだもの。

* `hercules.txt`: The Labors of Hercules（LIV〜LX）。Ritchie の Fabulae Faciles のヘラクレスの話を
  もとに書き直したものなので、`texts/fabulae_faciles/hercules.txt` と内容が重なる。
* `lentulus.txt`: P. Cornelius Lentulus: The Story of a Roman Boy（LXI〜LXXVI）。
* 英語の見出し・説明、脚注、挿絵の注記、強勢の記号（´）、短音記号（ĕ など）は除いた。綴りは原文のまま。
* 隠れた長音（`magnus`、`eius`）には Fabulae Faciles ほど印を付けない流儀。
* 電子化の誤りと思われる箇所がある（`lūlia` → Iūlia、`sūmmit` → sūmit、`genit` → gerit、
  `plāribus` → plūribus、マクロンの落ち `Rōmāni` など）。マクロン推定の評価に使うときは、正解側の誤りも含む。
