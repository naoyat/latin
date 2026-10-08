#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の助詞 (格助詞・接続助詞・文末の助詞) と、よく使う機能語の表
#
# 格助詞の形は前の音節の終わりで変わる (能格・具格 gis: -g/-d/-b/-s の後 kyis、-ng/-n/-m/-r/-l の後 gyis、母音の後
# -s (語に付く) か yis)。どの形も同じ働きとして扱う。
#

# 異形 → 代表の形
ALLOMORPHS = {
    'kyis': 'gis', 'gyis': 'gis', 'yis': 'gis', 's': 'gis',
    'kyi': 'gi', 'gyi': 'gi', 'yi': 'gi', "'i": 'gi',
    'du': 'la', 'tu': 'la', 'su': 'la', 'ru': 'la', 'r': 'la',
    'yang': 'kyang', "'ang": 'kyang',
    'ste': 'te',
    'zhing': 'cing', 'shing': 'cing',
    # de は用言の後ろなら接続 (= te)、体言の後ろなら指示詞 (analyzer で決める)
    'ngo': 'go', 'do': 'go', 'no': 'go', 'bo': 'go', 'mo': 'go', "'o": 'go', 'ro': 'go', 'so': 'go', 'to': 'go',
    'ngam': 'gam', 'dam': 'gam', 'nam': 'gam', 'bam': 'gam', 'mam': 'gam', "'am": 'gam', 'ram': 'gam',
    'lam': 'gam', 'sam': 'gam', 'tam': 'gam',
    'ces': 'zhes', 'shes': 'zhes',
    'zhig': 'cig', 'shig': 'cig',
}

# 代表の形 → (働き, 体言の後ろの訳, 用言の後ろの訳)。訳の None は「語順と形で決める」
PARTICLES = {
    'gis': ('能格・具格', None, 'ので'),          # 動作主「が」/ 道具「で」。用言の後ろは理由
    'gi': ('属格', 'の', 'が'),                   # 用言の後ろは逆接・並列「〜が」
    'la': ('与格・処格 (la don)', 'に', 'て'),    # 「に・へ」。用言の後ろは「〜して」
    'na': ('処格', 'で', 'なら'),                 # 用言の後ろは条件「〜なら・〜すると」
    'nas': ('奪格', 'から', 'てから'),
    'las': ('奪格・比較', 'から', 'てから'),
    'dang': ('共格', 'と', 'と'),                 # 用言の後ろは「〜すると」
    'ni': ('主題', 'は', 'のは'),
    'kyang': ('添加', 'も', 'ても'),
    'te': ('接続', '', 'て'),
    'cing': ('接続', '', 'て'),
    'go': ('文末', '', ''),
    'gam': ('疑問', 'か', 'か'),
    'zhes': ('引用', 'と', 'と'),
    'cig': ('不定', '', ''),                      # 体言の後ろ「ある〜」、用言の後ろは命令「〜せよ」
    'tsam': ('程度', 'ほど', 'だけ'),
    'bas': ('比較', 'より', 'より'),
    'lo': ('伝聞', '', 'そうだ'),
    'dag': ('複数', 'たち', ''),
    'rnams': ('複数', 'たち', ''),
    'cag': ('複数', 'たち', ''),
}
CASES = {'gis', 'gi', 'la', 'na', 'nas', 'las', 'dang'}

# 否定 (mi: 現在・未来、ma: 過去・命令) と、存在・繋辞の動詞
NEGATIONS = {'mi', 'ma'}
COPULAS = {'yin': 'である', 'red': 'である', 'lags': 'でございます', 'min': 'ではない', 'ma yin': 'ではない'}
EXISTENTIALS = {'yod': 'ある', "'dug": 'ある', 'med': 'ない', 'mchis': 'ある', 'bzhugs': 'いらっしゃる'}

# 指示詞・代名詞 (訳語を決めておく)
DETERMINERS = {"'di": 'この', 'de': 'その', 'gzhan': 'ほかの', 'thams cad': 'すべての', 'kun': 'すべての'}
PRONOUNS = {'nga': '私', 'bdag': '私', 'kho': '彼', 'khyed': 'あなた', 'khyod': 'お前', 'kho bo': '私',
            'nged': '私たち', 'kho mo': '彼女', 'su': '誰', 'ci': '何', 'gang': 'どれ', 'de': 'それ', "'di": 'これ',
            'rang': '自分', 'kho rang': '彼自身'}
NUMERALS = {'gcig': '一', 'gnyis': '二', 'gsum': '三', 'bzhi': '四', 'lnga': '五', 'drug': '六', 'bdun': '七',
            'brgyad': '八', 'dgu': '九', 'bcu': '十', 'brgya': '百', 'stong': '千'}

# 訳語を決めておく語 (辞書の最初の英語の訳語からでは外れるもの。仏典に多い意味を優先)
GLOSSES = {
    'dus': '時', 'chos': '法', 'sangs rgyas': '仏陀', 'bstan': '説く', 'gcod': '切る', 'bcad': '切る',
    'lha sa': 'ラサ', 'dngul': 'お金', 'yi ge': '手紙', 'bla ma': 'ラマ', 'byang chub sems dpa\'': '菩薩',
    'bcom ldan \'das': '世尊', 'dge slong': '比丘', 'sems can': '衆生', 'sems': '心', 'stong pa nyid': '空性',
    'shes rab': '智慧', 'snying rje': '慈悲', 'dkon mchog': '三宝', 'mdo': '経', 'rgyal po': '王', 'lha': '神',
    'thos': '聞く', 'gsungs': 'おっしゃる', 'gsung': 'おっしゃる', 'smras': '言う', 'smra': '言う', 'zer': '言う',
    'mthong': '見る', 'bltas': '見る', 'lta': '見る', "'gro": '行く', 'song': '行く', 'phyin': '行く',
    'byon': 'いらっしゃる', 'bzhugs': 'いらっしゃる', 'byin': '与える', 'sbyin': '与える', 'za': '食べる',
    'zos': '食べる', 'btung': '飲む', "'thung": '飲む', 'bris': '書く', "'bri": '書く', 'shing': '木',
    'zas': '食べ物', 'khyim': '家', 'rta': '馬', 'bu': '息子', 'bu mo': '娘', 'slob ma': '弟子',
    'gser': '金', 'ldan': '具える', 'len': '取る', 'blangs': '取る', 'bde ba': '幸せ', 'gyur': 'なる',
    "'gyur": 'なる', 'ri bo': '山', 'mi': '人', 'yul': '国', 'ri': '山', 'chu': '水', 'nyi ma': '太陽', 'zla ba': '月',
    'ston': '説く', 'lhung': '落ちる', 'ltung': '落ちる', 'shi': '死ぬ', "'chi": '死ぬ', 'skyes': '生まれる', 'skye': '生まれる',
}
HUMANS = {'sangs rgyas', 'bla ma', 'dge slong', "byang chub sems dpa'", "bcom ldan 'das", 'rgyal po', 'blon po',
          'slob ma', 'bu', 'bu mo', 'mi', 'sems can', 'lha', 'dge bshes', 'mkhan po', 'slob dpon', 'btsun mo',
          'rgyal bu', 'yab', 'yum', 'pha', 'ma', 'bu tsha', 'grogs po', 'dgra'}
TIME_NOUNS = {'時', '日', '年', '夜', '朝', '昔', '月', '晩'}
# 名詞 + 動詞の慣用的な組み合わせ (敬語が多い) → 1つの動詞
COMPOUND_VERBS = {('phyag', "'tshal"): '礼拝する', ("bka'", 'stsal'): 'おっしゃる', ("bka'", 'gnang'): 'おっしゃる',
                  ('zhal', 'gyis'): 'お召し上がりになる', ('thugs', 'rje'): '慈しむ', ('gsol ba', "'debs"): '祈る',
                  ('gsol ba', 'btab'): '祈る', ('mchod pa', 'byed'): '供養する', ('mchod pa', 'byas'): '供養する',
                  ('dad pa', 'skyes'): '信じる', ('mgo', 'bo'): ''}
MOTION_VERBS = {"'gro", 'song', 'phyin', "'ong", 'byon', 'yong', 'gshegs'}
FIRST_PERSON = {'nga', 'bdag', 'kho bo', 'nged', 'bdag cag'}
ADVERBS = {"'di skad": 'このように', "'di ltar": 'このように', 'de nas': 'それから', 'yang': 'また', 'shin tu': 'とても',
           'da': '今', 'sngon': '昔', 'slar': 'ふたたび'}

# 時制
TENSE_NAMES = {'pres': '現在', 'past': '過去', 'fut': '未来', 'imp': '命令'}


def normalize(wylie):
    return ALLOMORPHS.get(wylie, wylie)


def particle(wylie):
    return PARTICLES.get(normalize(wylie))
