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

## Author

@naoya_t
http://github.com/naoyat | http://twitter.com/naoya_t | http://naoyat.hatenablog.jp/

## Comment

皆さんの期待に反して（？）、今日まで書いた所では全てルールベースです。

## License

(c)2013 @naoya_t, with MIT License

