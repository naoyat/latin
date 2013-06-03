ラテン語んご

初級ラテン語リーディングに参加しながらラテン語そしてPythonと親しんでみた

## demo

```
# 音読あり
$ python latin.py -s texts/1.TESSEUS_ET_ARIADNE.txt

# 音読なし
$ python latin.py texts/1.TESSEUS_ET_ARIADNE.txt | less -R
```

## usage

```
使い方: python ./latin.py [オプション] [ファイル名]
オプション:
  -w, --no-word-detail               単語の詳細を表示しない
  -q, --no-translation               日本語訳を表示しない
  -m, --strict-macron                [REPL] 大文字でのマクロン入力を行わない
  -a, --auto-macron                  マクロンなしでも何とかする
  -s, --speech                       合成音声で音読する (MacOS only)
  -h, --help                         オプション解説など表示して終了
```

音読機能（-s）は、北米英語の音素で無理やり読ませているのでアメリカ英語訛りです。

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

## Author

@naoya_t
http://github.com/naoyat | http://twitter.com/naoya_t | http://naoyat.hatenablog.jp/

## Comment

皆さんの期待に反して（？）、今日まで書いた所では全てルールベースです。

## License

(c)2013 @naoya_t, with MIT License

