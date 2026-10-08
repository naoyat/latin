# 聖書ヘブライ語（作りかけ）

[Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb)（本文は Westminster Leningrad Codex、パブリック
ドメイン。語形の解析は CC BY 4.0）の全語（約26万語）の解析を語形の辞書にし、見出し語の番号は
[HebrewLexicon](https://github.com/openscriptures/HebrewLexicon)（Strong の辞書・BDB の索引）で語・転写・語義に、
日本語訳は Wiktionary から付けます。解析・訳は共通の解析器（`core/`）をヘブライ語の設定で使います。

```
mkdir -p ~/.local/share/dragoman-data/he/oshb ~/.local/share/dragoman-data/he/lexicon
# oshb/ に morphhb の wlc/*.xml、lexicon/ に HebrewLexicon の AugIndex.xml・LexicalIndex.xml・HebrewStrong.xml
# (態ごとの語義には BrownDriverBriggs.xml も) を置く
python3 tools/build_hebrew_dic.py        # → ~/.local/share/dragoman-data/he/hebrew.sqlite (語形 約5.8万、見出し語 約9,300)
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


## 聖書アラム語

ヘブライ語聖書のアラム語の部分（ダニエル書 2:4後半〜7章、エズラ記 4:8〜6:18・7:12〜26、エレミヤ書 10:11。約5,000語）も、
OSHB の解析で同じように読めます（`hebrew.py` に入れるだけ。語ごとに言語を判定し、ダニエル書 2:4 のように文の途中で
変わってもよい）。

* 態の型はアラム語の名前で（peal, peil, pael, haphel / aphel, shaphel, hithpeel, hithpaal…）、解説と BDB の態ごとの語義も
  （yədaʿ「知る」: peal know / haphel cause to know）。
* 限定状態（emphatic）の語尾 -āʾ（malkāʾ「その王」）は名詞に付けて「※限定状態の語尾」と説明。命令形の前の限定状態の名詞は
  呼びかけ（malkāʾ ləʿālmîn ḥĕyî「王よ、とこしえに生きよ」）。
* dî（דִּי）は、名詞と名詞の間で後ろに定動詞が無ければ属格「〜の」（šəmēh dî ʾĕlāhāʾ「神の名」）、それ以外は関係詞・接続詞。
* まだ: 分詞の述語（アラム語に多い）、関係節の中の主語、態の型の表（`--binyan` はヘブライ語の態だけ）。
