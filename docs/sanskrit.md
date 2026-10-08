# サンスクリット（作りかけ）

ギリシア語と同じく、辞書引きだけをサンスクリット用に書き、解析・訳はラテン語と共通の解析器を使います。
語形の解析・連声の分解・文字の変換には [Vidyut](https://github.com/ambuda-org/vidyut)（MIT。パーニニ文法に基づく
語形の辞書 kosha）を使い、訳語は Wiktionary から取ります。デーヴァナーガリーでも IAST でも入力できます。

```
pip install vidyut
mkdir -p ~/.local/share/dragoman-data/sa && cd ~/.local/share/dragoman-data/sa
curl -L -o vidyut-data-0.4.0.zip https://github.com/ambuda-org/vidyut/releases/download/py-0.4.0/data-0.4.0.zip
unzip vidyut-data-0.4.0.zip -d vidyut-data
curl -L -o kaikki-Sanskrit.jsonl.gz "https://kaikki.org/dictionary/Sanskrit/kaikki.org-dictionary-Sanskrit.jsonl.gz"
cd - && python3 tools/build_sanskrit_dic.py     # → ~/.local/share/dragoman-data/sa/wiktionary.sqlite
python3 tools/samples.py --lang=sa             # サンプルの訳 (-t 構造、-d 語ごとの辞書引き)
python3 dragoman.py --lang=sa samples/sanskrit.txt        # 解析の詳細 (-w で語ごとの辞書引きを省く、-D 子孫語、-E 語源)
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
* 評価用に UD Sanskrit-Vedic と UD Sanskrit-UFAL（どちらも CC BY-SA 4.0）を `~/.local/share/dragoman-data/sa/ud/` に置き、
  `python3 tools/ud_eval.py --lang=sa [--source=vedic,ufal]` で測ります（連声を解いて複合語を分けた語の列を入力にする）。

| UD Sanskrit | 網羅率 | 格 | 形容詞→名詞 | 属格→名詞 | 述語の検出 | 主語 | 目的語 |
|---|---|---|---|---|---|---|---|
| Vedic（test、約2.1万語） | 97.4% | 76.6% | 26.9% | 12.9% | 57.9% | 41.1% | 51.3% |
| UFAL『パンチャタントラ』（test、約1,600語） | 98.9% | 75.7% | 38.8% | 14.3% | 60.3% | 45.6% | 38.5% |

（述語の検出には、繋辞の無い名詞文の述語（UD では名詞が述語になる）も正解に含まれる）

### 音読

```
mkdir -p ~/.local/share/mbrola/voices/in1 && cd ~/.local/share/mbrola/voices/in1
curl -L -O https://github.com/numediart/MBROLA-voices/raw/master/data/in1/in1    # in2 (女声) も同様に
cd - && python3 tools/speak.py --lang=sa -d "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः ।"   # -d で IPA と .pho
python3 dragoman.py --lang=sa -s samples/sanskrit.txt                                    # 解析しながら読む (-v in2 で女声)
```

* MBROLA のヒンディー語音声 in1 / in2 で読みます（そり舌音・有声有気音がある。短い i u・音節の ṛ は無いので、
  ii uu を短くしたもの・r + 短い i で代用し、ṣ は ś と同じ sh、クシャ kṣ は in1 の ks）。無ければ espeak-ng の
  ヒンディー語音声（`-b espeak`）にデーヴァナーガリーで渡します（ヒンディー語の読み方で、語末の a が落ちる）。
* 母音の長さは短 1 : 長 2（e ai o au は長い）。ḥ は前の母音を短く添えて読み（rāmaḥ → rāmaha）、ṃ は後ろの子音と
  同じ位置の鼻音（vanaṃ gacchati → vanaŋ）にします。古典期の文には元の高低アクセントが書かれないので、
  現代のインドの読み方に近い「重い次末音節、無ければその前の重い音節」に軽い強勢（高さ）を置きます。
* in1 には子音どうしのダイフォンがほとんど無いので、子音の間に短い無音を挟みます（音声の README の書き方 k a c _ r aa に従う）。

## 仏典の語彙

Wiktionary の訳語は一般の意味なので（śāri「チェスの駒」、śruta「筒抜け」）、仏典によく出る語は漢訳語を先に使います
（`dragoman/sanskrit/buddhist.py`）。文章に bodhisattva・śāriputra・prajñāpāramitā・tathāgata などがあれば自動で使い
（`--buddhist` / `--no-buddhist` で指定）、一般のテキスト（devāḥ → 神）には効きません。

* 術語: 菩薩・世尊・如来・舎利子・観自在、般若波羅蜜多・空性・自性、五蘊（色・受・想・行・識）、眼・耳・鼻・舌・身・意、
  界、無明・老死、苦・集・滅・道、智・得、罣礙・顛倒・涅槃、阿耨多羅三藐三菩提、大明呪・無上呪・無等等呪、菩提・薩婆訶 …
  複合語の要素にも効く（prajñāpāramitāyām → 般若波羅蜜多、vedanāsaṃjñāsaṃskāravijñānāni → 受の想の行の識）。
* 動詞は接頭辞つきの語根で（vyavalokayati → 観察する、viharati → 住する、abhinandan → 歓喜する）。
* 般若心経（`samples/heart-sutra.sa.txt`）: evaṃ mayā śrutam → このように / 私 / 聞いた、na rūpaṃ na vedanā … → 色・受・想・行・識
  が無い、など。連声で語がつながった箇所（tasmācchāriputra、pṛthakśūnyatā、cakṣuḥśrotra…）はまだ分け損なう。

