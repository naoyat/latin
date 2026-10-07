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

* **解析と訳**: 語ごとの辞書引き（変化形からの逆引き）、並列句・形容詞と属格の係り先・前置詞句・独立奪格・分詞句・不定詞句・述語の検出、
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
python3 read.py --lang=la|grc|sa|ru|he [オプション] [ファイル...]   # 言語を選んで (各言語のコマンドを呼ぶ)
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
| `-D`, `--descendants` | 語ごとの辞書引きの結果に、フランス語・英語などに残った語（子孫語）を添える |
| `-E`, `--etymology` | 語ごとの辞書引きの結果に、語源（祖語の系統・同源語・Wiktionary の英語の説明）を添える |

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

### サンプル

現行の解析器が例文（`samples/samples.txt`。文型・並列・係り先・独立奪格・まだ苦手なもの、などの節に分けた自作の文）を
どう解析・翻訳するかを、いつでも見られます。

```
python3 tools/samples.py                 # 全サンプルの訳を1行ずつ
python3 tools/samples.py 独立 繋辞        # 見出しにその文字列を含む節だけ (-l で見出しの一覧)
python3 tools/samples.py -t              # 述語と格の枠の構造も表示 (-d でさらに語ごとの辞書引きも)
python3 tools/samples.py > before.txt    # ファイルへは色なしで出るので、版ごとに diff で比べられる
python3 tools/samples.py --lang=grc      # 古典ギリシア語 (samples/greek.txt)。--lang=sa でサンスクリット
python3 tools/samples.py --lang=grc -r   # ラテン文字以外の文に転写を添える (-d なら語ごとにも)
```

```
Hīs rēbus cognitīs agricola ad vīllam vēnit.
  →  {{この,これ}物,事が 知られて} / 農夫が / {邸宅,別荘,農場,都市}〜の方へ,〜のところまで / 来た
```

例文を足すときは `samples/samples.txt` に書き足します（`## 見出し` で節を分け、見出しに `[auto-macron]` を
付けた節はマクロンを推定してから解析）。権利関係の分からない文は入れないでください。

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
* 項目の子孫語（descendants）から、フランス語・英語・イタリア語・スペイン語に残った語を、継承か借用か、
  経由した語と一緒に取り込みます（`-D` で表示）。語源（祖語の系統・ギリシア語やサンスクリットなどの同源語・
  英語の説明文）も取り込みます（`-E` で表示）。

```
   3  acūtō       (acūtus) p.sharpened,made sharp,sharp [Abl.sg.m|…]
                 acūtus: 仏 aigu (継承: 古仏 agu → 中仏 aigu) / 英 acute (借用: 中英 acute), ague (借用: 古仏 agu → 中仏 aigu → 中英 agu)
```

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

| カエサル『ガリア戦記』（約2.7万語） | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 独立奪格 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| すべてあり | 82.1% | 64.7% | 50.4% | 86.4% | 61.6%（適合率 82.5%） | 46.5% | 56.2% |

（格は正解率。係り先・独立奪格・主語・目的語は再現率）

## 古典ギリシア語（作りかけ）

同じ枠組みで古典ギリシア語も扱えるようにしていくところです。辞書引きと冠詞の処理だけをギリシア語用に書き、
並列・係り先・格の枠・日本語訳はラテン語と共通の解析器（`core/`）を、ギリシア語の設定（接続詞・繋辞・否定など。
`core/language.py`）で使います。

```
mkdir -p ~/.local/share/latin-data/grc && cd ~/.local/share/latin-data/grc
curl -L -o kaikki-AncientGreek.jsonl.gz "https://kaikki.org/dictionary/Ancient%20Greek/kaikki.org-dictionary-AncientGreek.jsonl.gz"
cd - && python3 tools/build_greek_dic.py      # → ~/.local/share/latin-data/grc/wiktionary.sqlite（約2.2万語・106万形）
python3 tools/samples.py --lang=grc           # サンプルの訳 (-t 構造、-d 語ごとの辞書引き)
python3 greek.py samples/greek.txt           # 解析の詳細 (-w で語ごとの辞書引きを省く、-D 子孫語、-E 語源)
```

```
ὁ ἀγαθὸς ἀνὴρ τῷ παιδὶ βιβλίον δίδωσιν.
  →  {good,brave,noble}男性,夫,人,人間が / 息子,娘,年少者,少年に / パピルスの一片,小冊子,書物を / 与える,許す,許可する
καὶ θεὸς ἦν ὁ λόγος.
  →  そして / ロゴスは / 神…であった
```

* 冠詞は後ろの一致する名詞（間に形容詞が入ってもよい）に付け、その名詞の格の候補を絞ります（訳には出さない）。
  繋辞の文では冠詞の付いた主格を主語とします（θεὸς ἦν ὁ λόγος「ことばは神であった」）。

* 表記は、重アクセントを鋭アクセントに（τὸν → τόν）、長短の印・前接語で付いた2つ目のアクセントを除いて照合し、
  見つからなければアクセント・気息記号を除いた形で引きます。
* 双数・中動態・アオリスト・希求法・方言（叙事詩・イオニア・アッティカ・コイネー）の別を取り込みます。
* `-D` で子孫語（ラテン語・英語・フランス語など）、`-E` で語源を表示します。
* 評価用に UD Ancient Greek-PROIEL / Perseus（CC BY-NC-SA）を `~/.local/share/latin-data/grc/ud/` に置きます
  （リポジトリには入れない）。`python3 tools/ud_eval.py --lang=grc [--source=nt,herodotus,homer,…]` で測ります。

| UD Ancient Greek | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 属格独立 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|---|
| 新約聖書（約13万語） | 98.4% | 81.7% | 87.3% | 55.4% | 81.8% | 35.4%（適合率 51.2%） | 60.9% | 45.9% |
| ヘロドトス（約10万語） | 97.3% | 78.8% | 73.0% | 38.9% | 80.3% | 25.7%（適合率 52.5%） | 49.5% | 40.1% |
| ホメロス（UD Perseus、約7万語） | 98.5% | 80.2% | 44.9% | 37.9% | 86.2% | 38.5%（適合率 27.8%） | 78.0% | 50.8% |

（Morpheus あり。UD Perseus の語形の注釈は Morpheus を使って作られているので、ホメロスの数字はやや良く出うる）

* 母音の省略（ἀλλ’ → ἀλλά、ἐφ’ ἡμῖν → ἐπί。語末の気息記号 δ̓ で書くテキストも）と母音の融合（κἀγώ = καὶ ἐγώ）を戻し、
  辞書に無い叙事詩・イオニア方言の語形（ἀγορήν → ἀγοράν、ἑτάροισι の -οισι、Οὐλύμποιο の -οιο、μέσσον）は
  アッティカ方言の形に読み替えて引きます（`greek/elision.py`, `greek/dialect.py`）。加音の無い過去形（φάτο → ἔφατο、
  καταβῆ → κατέβη）、韻律のための長音化（Οὐλύμποιο → Ὀλύμπου）、語幹の違う形（πτόλεμος → πόλεμος）も読み替えます。

* 属格独立は、ラテン語の独立奪格と同じ仕組みで、属格の分詞と一致する属格の名詞を探します。冠詞と名詞の間の分詞
  （τοῦ λέγοντος ἀνθρώπου）と、主節の動詞が属格を取るもの（ἤκουσα φωνῆς λεγούσης「声が言うのを聞いた」）は除きます。
* 分詞の変化形は、Wiktionary の活用表にある男性単数主格から、型（-ων, -ας, -είς, -ώς, -μενος）ごとの規則で作ります。
* 前置詞の無い属格・与格・対格は、文脈で助詞を読み替えます（`greek/government.py`）: 動詞が支配する格（ἀκούω + 属格
  「〜を聞く」、πιστεύω + 与格「〜を信じる」、μάχομαι + 与格「〜と戦う」）、比較の属格（μείζων τοῦ πατρός「父より」）、
  時の名詞（νυκτός「夜のうちに」、τῇ τρίτῃ ἡμέρᾳ「三日目に」、τρεῖς ἡμέρας「三日の間」）。
* 冠詞の付いた名詞の外にある、冠詞の無い形容詞は述語的位置として補語にします（ὁ ἀνὴρ ἀγαθός ἐστιν「その人は善い」）。

#### Morpheus（任意）

辞書に無い語形（叙事詩・方言の形、加音の無い過去形など）は、Perseus の語形解析器 [Morpheus](https://github.com/perseids-tools/morpheus)
（MPL-2.0）があれば、それで解析します（見出し語を Wiktionary の辞書で引いて品詞と訳語を決める）。無ければ規則による読み替え
（`greek/dialect.py`）だけを使います。

```
mkdir -p ~/.local/share/latin-data/grc/morpheus && cd ~/.local/share/latin-data/grc
curl -L https://codeload.github.com/perseids-tools/morpheus/tar.gz/refs/heads/master | tar xz -C morpheus --strip-components=1
cd morpheus/src && make clean
CFLAGS='-std=gnu89 -Wno-return-type -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types' make LOADLIBES='-ll' && make install
```

#### 音読

```
python3 tools/speak.py --lang=grc "μῆνιν ἄειδε θεὰ Πηληϊάδεω Ἀχιλῆος"     # 復元アッティカ発音・高低アクセント
python3 tools/speak.py --lang=grc --pron=koine -d "ἐν ἀρχῇ ἦν ὁ λόγος"    # コイネー (-d で IPA と .pho)
python3 greek.py -s samples/greek.txt                                     # 解析しながら読む
```

* MBROLA のラテン語音声 la1 で読みます（有気音 [pʰ tʰ kʰ]・[y]・長母音があるので、ほぼそのまま使える。
  現代ギリシア語式は現代ギリシア語音声 gr1 / gr2 を `~/.local/share/mbrola/voices/` に置く。
  開いた長母音 η [ɛː]・ω [ɔː] は短い e・o を伸ばして代用）。`-b espeak` なら espeak-ng の古典ギリシア語音声で読みます。
* 発音の流儀 (`--pron`):
  * `attic`（既定）: 前5世紀の復元発音。ζ = [zd]、η = [ɛː]、ει = [eː]、ου = [oː]、υ = [y]、気息 [h]、母音の長短。
    アクセントは綴りのとおりの高低アクセント（鋭アクセントは上がる。長い母音では後半のモーラで上がる。
    曲アクセントは長い母音の中で上がって下がる。重アクセントは上がらない）
  * `koine`: 1〜2世紀ごろ。母音の長短と気息が消え、αι = [ɛ]、ει = [i]、η = [e]、οι = [y]、ου = [u]。強弱アクセント
  * `erasmian`: 学校式。η = [ɛː]、ει = [ei]、ου = [uː]、ζ = [dz]。強弱アクセント
  * `modern`: 現代ギリシア語式。η ι υ ει οι = [i]、αι = [e]、ου = [u]、β = [v]、δ = [ð]、θ = [θ]、χ = [x]/[ç]、
    αυ ευ = [av ev]/[af ef]、μπ ντ γκ = [b d g]（語中は [mb nd ŋg]）。MBROLA の現代ギリシア語音声 gr2（`-v gr1` で gr1）で読む
* 長短どちらもある α ι υ は、辞書（Wiktionary の変化表の形の長短の印 θεᾱ́, ἔλῡσᾰ）で長さが分かればそれに従い、
  分からなければ曲アクセント・下書きのイオータ・長音の印があれば長く、なければ短く読みます（attic, erasmian）。

## サンスクリット（作りかけ）

ギリシア語と同じく、辞書引きだけをサンスクリット用に書き、解析・訳はラテン語と共通の解析器を使います。
語形の解析・連声の分解・文字の変換には [Vidyut](https://github.com/ambuda-org/vidyut)（MIT。パーニニ文法に基づく
語形の辞書 kosha）を使い、訳語は Wiktionary から取ります。デーヴァナーガリーでも IAST でも入力できます。

```
pip install vidyut
mkdir -p ~/.local/share/latin-data/sa && cd ~/.local/share/latin-data/sa
curl -L -o vidyut-data-0.4.0.zip https://github.com/ambuda-org/vidyut/releases/download/py-0.4.0/data-0.4.0.zip
unzip vidyut-data-0.4.0.zip -d vidyut-data
curl -L -o kaikki-Sanskrit.jsonl.gz "https://kaikki.org/dictionary/Sanskrit/kaikki.org-dictionary-Sanskrit.jsonl.gz"
cd - && python3 tools/build_sanskrit_dic.py     # → ~/.local/share/latin-data/sa/wiktionary.sqlite
python3 tools/samples.py --lang=sa             # サンプルの訳 (-t 構造、-d 語ごとの辞書引き)
python3 sanskrit.py samples/sanskrit.txt        # 解析の詳細 (-w で語ごとの辞書引きを省く、-D 子孫語、-E 語源)
```

```
रामः लक्ष्मणः च वनं गच्छतः ।
  →  RāmaとLakshmanaが / 森,森林,水,住居を / go
सूर्ये उदिते सर्वे जनाः उत्तिष्ठन्ति ।
// ABL.ABS #0..#1 (sūrye udite)
  →  {太陽の神,スーリヤが speak[完了分詞・受動]} / {whole,entire,all}person,human being,humanが / stand up
तत् त्वम् असि ।
  →  それ,彼,彼女は / あなたである
```

* 語末の連声を戻して引きます（rāmo → rāmaḥ、vanaṃ → vanam、sa → saḥ）。引けなければ Vidyut の分解器で連声・複合語を分けます。
* 後置の ca・vā（A B ca）は前の語の手前に移し、ラテン語と同じ並列（et A et B）として扱います。
* 同綴の語根は、Vidyut の類（gaṇa）と使役かどうかを Wiktionary の動詞の見出し（class 1, root पा）と合わせて選びます
  （pibati → pā「飲む」、pāti → pā「守る」）。接頭辞の付いた語根は、辞書に無ければ接頭辞を除いて引きます（udeti → ud-行く）。
* タガーが無いので、定動詞の読みが一番の語を述語にし、形容詞と名詞は隣り合って性・数・格が合えば係り受けにします。
* 独立奪格の枠組みで処格独立（sūrye udite「太陽が昇ると」）を探します。
* 複合語（`sanskrit/compound.py`）: 辞書に無い語は、前の語を kosha の語幹（約17万）、最後の語を変化形として分けます。
  語の境目の連声は Vidyut の連声の規則を逆にたどって戻します（nīlotpala = nīla + utpala、gajendra = gaja + indra、
  mahā- ← mahat、vaṇik- ← vaṇij）。動詞の接頭辞（anu-, abhi-, sam- など）は複合語の語として分けません。
  分けた語は複合語の種類に分けて訳を合成します。種類の名称は `--compound-labels=sa|ja|en` で、サンスクリットの名称
  （tatpuruṣa, bahuvrīhi…。既定）、六合釈（依主釈, 有財釈…）、英語（determinative, possessive…）を選べます。辞書にある複合語にも成り立ちを書き添えます（rājaputra = rāja-putra tatpuruṣa）。

| 種類 | 例 | 訳 |
|---|---|---|
| tatpuruṣa | vaṇik-putreṇa | merchantのsonで（格の関係は「の」で代表） |
| karmadhāraya | mahā-rājaḥ | 偉大な君主（前の語が形容詞・分詞） |
| dvigu | tri-lokaḥ | 三つの〜（前の語が数詞） |
| dvandva | rāma-lakṣmaṇau | RāmaとLakshmana（双数・複数で固有名詞を含む） |
| bahuvrīhi | pīta-ambaraḥ | 〜を持つ（者）（最後の語の本来の性と合わないか、隣の名詞に掛かるとき） |
| nañ-tatpuruṣa | a-dharmaḥ | 非ダルマ（前の語が否定の a(n)-） |
| avyayībhāva | yathā-śakti | strengthに応じて（前の語が不変化詞で全体が副詞） |

  UD Sanskrit-UFAL の複合語 136 語で、分けられたもの 94.9%、語の数が合うもの 90.4%、語幹まで合うもの 84.6%
  （`python3 tools/sa_compound_eval.py`）。前の語の訳語は Wiktionary の語義の多い見出しの最初の訳語なので、
  ずれることがあります（pīta「飲まれた / 黄色い」）。
* 評価用に UD Sanskrit-Vedic と UD Sanskrit-UFAL（どちらも CC BY-SA 4.0）を `~/.local/share/latin-data/sa/ud/` に置き、
  `python3 tools/ud_eval.py --lang=sa [--source=vedic,ufal]` で測ります（連声を解いて複合語を分けた語の列を入力にする）。

| UD Sanskrit | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| Vedic（test、約2.1万語） | 97.4% | 76.6% | 26.9% | 12.9% | 57.9% | 41.1% | 51.3% |
| UFAL『パンチャタントラ』（test、約1,600語） | 98.9% | 75.7% | 38.8% | 14.3% | 60.3% | 45.6% | 38.5% |

（述語の検出には、繋辞の無い名詞文の述語（UD では名詞が述語になる）も正解に含まれる）

#### 音読

```
mkdir -p ~/.local/share/mbrola/voices/in1 && cd ~/.local/share/mbrola/voices/in1
curl -L -O https://github.com/numediart/MBROLA-voices/raw/master/data/in1/in1    # in2 (女声) も同様に
cd - && python3 tools/speak.py --lang=sa -d "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।"   # -d で IPA と .pho
python3 sanskrit.py -s samples/sanskrit.txt                                    # 解析しながら読む (-v in2 で女声)
```

* MBROLA のヒンディー語音声 in1 / in2 で読みます（そり舌音・有声有気音がある。短い i u・音節の ṛ は無いので、
  ii uu を短くしたもの・r + 短い i で代用し、ṣ は ś と同じ sh、クシャ kṣ は in1 の ks）。無ければ espeak-ng の
  ヒンディー語音声（`-b espeak`）にデーヴァナーガリーで渡します（ヒンディー語の読み方で、語末の a が落ちる）。
* 母音の長さは短 1 : 長 2（e ai o au は長い）。ḥ は前の母音を短く添えて読み（rāmaḥ → rāmaha）、ṃ は後ろの子音と
  同じ位置の鼻音（vanaṃ gacchati → vanaŋ）にします。古典期の文には元の高低アクセントが書かれないので、
  現代のインドの読み方に近い「重い次末音節、無ければその前の重い音節」に軽い強勢（高さ）を置きます。
* in1 には子音どうしのダイフォンがほとんど無いので、子音の間に短い無音を挟みます（音声の README の書き方 k a c _ r aa に従う）。

## ロシア語（作りかけ）

語形の解析は [pymorphy3](https://github.com/no-plagiarism/pymorphy3)（MIT。OpenCorpora の辞書）、訳語・強勢の位置・語源は
Wiktionary から取り、解析・訳は共通の解析器（`core/`）をロシア語の設定で使います。

```
pip install pymorphy3 pymorphy3-dicts-ru
mkdir -p ~/.local/share/latin-data/ru && cd ~/.local/share/latin-data/ru
curl -L -o kaikki-Russian.jsonl.gz "https://kaikki.org/dictionary/Russian/kaikki.org-dictionary-Russian.jsonl.gz"
cd - && python3 tools/build_russian_dic.py      # → ~/.local/share/latin-data/ru/wiktionary.sqlite (約5.8万語、強勢付きの変化形 約140万)
python3 tools/samples.py --lang=ru              # サンプルの訳
python3 russian.py samples/russian.txt          # 解析の詳細 (-w, -D 子孫語, -E 語源, -s 音読)
```

```
Девочка читала интересную книгу в школе.   (Де́вочка чита́ла интере́сную кни́гу в шко́ле.)
  →  少女が / {学校 }〜で,〜の中で / {面白い,興味深い,きれいな,魅力的な}本,書物,書籍,著書を / 読んでいた,…
Москва — столица России.
  →  モスクワ,ロシア連邦の首都,モスクワ川は / {ロシアの}首都である
```

* 見出しの行に、Wiktionary の変化表から強勢記号を付けた文と学術転写を添えます。
* 動詞のアスペクト: 不完了体の過去は「〜していた」、完了体の過去は「〜した」。быть の未来形 + 不定形（буду читать）は
  未来、быть + 短語尾分詞（была прочитана）は受動にまとめます。副動詞（читая）は「〜して」。
* 前置詞は支配する格ごとに訳を持たせ（в + 対格「〜へ」/ 前置格「〜で」）、前置詞の後ろの語は支配する格の読みを先にします。
* 現在形で省かれる繋辞（Он студент. / Москва — столица России.）は、主格の名詞類が2つあれば補います。
* 所有と存在: у меня есть книга「私には本がある」、у меня нет книги「私には本が無い」（нет・не было + 生格は生格の名詞を
  主語に）、в комнате есть стол「部屋に机がある」。есть は хочу есть のような動詞の後ろでだけ「食べる」と読みます。
  存在・所有の文の訳（場所・所有者を先に。場所は「〜に」、所有者は「〜には」、主語「〜が」、生き物なら「いる」:
  в лесу есть волк「森に狼がいる」、у меня есть книга「私には本がある」。否定の文は場所も「〜には」（в комнате нет стола
  「部屋には机がない」）。
  主語が人称代名詞なら「私たちは劇場にいた」）は共通の解析器にあり、ラテン語（mihi est liber）・ギリシア語
  （ἔστι μοι βιβλίον）・サンスクリット（mama pustakam asti、vane siṃhaḥ asti）でも同じように訳します。所有者を表す格は
  言語の設定（`possessor_cases`。ラテン語・ギリシア語は与格、サンスクリットは属格と与格）。
* 語順の違いは言語の設定で吸収します: 属格は前の名詞にだけ掛け、動詞を越えない（`genitive_follows_head`）。
  2つの動詞の間の語は前の動詞へ（目的語は動詞の後ろ、`objects_follow_verb`）。
* 音読（`-s`）は macOS の音声合成 `say` のロシア語音声 Milena にテキストをそのまま渡します（無ければ espeak-ng の
  ロシア語音声。`-t espeak`）。強勢記号はどちらも読まないので、強勢は音声の辞書に任せます。
* `say` は現代語向けの方式として `tools/speak.py -b say` でほかの言語にも使えます（サンスクリットはヒンディー語の Lekha、
  ギリシア語は現代ギリシア語の Melina で、多調符を単調符に直して渡す。どちらも現代語の読み方になる）。
* 評価用に UD Russian-GSD・Taiga（CC BY-SA 4.0）と SynTagRus（CC BY-NC-SA 4.0）の test を `~/.local/share/latin-data/ru/ud/` に置き、
  `python3 tools/ud_eval.py --lang=ru [--source=gsd,taiga,syntagrus]` で測ります。

| UD Russian | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| GSD（約1万語） | 91.8% | 72.3% | 69.8% | 72.4% | 88.1% | 64.5% | 44.0% |
| Taiga（約1.3万語） | 93.0% | 76.3% | 72.2% | 65.1% | 83.4% | 64.6% | 44.7% |
| SynTagRus（約13万語） | 96.7% | 79.0% | 76.5% | 72.9% | 87.2% | 66.6% | 45.8% |

（繋辞を補った名詞文は、UD では述語の名詞が中心語なので、補った繋辞の枠の中で主語を従える語を述語とみなして数えます。）

## 聖書ヘブライ語（作りかけ）

[Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb)（本文は Westminster Leningrad Codex、パブリック
ドメイン。語形の解析は CC BY 4.0）の全語（約26万語）の解析を語形の辞書にし、見出し語の番号は
[HebrewLexicon](https://github.com/openscriptures/HebrewLexicon)（Strong の辞書・BDB の索引）で語・転写・語義に、
日本語訳は Wiktionary から付けます。解析・訳は共通の解析器（`core/`）をヘブライ語の設定で使います。

```
mkdir -p ~/.local/share/latin-data/he/oshb ~/.local/share/latin-data/he/lexicon
# oshb/ に morphhb の wlc/*.xml、lexicon/ に HebrewLexicon の AugIndex.xml・LexicalIndex.xml・HebrewStrong.xml
# (態ごとの語義には BrownDriverBriggs.xml も) を置く
python3 tools/build_hebrew_dic.py        # → ~/.local/share/latin-data/he/hebrew.sqlite (語形 約5.8万、見出し語 約9,300)
python3 tools/samples.py --lang=he       # サンプルの訳
python3 hebrew.py samples/hebrew.txt     # 解析の詳細 (-w, -D, -E, -s 音読)
```

```
בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ׃  (bərēʾšît bārā ʾĕlōhîm ʾēt haššāmayim wəʾēt hāʾāreṣ)
  →  神が / {最初,初め}〜で,〜の中で,〜によって / 天,天界,天国,神と大地,地面,地上を / 創造した,つくりだした
וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר וַיְהִי־אוֹר׃
  →  そして / 神が / 言った  →  ひかりが / あれ  →  そして / ひかりが / あった
```

* 語を接続詞 ו・定冠詞 ה・前置詞 ב ל כ מ・本体・人称接尾辞に分けます（וְאִשְׁתּוֹ = ו + אִשָּׁה の連語形 +「彼の」）。
* 格の無い言語なので、名詞は「主格か対格」のどちらにも読めるものにし、目的語の標識 אֵת の後ろは対格、
  連語形（construct）の後ろの名詞・人称接尾辞は属格「〜の」、前置詞の後ろは前置詞句にします。主語は3人称の動詞と
  性・数が合う名詞（動詞-主語-目的語の順で、動詞の後ろの最初のもの）。אֱלֹהִים は形が複数でも単数の動詞の主語。
* 動詞の型: 完了 qatal「〜した」、連続未完了 wayyiqtol「そして〜した」、未完了 yiqtol、連続完了 weqatal、
  命令・指示形（יְהִי「あれ」）。態の型（binyan: qal, niphal, piel…）は語ごとの表示に。
* 動詞の無い文（名詞文: יְהוָה רֹעִי「主は私の羊飼い」）には見えない繋辞を補います。節の区切りに朗唱記号のアトナハ（֑）を使います。
* 語ごとの表示に初学者向けの解説を添えます（`--no-explain` で出さない）: 動詞は語根（א-מ-ר ʾ-m-r。BDB の索引から。
  名詞は派生元の語根までたどる）、態の型（qal (paʿal パアル): 基本の態、hithpael (hitpaʿel ヒトパエル): 再帰・相互 …）、
  時制の型（wayyiqtol: 物語の流れ「そして〜した」…）。名詞・形容詞・分詞の連語形（smikhut）は、組んでいる後ろの名詞か
  人称接尾辞を添える（pənê「face」: 後ろの māyim「waters」と組んで「watersのface」）。絶対形と連語形が同じ綴りの名詞
  （rûaḥ）は、すぐ後ろに名詞があれば連語形と読む（rûaḥ ʾĕlōhîm「神の霊」）。
* 態の型の表: `python3 hebrew.py --binyan כתב`（`ktb` や語形でも）で、qal〜hithpael の完了・未完了・命令・分詞・不定詞を
  並べます。聖書（OSHB）に現れた形は回数を添え、無い形は作ります:
  * 弱い語根・喉音を含む語根は、同じ分類（1字目の נ、2字目の ו・י、3字目の ה・א、喉音、ר、重複語根）の別の語根で
    聖書に現れた形から類推し（上位9語根の多数決。同じ分類が無ければ、形への影響の小さい性質から分類をゆるめる）、
    † と借りた語根を添える（נפל の niphal † nippal ← נגש、בוא の完了 † bāʾ ← שוב）。中空動詞は polel、重複語根は piel か poel の系統。
  * 強い語根は強い語根の型から作って * を付ける（hiphil * hiḵtîv הִכְתִּיב）。歯擦音で始まる語根の hithpael は ת と入れ替え（hištammēr）。
  * 態ごとの語義を BDB（Brown-Driver-Briggs の本体 BrownDriverBriggs.xml、パブリックドメイン。`lexicon/` に置く）から添える
    （כתב: qal write, write down… / niphal be written, recorded）。語ごとの解説にも「この語根の niphal (BDB): …」と出す。
  * 作った形の当たり具合（聖書によく出る 400 語根で、自分の形を使わずに作って比べる）: 強い語根 73.5%、弱い語根 62.3%
    （`python3 tools/hebrew_binyan_eval.py`。外れの多くは状態動詞 זָקֵן・מָלֵא や piel の母音の揺れ קִדַּשׁ/קִדֵּשׁ など語ごとの性質）。
* 見出しの行はヘブライ文字（Unicode の隔離記号で囲む）と転写を並べます。音読は macOS の say のヘブライ語音声 Carmit
  （現代ヘブライ語の発音）。朗唱記号は除き（Carmit も読まない）、母音記号は残して渡します。神の名 יְהוָה は伝統どおり
  母音記号のとおりに「アドナイ」と読み替え、ヒリクの付いた形（אֲדֹנָי יֱהֹוִה と並ぶとき）は「エロヒム」と読みます
  （画面の転写と解析は書かれたとおり）。`--divine-name=hashem` で「ハシェム」、`--divine-name=literal` で字面のまま。

## ラテン文字への転写

ラテン文字以外の言語では、`-r` / `--romanize` で語ごとの辞書引きの結果に転写を添えます（greek.py, russian.py, hebrew.py, arabic.py。
`tools/samples.py -r` は文にも）。ギリシア語は学術的な転写の簡略版（ἐν ἀρχῇ ἦν ὁ λόγος → en archêi ên ho lógos）、
ロシア語は Wiktionary の強勢を付けた学術転写（Девочка → Dévočka）、ヘブライ語は母音記号からの転写（וַיֹּאמֶר → wayyōʾmer）、
アラビア語は解析で補った母音記号からの転写（ذهب الولد → ḏahaba al-waladu。見出しの行には常に添える）。
サンスクリットは語の表示がもとから IAST です。

### 聖書アラム語

ヘブライ語聖書のアラム語の部分（ダニエル書 2:4後半〜7章、エズラ記 4:8〜6:18・7:12〜26、エレミヤ書 10:11。約5,000語）も、
OSHB の解析で同じように読めます（`hebrew.py` に入れるだけ。語ごとに言語を判定し、ダニエル書 2:4 のように文の途中で
変わってもよい）。

* 態の型はアラム語の名前で（peal, peil, pael, haphel / aphel, shaphel, hithpeel, hithpaal…）、解説と BDB の態ごとの語義も
  （yədaʿ「知る」: peal know / haphel cause to know）。
* 限定状態（emphatic）の語尾 -āʾ（malkāʾ「その王」）は名詞に付けて「※限定状態の語尾」と説明。命令形の前の限定状態の名詞は
  呼びかけ（malkāʾ ləʿālmîn ḥĕyî「王よ、とこしえに生きよ」）。
* dî（דִּי）は、名詞と名詞の間で後ろに定動詞が無ければ属格「〜の」（šəmēh dî ʾĕlāhāʾ「神の名」）、それ以外は関係詞・接続詞。
* まだ: 分詞の述語（アラム語に多い）、関係節の中の主語、態の型の表（`--binyan` はヘブライ語の態だけ）。

## アラビア語（作りかけ）

現代標準アラビア語（MSA）。語形の解析と曖昧性解消（母音記号の無い語の読みの選択）は
[CAMeL Tools](https://github.com/CAMeL-Lab/camel_tools)（MIT。形態素辞書 calima-msa-r13 と MLE の曖昧性解消のモデルは
GPL v2 のデータで、リポジトリには入れない）、訳語・語根・動詞の型・語源は Wiktionary から取り、解析・訳は共通の解析器
（`core/`）をアラビア語の設定で使います。

```
pip install camel-tools
mkdir -p ~/.local/share/latin-data/ar/camel && cd ~/.local/share/latin-data/ar
CAMELTOOLS_DATA=$PWD/camel camel_data -i morphology-db-msa-r13 disambig-mle-calima-msa-r13   # 約130MB
curl -L -o kaikki-Arabic.jsonl.gz "https://kaikki.org/dictionary/Arabic/kaikki.org-dictionary-Arabic.jsonl.gz"
cd - && python3 tools/build_arabic_dic.py       # → ~/.local/share/latin-data/ar/wiktionary.sqlite (約2.7万語)
python3 tools/samples.py --lang=ar              # サンプルの訳
python3 arabic.py samples/arabic.txt            # 解析の詳細 (-w, -D, -E, -s 音読, -r 転写)
```

```
ذهب الولد إلى المدرسة.
  ⁧ذَهَبَ الوَلَدُ إِلَى المَدْرَسَةِ.⁩  (ḏahaba al-waladu ilā al-madrasati.)
  →  少年,子どもが / {学校}〜へ,〜まで / 行った
أكل الولد الخبز وشرب الماء.
  →  少年,子どもが / パンを / 食べた  →  そして / 彼,彼女,それが / 水を / 飲んだ
```

* 母音記号は無くてもよく、あればそれに合う読みだけを使います。見出しの行には、解析で選んだ読みと格の語尾
  （主格 -u・対格 -a・属格 -i、非限定の -un/-an/-in）、動詞の法の語尾（lam の後ろの要求法 يَذْهَبْ）を補った形と転写
  （DIN 31635 に近い形。太陽文字への同化 as-sūq、li + al- の lil-）を並べます。
* 語を接続詞 wa-/fa-・前置詞 bi-/li-/ka-・本体・人称接尾辞に分けます（定冠詞 al- は本体に付けたまま。未来の sa- は動詞に含める）。
* 語の読み（見出し語・品詞）は曖昧性解消の点数に、前後の手がかりを掛けて選びます: lam・lan・qad の後ろは動詞、前置詞の後ろは
  名詞、إن の後ろが名詞なら inna「実に」、節の頭の動詞 + 定冠詞付きの名詞は動詞文。
* 格: 前置詞の後ろと連語（iḍāfa: 定冠詞の無い名詞 + 名詞。kitābu l-muʿallimi「先生の本」）の後ろの名詞は属格。人称接尾辞は
  名詞に付けば属格「彼の」、動詞に付けば対格。形容詞は定冠詞の有無が名詞と合うときだけ名詞に掛け、合わなければ述語
  （al-waladu kabīrun「少年は大きい」）。人以外の複数は女性単数として一致させます。
* 主語: 動詞が前なら動詞の後ろの性の合う名詞（数は合わなくてよい: ḏahaba ṭ-ṭullābu「学生たちは行った」）、節の頭の定まった
  名詞が性・数とも合えばそれ（見出しに多い名詞-動詞の順）。wa- でつながった2つ目の動詞は、前と主語が同じなら後ろの名詞を目的語に。
* 動詞の無い文（名詞文）には見えない繋辞を補います（定まった主語 + 定まらない述語・前置詞句。前置詞句が先なら存在文
  fī l-bayti raǧulun「家に男がいる」）。kāna は繋辞、laysa は否定の繋辞「〜でない」。inna とその姉妹（أَنَّ・لٰكِنَّ）は
  新しい節の頭で、後ろの名詞・人称接尾辞を主語に（形は対格: inna ṭ-ṭālibāti）。lam + 未完了は過去の否定、lan は未来の否定。
* 語ごとの解説（`--no-explain` で出さない）: 動詞の語根（ك-ت-ب k-t-b）、型（I faʿala〜X istafʿala と意味の傾向）、
  完了形・未完了形・命令形、要求法・接続法。名詞の語根、連語形の相手。
* 訳語は手で決めた基本語、母音まで同じ Wiktionary の項目（日本語版 Wiktionary のアラビア語の項目と、日本語の項目の訳語の表を
  逆に引いたもの。約2,100語）、CAMeL Tools の語義（英語）の順。まだ英語の訳語が多いです。
* 音読（`-s`）は macOS の say のアラビア語音声 Majed に、母音記号を補った形を渡します。
* 評価用に UD Arabic-PADT（新聞記事。CC BY-NC-SA 3.0）の test を `~/.local/share/latin-data/ar/ud/` に置き、
  `python3 tools/ud_eval.py --lang=ar` で測ります（書かれたとおりの語を渡し、解析器が分けた切れ目を UD の語に対応させる）。

| UD Arabic | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| PADT（約2.6万語） | 97.3% | 72.6% | 70.5% | 49.7% | 85.0% | 53.9% | 52.6% |

* 主語の取りこぼしの多くは関係代名詞（الَّذِي・الَّتِي。UD では関係節の主語。こちらは「〜するところの」の接続詞として扱う）。
  inna の主語は訳のために主格とするので、格の数字では対格の正解と食い違います。
* まだ: 関係節、疑問文の名詞文（أَيْنَ الكِتابُ）、五つの名詞（أَبُو・أَبِي）の語形、固有名詞の多くは辞書に無い。

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
read.py                  言語を選んで解析・訳する (--lang=la|grc|sa|ru|he|ar。下の各言語のコマンドを呼ぶ)
latin.py                 ラテン語の解析・訳のコマンド (REPL を含む)
greek.py                 古典ギリシア語の解析・訳のコマンド (作りかけ)
sanskrit.py              サンスクリットの解析・訳のコマンド (作りかけ)
russian.py               ロシア語の解析・訳のコマンド (作りかけ)
hebrew.py                聖書ヘブライ語の解析・訳のコマンド (作りかけ)
arabic.py                アラビア語 (現代標準アラビア語) の解析・訳のコマンド (作りかけ)
core/                    言語に依存しない共通部分
  analyzer.py            解析の骨組み (並列・係り先・前置詞句・独立奪格・分詞句・不定詞句・述語の検出) → SentenceAnalysis
  language.py            言語ごとの設定 (接続詞・繋辞・否定・格の助詞・独立奪格の格、辞書を引く関数など)
  render.py              解析結果の表示
  Word.py Item.py AndOr.py PrepClause.py Predicate.py   解析の要素と訳
  Absolute.py Participle.py Infinitive.py               独立奪格・分詞句・不定詞句
  japanese.py verb_flags.py                             日本語の動詞の活用
  wiktionary_import.py keys.py                          Wiktionary (kaikki.org) の項目の取り込み、照合用のキー
  descendants.py etymology.py languages.py              子孫語・語源の表示 (言語名の日本語表記)
  speech.py                                             音声合成 (MBROLA / espeak-ng / Piper / say)
latin/                   ラテン語
  analyzer.py profile.py 辞書引き・品詞タガーによる前処理と、ラテン語の設定
  latindic.py words.py   辞書 (手作りの辞書の読み込みと検索)
  latin_noun.py latin_adj.py latin_verb_reg.py ...      変化形の生成
  wiktionary.py morpheus.py ldt.py rftagger.py          補助辞書と品詞タガー
  orthography.py katakana.py                            綴りの流儀の吸収、固有名詞のカタカナ表記
  macronizer.py hidden_quantity.py catalog.py           マクロンの推定、テキストの目録
  latin_phonology.py latin_prosody.py                   発音と韻律
greek/                   古典ギリシア語 (表記の正規化、Wiktionary の取り込み、辞書、冠詞の処理、格の読み替え、
                         発音と韻律)
sanskrit/                サンスクリット (文字の変換、Vidyut による語形の解析と連声を戻す辞書引き、複合語、Wiktionary の訳語、
                         発音と韻律)
russian/                 ロシア語 (pymorphy3 による語形の解析、前置詞の格、繋辞の補い、Wiktionary の訳語と強勢)
hebrew/                  聖書ヘブライ語 (OSHB の語形の解析、接頭辞・人称接尾辞の切り分け、格の代わりの手がかり、転写)
arabic/                  アラビア語 (CAMeL Tools による語形の解析と読みの選択、接語の切り分け、連語・inna・名詞文、
                         格の語尾を補った形と転写)
tools/                   マクロン推定・音読のコマンド、データの作成・取り込み、評価
words/                   手作りの辞書
texts/                   テキストと目録
samples/                 解析・翻訳のサンプル (tools/samples.py で表示)
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
