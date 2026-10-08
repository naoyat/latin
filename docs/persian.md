# ペルシア語（作りかけ）

現代ペルシア語（イラン）。語形の解析は自前の規則（動詞の接頭辞・語幹・人称語尾、名詞の複数・接語）で、見出し語・
動詞の現在語幹と過去語幹・訳語・転写（イラン式: ketâb, raftan）は Wiktionary から取り、解析・訳は共通の解析器
（`core/`）をペルシア語の設定で使います。

```
mkdir -p ~/.local/share/dragoman-data/fa && cd ~/.local/share/dragoman-data/fa
curl -L -o kaikki-Persian.jsonl.gz "https://kaikki.org/dictionary/Persian/kaikki.org-dictionary-Persian.jsonl.gz"
cd - && python3 tools/build_persian_dic.py      # → ~/.local/share/dragoman-data/fa/wiktionary.sqlite (約1.7万語)
python3 tools/samples.py --lang=fa              # サンプルの訳
python3 persian.py samples/persian.txt          # 解析の詳細 (-w, -D, -E, -s 音読, -r 転写)
```

```
دختر کوچک گل‌های زیبا را دید.   (doxtar-e kučak golhâ-ye zibâ râ did.)
  →  {小さい}娘,少女が / {美しい}花を / 見た
ما فردا به تهران خواهیم رفت.   (mâ fardâ be tehrân xâhim raft.)
  →  明日 / 私たちが / {テヘラン}〜に,〜へ / 行くだろう
```

* 動詞: (否定 na- / ne-) + (mi- 現在・継続 / be- 接続法・命令) + 現在語幹または過去語幹 + 人称語尾（mi-rav-am「私は行く」、
  na-raft-and「彼らは行かなかった」、biyâ「来い」）。過去分詞 + 繋辞の接語は現在完了（rafte-am）。母音で終わる語幹は
  y を挟む（mi-â-yad）。前つづり（bar-mi-gardad）も。同じ語幹の動詞は基本の動詞を先に（kon は kardan「する」）。
* 複数語の動詞をまとめます: 未来（xâham raft）、受動（nevešte šod「書かれた」）、過去完了（rafte bud）、
  複合動詞（名詞 + 軽動詞: kâr kardan「働く」。Wiktionary にあるもの）。
* 名詞類: 複数 -hâ / -ân、不定の -i、人称の接語（ketâbhâ-yam「私の本」）、繋辞の接語（xaste-am「私は疲れている」）。
  ZWNJ（半スペース）の前を語の本体とみなします（gol‧hâ-ye、nâme‧'i）。名詞 + -i の関係形容詞（jahâni「世界の」）は辞書に
  無くても作ります。
* エザーフェ（-e。文字には書かれない）を推定し、見出しの行の転写に補います: 名詞 + 形容詞は修飾、名詞 + 名詞は属格「〜の」。
  形容詞はエザーフェでつながったときだけ前の名詞に掛け（名詞の前に置く数量詞・最上級・序数は後ろの名詞に）、名詞 +
  形容詞 + 繋辞は述語（in ketâb xub ast「この本は良い」）。節の頭の名詞 + را の付いた名詞句は主語 + 目的語、名詞 + 名詞 +
  軽動詞の後ろの名詞は複合動詞の一部とみなし、つながないことにします。
* را（râ）の前の名詞句は目的語。前置詞の目的語とエザーフェの後ろの名詞だけを属格にして、前置詞句が後ろの目的語まで
  取り込まないようにします。主語は動詞の前の最初の名詞類（代名詞は人称が合うもの）、残りは目的語。主語の代名詞は
  省かれることが多く、動詞の人称語尾から補います（共通の解析器）。
* 否定の接頭辞は動詞の項目の `negative` で表します（共通の解析器が否定形に訳す。存在文の「〜には」も）。
* 語ごとの解説（`--no-explain` で出さない）: 不定形と現在語幹・過去語幹（raftan: rav / raft）、形の作り方、
  複合動詞の軽動詞、エザーフェ、関係形容詞、不定の -i。
* 音読（`-s`）は espeak-ng のペルシア語音声（macOS の say にはペルシア語の音声が無い）。
* 評価用に UD Persian-PerDT と Seraji（どちらも CC BY-SA 4.0）の test を `~/.local/share/dragoman-data/fa/ud/` に置き、
  `python3 tools/ud_eval.py --lang=fa [--source=perdt,seraji]` で測ります。格の無い言語なので格は測らず、属格→名詞は
  エザーフェでつながった名詞（nmod / nmod:poss）を測ります。辞書に無い語にも大まかな転写の項目を付けるので網羅率は 100% に見えます。

| UD Persian | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|
| PerDT（約2.1万語） | 48.3% | 42.1% | 86.3% | 54.9% | 43.0% |
| Seraji（約1.4万語） | 48.7% | 37.5% | 76.0% | 41.0% | 31.6% |

* まだ: 関係節（که）、名詞 + 名詞が主語 + 目的語か属格かの見分け（را の無い目的語）、存在文（در باغ درختان بزرگ هست）、
  辞書に無い語（複合語・派生語）、訳語の多くが英語、口語体。
