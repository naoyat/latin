# アラビア語（作りかけ）

現代標準アラビア語（MSA）。語形の解析と曖昧性解消（母音記号の無い語の読みの選択）は
[CAMeL Tools](https://github.com/CAMeL-Lab/camel_tools)（MIT。形態素辞書 calima-msa-r13 と MLE の曖昧性解消のモデルは
GPL v2 のデータで、リポジトリには入れない）、訳語・語根・動詞の型・語源は Wiktionary から取り、解析・訳は共通の解析器
（`core/`）をアラビア語の設定で使います。

```
pip install camel-tools
mkdir -p ~/.local/share/dragoman-data/ar/camel && cd ~/.local/share/dragoman-data/ar
CAMELTOOLS_DATA=$PWD/camel camel_data -i morphology-db-msa-r13 disambig-mle-calima-msa-r13   # 約130MB
curl -L -o kaikki-Arabic.jsonl.gz "https://kaikki.org/dictionary/Arabic/kaikki.org-dictionary-Arabic.jsonl.gz"
cd - && python3 tools/build_arabic_dic.py       # → ~/.local/share/dragoman-data/ar/wiktionary.sqlite (約2.7万語)
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
* 評価用に UD Arabic-PADT（新聞記事。CC BY-NC-SA 3.0）の test を `~/.local/share/dragoman-data/ar/ud/` に置き、
  `python3 tools/ud_eval.py --lang=ar` で測ります（書かれたとおりの語を渡し、解析器が分けた切れ目を UD の語に対応させる）。

| UD Arabic | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| PADT（約2.6万語） | 97.3% | 72.6% | 70.5% | 49.7% | 85.0% | 53.9% | 52.6% |

* 主語の取りこぼしの多くは関係代名詞（الَّذِي・الَّتِي。UD では関係節の主語。こちらは「〜するところの」の接続詞として扱う）。
  inna の主語は訳のために主格とするので、格の数字では対格の正解と食い違います。
* まだ: 関係節、疑問文の名詞文（أَيْنَ الكِتابُ）、五つの名詞（أَبُو・أَبِي）の語形、固有名詞の多くは辞書に無い。
