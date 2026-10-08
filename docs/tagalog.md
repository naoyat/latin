# タガログ語（作りかけ）

オーストロネシア語族のタガログ語を、名詞句の標識（ang / ng / sa）と動詞の焦点（接辞）から格を決めて日本語に訳します。
語順が日本語と違う（動詞が先頭）ので、インドネシア語と同じく共通の解析器を使います。

```
./dragoman.py tl -e "Binili ng lalaki ang isda."
  →  魚は / 男が / 買った
./dragoman.py tl samples/tagalog.txt              # -w で語ごとの辞書引きを省く
python3 tools/samples.py --lang=tl
```

## 焦点（態）の仕組みと訳し方

タガログ語の動詞は、どの名詞を ang で目立たせるか（焦点・ピボット）を接辞で示します。dragoman は ang の名詞を
日本語の主題「は」にして文の頭に置き、残りの名詞の格を焦点から決めます。

| 焦点 | 接辞 | ang の名詞 | ng の名詞 | 例 | 訳 |
|---|---|---|---|---|---|
| 行為者 | -um-, mag-, mang-, maka- | 動作主（は） | 対象（を） | Bumili ang lalaki ng isda. | 男は / 魚を / 買った |
| 対象 | -in, ma-（可能） | 対象（は） | 動作主（が） | Binili ng lalaki ang isda. | 魚は / 男が / 買った |
| 場所 | -an | 場所・受け手（には） | 動作主（が）・対象（を） | Binilhan ng lalaki ng isda ang tindahan. | 店には / 男が / 魚を / 買った |
| 移動物・受益者 | i-, ipag- | 移動するもの・受益者（は） | 動作主（が） | Isinulat ng babae ang liham. | 手紙は / 女が / 書いた |

* アスペクトは重複と -in- / -um- の組み合わせ: 完了（bumili → 〜した）、進行（bumibili → 〜している）、未然（bibili →
  〜するだろう）。
* 代名詞は形で標識が決まる（ako / ko / akin「私」の ang / ng / sa の形）。sa / kay は「に・で」。
* 名詞の後ろの ng 名詞句は、動詞の取る ng の補語の数（行為者・対象焦点は1つ、場所焦点は2つ）を超えたものと、ng の
  代名詞・sa 句の中のものを所有にする（libro ng bata「子供の本」、bahay ko「私の家」）。
* 繋ぎ（na / -ng）: 形容詞を名詞に掛ける（magandang bahay「美しい家」）。名詞 + 繋ぎ + 動詞は関係節（lalaking bumili ng
  isda「魚を買った男」）。
* ay の倒置（Si Juan ay guro）、動詞の無い文（Maganda ang bahay「家は美しい」）には見えない繋辞を補う。
* 縮約形（ngayo'y → ngayon ay、ligaya't → ligaya at、sa'kin → sa akin）、動名詞（pag-ikot「回ること」）、部分的な重複
  （iniisip-isip「何度も考える」）、接辞 + 英語の語根（mag-operate → 操作する）。

文は句点・疑問符と改行で区切ります（歌詞・詩の行は意味のまとまりなので、行末にピリオドが無くてもよい）。
行末がカンマのときは次の行に続けて読みます。語ごとの表は、訳のためにまとめた語（標識・関係節の語）も元の語ごとに出し、
「標識: 焦点 (ang)」「関係節の語 (lalaking に掛かる)」「繋ぎ」などの役割を添えます。

## 準備

```
mkdir -p ~/.local/share/dragoman-data/tl/ud && cd ~/.local/share/dragoman-data/tl
curl -L -O https://kaikki.org/dictionary/Tagalog/kaikki.org-dictionary-Tagalog.jsonl     # 約125MB (CC BY-SA)
cd - && python3 tools/build_tagalog_dic.py        # → ~/.local/share/dragoman-data/tl/wiktionary.sqlite
```

語形の辞書は、Wiktionary の動詞の見出しの活用形（completive / progressive / contemplative の印のあるもの）と、
「complete aspect of bilhin」のような語義から作ります。無い形は接辞と重複の規則で語根に戻します（`tagalog/morphology.py`）。

評価用に UD Tagalog-NewsCrawl（dev ブランチの test、CC BY-SA 4.0）・TRG（CC BY-SA 4.0）・Ugnayan（CC BY-NC-SA 4.0）を
`~/.local/share/dragoman-data/tl/ud/` に置きます。

## 評価

```
python3 tools/ud_eval.py --lang=tl [--source=newscrawl,trg,ugnayan]
```

UD のタガログ語は対象焦点を受動として注釈する（ang = nsubj:pass、ng の動作主 = obj:agent）。dragoman の訳では動作主を
主語「が」、対象を「は / を」にするので、評価では受動の主語を目的語、動作主を主語として突き合わせる。存在文（may / wala +
名詞）の名詞も、訳に合わせて主語として数える。

| UD Tagalog（NewsCrawl・TRG・Ugnayan の test、約2.4万語） | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|
| | 11.4% | 24.1% | 68.5% | 51.5% | 35.4% |

## 音読

macOS の say にも espeak-ng にもタガログ語の音声が無いので、綴りと発音の近いインドネシア語の音声（espeak-ng `id`）で読みます。
Meta の MMS-TTS にはタガログ語のモデル（facebook/mms-tts-tgl）があります。

## まだ

* 形容詞の係り先（繋ぎの無い修飾、英語の形容詞）、ニュースの英語の混ざった文。
* 使役（magpa- / pa-…-in）、社交（maki-）、可能（maka- / ma-）の訳し分け。命令、疑問の ba。
* 第2位の接語（na「もう」、pa「まだ」、daw「〜そうだ」）の位置と訳。
