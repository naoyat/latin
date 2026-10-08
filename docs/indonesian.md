# インドネシア語・マレー語（作りかけ）

オーストロネシア語族のインドネシア語（`id`）と、ほぼ同じ言語のマレー語（`ms`）を、語を接辞と接語に分けて辞書を引き、
語順から格の枠を決めて日本語に訳します。語順が日本語と違う（主語-動詞-目的語、修飾語は名詞の後ろ）ので、ペルシア語・
ヒンディー語と同じく共通の解析器（格の枠を決めて日本語の語順に並べ替える）を使います。マレー語は同じ解析器を、
マレー語の辞書の項目を先に引く設定で使います（kerana / karena、wang / uang、Inggeris / Inggris などの綴りの違い）。

```
./dragoman.py id -e "Anak itu membaca buku di sekolah."
  →  {その}子供が / {学校}で / 本を / 読む
./dragoman.py id samples/indonesian.txt          # -w で語ごとの辞書引きを省く
./dragoman.py ms -e "Saya pergi ke sekolah kerana hendak belajar bahasa Inggeris."
python3 tools/samples.py --lang=id
```

## 準備

```
mkdir -p ~/.local/share/dragoman-data/id/ud ~/.local/share/dragoman-data/ms
cd ~/.local/share/dragoman-data
curl -L -o id/kaikki.org-dictionary-Indonesian.jsonl https://kaikki.org/dictionary/Indonesian/kaikki.org-dictionary-Indonesian.jsonl
curl -L -o ms/kaikki.org-dictionary-Malay.jsonl https://kaikki.org/dictionary/Malay/kaikki.org-dictionary-Malay.jsonl
cd - && python3 tools/build_indonesian_dic.py     # → ~/.local/share/dragoman-data/id/wiktionary.sqlite (約5.7万項目)
```

評価用に UD Indonesian-GSD・CSUI（CC BY-SA 4.0）・PUD（CC BY-SA 3.0）の test を `~/.local/share/dragoman-data/id/ud/` に置きます。

## しくみ

* 語形（`indonesian/morphology.py`）: 辞書（Wiktionary）にある形はそのまま引き、「active of baca」「passive of menulis」の
  つながりは語根の訳語に引き当てる。辞書に無ければ接辞を外して語根を引く:
  * meN-（能動）の鼻音と語根の頭の交替: menulis ← tulis、memakai ← pakai、menyapu ← sapu、mengirim ← kirim、
    membaca ← baca、mendengar ← dengar、melihat ← lihat、mengecat ← cat
  * di-（受動）、ber-（自動詞・〜を持つ。berencana ← rencana は r が1つ落ちる）、ter-（状態・最上級）、memper- / diper-、
    -kan、-i、-an、ke-…-an（抽象名詞: kebersihan ← bersih）、pe(N)-（〜する人）、pe(N)-…-an、per-…-an、se-
  * 接語: -nya（彼の・その）、-ku（私の）、-mu（あなたの）は前の名詞の所有者（anaknya → 彼の子供）。-lah・-kah・-pun
  * 重複: anak-anak → 子供（複数）
* 文（`indonesian/analyzer.py`）:
  * 動詞の前の、前置詞の目的語でない最初の名詞類が主語、動詞の後ろの名詞類が目的語（自動詞の表の動詞・受動・繋辞を除く）。
    di- の受動は前の名詞が主語（受け手）、oleh が動作主（Buku itu ditulis oleh guru → その本が先生によって書かれる）。
    引用の後の報告の動詞（…, kata dia）は後ろの名詞が主語。
  * 前置詞句（di で、ke へ、dari から、kepada に、oleh によって …、di atas の上に など2語の前置詞）。
  * 名詞 + 名詞・代名詞・固有名詞は所有（kucing saya → 私の猫、pemerintah Indonesia → インドネシアの政府）、
    bahasa + 国名は「〜語」（bahasa Jepang → 日本語）。
  * 指示詞（ini / itu）は前の名詞に掛け、その後ろの形容詞・名詞は述語。動詞の無い節には見えない繋辞を補う
    （Rumah itu besar → その家は大きい、Dia guru → 彼は先生である）。
  * yang の関係節は連体節にして前の名詞に（Orang yang membaca buku itu → その本を読む人、
    buku yang ditulis oleh guru → 先生によって書かれる本）。
  * 時制・相: sudah / telah → 過去、akan → 未来、sedang → 進行、時の副詞（kemarin → 過去、besok → 未来）。
    否定 tidak / bukan / belum。助動詞的な語は後ろの動詞と1つに（ingin belajar → 勉強したい、bisa membaca →
    読むことができる、harus pergi → 行かなければならない、boleh → 〜てもよい）。
* 訳語は Wiktionary の英語の語義を、ほかの言語と共通の英語 → 日本語の表で日本語に。よく使う語は表で決める。
* 音読（`-s`）は macOS の say のインドネシア語音声 Damayanti（マレー語は Amira）、無ければ espeak-ng。
* `auto`（言語の推定）: ラテン文字の文に yang, dan, di, ini, itu … が2つ以上あればインドネシア語、kerana, sahaja,
  bahawa … があればマレー語。

## 評価

```
python3 tools/ud_eval.py --lang=id [--source=gsd,csui,pud]
```

| UD Indonesian（GSD・CSUI・PUD の test、約3万語） | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|
| | 59.3% | 46.7% | 68.5% | 58.9% | 65.1% |

## まだ

* 数詞と類別詞（dua orang anak「二人の子供」）、比較（lebih … daripada）、命令・依頼（tolong, silakan）。
* 時制の無い文の時制（文脈で過去にする）、語の多義の選び分け（kata: 語 / 言う）。
* 接辞の付いた語の訳語（kebersihan は「清潔」ではなく bersih「清潔な」のまま）。
* タガログ語（次に。フィリピン型の態の仕組み）。
