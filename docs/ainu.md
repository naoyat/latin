# アイヌ語（作りかけ）

アイヌ語（北海道方言、ローマ字）の語を人称の接辞と語幹に分け、後置詞・助詞から語順のまま日本語に訳します。
語順が日本語と同じ（主語-目的語-動詞、後置詞、修飾語は名詞の前）なので、チベット語・古文と同じく共通の解析器は通しません。

```
./dragoman.py ain samples/ainu.txt          # 知里幸惠『アイヌ神謡集』第1話の冒頭 (-w で語ごとの分解を省く)
./dragoman.py ain -e "teeta wenkur tane nishpa ne, teeta nishpa tane wenkur ne kotom shiran."
  →  昔貧乏人が今金持ちである、昔金持ちが今貧乏人のようだ。
```

```
“Shirokanipe ranran pishkan, konkanipe ranran pishkan.” arian rekpo chiki kane petesoro sapash aine, …
  →  「銀の滴がまわりに降る降る、金の滴がまわりに降る降る。」
  →  という歌を私が歌いながら川に沿って下って、人間の村の上を通りながら下の方を見ると …
```

## しくみ

* 表記: 知里幸惠のローマ字（1923）などの古い表記を、現代の表記に寄せて照合する（sh → s、ch → c、母音の後ろの
  i / u → y / w、ng → nk。kamui → kamuy、yaieyukar → yayeyukar）。人称の接辞の = は書いても書かなくてもよい。
  見出しの下にカタカナ（[ainu-utils](https://github.com/aynumosir/ainu-utils)、MIT。`pip install ainu-utils`）。
* 人称の接辞: 主語 ku=（私）、e=（あなた）、eci=（あなたたち）、ci= / a= / an=（語りの「私」）、目的語 en=（私を）、
  un=（私たちを）、i=（何かを）、自動詞の接尾辞 -as / -an（語りの「私」）。主語の名詞が無ければ「私が」などを補う
  （同じ主語は繰り返さない）。
* 後置詞（ta「で」、un「に」、orowa「から」、enkasike「の上を」…）、用言の後ろの助詞（wa「〜て」、kor / kane「〜ながら」、
  ko / akusu「〜すると」、ciki「〜たら」、kusu「〜ので」、korka「〜けれど」、sekor「〜と」、ruwe ne「〜のだ」…）、
  否定 somo、完了の a、繋辞 ne、kotom siran「〜のようだ」、名詞 + ki「する」の決まった言い方（rekpo ki → 歌う）。
* 格の印が無いので、後置詞の無い名詞は「他動詞で2つなら が・を、1つなら を、自動詞なら が」とする。
* 訳語: 手作りの語彙表（`dragoman/ainu/grammar.py`。神謡集によく出る語が中心）→ Wiktionary（約2000語）→ 動詞の単複・
  名詞の所属形の表（[ainu-morphology-data](https://github.com/aynumosir/ainu-morphology-data)。出典が既存の辞典なので
  手元だけで使う）。引けない語（人名・繰り返し句）は訳の中でカタカナにする。

## 準備

```
mkdir -p ~/.local/share/dragoman-data/ain/morphology-data && cd ~/.local/share/dragoman-data/ain
curl -L -O https://kaikki.org/dictionary/Ainu/kaikki.org-dictionary-Ainu.jsonl       # 約3MB (CC BY-SA)
for f in noun_possessives.tsv verb_plurals.tsv; do
  curl -L -o morphology-data/$f https://raw.githubusercontent.com/aynumosir/ainu-morphology-data/main/$f
done
pip install ainu-utils
```

## 資料について

* 国立国語研究所のアイヌ語口承文芸コーパス（形態素の注釈つき）と、国立アイヌ民族博物館のアイヌ語アーカイブの辞典は、
  利用条件（All rights reserved、スクレイピング・一括ダウンロードの禁止）のため使わない。調べるときの参照先にとどめる。
* 『アイヌ神謡集』（パブリックドメイン）の本文は、引けない語の多い順に語彙表を補うのに使っている（全体約5700語のうち、
  いま辞書で引けない語は約45%）。

## まだ

* 語彙表の拡充（神謡集の残り、日常語）、充当の接頭辞（e- / ko- / o-）・使役（-re / -te / -e）・複数（-pa）・名詞の
  抱合の分解、所属形（-hV / -ke）の規則。
* 語りの人称（a= / an= を「私」とするか「人」とするか）の文脈での選び分け。
* 『アイヌ神謡集』の対訳（知里幸惠の日本語訳）との突き合わせによる評価。
