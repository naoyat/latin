# 古典ギリシア語（作りかけ）

同じ枠組みで古典ギリシア語も扱えるようにしていくところです。辞書引きと冠詞の処理だけをギリシア語用に書き、
並列・係り先・格の枠・日本語訳はラテン語と共通の解析器（`core/`）を、ギリシア語の設定（接続詞・繋辞・否定など。
`core/language.py`）で使います。

```
mkdir -p ~/.local/share/dragoman-data/grc && cd ~/.local/share/dragoman-data/grc
curl -L -o kaikki-AncientGreek.jsonl.gz "https://kaikki.org/dictionary/Ancient%20Greek/kaikki.org-dictionary-AncientGreek.jsonl.gz"
cd - && python3 tools/build_greek_dic.py      # → ~/.local/share/dragoman-data/grc/wiktionary.sqlite（約2.2万語・106万形）
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
* 評価用に UD Ancient Greek-PROIEL / Perseus（CC BY-NC-SA）を `~/.local/share/dragoman-data/grc/ud/` に置きます
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

### Morpheus（任意）

辞書に無い語形（叙事詩・方言の形、加音の無い過去形など）は、Perseus の語形解析器 [Morpheus](https://github.com/perseids-tools/morpheus)
（MPL-2.0）があれば、それで解析します（見出し語を Wiktionary の辞書で引いて品詞と訳語を決める）。無ければ規則による読み替え
（`greek/dialect.py`）だけを使います。

```
mkdir -p ~/.local/share/dragoman-data/grc/morpheus && cd ~/.local/share/dragoman-data/grc
curl -L https://codeload.github.com/perseids-tools/morpheus/tar.gz/refs/heads/master | tar xz -C morpheus --strip-components=1
cd morpheus/src && make clean
CFLAGS='-std=gnu89 -Wno-return-type -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types' make LOADLIBES='-ll' && make install
```

### 音読

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
