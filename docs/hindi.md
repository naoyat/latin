# ヒンディー語（作りかけ）

Wiktionary の変化表（名詞の直格・斜格、形容詞の性・数、動詞の分詞・未来・接続法・命令、代名詞の能格・与格）を
語形の辞書にし（約20万形）、解析・訳は共通の解析器（`core/`）をヒンディー語の設定で使います。ウルドゥー語は文法が
同じなので、同じ解析器にウルドゥー文字の入口を付けています（[docs/urdu.md](urdu.md)）。

```
mkdir -p ~/.local/share/dragoman-data/hi && cd ~/.local/share/dragoman-data/hi
curl -L -o kaikki-Hindi.jsonl.gz "https://kaikki.org/dictionary/Hindi/kaikki.org-dictionary-Hindi.jsonl.gz"
cd - && python3 tools/build_hindi_dic.py        # → ~/.local/share/dragoman-data/hi/wiktionary.sqlite (約2.4万語、約20万形)
python3 tools/samples.py --lang=hi              # サンプルの訳
python3 dragoman.py --lang=hi samples/hindi.txt              # 解析の詳細 (-w, -D, -E, -s 音読, -r 転写)
```

```
लड़के ने किताब पढ़ी।   (laṛke ne kitāb paṛhī.)
  →  少年,息子が / 本を / 読んだ,学んだ
मेरे पास एक नई किताब है।   (mere pās ek naī kitāb hai.)
  →  {私}〜のところに / {新しい}本が / ある
```

* 転写: 辞書にある語は Wiktionary の転写から作ります（見出し語はそのまま、変化形は見出し語で規則と違う所を同じ位置に
  写す: parameśvar → parameśvarõ）。辞書に無い語はデーヴァナーガリーから規則で作ります。内在の a は語末と
  「母音 + 子音 _ 子音 + 母音」の位置で読まず（कमरा kamrā、समझना samajhnā）、anusvāra は後ろの子音で読み分けます
  （Wiktionary の転写を数えて決めた: अंश añś、सिंह sĩh）。規則だけでの Wiktionary の見出し語の転写との一致は約92%。
  外れの多くは複合語の境目（śabdkoś）、サンスクリット系の語の語末（prayatna）、ヌクタの無い綴り（jabān / zabān）で、
  文脈から a の有無を学ばせる方法も試しましたが、規則への上乗せは +0.4 ポイントほどでした。
* 動詞と助動詞・補助動詞の並びを1つの動詞にまとめます: 習慣（paṛhtā hai「読む」）、進行（paṛh rahā hai「読んでいる」、
  khel rahe the「遊んでいた」）、完了（paṛhā / paṛhā thā）、未来（jāẽge）、可能（bol saktā「話せる」）、受動（likhā gayā
  「書かれた」）、複合動詞（kar diyā）、義務（paṛhnā hai / cāhie）。
* 後置詞は前の名詞（斜格）に掛けます: ne → 主語（能格。完了形の他動詞の文）、ko → 目的語「〜を」か与格「〜に」（ほかに目的語
  があるか、देना など与える・告げる動詞なら与格）、kā / kī / ke → 属格「〜の」（後ろの名詞に掛ける。共通の解析器の
  `genitive_precedes_head`）、mẽ・par・se・ke liye など → 後置詞句（共通の解析器の前置詞句にするため名詞句の前に移す）。
  複合後置詞（ke liye, ke bāre mẽ）と、所有の形容詞 + 名詞由来の後置詞（mere pās「私のところに」）は1語にまとめます。
* 主語: ne の句、無ければ動詞と人称・性・数の合う直格の名詞句。完了形の他動詞で ne の句が無ければ（主語の省略）
  直格の名詞句は目的語（Wiktionary の他動性を使う）。移動の動詞の後置詞の無い行き先は「〜に」（skūl jātā hū̃「学校に行く」）。
* yah / vah + 名詞は「この / その」（斜格の is / us の後ろの名詞も斜格: is sāl「今年」）、ek + 名詞は不定の印（訳に出さない）。
* 語ごとの解説（`--no-explain` で出さない）: 動詞の形（未完了分詞・完了分詞・未来…）、性・数の一致、能格、斜格。
* 音読（`-s`）は macOS の say のヒンディー語音声 Lekha。
* 評価用に UD Hindi-HDTB（CC BY-NC-SA 4.0）の test を `~/.local/share/dragoman-data/hi/ud/` に置き、
  `python3 tools/ud_eval.py --lang=hi` で測ります。UD の格（直格・斜格）と解析器の格（後置詞の働きで読み替えたもの）は
  体系が違うので格は測りません。HDTB は受動文の主語（mūrti sthāpit kī gaī「像が据えられた」の mūrti）を目的語とするので、
  目的語の数字は低めに出ます。

| UD Hindi | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|
| HDTB（約3万語） | 36.8% | 41.2% | 91.5% | 53.0% | 29.7% |

* まだ: 関係節（jo … vah）、従属節（ki）、複合動詞（名詞 + karnā）の訳、与格の主語（mujhe … pasand hai）、
  訳語の多くが英語（日本語は約1,400語 + 手作りの表）。
