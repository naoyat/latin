#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語の文法の語 (人称の接辞・後置詞・助詞) と、手作りの語彙表
#
# 見出しは照合用の形 (script.key: 現代の表記、= を除く)。語彙表は北海道方言 (沙流・幌別など) の、知里幸惠『アイヌ神謡集』
# によく出る語を中心にした手作りのもの (Wiktionary のアイヌ語は約2000語で、よく使う動詞・助詞が少ないため)。
#

# 人称の接辞 (動詞の前): 接辞 → (働き, 訳)
#   語り (ユーカラ・神謡) では語り手「私」を ci= (他動詞の主語)・a= / an= (第4人称)・-as (自動詞) で表す
SUBJECT_PREFIXES = {'ku': ('主語', '私'), 'k': ('主語', '私'), 'e': ('主語', 'あなた'), 'eci': ('主語', 'あなたたち'),
                    'ci': ('主語', '私'), 'a': ('主語', '私'), 'an': ('主語', '私'), 'as': ('主語', '私')}
OBJECT_PREFIXES = {'en': ('目的語', '私'), 'un': ('目的語', '私たち'), 'i': ('目的語', '何か')}
# 人称の接尾辞 (自動詞の後ろ): -as (語り手「私」・1人称複数の除外形)、-an (第4人称)
SUBJECT_SUFFIXES = {'as': '私', 'an': '私'}

# 後置詞 (名詞の後ろ): 語 → 訳 (日本語の助詞)
POSTPOSITIONS = {'ta': 'で', 'un': 'に', 'orowa': 'から', 'wano': 'から', 'ari': 'で', 'tura': 'と一緒に', 'peka': 'を通って',
                 'kurka': 'の上で', 'corpok': 'の下で', 'sicorpok': 'の下で', 'oske': 'の中で', 'sam': 'のそばで',
                 'pakno': 'まで', 'ekimne': '山へ', 'enkasike': 'の上を', 'kasike': 'の上で', 'otta': 'で', 'konna': 'は',
                 'anakne': 'は', 'anak': 'は', 'ka': 'も', 'newa': 'と', 'turano': 'と一緒に', 'kari': 'を通って',
                 'pa': 'の頭で', 'ohta': 'に', 'kotca': 'の前で', 'sikerpe': 'の跡で', 'orowano': 'から', 'kata': 'の上に',
                 'orun': 'の中に', 'tapkasike': 'のその上に', 'nakka': 'も', 'turano': 'と一緒に', 'peka': 'の上を'}
# 用言の後ろの助詞 (接続・文末): 語 → (種類, 訳)。種類: te (〜て)、while (〜ながら)、if (〜たら)、when (〜すると)、
# because (〜ので)、but (〜けれど)、final (文末)、quote (〜と)
VERB_PARTICLES = {'wa': ('te', 'て'), 'kor': ('while', 'ながら'), 'kane': ('while', 'ながら'), 'ciki': ('if', 'たら'),
                  'yakun': ('if', 'ならば'), 'akusu': ('when', 'と'), 'ko': ('when', 'と'), 'ike': ('when', 'と'),
                  'hike': ('when', 'ところ'), 'kusu': ('because', 'ので'), 'korka': ('but', 'けれど'),
                  'awa': ('but', 'が'), 'ayne': ('te', 'て'), 'ine': ('te', 'て'), 'sekor': ('quote', 'と'),
                  'yak': ('quote', 'と'), 'na': ('final', 'よ'), 'ya': ('final', 'か'), 'ruwe ne': ('final', 'のだ'),
                  'ruwene': ('final', 'のだ'), 'siri ne': ('final', 'のだ'), 'hawe ne': ('final', 'そうだ'),
                  'kuni': ('purpose', 'ように'), 'pakno': ('until', 'まで'), 'koraci': ('like', 'ように'),
                  'noine': ('like', 'ように'), 'gusu': ('because', 'ので'), 'yakka': ('but', 'ても'),
                  'wakusu': ('because', 'ので'), 'kusne': ('purpose', 'つもりだ'), 'yan': ('final', 'よ'),
                  'ayneno': ('te', 'て'), 'siri': ('final', 'のだ'), 'okere': ('te', 'てしまって')}
# 否定・相・補助動詞 (動詞の前後)
NEGATIONS = {'somo': 'ない', 'somoki': 'ない'}
AUXILIARIES = {'a': '完了', 'okere': '〜し終える', 'rusuy': '〜したい', 'easkay': '〜できる', 'kusu ne': '〜するつもりだ',
               'nankor': '〜だろう', 'kun': '〜べき', 'nispa': None}
# 名詞 + ki「する」の決まった言い方 → 1つの動詞
KI_COMPOUNDS = {'rekpo': '歌う', 'sinot': '遊ぶ', 'itak': '話す', 'upopo': '歌う', 'rimse': '踊る', 'apkas': '歩く',
                'ipe': '食事する', 'sake': '酒を飲む', 'yukar': 'ユーカラを語る', 'cise': '家を建てる'}
COPULAS = {'ne': 'である', 'an': 'いる', 'oka': 'いる', 'isam': 'いない'}

# 手作りの語彙表: 語 → (訳, 品詞)。品詞: noun, vi (自動詞), vt (他動詞), adj (性質の自動詞), adv, pron, num, det
LEXICON = {
    # 神・人・家族
    'kamuy': ('神', 'noun'), 'aynu': ('人間', 'noun'), 'kur': ('人', 'noun'), 'menoko': ('女', 'noun'),
    'okkayo': ('男', 'noun'), 'hekaci': ('子供', 'noun'), 'hekattar': ('子供たち', 'noun'),
    'aynuhekattar': ('人間の子供たち', 'noun'), 'ekasi': ('老人', 'noun'), 'huci': ('老婆', 'noun'),
    'mici': ('父', 'noun'), 'hapo': ('母', 'noun'), 'yupi': ('兄', 'noun'), 'sapo': ('姉', 'noun'),
    'nispa': ('金持ち', 'noun'), 'wenkur': ('貧乏人', 'noun'), 'sinrit': ('先祖', 'noun'), 'utari': ('仲間', 'noun'),
    'po': ('子', 'noun'), 'matnepo': ('娘', 'noun'), 'okkaypo': ('若者', 'noun'), 'katkemat': ('奥方', 'noun'),
    # 自然・物
    'kotan': ('村', 'noun'), 'aynukotan': ('人間の村', 'noun'), 'cise': ('家', 'noun'), 'nupuri': ('山', 'noun'),
    'kim': ('山', 'noun'), 'pet': ('川', 'noun'), 'atuy': ('海', 'noun'), 'atuyteksam': ('海辺', 'noun'),
    'wakka': ('水', 'noun'), 'cep': ('魚', 'noun'), 'ape': ('火', 'noun'), 'ni': ('木', 'noun'), 'kina': ('草', 'noun'),
    'cikap': ('鳥', 'noun'), 'kamuycikap': ('梟の神', 'noun'), 'kamuycikapkamuy': ('梟の神', 'noun'),
    'cironnup': ('狐', 'noun'), 'isepo': ('兎', 'noun'), 'kimunkamuy': ('熊 (山の神)', 'noun'),
    'repunkamuy': ('沖の神', 'noun'), 'nupurkamuy': ('山の神', 'noun'), 'sirokani': ('銀', 'noun'),
    'konkani': ('金', 'noun'), 'sirokanipe': ('銀の滴', 'noun'), 'konkanipe': ('金の滴', 'noun'),
    'ay': ('矢', 'noun'), 'akusinotponpe': ('おもちゃの弓矢', 'noun'),
    'sinotponku': ('おもちゃの弓', 'noun'), 'sinotponay': ('おもちゃの矢', 'noun'), 'rera': ('風', 'noun'),
    'cup': ('太陽', 'noun'), 'sir': ('大地・様子', 'noun'), 'mosir': ('国土', 'noun'), 'kanto': ('天', 'noun'),
    'nis': ('雲', 'noun'), 'apto': ('雨', 'noun'), 'upas': ('雪', 'noun'), 'to': ('日・湖', 'noun'),
    'kewtum': ('心', 'noun'), 'hawe': ('声', 'noun'),
    'yayeyukar': ('自ら歌った謡', 'noun'), 'yukar': ('英雄叙事詩', 'noun'), 'kamuyyukar': ('神謡', 'noun'),
    'piskan': ('まわりに', 'adv'), 'arian': ('という', 'det'), 'pis': ('浜', 'noun'), 'sicorpokun': ('下の方を', 'adv'), 'rikun': ('上の方の', 'adv'),
    'petesoro': ('川に沿って', 'adv'), 'teeta': ('昔', 'adv'), 'tane': ('今', 'adv'), 'nisatta': ('明日', 'adv'),
    'kotom': ('〜らしい', 'adv'), 'siran': ('ようだ', 'vi'), 'kotomsiran': ('ようだ', 'vi'),
    # 動詞
    'an': ('いる', 'vi'), 'oka': ('いる', 'vi'), 'isam': ('いない', 'vi'), 'ne': ('である', 'vi'),
    'oman': ('行く', 'vi'), 'arpa': ('行く', 'vi'), 'paye': ('行く', 'vi'), 'ek': ('来る', 'vi'), 'arki': ('来る', 'vi'),
    'sap': ('下る', 'vi'), 'san': ('下る', 'vi'), 'kus': ('通る', 'vi'),
    'hosipi': ('帰る', 'vi'), 'ray': ('死ぬ', 'vi'), 'siknu': ('生きる', 'vi'), 'cis': ('泣く', 'vi'),
    'mina': ('笑う', 'vi'), 'hotuyekar': ('叫ぶ', 'vi'), 'ran': ('降る', 'vi'), 'ranran': ('降る降る', 'vi'),
    'sinot': ('遊ぶ', 'vi'), 'mokor': ('眠る', 'vi'), 'hopuni': ('起きる', 'vi'), 'a': ('座る', 'vi'),
    'ahun': ('入る', 'vi'), 'soyne': ('外に出る', 'vi'), 'rikin': ('登る', 'vi'), 'apkas': ('歩く', 'vi'),
    'hum': ('音がする', 'vi'), 'itak': ('言う', 'vi'), 'ye': ('言う', 'vt'), 'hawean': ('言う', 'vi'),
    'inkar': ('見る', 'vi'), 'nukar': ('見る', 'vt'), 'nu': ('聞く', 'vt'),
    'e': ('食べる', 'vt'), 'ipe': ('食事する', 'vi'), 'ku': ('飲む', 'vt'), 'kor': ('持つ', 'vt'),
    'uk': ('取る', 'vt'), 'kore': ('与える', 'vt'), 'ki': ('する', 'vt'), 'kar': ('作る', 'vt'), 'ak': ('射る', 'vt'),
    'rayke': ('殺す', 'vt'), 'ama': ('置く', 'vt'), 'ante': ('置く', 'vt'), 'tura': ('連れる', 'vt'),
    'eramuan': ('知る', 'vt'), 'eramiskari': ('知らない', 'vt'), 'ramu': ('思う', 'vt'), 'nuye': ('書く', 'vt'),
    'ekarkar': ('〜にする', 'vt'), 'kasuy': ('手伝う', 'vt'), 'kopuntek': ('喜ぶ', 'vt'), 'erampewtek': ('知らない', 'vt'),
    'koyki': ('いじめる', 'vt'), 'tukan': ('射る', 'vt'), 'sikkewe': ('目の端', 'noun'), 'rekpo': ('歌', 'noun'),
    'rek': ('鳴る・歌う', 'vi'), 'ari': ('と言って', 'adv'), 'ike': ('〜すると', 'adv'),
    # 性質
    'pirka': ('良い', 'adj'), 'wen': ('悪い', 'adj'), 'poro': ('大きい', 'adj'), 'pon': ('小さい', 'adj'),
    'sirpirka': ('天気が良い', 'adj'), 'sirwen': ('天気が悪い', 'adj'), 'retar': ('白い', 'adj'),
    'kunne': ('黒い', 'adj'), 'hure': ('赤い', 'adj'), 'tanne': ('長い', 'adj'), 'takne': ('短い', 'adj'),
    'nupe': ('涙', 'noun'), 'sipirka': ('美しい', 'adj'), 'pewre': ('若い', 'adj'), 'onne': ('年老いた', 'adj'),
    # 代名詞・指示・数
    'kani': ('私', 'pron'), 'eani': ('あなた', 'pron'), 'ciokay': ('私たち', 'pron'), 'aokay': ('私たち', 'pron'),
    'tapan': ('この', 'det'), 'taan': ('この', 'det'), 'tan': ('この', 'det'), 'toan': ('あの', 'det'),
    'nea': ('その', 'det'), 'opitta': ('みんな', 'pron'), 'hemanta': ('何', 'pron'),
    'nep': ('何か', 'pron'), 'hunak': ('どこ', 'pron'), 'nekon': ('どのように', 'adv'), 'sine': ('一つの', 'num'),
    'tu': ('二つの', 'num'), 're': ('三つの', 'num'), 'ine': ('四つの', 'num'), 'asikne': ('五つの', 'num'),
    # 副詞
    'naa': ('まだ', 'adv'), 'nani': ('すぐに', 'adv'), 'oasir': ('新たに', 'adv'), 'ponno': ('少し', 'adv'),
    'sino': ('本当に', 'adv'), 'ekesine': ('とても', 'adv'), 'easir': ('本当に', 'adv'), 'kanna': ('再び', 'adv'),
    'oyakta': ('よそで', 'adv'), 'tani': ('今', 'adv'), 'hoskino': ('先に', 'adv'),
    # 神謡集によく出る語 (人名・物・動詞)
    'okikirmuy': ('オキキリムイ', 'noun'), 'okikurmi': ('オキキリムイ', 'noun'), 'samayunkur': ('サマユンクル', 'noun'),
    'aynupitowtar': ('人間たち', 'noun'), 'aynupito': ('人間', 'noun'), 'kamuywtar': ('神々', 'noun'),
    'utar': ('人々', 'noun'), 'kamuyutar': ('神々', 'noun'), 'too': ('とても', 'adv'), 'sirki': ('〜ようだ', 'adv'), 'powtari': ('子供たち', 'noun'), 'cikappo': ('小鳥', 'noun'), 'ponku': ('小弓', 'noun'),
    'ponay': ('小矢', 'noun'), 'inaw': ('イナウ', 'noun'), 'yuk': ('鹿', 'noun'), 'humpe': ('鯨', 'noun'),
    'rametok': ('勇者', 'noun'), 'nitney': ('魔物', 'noun'), 'heper': ('子熊', 'noun'), 'toy': ('土', 'noun'),
    'nesko': ('クルミ', 'noun'), 'kosonte': ('小袖', 'noun'), 'sonko': ('伝言', 'noun'), 'irara': ('いたずら', 'noun'),
    'wenpuri': ('悪い行い', 'noun'), 'kotankor': ('村の主の', 'adj'), 'kotankorkamuy': ('村の守り神', 'noun'),
    'pase': ('尊い', 'adj'), 'yayan': ('普通の', 'adj'), 'cisewpsoro': ('家の中', 'noun'), 'pinnay': ('小さな沢', 'noun'),
    'petetok': ('川の水源', 'noun'), 'atuyka': ('海の上', 'noun'), 'tutko': ('二日', 'noun'), 'rerko': ('三日', 'noun'),
    'sineantota': ('ある日', 'adv'), 'suy': ('再び', 'adv'), 'opittano': ('みんな', 'adv'), 'tapne': ('このように', 'adv'),
    'ranke': ('何度も', 'adv'), 'usa': ('いろいろな', 'adj'), 'hetak': ('さあ', 'adv'), 'teta': ('ここに', 'adv'),
    'taporowa': ('それから', 'adv'), 'hepasi': ('下の方へ', 'adv'), 'heperay': ('子熊の', 'adj'),
    'terke': ('跳ぶ', 'vi'), 'kira': ('逃げる', 'vi'), 'yaynu': ('思う', 'vi'), 'hawokay': ('声を上げる', 'vi'),
    'mina': ('笑う', 'vi'), 'emina': ('笑う', 'vt'), 'onkami': ('拝む', 'vi'), 'isoytak': ('話をする', 'vi'),
    'yupinekur': ('兄', 'noun'), 'cisanasanke': ('私が出す', 'vt'), 'hawe as': ('声がする', 'vi'),
    'hawas': ('声がする', 'vi'), 'ikici': ('する', 'vi'), 'okaype': ('いた物', 'noun'), 'kata': ('の上に', 'adv'),
    'orun': ('の中に', 'adv'), 'tewano': ('今から', 'adv'), 'eyaykopuntek': ('喜ぶ', 'vi'), 'kamuyyaieyukar': ('神が自ら歌った謡', 'noun'),
}
