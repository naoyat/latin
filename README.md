# ラテン語んご

ラテン語の文を辞書引き・構文解析して、日本語の逐語訳を付けるプログラムです。
マクロン（長音記号）の推定や、合成音声での音読もできます。

```
$ echo "Agricola in silvā magnam casam aedificat." | python3 latin.py

Agricola in silvā magnam casam aedificat .

  ---
   0  Agricola   (agricola) 農夫 [Nom.sg.m|Voc.sg.m] // []
   1  in         prep<Acc> 〜へ,〜の中へ,… | prep<Abl> 〜で,〜の中で,〜の上で
   2  silvā      (silva) 森 [Abl.sg.f] // []
   3  magnam     (magnus) a.大きな [Acc.sg.f]
   4  casam      (casa) あばら屋 [Acc.sg.f] // []
   5  aedificat  (aedificō) v.建てる 3sg 直説法.能動.現在
  ---

1 VERB FOUND: aedificat

  aedificat (indicative 3sg)
    Nom:
      Agricola
    prep:
      in <Abl>
        silvā
    Acc:
      casam
        magnam

  →  農夫が / {森}〜で,〜の中で,〜の上で / {大きな}あばら屋を / 建てる
```

## できること

* **解析と訳**: 語ごとの辞書引き（変化形からの逆引き）、並列句・形容詞と属格の係り先・前置詞句・独立奪格・述語の検出、
  名詞句の格の枠への割り当て、日本語の逐語訳（日本語の動詞は時制・態に合わせて活用）。基本はルールベースで、
  品詞タガー（任意）の判定で格の候補を絞り込む
* **マクロンの推定**: マクロンの無い文に長音記号を付ける（隠れた長音の流儀も選べる）
* **音読**: 古典ラテン語の発音規則（音節・アクセント・母音の長短）に従って音声合成する
* **変化表**: 名詞の格変化表、動詞の活用表

## セットアップ

Python 3.11 以降。日本語の動詞の活用に MeCab（辞書は UniDic）を使います。

```
pip install -r requirements.txt
```

これだけで、手作りの辞書（約1,500語）を使った解析・訳・変化表・マクロンの推定ができます。
次の追加データは任意で、無ければ使わずに動きます。データは `~/.local/share/latin-data/`
（環境変数 `LATIN_DATA` で変更可）に置き、リポジトリには入れません。

| 追加データ | 効果 | 作り方 |
|---|---|---|
| Wiktionary の補助辞書 | 未知語が大きく減る（約6万語） | [辞書](#辞書) |
| Latin Macronizer の資源（Morpheus の解析結果、RFTagger） | マクロンの推定と解析の精度が上がる | [Latin Macronizer の資源](#latin-macronizer-の資源) |
| 音声合成（MBROLA / espeak-ng / Piper） | 音読 | [音読](#音読) |

## 使い方

```
python3 latin.py [オプション] [ファイル...]    # ファイルを解析
python3 latin.py [オプション]                  # 対話モード (REPL)
```

| オプション | |
|---|---|
| `-w`, `--no-word-detail` | 語ごとの辞書引きの結果を表示しない |
| `-q`, `--no-translation` | 日本語訳を表示しない |
| `-m`, `--capital-to-macron` | 大文字の母音を長母音として読む（`rEx` → `rēx`。主に対話モードでの入力用） |
| `-a`, `--auto-macron` | マクロンの無い入力にマクロンを推定して付けてから解析する |
| `-s`, `--speech` | 音読する（既定の方式） |
| `-t`, `--tts=BACKEND` | 音読の方式を指定する（`mbrola` / `espeak` / `piper`） |
| `--accent=ACCENT` | MBROLA のアクセント（`pitch`: 高低（既定）/ `stress`: 強弱） |
| `--no-wiktionary` | 手作りの辞書だけを使う |

対話モードでは、ラテン語の文を入力すると解析します。`.` で始まる行はコマンドです。

| コマンド | |
|---|---|
| `.decl 語` (`.d`) | 名詞の格変化表（単数主格で指定） |
| `.conjug 語` (`.c`) | 動詞の活用表（直説法現在1人称単数で指定） |
| `.macron 文` (`.m`) | マクロンを推定して付ける |
| `.lookup 語` (`.l`) | 辞書の項目をそのまま表示する |

```
$ python3 latin.py -m
> .decl rEx
rēx (noun, m), 王,指導者
  sg:
    Nom: rēx
    Voc: rēx
    Acc: rēgem
    Gen: rēgis
    ...
> .macron puella in silva ambulat
puella in silvā ambulat
```

## マクロンの推定

```
echo "Gallia est omnis divisa in partes tres" | python3 tools/macronize.py
python3 tools/macronize.py -v FILE              # 候補が複数あった語を [選んだ形|他の候補] で表示
python3 tools/macronize.py --hidden=mark FILE   # 隠れた長音の流儀 (keep / strip / mark)
```

* 辞書（手作りの辞書、Wiktionary、Morpheus）から、マクロンを除いた形が一致する候補を集め、
  複数あれば次の手がかりで選びます: マクロン付きテキストでの頻度、品詞タガーの判定、前置詞の支配格、
  隣の語との一致、文書の時制の傾向（物語なら完了形）。
* **隠れた長音**（閉音節の母音 `māgnus`/`magnus`、子音の i の前の母音 `ēius`/`eius`）は資料によって
  付け方が違うので、`--hidden` で流儀を選べます。`keep`: 辞書のまま、`strip`: 付けない、
  `mark`: マクロン付きテキストから語幹ごとの知識を集めて付ける。定義は `latin/hidden_quantity.py`。

### 精度

`tools/macron_eval.py` で、マクロン付きのテキストからマクロンを外して推定し、元と比べます。
隠れた長音の流儀の違いを無視した正解率を主な指標とします。`-p DIR` で他のツールの出力も同じ物差しで採点できます。

| 評価データ | このプログラム | [Latin Macronizer](https://github.com/Alatius/latin-macronizer) |
|---|---|---|
| Fabulae Faciles（約1.1万語） | 語 96.9% / 母音 98.4% | 語 96.9% / 母音 98.4%（`--maius`） |
| D'Ooge の読み物（約5,200語） | 語 96.4% / 母音 98.2% | 語 96.2% / 母音 98.1% |

（Fabulae Faciles の行は、頻度などの知識を Fabulae Faciles 以外から取った条件。
D'Ooge の行は、知識を元の教材テキストと Fabulae Faciles から取った条件。どちらも Morpheus と RFTagger あり）

## 音読

```
python3 latin.py -s FILE                   # 解析しながら音読
python3 tools/speak.py "Arma virumque canō, Trōiae quī prīmus ab ōrīs"
python3 tools/speak.py -b mbrola -a stress -w out.wav "..."   # 強弱アクセントで WAV に書き出す
```

| 方式 | |
|---|---|
| `mbrola`（既定） | 自前の音韻処理（音節・アクセント・母音の長短）で作った音素列を、MBROLA の古典ラテン語音声 la1 で合成。無ければ espeak を使う |
| `espeak` | espeak-ng のラテン語音声にテキストをそのまま渡す |
| `piper` | 自前の音韻処理で作った IPA を、Piper のイタリア語/スペイン語モデルで合成（聞き取りやすさは低い） |

再生には macOS の `afplay` を使います（`-w` で WAV に書き出すだけなら他の OS でも動きます）。

セットアップ:

* espeak: `brew install espeak-ng`
* mbrola: [MBROLA](https://github.com/numediart/MBROLA) をビルドして `~/.local/share/mbrola/bin/mbrola` に、
  [la1 音声](https://github.com/numediart/MBROLA-voices/tree/master/data/la1) を `~/.local/share/mbrola/voices/la1/la1` に置く
  （場所は `MBROLA_HOME` で変更可）。macOS では次の修正が必要:
  * `make CC=gcc`（`-ansi` を外す。`swab` の宣言が衝突するため）
  * `Misc/common.h` の `#if defined(__i386) || ...` に `|| defined(__x86_64__) || defined(__aarch64__) || defined(__arm64__)` を追加
    （システムヘッダが `BIG_ENDIAN` マクロを定義しているため、サンプルがビッグエンディアンの WAV が出力される）
* piper: `pip install piper-tts` し、[piper-voices](https://huggingface.co/rhasspy/piper-voices) の
  `it_IT-paola-medium` などの `.onnx` と `.onnx.json` を `~/.local/share/piper/voices/` に置く（`PIPER_VOICES` で変更可）

合成音声の聞き取りやすさは `tools/tts_eval.py` で測れます（Whisper にラテン語として書き起こさせ、WER/CER を出す）。

## データ

### 辞書

手作りの辞書（`words/*.def`。日本語の訳語付き）を優先し、そこに無い語は Wiktionary 由来の補助辞書で引きます。

```
mkdir -p ~/.local/share/latin-data && cd ~/.local/share/latin-data
curl -L -o kaikki-Latin.jsonl.gz https://kaikki.org/dictionary/Latin/kaikki.org-dictionary-Latin.jsonl.gz
curl -LO https://kaikki.org/dictionary/downloads/ja/ja-extract.jsonl.gz   # 日本語の訳語（任意）
cd - && python3 tools/build_wiktionary_dic.py
```

* 英語版 Wiktionary のラテン語の項目（[kaikki.org](https://kaikki.org/) の抽出データ）から、
  全変化形を表層形で引ける SQLite 辞書を作ります（約6万語・140万形）。
* 日本語版 Wiktionary に同じ見出し語があれば日本語の訳語を、なければ英語の訳語を使います。

### Latin Macronizer の資源

[Latin Macronizer](https://github.com/Alatius/latin-macronizer)（Johan Winge）に同梱の、
Morpheus の解析結果と、Latin Dependency Treebank で学習した RFTagger のモデルを借ります。

```
cd ~/.local/share/latin-data
git clone https://github.com/Alatius/latin-macronizer.git
curl -LO https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/data/RFTagger.zip
unzip RFTagger.zip && (cd RFTagger/src && make)
cd - && python3 tools/build_morpheus_dic.py
```

場所は `LATIN_RFTAGGER`、`LATIN_RFTAGGER_MODEL` でも変更できます。品詞タガーを使わない場合は `LATIN_TAGGER=0`。

### テキスト

| テキスト | 出典 | ライセンス |
|---|---|---|
| `texts/fabulae_faciles/` | Ritchie, *Fabulae Faciles* (1903), Project Gutenberg #8997 | パブリックドメイン |
| `texts/dooge/` | D'Ooge, *Latin for Beginners* (1909) の読み物, Project Gutenberg #18251 | パブリックドメイン |
| `texts/GLORIA.txt` | 典礼文 Gloria in excelsis | パブリックドメイン |
| `texts/RIMINI.txt` | リミニの碑文（後世の作とされる） | パブリックドメイン |

`texts/catalog.json` に、テキストごとの使い方を記録しています。

* `macrons`: マクロンが信頼できるか（`full` / `partial` / `none`）
* `hidden`: 隠れた長音の流儀（`mark` / `nomark` / `mixed`）
* `family`: 内容が重なるテキストのまとまり（Fabulae Faciles と D'Ooge のヘラクレスなど）
* `used_for_dictionary`: 手作りの辞書を作るのに使ったか
* `source`, `license`, `notes`

マクロン推定の頻度は `macrons: full` のテキストから、隠れた長音の `mark` の知識は `hidden: mark` の
テキストから集めます。評価は目録で評価に使えるとされたテキストで行い、評価するテキストと同じ `family` の
テキストは知識から除きます。**目録に無いテキストは「読む対象のみ」**（知識にも評価にも使わない）なので、
マクロンの無いテキストを読みたいときは `texts/` に置くだけで構いません。

**権利関係が不明なテキストはリポジトリに入れません。** `$LATIN_DATA/private-texts/` に、同じ書式の目録
`catalog.json` と一緒に置くと、知識・評価・テストに使われます（golden テストの正解ファイルは `golden/` に置く）。

### 解析の精度

`tools/ud_eval.py` で、Universal Dependencies のラテン語ツリーバンクを正解として、格・形容詞と属格の係り先・
主語と目的語を測ります。既定は [UD Latin-PROIEL](https://github.com/UniversalDependencies/UD_Latin-PROIEL)
（CC BY-NC-SA 3.0。`$LATIN_DATA/ud/` に置き、リポジトリには入れない）のカエサルとキケロの文です
（ウルガタは、品詞タガーの学習データと重なりうるので既定では使わない）。

| カエサル『ガリア戦記』（約2.7万語） | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|
| すべてあり | 82.1% | 64.6% | 50.2% | 79.5% | 41.5% | 52.9% |

（格は正解率。係り先・主語・目的語は再現率）

## テスト

```
python3 -m unittest discover -s test -p '*_test.py'
```

* 追加データが無い環境でも動きます（データが必要なテストはスキップ）。
* `test/golden_test.py` は、テキストの解析結果を正解ファイルと比べる回帰テストです（手作りの辞書だけで、
  タガーを使わずに解析）。意図して解析結果を変えたときは `UPDATE_GOLDEN=1 python3 test/golden_test.py`
  で更新し、差分を確認してからコミットします。
* `test/corpus_test.py` は、全テキストを解析から表示まで例外なく通せるかを確かめます。

## 構成

```
latin.py                 解析・訳のコマンド (REPL を含む)
latin/
  analyzer.py            解析 (辞書引き、並列・係り先・前置詞句・述語の検出) → SentenceAnalysis
  render.py              解析結果の表示
  Word.py Item.py AndOr.py PrepClause.py Predicate.py   解析の要素と訳
  latindic.py words.py   辞書 (手作りの辞書の読み込みと検索)
  latin_noun.py latin_adj.py latin_verb_reg.py ...      変化形の生成
  wiktionary*.py morpheus.py ldt.py rftagger.py         補助辞書と品詞タガー
  japanese.py verb_flags.py                             日本語の動詞の活用
  macronizer.py hidden_quantity.py catalog.py           マクロンの推定、テキストの目録
  latin_phonology.py latin_prosody.py speech.py         発音と音声合成
tools/                   マクロン推定・音読のコマンド、データの作成・取り込み、評価
words/                   手作りの辞書
texts/                   テキストと目録
test/                    テスト
```

## 経緯

2013年に、初級ラテン語のリーディングの授業に参加しながら書いたプログラムを、2026年に Python 3 へ移行し、
改修したものです。2013年からの開発履歴は、権利関係が不明なテキストを含むため、非公開のリポジトリに保管しています。

## Author

naoya_t (@naoya_t)
http://github.com/naoyat | http://twitter.com/naoya_t | http://naoyat.hatenablog.jp/

2026年の改修は Claude Opus 5.5（Anthropic）と共同で行いました。

## License

(c) 2013-2026 naoya_t, MIT License（`LICENSE.md`）

追加データ（リポジトリには含まない）はそれぞれのライセンスに従います:
Wiktionary（CC BY-SA）、Latin Macronizer（GPL-3.0）、RFTagger（教育・研究・評価目的なら無償）、
MBROLA（AGPL-3.0）と la1 音声（MBROLA でのみ使用可・販売不可）、Piper の音声（モデルごと）。
