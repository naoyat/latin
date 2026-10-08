# dragoman

古典語・現代語の文を辞書引き・構文解析して、日本語の逐語訳を付けるプログラムです（日本語の古文は現代語に組み立て直します）。語ごとの辞書引きと文法の解説、
並列・係り先・前置詞句・格の枠の解析、日本語の動詞の活用を含む逐語訳、音読ができます。
もとはラテン語の読解のための「latin」で、解析の骨組みを言語に依存しない形（`core/`）にして、ほかの言語へ広げています。

```
$ echo "लड़के ने किताब पढ़ी।" | python3 dragoman.py -w

लड़के ने किताब पढ़ी।  (laṛke ne kitāb paṛhī.)

1 VERB FOUND: पढ़ी

  पढ़ी (indicative 3sg)
    Nom:
      लड़के
        ने
    Acc:
      किताब

  →  少年,息子が / 本を / 読んだ,学んだ
```

## 対応している言語

| 言語 | `--lang` | 語形の解析・辞書 | 評価 (Universal Dependencies の主語・目的語の再現率) | 音読 | 詳しく |
|---|---|---|---|---|---|
| ラテン語 | `la` | 手作りの辞書 + Wiktionary、品詞タガー、マクロンの推定 | PROIEL (カエサル): 主語 47%・目的語 56% | MBROLA / espeak-ng / Piper | [docs/latin.md](docs/latin.md) |
| 古典ギリシア語 | `grc` | Wiktionary、Morpheus | 新約聖書: 主語 61%・目的語 46% | MBROLA (古典式 / 現代式) | [docs/greek.md](docs/greek.md) |
| サンスクリット | `sa` | Vidyut (連声・複合語)、Wiktionary | Vedic: 主語 41%・目的語 51% | MBROLA (in1 / in2) | [docs/sanskrit.md](docs/sanskrit.md) |
| ロシア語 | `ru` | pymorphy3、Wiktionary (訳語・強勢) | SynTagRus: 主語 67%・目的語 46% | say (Milena) | [docs/russian.md](docs/russian.md) |
| 聖書ヘブライ語・アラム語 | `he` | OSHB、HebrewLexicon (Strong・BDB) | (OSHB の解析の選択 97%) | say (Carmit) | [docs/hebrew.md](docs/hebrew.md) |
| アラビア語 (MSA) | `ar` | CAMeL Tools、Wiktionary | PADT: 主語 54%・目的語 53% | say (Majed) | [docs/arabic.md](docs/arabic.md) |
| ペルシア語 | `fa` | 自前の規則 + Wiktionary | PerDT: 主語 55%・目的語 43% | espeak-ng | [docs/persian.md](docs/persian.md) |
| ヒンディー語 | `hi` | Wiktionary の変化表 | HDTB: 主語 53%・目的語 30% | say (Lekha) | [docs/hindi.md](docs/hindi.md) |
| ウルドゥー語 | `ur` | ヒンディー語の語形に引き当てる | UDTB: 主語 39%・目的語 32% | espeak-ng | [docs/urdu.md](docs/urdu.md) |
| 古典チベット語 | `bo` | botok で語に分ける、Hill & Garrett の品詞辞書・Wiktionary・蔵英辞書。語順のまま日本語に | Hill & Garrett のコーパス: 語の区切り 87%・格助詞 87% | MMS-TTS / espeak-ng (ラサ方言の音素・声調) | [docs/tibetan.md](docs/tibetan.md) |
| 古文（平安の和文） | `kobun` | MeCab + 中古和文UniDic。品詞分解して現代語に組み立て直す | — | say (Kyoko) | [docs/kobun.md](docs/kobun.md) |

ラテン語以外は作りかけです。日本語の訳語の無い語は、英語の語義（Wiktionary・CAMeL Tools）を英語 → 日本語の表で
置き換えます（下の「訳語」）。それでも訳せない語は英語のまま出ます。

## セットアップ

Python 3.11 以降。日本語の動詞の活用に MeCab（辞書は UniDic）を使います。

```
pip install -r requirements.txt     # または pip install -e .  (dragoman コマンドができる。任意の依存は .[russian] など)
```

これだけでラテン語（手作りの辞書、約1,500語）が読めます。ほかの言語と追加の辞書・コーパスは、言語ごとの文書の
手順でデータを用意します。データは `~/.local/share/dragoman-data/`（環境変数 `DRAGOMAN_DATA` で変更可。旧名の
`LATIN_DATA` と `~/.local/share/latin-data` も読む）に置き、リポジトリには入れません。

英語 → 日本語の訳語の表は、日本語版 Wiktionary の抽出（[kaikki.org の ja-extract](https://kaikki.org/dictionary/rawdata.html)、
`ja-extract.jsonl.gz`）と [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html)（`JMdict_e.gz`、EDRDG、CC BY-SA 4.0。任意）を
データの置き場所に置いて作ります:

```
curl -L -o ~/.local/share/dragoman-data/JMdict_e.gz http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz
python3 tools/build_en_ja.py        # → ~/.local/share/dragoman-data/en-ja.sqlite (Wiktionary 約3.6万 + JMdict 約3.8万)
```

## 使い方

```
./dragoman.py [LANG] [オプション] [ファイル...]   # ファイル (無ければ標準入力) を解析 (python3 dragoman.py / python3 -m dragoman でも)
./dragoman.py hi -e "लड़के ने किताब पढ़ी।"        # 引数の文を解析 (-e は何度でも)
./dragoman.py he --help                          # 言語ごとのオプション
./dragoman.py la                                 # ラテン語の対話モード (変化表・マクロンの推定)
./dragoman.py --languages                        # 対応している言語の一覧
```

言語は最初の引数（`grc` など。`--lang=grc` でも）で指定します。知らない符号なら言語の一覧を出して終わります。
`auto` は省略したときと同じく文字から推定します（推定した言語は標準エラー出力に「推定した言語: ru (ロシア語)」と出す）。
言語を省略すると文字から推定します（ラテン文字 → ラテン語、ギリシア文字 → 古典ギリシア語、キリル文字 → ロシア語、
ヘブライ文字 → ヘブライ語、アラビア文字はウルドゥー語の字（ٹ ڈ ڑ ں ے ھ）があればウルドゥー語、ペルシア語の字の多さで
ペルシア語かアラビア語、デーヴァナーガリーはヒンディー語らしい語の有無でヒンディー語かサンスクリット、チベット文字 →
古典チベット語、かな交じりの日本語は古文）。

| 共通のオプション | |
|---|---|
| `-w`, `--no-word-detail` | 語ごとの辞書引きの結果を表示しない |
| `-D`, `--descendants` | ほかの言語に入った語（子孫語）も表示する |
| `-E`, `--etymology` | 語源も表示する |
| `-s`, `--speech` | 音読する（`-t BACKEND` で方式: mbrola / espeak / piper / say） |
| `-r`, `--romanize` | 語ごとの辞書引きの結果に転写を添える |
| `--no-explain` | 初学者向けの解説（動詞の型・語根・連語形など）を出さない |
| `--english-glosses` | 英語の訳語を日本語に置き換えない |

言語ごとの例文とその訳は `python3 tools/samples.py --lang=xx` で、解析の精度は `python3 tools/ud_eval.py --lang=xx` で
見られます（評価用のツリーバンクは言語ごとの文書を参照）。

## 訳語

訳語は、各言語の辞書の日本語の訳語（日本語版 Wiktionary、その訳語の表を逆に引いたもの、手で決めた基本語）を使い、
無ければ英語の語義を英語 → 日本語の表（`core/en_ja.py`）で置き換えます。英語の語義は品詞ごとに引き、訳せた最初の語義の
一番の訳語を使います（go,travel → 行く。動詞は日本語の活用に通すため辞書形のものだけ）。元の英語は項目の `ja_en` に残します。
表は日本語版 Wiktionary の英語の項目を先に使い、無い語を JMdict（よく使う語の印・頻度の順位の高い見出し語から）で補い、
順位では決めにくい基本語（minister → 大臣 など）は手で決めます。UD の各言語の先頭 300 文で、名詞・動詞・形容詞の訳語に
英語が残る割合は、ロシア語 49% → 6%、アラビア語 70% → 7%、古典ギリシア語 84% → 21%、ヒンディー語 68% → 24%、
サンスクリット 89% → 31% になりました。残りの多くは固有名詞・民族名（Corinthian）、説明的な語義（comparative degree of …）、
辞書に無い語です。

## ラテン文字への転写

ラテン文字以外の言語では、`-r` / `--romanize` で語ごとの辞書引きの結果に転写を添えます（
`tools/samples.py -r` は文にも）。ギリシア語は学術的な転写の簡略版（ἐν ἀρχῇ ἦν ὁ λόγος → en archêi ên ho lógos）、
ロシア語は Wiktionary の強勢を付けた学術転写（Девочка → Dévočka）、ヘブライ語は母音記号からの転写（וַיֹּאמֶר → wayyōʾmer）、
アラビア語は解析で補った母音記号からの転写（ذهب الولد → ḏahaba al-waladu。見出しの行には常に添える）、
ペルシア語は Wiktionary のイラン式の転写に、解析で推定したエザーフェを補ったもの（کتاب علی → ketâb-e ali）。
サンスクリットは語の表示がもとから IAST です。

ヒンディー語は辞書の語は Wiktionary の転写から、それ以外はデーヴァナーガリーから規則で（लड़का → laṛkā）。

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
dragoman.py              入口 (python3 -m dragoman と同じ。--lang=la|grc|sa|ru|he|ar|fa|hi|ur。省略すると文字から言語を推定)
dragoman/                パッケージ
  main.py                入口の本体 (言語の推定と振り分け)
  core/                  言語に依存しない共通部分
    cli.py                 コマンドの骨組み (共通のオプション・見出しの行・音読・表示。言語ごとの違いは <言語>/command.py)
    paths.py               データの置き場所
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
  persian/                 ペルシア語 (規則による語形の解析: 動詞の語幹・接頭辞・人称語尾、複数・接語。エザーフェの推定、
                           را、複数語の動詞)
  hindi/                   ヒンディー語 (Wiktionary の変化表による語形の辞書、schwa の脱落を含む転写、動詞の並び、後置詞と能格)
  urdu/                    ウルドゥー語 (ウルドゥー文字の語をヒンディー語の語形に引き当てる綴りの骨組み。解析は hindi/)
  tibetan/                 古典チベット語 (ワイリー式の転写、botok による語の区切りと補正、格助詞と能格、動詞の語幹の時制、
                           語順のままの日本語訳)
  kobun/                   古文 (中古和文UniDic による品詞分解、助動詞の連なりからの現代語への組み立て直し、係り結び)
tools/                   マクロン推定・音読のコマンド、データの作成・取り込み、評価
latin/                   ラテン語のデータ
  words/                 手作りの辞書 (*.def)
  texts/                 テキストと目録 (catalog.json)。src/ は大文字で長母音を書いた原稿 (make で .txt に)
  scripts/               原稿の変換 (trans.sed: 大文字 → 長母音)
samples/                 解析・翻訳のサンプル (tools/samples.py で表示)
test/                    テスト
```

## 経緯

2013年に、初級ラテン語のリーディングの授業に参加しながら書いたプログラム（latin）を、2026年に Python 3 へ
移行して改修し、古典ギリシア語・サンスクリット・ロシア語・ヘブライ語・アラビア語・ペルシア語・ヒンディー語・ウルドゥー語へ
広げたものです。
名前の dragoman は、オスマン帝国などで通訳・翻訳を務めた人々の呼び名（アラビア語 tarjumān から）。
2013年からの開発履歴は、権利関係が不明なテキストを含むため、非公開のリポジトリに保管しています。

## Author

naoya_t (@naoya_t)
http://github.com/naoyat | http://twitter.com/naoya_t | http://naoyat.hatenablog.jp/

2026年の改修は Claude Opus 5.5（Anthropic）と共同で行いました。

## License

(c) 2013-2026 naoya_t, MIT License（`LICENSE.md`）

追加データ（リポジトリには含まない）はそれぞれのライセンスに従います:
Wiktionary（CC BY-SA）、Latin Macronizer（GPL-3.0）、RFTagger（教育・研究・評価目的なら無償）、
MBROLA（AGPL-3.0）と la1 音声（MBROLA でのみ使用可・販売不可）、Piper の音声（モデルごと）、
Vidyut（MIT）、Morpheus（Perseus）、JMdict（EDRDG、CC BY-SA 4.0）、OSHB（本文はパブリックドメイン、解析は CC BY 4.0）、
CAMeL Tools の形態素辞書・曖昧性解消のモデル（GPL v2）、中古和文UniDic（国立国語研究所、CC BY-NC-SA 4.0）、Universal Dependencies の各ツリーバンク（評価用。ツリーバンクごと）。
