ラテン語んご

初級ラテン語リーディングに参加しながらラテン語そしてPythonと親しんでみた

## demo

```
# 音読あり
$ python latin.py -s texts/fabulae_faciles/perseus.txt

# 音読なし
$ python latin.py texts/fabulae_faciles/perseus.txt | less -R
```

## usage

```
使い方: python ./latin.py [オプション] [ファイル名]
オプション:
  -w, --no-word-detail               単語の詳細を表示しない
  -q, --no-translation               日本語訳を表示しない
  -m, --strict-macron                [REPL] 大文字でのマクロン入力を行わない
  -a, --auto-macron                  マクロンの無い入力にマクロンを推定して付けてから解析する
  -s, --speech                       合成音声で音読する (MacOS only)
  -h, --help                         オプション解説など表示して終了
```

## 音読（-s, --tts）

`-t/--tts=BACKEND` で音声合成の方式を選べます（`-s` は既定の mbrola。MBROLA が無ければ espeak）。
MBROLA のアクセントは高低アクセントが既定で、`--accent=stress` で強弱アクセントになります。

| BACKEND | 方式 |
|---|---|
| `mbrola` | 自前の音韻処理（音節・アクセント・母音の長短）で作った音素列を MBROLA の古典ラテン語音声 la1 で合成（既定） |
| `espeak` | espeak-ng のラテン語音声にテキストをそのまま渡す |
| `piper` | 自前の音韻処理で作った IPA を Piper のイタリア語/スペイン語モデルで合成 |

`speak_latin.py` 単体でも使えます（`-a pitch|stress` で MBROLA のアクセント方式、`-w` で WAV 出力）。

```
python speak_latin.py -b mbrola -a stress "Arma virumque canō, Trōjae quī prīmus ab ōrīs."
```

### セットアップ

* espeak: `brew install espeak-ng`
* mbrola: [MBROLA](https://github.com/numediart/MBROLA) をビルドして `~/.local/share/mbrola/bin/mbrola` に、
  [la1 音声](https://github.com/numediart/MBROLA-voices/tree/master/data/la1) を `~/.local/share/mbrola/voices/la1/la1` に置く
  （場所は環境変数 `MBROLA_HOME` で変更可）。macOS では次の修正が必要：
  * `make CC=gcc`（`-ansi` を外す。`swab` の宣言が衝突するため）
  * `Misc/common.h` の `#if defined(__i386) || ...` に `|| defined(__x86_64__) || defined(__aarch64__) || defined(__arm64__)` を追加
    （システムヘッダの `BIG_ENDIAN` マクロのせいでビッグエンディアンの WAV が出力されるため）
* piper: `pip install piper-tts` し、[piper-voices](https://huggingface.co/rhasspy/piper-voices) の
  `it_IT-paola-medium` 等の `.onnx` と `.onnx.json` を `~/.local/share/piper/voices/` に置く（`PIPER_VOICES` で変更可）。
  音声は `-v it_IT-paola-medium` のように指定

### 聞き取りやすさの評価

```
python tools/tts_eval.py -v -t 元テキスト.txt a.wav b.wav ...
```

Whisper（mlx-whisper または faster-whisper）にラテン語として書き起こさせ、元テキストとの WER/CER を出します。

## 動詞活用表・名詞変化表の表示

* 動詞の活用：.c[onjug] 直説法１人称現在形
* 名詞の変化表：.d[ecl] 単数主格形

```
$ python latin.py
> .conjug sum
sum, 〜である
  indicative
    active
      present
        sg
          1: sum
          2: es
          3: est
        pl
          1: sumus
          2: estis
          3: sunt
      imperfect
  ...
  infinitive
    present: esse
    perfect: fuisse
    future: futūrus esse
> .decl rEx
rēx (noun, m), 王,指導者
  sg:
    Nom: rēx
    Voc: rēx
    Acc: rēgem
    Gen: rēgis
    Dat: rēgī
    Abl: rēge
  pl:
    Nom: rēgēs
    Voc: rēgēs
    Acc: rēgēs
    Gen: rēgum
    Dat: rēgibus
    Abl: rēgibus
```

## マクロンの推定

マクロン（長音記号）の無いラテン語文に、マクロンを推定して付けます。

```
echo "Gallia est omnis divisa in partes tres" | python3 tools/macronize.py
python3 tools/macronize.py -v FILE     # 候補が複数あった語を [選んだ形|他の候補] で表示
python3 tools/macronize.py --hidden=mark FILE   # 隠れた長音の流儀 (keep / strip / mark)
python3 latin.py -a FILE               # マクロンを付けてから解析・音読
> .macron puella in silva ambulat     # REPL のコマンド (.m でも可)
```

* 辞書（手作りの辞書と Wiktionary 由来の補助辞書）から、マクロンを除いた形が一致する候補を集めます。
* 候補が複数あれば、マクロン付きテキスト（`texts/` 以下）での頻度、前置詞の支配格、隣の語との一致、
  文書の時制の傾向（物語なら完了形）などで選びます。
* [Latin Macronizer](https://github.com/Alatius/latin-macronizer)（Johan Winge）の資源を借りられる場合は、
  Morpheus の解析結果を候補の供給元に加え、RFTagger（Latin Dependency Treebank で学習したモデル）の
  品詞タグと矛盾しない候補を優先します。無ければ使わずに動きます。
* 隠れた長音（閉音節の母音 `māgnus`/`magnus`、子音の i の前の母音 `ēius`/`eius`）は資料によって
  付け方が違うので、`--hidden` で流儀を選べます（`keep`: 辞書のまま、`strip`: 付けない、
  `mark`: `texts/` と手作りの辞書から語幹ごとの知識を集めて付ける）。定義は `latin/hidden_quantity.py`。
* 精度の評価：`python3 tools/macron_eval.py`（マクロン付きのテキストからマクロンを外して推定し、元と比べる）。
  `-p DIR` で他のツールの出力も同じ物差しで採点できます。隠れた長音の流儀の違いを無視した値を主な指標とします。

  Fabulae Faciles（約1.1万語）での正解率。頻度と隠れた長音の知識は Fabulae Faciles 以外から取った公平な条件：

  | | 語単位（隠れた長音を無視） | 母音単位（隠れた長音を無視） | 語単位（厳密） |
  |---|---|---|---|
  | このプログラム（`--hidden=mark`、Morpheus + RFTagger あり） | 96.9% | 98.4% | 95.8% |
  | Latin Macronizer（`--maius`） | 96.9% | 98.4% | 94.9% |

  D'Ooge の読み物（約5,200語。流儀・著者の違う評価データ）では、隠れた長音を無視した語単位で
  このプログラム 96.4%（知識は `texts/` と Fabulae Faciles から）、Latin Macronizer 96.2%。

### Latin Macronizer の資源（任意）

```
cd ~/.local/share/latin-data
git clone https://github.com/Alatius/latin-macronizer.git
curl -LO https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/data/RFTagger.zip   # 教育・研究・評価目的なら無償
unzip RFTagger.zip && (cd RFTagger/src && make)
cd - && python3 tools/build_morpheus_dic.py
```

* `~/.local/share/latin-data/latin-macronizer/latin_macronizer/` の `macrons.txt`（Morpheus の解析結果）と
  `rftagger-ldt.model`、`~/.local/share/latin-data/RFTagger/src/rft-annotate` を使います
  （場所は `LATIN_DATA`、`LATIN_RFTAGGER`、`LATIN_RFTAGGER_MODEL` で変更可）。
* Latin Macronizer は GPL-3.0 なので、データはリポジトリに入れていません。

## テキストの目録

`texts/catalog.json` に、テキストごとの使い方を記録しています。

* `macrons`: マクロンが信頼できるか（`full` / `partial` / `none`）
* `hidden`: 隠れた長音の流儀（`mark` / `nomark` / `mixed`）
* `family`: 内容が重なるテキストのまとまり（例: Fabulae Faciles と D'Ooge のヘラクレス）
* `used_for_dictionary`: 手作りの辞書を作るのに使ったか

マクロン推定の頻度は `macrons: full` のテキストから、隠れた長音の `mark` の知識は `hidden: mark` の
テキストから集めます。評価（`tools/macron_eval.py`）は、目録で評価に使えるとされたテキストで行い、
評価するテキストと同じ `family` のテキストは知識から除きます。

**権利関係が不明なテキストはリポジトリに入れません**。`~/.local/share/latin-data/private-texts/`（`$LATIN_DATA/private-texts/`）に、
同じ書式の目録 `catalog.json` と一緒に置くと、知識・評価・テストに使われます（golden テストの正解ファイルは
その中の `golden/` に置きます）。フォルダが無ければ、それらを使うテストはスキップされます。

**目録に無いテキストは「読む対象のみ」**です（解析・翻訳・音読には使うが、知識にも評価にも使わない）。
マクロンの無いテキストを読みたいときは、`texts/` に置くだけで構いません。

## 辞書

手作りの辞書（`words/*.def`。日本語の訳語付き）を優先し、そこに無い語は Wiktionary 由来の補助辞書で引きます。
補助辞書が無くても動きます（`--no-wiktionary` で無効化も可能）。

補助辞書の作り方：

```
mkdir -p ~/.local/share/latin-data && cd ~/.local/share/latin-data
curl -LO https://kaikki.org/dictionary/Latin/kaikki.org-dictionary-Latin.jsonl.gz
mv kaikki.org-dictionary-Latin.jsonl.gz kaikki-Latin.jsonl.gz
curl -LO https://kaikki.org/dictionary/downloads/ja/ja-extract.jsonl.gz   # 日本語の訳語（任意）
cd - && python3 tools/build_wiktionary_dic.py
```

* 英語版 Wiktionary のラテン語の項目（[kaikki.org](https://kaikki.org/) の抽出データ）から、全変化形を表層形で引ける SQLite 辞書を作ります（約137万形）。
* 日本語版 Wiktionary に同じ見出し語があれば日本語の訳語を、なければ英語の訳語を使います。
* 置き場所は環境変数 `LATIN_DATA` で変更できます。データは Wiktionary 由来（CC BY-SA）なのでリポジトリには入れていません。

## テスト

```
python3 -m unittest discover -s test -p '*_test.py'
```

`test/golden_test.py` は `texts/*.txt` の解析結果を `test/golden/*.out` と比較する回帰テストです（手作りの辞書だけで解析します）。
意図して解析結果を変えたときは `UPDATE_GOLDEN=1 python3 test/golden_test.py` で更新し、差分を確認してからコミットします。

## 経緯

2013年に書いたラテン語読解プログラムを、2026年に Python 3 へ移行し、改修したものです。
2013年からの開発履歴は、権利関係が不明なテキストを含むため、非公開のリポジトリに保管しています。

## Author

@naoya_t
http://github.com/naoyat | http://twitter.com/naoya_t | http://naoyat.hatenablog.jp/

## Comment

皆さんの期待に反して（？）、今日まで書いた所では全てルールベースです。

## License

(c)2013 @naoya_t, with MIT License

