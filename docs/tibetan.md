# 古典チベット語（作りかけ）

古典チベット語（仏典・史書・伝記の文語）を語に分け、格助詞（能格・属格・la don …）・動詞の語幹の時制・否定を示して、
日本語に訳します。語順はほぼ日本語と同じ（動詞が文末、格助詞は後ろ）なので、古文と同じく共通の解析器（格の枠）は
通さず、語順をそのまま日本語にします（名詞の後ろに来る形容詞・数詞・指示詞だけ前へ）。

```
./dragoman.py bo samples/tibetan.txt          # -w で語ごとの分解を省く
./dragoman.py bo -e "རྒྱལ་པོས་བློན་པོ་ལ་གསེར་བྱིན་ནོ།"
python3 tools/samples.py --lang=bo            # サンプルの訳 (-d で語ごとの分解)
```

```
ཁོས་སྟ་རེས་ཤིང་བཅད་དོ།  (khos sta res shing bcad do/)
  ཁོ  kho     代名詞  彼  能格 (動作主) →「が」
  ས  s       助詞  能格・具格 (gis の形)
  སྟ་རེ  sta re  名詞  斧  具格 (道具・手段) →「で」
  ས  s       助詞  能格・具格 (gis の形)
  ཤིང  shing   名詞  木  絶対格 (目的語) →「を」
  བཅད  bcad    動詞  切る  過去形 (見出し gcod)
  དོ  do      助詞  文末 (go の形)
  →  彼が斧で木を切った。

འདི་སྐད་བདག་གིས་ཐོས་པའི་དུས་གཅིག་ན།  ('di skad bdag gis thos pa'i dus gcig na/)
  →  このように私が聞いたある時に。
```

## 準備

データはリポジトリに入れず、`~/.local/share/dragoman-data/bo/` に置きます。

```
pip install botok                                   # 語の区切り (OpenPecha、Apache-2.0。無くても辞書の最長一致で動く)
mkdir -p ~/.local/share/dragoman-data/bo/{hill,kaikki,dict} && cd ~/.local/share/dragoman-data/bo
curl -L -o hill/Lexicons.zip "https://zenodo.org/records/574876/files/Lexicons.zip?download=1"   # 品詞辞書 (CC BY 4.0)
curl -L -o hill/Texts.zip "https://zenodo.org/records/574878/files/Texts.zip?download=1"         # 評価用コーパス (CC BY 4.0)
(cd hill && unzip -o Lexicons.zip -d lex && unzip -o Texts.zip -d texts)
curl -L -o kaikki/kaikki.org-dictionary-Tibetan.jsonl https://kaikki.org/dictionary/Tibetan/kaikki.org-dictionary-Tibetan.jsonl
# 任意: 蔵英・梵蔵の辞書 (著作権はそれぞれの著者。手元だけで使う)
for f in 01-Hopkins2015 02-RangjungYeshe 15-Hopkins-Skt2015 21-Mahavyutpatti-Skt; do
  curl -L -o dict/$f https://raw.githubusercontent.com/christiansteinert/tibetan-dictionary/master/_input/dictionaries/public/$f
done
cd - && python3 tools/build_tibetan_dic.py         # → ~/.local/share/dragoman-data/bo/tibetan.sqlite
```

botok の辞書パック（約12MB）は初回に `~/.local/share/dragoman-data/bo/botok/` へ自動でダウンロードされます。

## しくみ

* 転写はワイリー式（EWTS）。音節ごとに基字（母音の付く字。重ね字なら全体）を決めて、母音記号が無ければ a を補う
  （བསྒྲུབས → bsgrubs、དགའ → dga'、གཡོ → g.yo、པའི → pa'i、པདྨ → padma）。基字の分からない音節（དགས: dags / dgas）は
  辞書にある方を選ぶ。Wiktionary の転写と 99% 一致。
* 語の区切りは botok。語に付いた格助詞（རྒྱལ་པོས → rgyal po + s）も切り離す。botok の誤りのうち規則で直せるもの:
  奪格の las を語の一部と取り違えたもの（རྟ་ལ + ས → rta + las）、動詞の過去の語幹の -s を助詞として切ったもの
  （smra + s → smras）、代名詞に付いた能格（khos → kho + s）、文末の 'o の付いたまま（bsgo'o）、命令の cig の付いたまま
  （gyur cig）。
* 格助詞は異形をまとめる（kyis / gyis / yis / -s → gis、kyi / gyi / yi / 'i → gi、du / tu / su / ru / -r → la）。
  * 能格・具格 gis: 人（代名詞・人を表す語）なら動作主「が」、物なら道具「で」（khos sta res → 彼が斧で）。
  * 何も付かない名詞（絶対格）: 同じ節に能格の名詞があるか、動詞が他動詞なら目的語「を」、ほかは主語「が」。
    他動詞かどうかは日本語の訳語の自他（JMdict。古文と共通の `ja-transitivity.tsv`）で見る。
  * 繋辞 yin の文は最初の名詞を「は」（kho slob ma yin → 彼は弟子である）。存在動詞 yod / med の文の、人の la は
    所有者「〜には」（nga la dngul med → 私にはお金がない）。X dang ldan →「X を具える」。
  * 属格 gi →「の」、la →「に」、na →「で」（時の名詞なら「に」）、nas / las →「から」、dang →「と」、ni →「は」、
    kyang →「も」、zhes →「と」、bas →「より」。
* 動詞は語幹（現在・過去・未来・命令）から時制を決める。語幹の対応は Wiktionary の活用表と Rangjung Yeshe の
  「pf. of {sgrub pa}」などから（bsgrubs → sgrub の過去）、時制は Hill & Garrett の品詞の印（v.past, v.fut.v.pres …）を先に使う。
  * 否定 mi（現在・未来）→「〜ない」、ma（過去・命令）→「〜なかった・〜するな」。
  * 接続の te / cing / la →「〜て」、nas →「〜てから」、na →「〜なら」、kyang →「〜ても」。
  * 動名詞（+ pa / ba）+ 属格は連体形で名詞に掛ける（thos pa'i dus → 聞いた時）。ほかの格助詞なら「〜こと + 助詞」、
    文末なら言い切り（bka' stsal pa → おっしゃった）。V-par gyur →「〜ようになる」、V-bar bya →「〜しよう」（一人称）。
  * 目的: V + du + 行く →「〜しに行く」（chu len du song → 水を取りに行った）。祈願 gyur cig →「〜なりますように」。
  * 名詞 + 動詞の慣用的な組み合わせ（phyag 'tshal → 礼拝する、bka' stsal → おっしゃる）。
* 仏教の術語は、助詞をまたぐ言い方も1語として漢訳語で訳す（shes rab kyi pha rol tu phyin pa → 般若波羅蜜多、
  rgyal po'i khab → 王舎城、bla na med pa yang dag par rdzogs pa'i byang chub → 阿耨多羅三藐三菩提、色・受・想・行・識、
  眼・耳・鼻・舌・身・意、無明・老死、苦・集・滅・道 …。`tibetan/grammar.py` の TERMS）。称号と名前は1つの名詞句に
  （tshe dang ldan pa shA ri'i bus → 具寿舎利子が）。
* チベット文字で書いたサンスクリット（経題・真言。長母音 ཱ、そり舌音、有声の有気音、ཾ などで見分ける）は訳さずに
  IAST で出す（ག་ཏེ་ག་ཏེ་པཱ་ར་ག་ཏེ → 〔gategatepāragate〕）。
* 訳語は Wiktionary → Hopkins → Rangjung Yeshe の英語を、ほかの言語と共通の英語 → 日本語の表（`core/en_ja.py`）で
  日本語にする。よく使う語（特に仏典の語: chos → 法、sangs rgyas → 仏陀、sems can → 衆生）は `tibetan/grammar.py` の表で決める。
* サンスクリットの原語を注に出す:
  * 仏典の定型句は、原文と漢訳の名前で（'di skad bdag gis thos pa → evaṃ mayā śrutam（如是我聞）、dus gcig na →
    ekasmin samaye（一時）、sangs rgyas la skyabs su mchi → buddhaṃ śaraṇaṃ gacchāmi（帰依仏）、帰敬の句など。
    `tibetan/grammar.py` の FORMULAS）。
  * 語ごとの原語は Mahāvyutpatti（翻訳名義大集）と Hopkins の表から2つまで（rgyal po → rājā, nṛpa、chos → dharma）。
    動詞は見出し（現在の語幹）でも引く。外れるもの（bla ma → uttaraḥ ではなく guru）は表で直す。

## 発音と音読

見出しの下に、ラサ方言を土台にした発音を IPA と声調で出します（`tibetan/phonology.py`）。

音読（`-s`）は、Meta の [MMS-TTS](https://huggingface.co/facebook/mms-tts-bod)（中央チベット語の録音で学習した VITS の
モデル。CC BY-NC 4.0、約145MB。transformers と torch が要る）があればそれでチベット文字のまま読み、無ければ（`-t espeak`
でも）espeak-ng の普通話の音声（`-v cmn`。有気・無気、そり舌・歯茎硬口蓋の破擦音、声調がある）に上の発音を音素で渡します。

```
mkdir -p ~/.local/share/dragoman-data/bo/mms-tts-bod && cd ~/.local/share/dragoman-data/bo/mms-tts-bod
for f in config.json vocab.json tokenizer_config.json special_tokens_map.json model.safetensors; do
  curl -L -O https://huggingface.co/facebook/mms-tts-bod/resolve/main/$f
done
```

```
./dragoman.py bo -s -e "བླ་མ་ལ་ཕྱག་འཚལ་ལོ།"                 # [la˥.ma˩˧ la˩˧ cʰaʔ˥˩.tsʰɛː˥ lo˩˧]
./dragoman.py bo --pron=chant -e "བླ་མ་ལ་ཕྱག་འཚལ་ལོ།"        # 読誦式 [… cʰaʔ˥˩.tsʰal˥ …]
```

* 語頭の子音: 前置字・上に乗る字は読まない（bsgrubs → ʈup）。下に付く字で変わる（ky / py → c、khy / phy → cʰ、
  kr / tr / pr → ʈ、khr → ʈʰ、bl / kl / sl / rl → l、zl → t、sr → s、hr → ʂ）。lh → l̥（無声の l。lha sa → l̥a˥.sa˥）、
  db → w（dbang → waŋ）、dby → j。有声の基字 g j d b dz は無声になり、前置字・上に乗る字が無ければ有気（ga → kʰa）、
  あれば無気（dga → ka）。2音節目以降は無気。
* 声調: 無声の基字・ཨ、前置字か上に乗る字のある鳴音（rna, sna, g.yu）、lh は高い調子（˥）、有声の基字・前置字の
  無い鳴音・འ は低い調子（˩˧）。高い調子は -g / -b / -d / -s の音節で下がる（˥˩）。
* 語末: -g → ʔ、-ng → ŋ、-b → p、-m → m、-r → r、-n → n、-d / -s は読まない、-l は読まずに母音を伸ばす。
  -d / -s / -l / -n と語末の 'i の前で a → ɛ、o → ø、u → y（bod → pʰø、'tshal → tsʰɛː、pa'i → pɛː）。
  2つ目の後置字の -s（legs, sangs）の前では変わらない。ཾ → m、ྃ → ŋ（oM → om、hUM → huŋ）。
* 語の中の2音節目以降の前置字 ' / m は、前の音節の鼻音になる（dge 'dun → ken.tyn、bka' 'gyur → kaŋ.cur）。
* `--pron=chant`（読誦式）: 語末の母音を変えず、-l / -n を読む（'tshal → tsʰal、「チャク ツァル ロ」）。
* まだ: espeak-ng の音声に ø が無いので e で代用、声調は普通話の調子（55, 51, 35）で近似。語の中の声調の変化
  （2音節目の調子）、語中の有声化（mchod rten → tɕʰø.tɛn の t の有声化）、サンスクリットの音節は綴りのまま。

## 般若心経

`samples/heart-sutra.bo.txt` にデルゲ版カンギュルのチベット語訳（広本、全文。Wikisource から、パブリックドメイン）、
`samples/heart-sutra.sa.txt` にサンスクリット本（小本と広本。サンスクリット版 Wikisource から）を置いています。

```
./dragoman.py bo -w samples/heart-sutra.bo.txt
  →  具寿舎利子が菩薩摩訶薩聖観自在にこのように言った。
  →  色空である。
  →  阿耨多羅三藐三菩提に現等覚した。
  →  〔gategatepāragate〕。
```

長い文のために入れた規則（`tibetan/analyzer.py`）:

* 接続の助詞（dang, te, cing）の後の区切り記号では文を切らない（tshor ba dang། 'du shes dang། … stong pa'o → 受と想と行と識は空である）。
* 名詞 + 文末の 'o は述語で、前の名詞を「は」に（gzugs stong pa'o → 色は空である）。X gzhan ma yin → Xは別ではない。
* 属格の後の後置詞: X kyi bar du → Xまで、V-pa'i phyir → 〜ないために、X zhes bya ba'i Y → XというY。
* 動名詞: V-pa dang → 〜すると、V-pa med → 〜することがない、V-par 'dod pa → 〜しようと欲する、V-par byed → 〜する（他動詞に）、
  V-pa de（関係節）→ 〜するその者、時の名詞の前は連体（thos pa dus → 聞いた時）。
* 呼びかけ（文頭の shA ri'i bu → 舎利子よ、）、名詞 + de（接続）→ 〜であって、X-r + 見る動詞 → Xであると観察する、
  疑問詞（ji ltar …）の文は「〜か」（ji ltar … de bzhin du の相関は除く）。

```
具寿舎利子が菩薩摩訶薩聖観自在にこのように言った。
善男子か善女人を誰でも甚深な般若波羅蜜多の行を行じようと欲するその者がどのように学ぶべきか。
色は空である。空性は色である。色から空性は別ではない。空性からも色は別ではない。
そのように受と想と行と識たちは空である。
舎利子よ、それゆえすべての法が空性であって、相がない。
舎利子よ、それゆえ空性に色がない。受がない。… 意識界までもない。
般若波羅蜜多に依って住して、心に罣礙がないので恐れることがなく、顛倒からすっかり越えてから涅槃の究竟に至った。
```

奥書（訳者・校閲者の名前の並び）はまだ崩れます。

## 評価

Hill & Garrett の手で品詞を付けたコーパス（『賢愚経』、プトンの仏教史、ミラレパ伝・マルパ伝。約28万語）で測ります。
古典チベット語の Universal Dependencies はまだ無いので、主語・目的語の再現率ではなく、語の区切り・品詞・格助詞・時制。

```
python3 tools/bo_eval.py [--source=mdzangsblun,buston,mila,marpa] [--limit=N]
```

| 語の区切り (F1) | 品詞 (区切りの合った語) | 格助詞 | 時制 (時制が1つの動詞) |
|---|---|---|---|
| 86.1% | 95.1% | 86.2% | 92.2% |

* 語の区切りの食い違いの多くは流儀の違い: 正解のコーパスは決まった言い回し（'di skad、shin tu、de nas、gal te）を
  分け、語に付いた -r も切る（phyir → phyi + r、mngon par → mngon pa + r）。botok はこれらを1語にする（訳にはその方がよい）。
* Hill & Garrett の品詞辞書はこのコーパスから作られているので、品詞と時制、botok の分けた複合語をつなぐ処理
  （byang chub + sems dpa' → byang chub sems dpa'。品詞辞書の名詞を使う）の数字はやや良く出る。
* 仏教の術語を助詞ごと1語にする処理（shes rab kyi pha rol tu phyin pa）は、正解のコーパスの区切りとは合わないので、
  語の区切りと格助詞の数字は少し下がる（訳にはこの方がよい）。
* 能格と具格は正解の印が同じ（case.agn）なので、「が」と「で」の選び分けは測れていない。

## まだ

* 能格と具格の選び分けの改善（人でない動作主、主語の省略された文の道具）。
* 敬語の動詞（gsung, mdzad, gshegs …）を日本語の敬語に、動詞の語幹の表の拡充、複合動詞の表の拡充。
* 音読: チベット語の録音で学習した音声（Meta の MMS-TTS など。ライセンスと方言を確かめてから）。
* 長い文の節の切れ目（接続の助詞で切った節ごとの主語の引き継ぎ）。
* 対訳での確認（SansTib の梵蔵対訳、ACTib の大きなコーパス）。
