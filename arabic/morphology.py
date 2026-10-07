#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア語 (現代標準アラビア語) の語形の解析: CAMeL Tools の形態素辞書 (calima-msa-r13) の解析を、
# 切れ目 (接頭の接続詞・前置詞、本体、人称接尾辞) ごとの解析器 (core/) の項目 (dict) にする
#
#   وَبِالقَلَمِ  → وَ 接続詞「そして」 + بِ 前置詞「〜で」 + القَلَم 名詞「ペン」(定冠詞付き)
#   كِتابُهُم    → كِتاب 名詞「本」 + هُم 人称接尾辞「彼らの」(属格)
#   سَيَكْتُبُونَ → كَتَبَ 動詞 未完了・3人称男性複数 + سَ「〜だろう」(未来。動詞に含める)
#
# 母音記号の無い語は読みが多いので、MLE の曖昧性解消 (CAMeL Tools の disambig-mle-calima-msa-r13) の点数で
# 見出し語・品詞・切れ目の組 (読み) を並べ、文の解析 (arabic/analyzer.py) が文脈で選ぶ。格 (主格 -u・対格 -a・
# 属格 -i) は母音記号が無ければ決まらないので、読みの中の格の候補をすべて残し、前置詞・連語 (iḍāfa) などで絞る。
# 母音記号付きの語は、記号と合う解析だけを使う
#
import functools
import os
import re
import unicodedata
from dataclasses import dataclass, field

from . import dictionary, script

DATA_DIR = os.path.join(os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data')), 'ar')
os.environ.setdefault('CAMELTOOLS_DATA', os.path.join(DATA_DIR, 'camel'))

CASES = {'n': ('Nom',), 'a': ('Acc',), 'g': ('Gen',), 'u': ('Nom', 'Acc', 'Gen')}
NUMBERS = {'s': 'sg', 'd': 'du', 'p': 'pl'}
GENDERS = {'m': ('m',), 'f': ('f',)}
STATES = {'d': 'definite', 'i': 'indefinite', 'c': 'construct'}
NOMINAL_POS = {'noun', 'noun_prop', 'noun_num', 'noun_quant', 'adj', 'adj_comp', 'adj_num', 'pron', 'pron_dem',
               'pron_rel', 'pron_interrog', 'pron_exclam'}
# 読みを選ぶときに下げる品詞 (略語 إن「N.」など。ほかの読みがあれば使わない)
RARE_POS = {'abbrev', 'latin', 'digit'}

# 人称接尾辞・独立人称代名詞の訳 (人称・性・数 → 訳)
PERSONAL = {'1s': '私', '2ms': 'あなた', '2fs': 'あなた', '3ms': '彼', '3fs': '彼女', '1p': '私たち',
            '2mp': 'あなたたち', '2fp': 'あなたたち', '2d': 'あなたたち二人', '3mp': '彼ら', '3fp': '彼女ら',
            '3d': '彼ら二人'}
# 接頭辞 (proclitic) の訳
PROCLITICS = {
    'wa_conj': ('conj', 'وَ', 'そして,〜と'), 'wa_sub': ('conj', 'وَ', 'そして,〜と'),
    'wa_part': ('conj', 'وَ', 'そして,〜と'), 'fa_conj': ('conj', 'فَ', 'そして,すると'),
    'fa_conn': ('conj', 'فَ', 'そして,すると'), 'fa_sub': ('conj', 'فَ', 'すると'), 'fa_rc': ('conj', 'فَ', 'すると'),
    'bi_prep': ('preposition', 'بِ', '〜で,〜によって'), 'li_prep': ('preposition', 'لِ', '〜のために,〜に'),
    'la_prep': ('preposition', 'لَ', '〜のために,〜に'), 'ka_prep': ('preposition', 'كَ', '〜のように'),
    'fiy_prep': ('preposition', 'فِي', '〜の中で,〜で'), 'wa_prep': ('preposition', 'وَ', '〜にかけて'),
    'ta_prep': ('preposition', 'تَ', '〜にかけて'), 'yA_voc': ('adv', 'يا', '〜よ'), 'wA_voc': ('adv', 'وا', 'ああ'),
    '>a_ques': ('adv', 'أَ', '〜か (疑問)'), 'li_sub': ('conj', 'لِ', '〜するために'),
    'mA_neg': ('adv', 'ما', '〜ない'), 'lA_neg': ('adv', 'لا', '〜ない'),
}
# 動詞に含める接頭辞 (未来の sa-、強めの la-、命令の li-)
VERBAL_PROCLITICS = {'sa_fut', 'la_emph', 'la_rc', 'li_jus', 'bi_part', 'hA_dem'}

# 前置詞と、前置詞として扱う語 (CAMeL Tools では副詞的な名詞のものもある: عِنْدَ, قَبْلَ, بَعْدَ)。訳は手で
PREPOSITIONS = {
    'فِي': '〜の中で,〜で', 'إِلَى': '〜へ,〜まで', 'مِن': '〜から', 'مِنْ': '〜から', 'عَلَى': '〜の上に,〜に',
    'عَن': '〜について,〜から', 'عَنْ': '〜について,〜から', 'مَع': '〜とともに', 'مَعَ': '〜とともに',
    'حَتَّى': '〜まで', 'عِنْد': '〜のところに', 'عِنْدَ': '〜のところに', 'بَيْن': '〜の間に', 'بَيْنَ': '〜の間に',
    'قَبْل': '〜の前に', 'قَبْلَ': '〜の前に', 'بَعْد': '〜の後に', 'بَعْدَ': '〜の後に', 'تَحْت': '〜の下に',
    'تَحْتَ': '〜の下に', 'فَوْق': '〜の上に', 'فَوْقَ': '〜の上に', 'مُنْذُ': '〜以来', 'حَوْل': '〜の周りに',
    'حَوْلَ': '〜の周りに', 'خِلال': '〜の間に', 'خِلالَ': '〜の間に', 'أَمام': '〜の前に', 'أَمامَ': '〜の前に',
    'نَحْو': '〜の方へ', 'نَحْوَ': '〜の方へ', 'دُون': '〜なしに', 'دُونَ': '〜なしに', 'ضِدّ': '〜に反して',
    'لَدَى': '〜のもとに', 'لَدَيْ': '〜のもとに', 'وَراء': '〜の後ろに', 'وَراءَ': '〜の後ろに', 'ب': '〜で,〜によって',
    'ل': '〜のために,〜に', 'ك': '〜のように', 'مِثْل': '〜のように', 'ضِمْن': '〜の中に', 'ضِمْنَ': '〜の中に',
    'إِثْر': '〜の後に', 'عَبْر': '〜を通って', 'عَبْرَ': '〜を通って', 'لِ': '〜のために,〜に', 'بِ': '〜で,〜によって',
    'كَ': '〜のように', 'لَ': '〜のために,〜に',
}
# 機能語の訳 (見出し語 (CAMeL Tools の lex) → (品詞, 訳))
FUNCTION_WORDS = {
    'وَ': ('conj', 'そして,〜と'), 'فَ': ('conj', 'そして,すると'), 'ثُمَّ': ('conj', 'それから'),
    'أَو': ('conj', 'または'), 'أَوْ': ('conj', 'または'), 'أَم': ('conj', 'それとも'), 'أَمْ': ('conj', 'それとも'),
    'لٰكِن': ('conj', 'しかし'), 'لٰكِنَّ': ('conj', 'しかし'), 'لَكِن': ('conj', 'しかし'), 'لَكِنَّ': ('conj', 'しかし'),
    'بَل': ('conj', 'むしろ'), 'بَلْ': ('conj', 'むしろ'),
    'أَن': ('conj', '〜すること'), 'أَنْ': ('conj', '〜すること'), 'أَنَّ': ('conj', '〜ということ'),
    'إِنَّ': ('conj', '実に'), 'لِأَنَّ': ('conj', 'なぜなら'), 'كَأَنَّ': ('conj', 'あたかも〜のように'),
    'إِذا': ('conj', 'もし〜なら'), 'إِن': ('conj', 'もし'), 'إِنْ': ('conj', 'もし'), 'لَو': ('conj', 'もし'),
    'لَوْ': ('conj', 'もし'), 'كَي': ('conj', '〜するために'), 'كَيْ': ('conj', '〜するために'),
    'عِنْدَما': ('conj', '〜するとき'), 'بَيْنَما': ('conj', '〜する間に'), 'حَيْثُ': ('conj', '〜するところで'),
    'لَمّا': ('conj', '〜したとき'), 'كَما': ('conj', '〜のように'),
    'لا': ('adv', '〜ない'), 'لَم': ('adv', '〜ない'), 'لَمْ': ('adv', '〜ない'), 'لَن': ('adv', '〜ない'),
    'لَنْ': ('adv', '〜ない'), 'ما': ('adv', '〜ない'), 'غَيْر': ('adv', '〜でない'),
    'قَد': ('adv', 'すでに'), 'قَدْ': ('adv', 'すでに'), 'سَوْفَ': ('adv', '〜だろう'), 'هَل': ('adv', '〜か (疑問)'),
    'هَلْ': ('adv', '〜か (疑問)'), 'يا': ('adv', '〜よ'), 'إِلّا': ('adv', '〜を除いて'), 'أَيْضًا': ('adv', 'もまた'),
    'أَيْضاً': ('adv', 'もまた'), 'جِدًّا': ('adv', 'とても'), 'جِدّاً': ('adv', 'とても'), 'فَقَط': ('adv', '〜だけ'),
    'الآن': ('adv', '今'), 'هُنا': ('adv', 'ここに'), 'هُناكَ': ('adv', 'そこに'), 'هُناك': ('adv', 'そこに'),
    'نَعَم': ('adv', 'はい'), 'كَلّا': ('adv', 'いいえ'), 'غَدًا': ('adv', '明日'), 'غَداً': ('adv', '明日'),
    'أَمْسِ': ('adv', '昨日'), 'أَمْس': ('adv', '昨日'), 'اليَوْمَ': ('adv', '今日'), 'دائِمًا': ('adv', 'いつも'),
    'أَبَدًا': ('adv', '決して'), 'أَيْن': ('adv', 'どこに'), 'أَيْنَ': ('adv', 'どこに'), 'مَتَى': ('adv', 'いつ'),
    'كَيْفَ': ('adv', 'どのように'), 'لِماذا': ('adv', 'なぜ'),
}
PRONOUNS = {
    'أَنا': ('1', 's', ''), 'أَنْتَ': ('2', 's', 'm'), 'أَنْتِ': ('2', 's', 'f'), 'هُوَ': ('3', 's', 'm'),
    'هِيَ': ('3', 's', 'f'), 'نَحْنُ': ('1', 'p', ''), 'أَنْتُم': ('2', 'p', 'm'), 'أَنْتُنَّ': ('2', 'p', 'f'),
    'هُم': ('3', 'p', 'm'), 'هُنَّ': ('3', 'p', 'f'), 'هُما': ('3', 'd', ''), 'أَنْتُما': ('2', 'd', ''),
}
DEMONSTRATIVES = {'هٰذا': 'この,これ', 'هٰذِهِ': 'この,これ', 'هٰؤُلاءِ': 'これらの,これら', 'ذٰلِكَ': 'その,あれ',
                  'تِلْكَ': 'その,あれ', 'أُولٰئِكَ': 'それらの,それら', 'هَذا': 'この,これ', 'هَذِهِ': 'この,これ',
                  'ذَلِكَ': 'その,あれ', 'هَؤُلاءِ': 'これらの,これら'}
RELATIVE = '〜するところの'
# inna とその姉妹 (母音記号とハムザを除いた形 → 訳)
INNA = {'ان': '実に', 'لكن': 'しかし', 'كان': 'あたかも〜のように', 'ليت': '〜ならよいのに', 'لعل': 'おそらく',
        'لان': 'なぜなら'}
# 訳語を手で決める見出し語 (Wiktionary の英語の訳語の先頭が良くないもの)。動詞と名詞類で分ける
VERB_GLOSSES = {
    'كان': 'ある,いる,〜である', 'لَيْس': '〜でない', 'قال': '言う', 'ذَهَب': '行く', 'كَتَب': '書く', 'قَرَأ': '読む', 'جاء': '来る',
    'رَأَى': '見る', 'عَرَف': '知る', 'أَكَل': '食べる', 'شَرِب': '飲む', 'جَلَس': '座る', 'خَرَج': '出る', 'دَخَل': '入る',
    'سَأَل': '尋ねる', 'فَعَل': 'する', 'عَمِل': '働く,する', 'أَراد': '望む', 'اِسْتَطاع': '〜できる', 'وَجَد': '見つける',
    'أَخَذ': '取る', 'أَعْطَى': '与える', 'سَمِع': '聞く', 'فَهِم': '理解する', 'دَرَس': '学ぶ', 'عَلَّم': '教える',
    'تَعَلَّم': '学ぶ', 'أَحَبّ': '愛する',
}
GLOSSES = {
    'وَلَد': '少年,子ども', 'بَيْت': '家', 'كِتاب': '本', 'مَدْرَسَة': '学校', 'رَجُل': '男', 'اِمْرَأَة': '女',
    'طالِب': '学生', 'مُدَرِّس': '教師', 'مُعَلِّم': '先生', 'كَبِير': '大きい', 'صَغِير': '小さい', 'جَمِيل': '美しい',
    'جَدِيد': '新しい', 'قَدِيم': '古い', 'كُلّ': 'すべての,各々の', 'بَعْض': 'いくつかの', 'يَوْم': '日', 'وَقْت': '時', 'ماء': '水',
    'شَمْس': '太陽', 'قَمَر': '月', 'سَماء': '空,天', 'أَرْض': '大地,土地', 'اللّٰه': '神 (アッラー)', 'اللَّه': '神 (アッラー)',
    'إِلٰه': '神', 'سَيّارَة': '自動車', 'مَدِينَة': '町,都市', 'قَلَم': 'ペン', 'باب': '戸,門', 'طَعام': '食べ物', 'كَلْب': '犬',
    'قِطّ': '猫', 'أَب': '父', 'أُمّ': '母', 'أَخ': '兄弟', 'أُخْت': '姉妹', 'اِبْن': '息子', 'بِنْت': '娘', 'صَدِيق': '友人',
    'لُغَة': '言語', 'عَرَبِيّ': 'アラブの', 'جامِعَة': '大学', 'مَكْتَبَة': '図書館,書店', 'مَكْتَب': '事務所,机', 'سَنَة': '年',
    'عالَم': '世界', 'كَثِير': '多い', 'قَلِيل': '少ない', 'حَسَن': '良い', 'جَيِّد': '良い', 'طَوِيل': '長い', 'قَصِير': '短い',
    'عِلْم': '知識,学問', 'نَهْر': '川', 'بَحْر': '海', 'جَبَل': '山', 'شَجَرَة': '木', 'غابَة': '森', 'أَسَد': 'ライオン',
    'مَلِك': '王', 'كَلِمَة': '言葉,単語', 'اِسْم': '名前', 'رَسُول': '使者', 'نَبِيّ': '預言者', 'إِنْسان': '人間', 'ناس': '人々',
    'شَعْب': '民', 'مُجْتَهِد': '勤勉な,熱心な', 'جَوّ': '天気,空気', 'سُوق': '市場', 'وَزِير': '大臣',
    'شارِع': '通り', 'مَرِيض': '病気,病人', 'حَلّ': '解決,解決策', 'حُكُومَة': '政府', 'مِصْرِيّ': 'エジプトの', 'واسِع': '広い', 'غَد': '明日', 'أَمْس': '昨日', 'رِسالَة': '手紙', 'مَسْجِد': 'モスク', 'حُبّ': '愛', 'سَلام': '平和,平安', 'خُبْز': 'パン',
}
# 動詞の型 (I〜X) を見出し語の形から推定するための、語根の字を 1 2 3 にした子音の並び
VERB_PATTERNS = [('X', 'است123'), ('VIII', 'ا1ت23'), ('VII', 'ان123'), ('IX', 'ا123'), ('VI', 'ت1ا23'),
                 ('V', 'ت123'), ('IV', 'ا123'), ('III', '1ا23'), ('II', '123'), ('I', '123')]


@dataclass
class Reading:
    """1語の読み: 見出し語・品詞・切れ目が同じ解析をまとめたもの (格・状態の違うものは1つに)"""
    score: float
    analyses: list = field(default_factory=list)

    @property
    def main(self):
        return self.analyses[0]

    def feature(self, name):
        return self.main.get(name)

    @property
    def pos(self):
        return self.main['pos']

    @property
    def lex(self):
        return self.main['lex']


@functools.lru_cache(maxsize=1)
def _mle():
    from camel_tools.disambig.mle import MLEDisambiguator
    return MLEDisambiguator.pretrained(top=10000)


def available():
    try:
        _mle()
        return True
    except Exception:
        return False


def _letters(text):
    return [(c, marks) for c, marks in script._clusters(script.normalize(text) if False else text)]


def compatible(word, diac):
    """母音記号付きの入力 word と解析の形 diac が合うか (入力に書かれた記号は解析にもあること)"""
    a = [(script.normalize(c), m) for c, m in script._clusters(word)]
    b = [(script.normalize(c), m) for c, m in script._clusters(diac)]
    if [c for c, _ in a] != [c for c, _ in b]:
        return False
    for (_, ma), (_, mb) in zip(a, b):
        if ma - {script.SUKUN} - mb:
            return False
    return True


def _group_key(a):
    """読みをまとめるキー。接続詞 wa-/fa- の用法の違い (wa_conj / wa_sub / wa_part) は区別しない"""
    keys = ['lex', 'pos', 'prc3', 'prc1', 'prc0', 'enc0']
    if a['pos'] == 'verb':
        keys += ['asp', 'per', 'gen', 'num', 'vox']
    return tuple(a.get(k) for k in keys) + ((a.get('prc2') or '')[:2],)


@functools.lru_cache(maxsize=50000)
def readings(token):
    """語 → [Reading] (点数の高い順)。母音記号付きなら記号と合う解析だけ"""
    scored = _mle().disambiguate_word([script.bare(token)], 0).analyses if script.is_arabic(token) else []
    vocalized = script.has_diacritics(token)
    groups = {}
    for sa in scored:
        a = sa.analysis
        if vocalized and not compatible(token, a['diac']):
            continue
        # 綴りの違う解析 (قرأ を قَرَآ と読むなど、アリフの異体を同一視したもの) は下げる
        exact = script.bare(a['diac']).replace('ٱ', 'ا') == script.bare(token).replace('ٱ', 'ا')
        score = sa.score * (1 if exact else 0.3) * (0.05 if a['pos'] in RARE_POS else 1)
        if _lookup(VERB_GLOSSES if a['pos'] == 'verb' else GLOSSES, a['lex']):
            score *= 1.5  # 手で訳語を決めた基本語 (لَيْسَ を لَيِسَ より先に)
        key = _group_key(a)
        if key not in groups:
            groups[key] = Reading(score, [a])
        else:
            group = groups[key]
            group.analyses.append(a)
            group.score = max(group.score, score)
    return sorted(groups.values(), key=lambda r: -r.score)


def _cases(reading):
    out = []
    for a in reading.analyses:
        for case in CASES.get(a.get('cas'), ()):
            if case not in out:
                out.append(case)
    return out


def _cngs(reading):
    a = reading.main
    number = NUMBERS.get(a.get('num'), 'sg')
    genders = GENDERS.get(a.get('gen'), ('m', 'f'))
    out = [(case, number, g) for case in _cases(reading) for g in genders]
    if a.get('num') == 'p' and a.get('rat') in ('i', 'n') and a['pos'] in ('noun',):
        # 人以外の複数は女性単数として一致する (الكُتُبُ الجَدِيدَةُ「新しい本」)
        out += [(case, 'sg', 'f') for case in _cases(reading)]
    return out


def _gloss_pos(pos):
    return {'noun': ('noun',), 'noun_prop': ('name', 'noun'), 'adj': ('adj', 'noun'), 'adj_comp': ('adj',),
            'verb': ('verb',), 'adv': ('adv',), 'prep': ('preposition',), 'pron': ('pronoun',),
            'noun_num': ('num', 'noun'), 'adj_num': ('num', 'adj'), 'noun_quant': ('noun', 'adj')}.get(pos, ())


def lex_key(w):
    """見出し語の比べ方 (記号の順序をそろえ、スクーン・語末の短母音・長母音の前の補助の記号を無視する)"""
    w = unicodedata.normalize('NFC', w)
    w = w.replace('\u064e' + 'ا', 'ا').replace('\u0650' + 'ي', 'ي').replace('\u064f' + 'و', 'و')
    w = w.replace(script.SUKUN, '')
    while w and w[-1] in (script.FATHA, script.DAMMA, script.KASRA):
        w = w[:-1]
    return w.replace('ٰ', 'ا')


_KEYED = {}


def _lookup(table, lex):
    """手で作った表を、見出し語の比べ方 (lex_key) で引く"""
    keyed = _KEYED.get(id(table))
    if keyed is None:
        keyed = _KEYED[id(table)] = {lex_key(k): v for k, v in table.items()}
    return keyed.get(lex_key(lex))


def _same_vowels(a, b):
    return lex_key(a) == lex_key(b)


def entry(lex, pos, exact_only=False):
    """見出し語 (母音記号付き) と CAMeL Tools の品詞 → Wiktionary の項目 (dict) / None"""
    lemmas = dictionary.lemmas(lex)
    kinds = _gloss_pos(pos)
    found = [l for l in lemmas if l['pos'] in kinds] or ([] if kinds else lemmas)
    if not found:
        return None
    exact = [l for l in found if _same_vowels(l['word'], lex)]
    if exact_only and not exact:
        return None
    return max(exact or found, key=lambda l: (l['senses'], l['gloss_lang'] == 'ja'))


def _camel_gloss(a):
    """CAMeL Tools の語幹の訳語 (英語): 'industrious;diligent' → 'industrious,diligent'"""
    text = a.get('stemgloss') or ''
    glosses = []
    for g in text.split(';'):
        g = re.sub(r'\s+', ' ', g.replace('_', ' ')).strip()
        if g and g not in glosses:
            glosses.append(g)
    return ','.join(glosses[:3])


def gloss(a):
    """解析 → (訳語, 言語)。手で作った表、母音まで同じ Wiktionary の項目、CAMeL Tools の訳語 (英語)、
    綴りだけ同じ Wiktionary の項目の順"""
    lex, pos = a['lex'], a['pos']
    table = VERB_GLOSSES if pos == 'verb' else GLOSSES if pos != 'noun_prop' else {}
    ja = _lookup(table, lex)
    if ja:
        return ja, 'ja'
    found = entry(lex, pos, exact_only=True)
    if found and found['ja'].startswith('verbal noun of'):
        # 動名詞 (maṣdar)「〜すること」: 元の動詞の訳語から
        verb = re.search('[\u0621-\u064a\u064b-\u0652]+', found['ja'])
        verb_gloss = _lookup(VERB_GLOSSES, verb.group(0)) if verb else None
        if verb_gloss:
            return verb_gloss.split(',')[0] + 'こと', 'ja'
        found = None
    if found:
        return found['ja'], found['gloss_lang']
    camel = _camel_gloss(a)
    if camel:
        return camel, 'en'
    found = entry(lex, pos)
    if found:
        return found['ja'], found['gloss_lang']
    return lex, 'en'


def verb_form(lex, root):
    """動詞の見出し語と語根 → 型 ('I'〜'X')。Wiktionary にあればそれを使う"""
    found = entry(lex, 'verb')
    if found and found.get('form') and _same_vowels(found['word'], lex):
        return found['form']
    radicals = [c for c in (root or '').split('.') if c not in ('#', '')]
    if len(radicals) != 3:
        return found.get('form') if found else None
    bare = script.normalize(lex)
    skeleton = ''
    k = 0
    for c in bare:
        if k < 3 and c == script.normalize(radicals[k]):
            skeleton += str(k + 1)
            k += 1
        else:
            skeleton += c
    shadda = script.SHADDA in lex
    for name, pattern in VERB_PATTERNS:
        if skeleton == pattern:
            if name == 'II' and not shadda:
                continue
            if name == 'IX' and not shadda:
                continue
            if name == 'IV' and not lex.startswith('أ'):
                continue
            return name
    return found.get('form') if found else None


def _adjective(lex, ja):
    """CAMeL Tools が名詞とした語が形容詞か: 訳語が形容詞・形容動詞 (〜い・〜な) か、Wiktionary に形容詞としてだけある"""
    if any(g.endswith(('い', 'な')) for g in ja.split(',')[:1]):
        return True
    kinds = {l['pos'] for l in dictionary.lemmas(lex) if _same_vowels(l['word'], lex)}
    return 'adj' in kinds and 'noun' not in kinds


def is_function_word(reading):
    """前置詞・機能語の表にある読みか"""
    a = reading.main
    if any(a.get(k) not in (None, '0', 'na') for k in ('prc1', 'prc2', 'enc0')):
        return False
    return bool(_lookup(PREPOSITIONS, a['lex']) or _lookup(FUNCTION_WORDS, a['diac'])
                or a['pos'] not in ('noun', 'verb', 'adj') and _lookup(FUNCTION_WORDS, a['lex']))


WEAK = 'وي' + 'ءأإئؤ'


def weak_root(root, lex, pos):
    """CAMeL Tools の語根の # (弱い字 w / y / ʾ) を埋める: Wiktionary の語根、無ければ見出し語の字から
    (وَلَد の #.ل.د → و.ل.د、سُوق の س.#.ق → س.و.ق)。空洞動詞 (كان) のように見出し語に無い字は # のまま"""
    radicals = root.split('.')
    found = entry(lex, pos)
    if found and found.get('root') and len(found['root']) == len(radicals):
        return '.'.join(found['root'])
    pattern = ''.join('([%s])' % WEAK if r == '#' else '(%s)' % re.escape(r) for r in radicals)
    m = re.search(pattern.replace(')(', ').*?('), script.bare(lex))
    if not m:
        return root
    return '.'.join('ء' if g in 'أإئؤ' else g for g in m.groups())


def _pronoun_item(code, surface):
    """人称接尾辞 (3ms_poss, 1s_dobj, 3mp_pron) → 項目"""
    pgn, kind = code.split('_')
    person = int(pgn[0])
    number = NUMBERS.get(pgn[-1], 'sg')
    gender = pgn[1] if len(pgn) == 3 else None
    cases = {'poss': ('Gen',), 'dobj': ('Acc',), 'pron': ('Gen',)}.get(kind, ('Gen', 'Acc'))
    genders = (gender,) if gender in ('m', 'f') else ('m', 'f')
    return {'surface': surface, 'pos': 'pronoun', 'base': surface, 'ja': PERSONAL.get(pgn, '彼'), 'gloss_lang': 'ja',
            'suffix': True, 'suffix_kind': kind, 'person': person, 'diac': surface,
            '_': [(c, number, g) for c in cases for g in genders]}


def split(a):
    """解析 → (接頭辞の [(符号, 表記)], 本体の表記, 人称接尾辞の (符号, 表記) / None)。表記は d3tok の母音記号付きの形"""
    pieces = [p for p in a.get('d3tok', a['diac']).split('_') if p]
    pre = [p.rstrip('+') for p in pieces if p.endswith('+') and len(p) > 1]
    post = [p.lstrip('+') for p in pieces if p.startswith('+') and len(p) > 1]
    stem = [p for p in pieces if not p.endswith('+') and not p.startswith('+')]
    codes = [a.get(k) for k in ('prc3', 'prc2', 'prc1', 'prc0') if a.get(k) not in (None, '0', 'na')]
    out = []
    for code, surface in zip(codes, pre):
        out.append((code, surface))
    # 符号の無い接頭の切れ目 (لِأَنَّ「なぜなら」の لِ) は本体に付けたままにする
    stem_surface = ''.join(pre[len(codes):] + stem)
    # 定冠詞 al- は本体に付けたままにする (UD の語の切り方と同じ)。動詞に含める接頭辞もここで本体に戻す
    for code, surface in reversed(out[:]):
        if code == 'Al_det' or code in VERBAL_PROCLITICS:
            stem_surface = surface + stem_surface
            out.remove((code, surface))
    enc = a.get('enc0')
    suffix = (enc, post[0]) if enc not in (None, '0', 'na') and post else None
    return out, stem_surface, suffix


def stem_item(a, reading, surface):
    """本体の項目"""
    lex, pos = a['lex'], a['pos']
    ja, gloss_lang = gloss(a)
    root = a.get('root') if a.get('root') not in ('NTWS', None) else None
    if root and '#' in root:
        root = weak_root(root, lex, pos)
    item = {'surface': surface, 'diac': surface, 'lex': lex, 'root': root, 'camel_pos': pos,
            'base': '%s %s' % (script.translit(lex), script.isolate(lex)), 'ja': ja, 'gloss_lang': gloss_lang,
            'xlit': script.translit(surface)}
    if a.get('prc0') == 'Al_det' or a.get('stt') == 'd' or pos == 'noun_prop':
        item['definite'] = True
    states = {a2.get('stt') for a2 in reading.analyses}
    item['states'] = sorted(s for s in states if s)
    preposition = _lookup(PREPOSITIONS, lex)
    if preposition or pos == 'prep':
        return dict(item, pos='preposition', dominates='Gen', ja=preposition or ja,
                    gloss_lang='ja' if preposition else gloss_lang)
    by_form = _lookup(FUNCTION_WORDS, surface)
    function = by_form or _lookup(FUNCTION_WORDS, lex)
    # 見出し語で引けた語は名詞・動詞の読みなら使わない。語形で引けた語 (غَدًا「明日」) は品詞によらず
    if function and (by_form and not a.get('enc0') not in (None, '0', 'na')
                     or pos not in ('noun', 'verb', 'verb_pseudo')):
        kind, ja = function
        if pos == 'part_neg' or kind == 'adv':
            item['particle'] = lex
        inna_key = script.normalize(lex).replace('ٰ', '')
        if inna_key in INNA and (script.SHADDA in lex or a.get('enc0') not in (None, '0', 'na')):
            item['inna'] = True  # أَنَّ, لٰكِنَّ, لِأَنَّ (後ろの名詞・人称接尾辞が主語)
        return dict(item, pos=kind, ja=ja, gloss_lang='ja')
    if pos == 'pron' and _lookup(PRONOUNS, lex):
        person, number, gender = _lookup(PRONOUNS, lex)
        genders = (gender,) if gender else ('m', 'f')
        key = person + (gender if person != '1' and number != 'd' else '') + number
        return dict(item, pos='pronoun', ja=PERSONAL.get(key, ja), gloss_lang='ja', person=int(person),
                    _=[(c, NUMBERS[number], g) for c in ('Nom', 'Acc', 'Gen') for g in genders])
    if pos == 'pron_dem':
        return dict(item, pos='adj', desc='指示代名詞', ja=_lookup(DEMONSTRATIVES, lex) or 'この', gloss_lang='ja',
                    demonstrative=True, _=_cngs(reading) or [(c, NUMBERS.get(a.get('num'), 'sg'), g)
                                                             for c in ('Nom', 'Acc', 'Gen') for g in ('m', 'f')])
    if pos == 'pron_rel':
        return dict(item, pos='conj', ja=RELATIVE, gloss_lang='ja', relative=True)
    if pos == 'noun' and _adjective(lex, ja):
        pos = 'adj'  # CAMeL Tools では名詞の形容詞 (جَمِيل「美しい」)
    if pos in ('noun', 'noun_prop', 'noun_num', 'noun_quant', 'pron', 'pron_interrog', 'pron_exclam'):
        item.update(pos='noun' if pos != 'pron_interrog' else 'pronoun', _=_cngs(reading))
        if pos == 'noun_prop':
            item['proper'] = True
        if not item['_']:
            item['_'] = [(c, 'sg', g) for c in ('Nom', 'Acc', 'Gen') for g in ('m', 'f')]
        return item
    if pos in ('adj', 'adj_comp', 'adj_num'):
        item.update(pos='adj', _=_cngs(reading) or [(c, 'sg', g) for c in ('Nom', 'Acc', 'Gen') for g in ('m', 'f')])
        return item
    if pos == 'verb_pseudo':
        # inna とその姉妹 (إِنَّ أَنَّ لٰكِنَّ كَأَنَّ لَيْتَ لَعَلَّ): 後ろの名詞 (対格) が文の主語
        ja = INNA.get(script.bare(lex).replace('أ', 'ا').replace('إ', 'ا'), ja)
        return dict(item, pos='conj', ja=ja,
                    gloss_lang='ja', inna=True, particle=lex)
    if pos == 'verb':
        item.update(pos='verb', pres1sg=lex, voice='passive' if a.get('vox') == 'p' else 'active',
                    form=verb_form(lex, a.get('root')))
        if script.bare(lex) in ('كان',):
            item['existential'] = True
        asp = a.get('asp')
        if asp == 'c':
            item.update(mood='imperative', tense='present')
        else:
            tense = 'perfect' if asp == 'p' else 'future' if a.get('prc1') == 'sa_fut' else 'present'
            item.update(mood='indicative', tense=tense, aspect=asp)
        if a.get('mod') in ('s', 'j'):
            item['verb_mood'] = {'s': 'subjunctive', 'j': 'jussive'}[a['mod']]
        person = a.get('per')
        item.update(person=int(person) if person and person.isdigit() else 3,
                    number=NUMBERS.get(a.get('num'), 'sg'),
                    gender=a.get('gen') if a.get('gen') in ('m', 'f') else None)
        return item
    if pos.startswith('part') or pos in ('adv', 'adv_interrog', 'adv_rel', 'interj', 'conj', 'conj_sub'):
        kind = 'conj' if pos in ('conj', 'conj_sub') else 'adv'
        if pos == 'part_neg':
            item['particle'] = lex
        return dict(item, pos=kind)
    return dict(item, pos='adv')


def segments(reading):
    """読み → [(表記, 項目)] (接頭の接続詞・前置詞、本体、人称接尾辞)"""
    a = reading.main
    pre, stem, suffix = split(a)
    out = []
    for code, surface in pre:
        if code in PROCLITICS:
            kind, base, ja = PROCLITICS[code]
            item = {'surface': surface, 'diac': surface, 'pos': kind, 'base': base, 'ja': ja, 'gloss_lang': 'ja',
                    'proclitic': code, 'xlit': script.translit(surface)}
            if kind == 'preposition':
                item['dominates'] = 'Gen'
            if code in ('mA_neg', 'lA_neg'):
                item['particle'] = base
            out.append((surface, item))
    out.append((stem, stem_item(a, reading, stem)))
    if suffix:
        code, surface = suffix
        if code.split('_')[0][0].isdigit():
            out.append((surface, _pronoun_item(code, surface)))
    for _, item in out:
        item['compact'] = True
    return out
