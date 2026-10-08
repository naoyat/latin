#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語の語形の解析 (規則による)。Wiktionary の見出し語・動詞の現在語幹と過去語幹 (persian/dictionary.py) を使う
#
#   動詞:  (否定 na- / ne-) + (mi- 継続・現在 / be- 接続法・命令) + 語幹 + 人称語尾
#          می‌روم mi-rav-am「私は行く」、نرفتند na-raft-and「彼らは行かなかった」、بنویس be-nevis「書け」、
#          رفته‌ام rafte-am「私は行った (現在完了)」
#   名詞類: 語 + (複数 -hâ / -ân) + (不定 -i | 書かれたエザーフェ -ye | 人称の接語 -am, -at, -aš… | 繋辞の接語 -am, -ast…)
#          کتاب‌هایم ketâbhâ-yam「私の本 (複数)」、دانشجوی dânešju-ye「〜の学生」
#
# 1語の解析の候補を [(切れ目の表記, 項目)] のリスト (点数付き) で返し、文の解析 (persian/analyzer.py) が選ぶ。
# 格の無い言語なので、名詞類は主格・対格・属格のどれにも読めるものにし、文の解析で絞る (را の前は対格、
# エザーフェの後ろの名詞は属格「〜の」)
#
import functools
from dataclasses import dataclass, field

from . import dictionary, script

GENDER = 'c'  # 性の無い言語 (共通の解析器の一致の判定のため、すべて同じ性にする)
CASES = ('Nom', 'Acc', 'Gen')
PERSONAL = {(1, 'sg'): '私', (2, 'sg'): 'あなた', (3, 'sg'): '彼', (1, 'pl'): '私たち', (2, 'pl'): 'あなたたち',
            (3, 'pl'): '彼ら'}

# 人称語尾: (書かれた形, 転写, 人称, 数)
PRESENT_ENDINGS = [('م', 'am', 1, 'sg'), ('ی', 'i', 2, 'sg'), ('د', 'ad', 3, 'sg'), ('یم', 'im', 1, 'pl'),
                   ('ید', 'id', 2, 'pl'), ('ند', 'and', 3, 'pl')]
PAST_ENDINGS = [('م', 'am', 1, 'sg'), ('ی', 'i', 2, 'sg'), ('', '', 3, 'sg'), ('یم', 'im', 1, 'pl'),
                ('ید', 'id', 2, 'pl'), ('ند', 'and', 3, 'pl')]
# 母音で終わる現在語幹の後ろの語尾 (می‌گوید mi-gu-yad)
GLIDE_ENDINGS = [('ی' + w, 'y' + r, p, n) for w, r, p, n in PRESENT_ENDINGS if w]
# 現在完了の繋辞の接語 (رفته‌ام rafte-am)
PERFECT_ENDINGS = [('ام', 'am', 1, 'sg'), ('ای', 'i', 2, 'sg'), ('است', 'ast', 3, 'sg'), ('', '', 3, 'sg'),
                   ('ایم', 'im', 1, 'pl'), ('اید', 'id', 2, 'pl'), ('اند', 'and', 3, 'pl')]
# 動詞の接頭辞: (書かれた形, 転写, 否定, 種類)
VERB_PREFIXES = [('نمی', 'nemi', True, 'mi'), ('می', 'mi', False, 'mi'), ('ن', 'na', True, ''),
                 ('ب', 'be', False, 'be'), ('', '', False, '')]
# 動詞の前つづり (برگشتن bar-gaštan)。mi- はその後ろに入る (برمی‌گردد bar-mi-gardad)
PREVERBS = [('بر', 'bar'), ('در', 'dar'), ('باز', 'bâz'), ('فرو', 'foru'), ('فرا', 'farâ'), ('وا', 'vâ')]

# 名詞類の接尾辞
PLURALS = [('ها', 'hâ'), ('ان', 'ân'), ('یان', 'yân'), ('گان', 'gân'), ('ات', 'ât')]
POSSESSIVE = [('م', 'am', 1, 'sg'), ('ت', 'at', 2, 'sg'), ('ش', 'aš', 3, 'sg'), ('مان', 'emân', 1, 'pl'),
              ('تان', 'etân', 2, 'pl'), ('شان', 'ešân', 3, 'pl')]
COPULA_CLITICS = [('م', 'am', 1, 'sg'), ('ی', 'i', 2, 'sg'), ('ست', 'st', 3, 'sg'), ('است', 'ast', 3, 'sg'),
                  ('یم', 'im', 1, 'pl'), ('ید', 'id', 2, 'pl'), ('ند', 'and', 3, 'pl')]
VOWEL_FINAL = 'اوه'

# 機能語: 書かれた形 → (品詞, 転写, 訳, 追加の属性)
FUNCTION_WORDS = {
    'از': ('preposition', 'az', '〜から', {}), 'به': ('preposition', 'be', '〜に,〜へ', {}),
    'در': ('preposition', 'dar', '〜で,〜の中で', {}), 'با': ('preposition', 'bâ', '〜と,〜で', {}),
    'برای': ('preposition', 'barâye', '〜のために', {}), 'بی': ('preposition', 'bi', '〜なしに', {}),
    'بر': ('preposition', 'bar', '〜の上に', {}), 'جز': ('preposition', 'joz', '〜以外', {}),
    'درباره': ('preposition', 'darbâre-ye', '〜について', {}), 'درباره‌ی': ('preposition', 'darbâre-ye', '〜について', {}),
    'مثل': ('preposition', 'mesl-e', '〜のように', {}), 'روی': ('preposition', 'ru-ye', '〜の上に', {}),
    'زیر': ('preposition', 'zir-e', '〜の下に', {}), 'پیش': ('preposition', 'piš-e', '〜のところに', {}),
    'نزد': ('preposition', 'nazd-e', '〜のもとに', {}), 'کنار': ('preposition', 'kenâr-e', '〜のそばに', {}),
    'پشت': ('preposition', 'pošt-e', '〜の後ろに', {}), 'بین': ('preposition', 'beyn-e', '〜の間に', {}),
    'میان': ('preposition', 'miyân-e', '〜の中に', {}), 'داخل': ('preposition', 'dâxel-e', '〜の中に', {}),
    'توی': ('preposition', 'tu-ye', '〜の中に', {}), 'سوی': ('preposition', 'su-ye', '〜の方へ', {}),
    'طرف': ('preposition', 'taraf-e', '〜の方へ', {}), 'همراه': ('preposition', 'hamrâh-e', '〜とともに', {}),
    'را': ('postposition', 'râ', '※目的語の標識 râ: 前の名詞句が定まった目的語', {}),
    'و': ('conj', 'va', 'そして,〜と', {}), 'یا': ('conj', 'yâ', 'または', {}), 'اما': ('conj', 'ammâ', 'しかし', {}),
    'ولی': ('conj', 'vali', 'しかし', {}), 'که': ('conj', 'ke', '〜ということ,〜するところの', {}),
    'اگر': ('conj', 'agar', 'もし', {}), 'چون': ('conj', 'čon', '〜なので', {}), 'زیرا': ('conj', 'zirâ', 'なぜなら', {}),
    'تا': ('conj', 'tâ', '〜まで,〜するように', {}), 'وقتی': ('conj', 'vaqti', '〜するとき', {}),
    'هم': ('adv', 'ham', '〜も', {}), 'نیز': ('adv', 'niz', '〜もまた', {}), 'نه': ('adv', 'na', 'いいえ,〜ない', {}),
    'بله': ('adv', 'bale', 'はい', {}), 'آری': ('adv', 'âri', 'はい', {}), 'خیلی': ('adv', 'xeyli', 'とても', {}),
    'هنوز': ('adv', 'hanuz', 'まだ', {}), 'همیشه': ('adv', 'hamiše', 'いつも', {}), 'حالا': ('adv', 'hâlâ', '今', {}),
    'اکنون': ('adv', 'aknun', '今', {}), 'امروز': ('adv', 'emruz', '今日', {}), 'دیروز': ('adv', 'diruz', '昨日', {}),
    'فردا': ('adv', 'fardâ', '明日', {}), 'اینجا': ('adv', 'injâ', 'ここに', {}), 'آنجا': ('adv', 'ânjâ', 'そこに', {}),
    'کجا': ('adv', 'kojâ', 'どこに', {}), 'چرا': ('adv', 'čerâ', 'なぜ', {}), 'چطور': ('adv', 'četor', 'どのように', {}),
    'آیا': ('adv', 'âyâ', '〜か (疑問)', {}), 'فقط': ('adv', 'faqat', '〜だけ', {}), 'باید': ('adv', 'bâyad', '〜しなければならない', {}),
}
PRONOUNS = {'من': ('man', 1, 'sg'), 'تو': ('to', 2, 'sg'), 'او': ('u', 3, 'sg'), 'وی': ('vey', 3, 'sg'),
            'ما': ('mâ', 1, 'pl'), 'شما': ('šomâ', 2, 'pl'), 'آنها': ('ânhâ', 3, 'pl'), 'آن‌ها': ('ânhâ', 3, 'pl'),
            'ایشان': ('išân', 3, 'pl'), 'خود': ('xod', 3, 'sg')}
PRONOUN_GLOSSES = {'وی': '彼', 'خود': '自分', 'شما': 'あなた(たち)'}
DEMONSTRATIVES = {'این': ('in', 'この', 'これ'), 'آن': ('ân', 'その', 'それ'), 'اینها': ('inhâ', 'これらの', 'これら'),
                  'همین': ('hamin', 'まさにこの', 'まさにこれ'), 'همان': ('hamân', 'まさにその', 'まさにそれ'),
                  'هر': ('har', 'それぞれの', 'それぞれ'), 'چه': ('če', '何の', '何'), 'کدام': ('kodâm', 'どの', 'どれ'),
                  'همه': ('hame', 'すべての', 'すべて'), 'چنین': ('čenin', 'このような', 'このようなもの'),
                  'چنان': ('čenân', 'そのような', 'そのようなもの'), 'هیچ': ('hič', 'どんな…も', '何も')}
# 辞書に形容詞として無い (または別の品詞だけの) よく使う形容詞: 書かれた形 → (転写, 訳)
ADJECTIVES = {'دیگر': ('digar', '他の'), 'قرمز': ('qermez', '赤い'), 'سرخ': ('sorx', '赤い'), 'زرد': ('zard', '黄色い'),
              'سبز': ('sabz', '緑の'), 'آبی': ('âbi', '青い'), 'سیاه': ('siyâh', '黒い'), 'سفید': ('sefid', '白い'),
              'بسیار': ('besyâr', '多くの'), 'مهم': ('mohem', '重要な'), 'اصلی': ('asli', '主な'),
              'مختلف': ('moxtalef', 'さまざまな'), 'زیاد': ('ziyâd', '多い'), 'خاص': ('xâs', '特別な'),
              'بعدی': ('ba\'di', '次の'), 'قبلی': ('qabli', '前の'), 'جدید': ('jadid', '新しい')}
# 繋辞「〜である」: 書かれた形 → (転写, 人称, 数, 否定)
COPULA_FORMS = {'است': ('ast', 3, 'sg', False), 'هست': ('hast', 3, 'sg', False), 'هستم': ('hastam', 1, 'sg', False),
                'هستی': ('hasti', 2, 'sg', False), 'هستیم': ('hastim', 1, 'pl', False),
                'هستید': ('hastid', 2, 'pl', False), 'هستند': ('hastand', 3, 'pl', False),
                'نیست': ('nist', 3, 'sg', True), 'نیستم': ('nistam', 1, 'sg', True), 'نیستی': ('nisti', 2, 'sg', True),
                'نیستیم': ('nistim', 1, 'pl', True), 'نیستید': ('nistid', 2, 'pl', True),
                'نیستند': ('nistand', 3, 'pl', True)}
COPULA = 'بودن'
# 訳語を手で決める見出し語 (Wiktionary の訳語が英語・かなのもの)
GLOSSES = {'بودن': 'ある,いる,〜である', 'دانستن': '知る', 'خسته': '疲れた', 'میز': '机,テーブル', 'باغ': '庭,庭園', 'خریدن': '買う', 'فروختن': '売る', 'رسیدن': '着く',
           'شنیدن': '聞く', 'پرسیدن': '尋ねる', 'فهمیدن': '理解する', 'ساختن': '作る', 'آوردن': '持ってくる',
           'بردن': '持っていく', 'گذاشتن': '置く', 'خوابیدن': '眠る', 'دویدن': '走る', 'نشان دادن': '示す', 'شدن': 'なる,〜される', 'کردن': 'する', 'خوب': '良い', 'بزرگ': '大きい',
           'کوچک': '小さい', 'دانشجو': '学生', 'دانش‌آموز': '生徒', 'معلم': '先生', 'مدرسه': '学校',
           'دانشگاه': '大学', 'زیبا': '美しい', 'خواستن': '望む,〜したい', 'توانستن': '〜できる', 'داشتن': '持つ',
           'نان': 'パン', 'آب': '水', 'شهر': '町,都市', 'کشور': '国', 'زبان': '言語,舌', 'فارسی': 'ペルシア語',
           'ایران': 'イラン', 'تهران': 'テヘラン', 'دوست': '友人', 'پدر': '父', 'مادر': '母', 'برادر': '兄弟',
           'خواهر': '姉妹', 'پسر': '息子,少年', 'دختر': '娘,少女', 'مرد': '男', 'زن': '女,妻', 'روز': '日', 'شب': '夜',
           'سال': '年', 'کار': '仕事', 'نامه': '手紙', 'خوردن': '食べる,飲む', 'نوشیدن': '飲む', 'آمدن': '来る',
           'رفتن': '行く', 'دیدن': '見る', 'گفتن': '言う', 'خواندن': '読む,歌う', 'نوشتن': '書く', 'دادن': '与える',
           'گرفتن': 'つかむ,受け取る', 'زدن': '打つ', 'ماندن': 'とどまる', 'نشستن': '座る', 'زندگی': '生活,人生',
           'جدید': '新しい', 'قدیمی': '古い', 'گرم': '暖かい', 'سرد': '寒い,冷たい', 'زیاد': '多い', 'کم': '少ない',
           'سیب': 'りんご', 'خانه': '家', 'کتاب': '本', 'باغ': '庭', 'گل': '花', 'درخت': '木', 'شیر': 'ライオン,牛乳'}


@dataclass
class Analysis:
    """1語の解析の候補: 切れ目 [(表記, 項目)] と点数"""
    score: float
    segments: list = field(default_factory=list)
    kind: str = ''

    @property
    def main(self):
        return next(item for _, item in self.segments if item.get('main'))


def available():
    return dictionary.available()


def _roman(entry):
    return entry.get('roman') or script.rough_translit(entry.get('word', ''))


def _gloss(entry):
    key = script.key(entry['word'])
    for word, ja in GLOSSES.items():
        if script.key(word) == key:
            return ja, 'ja'
    return entry['ja'], entry['gloss_lang']


def _nominal_cngs(number):
    return [(case, number, GENDER) for case in CASES]


def _adj_cngs():
    return [(case, number, GENDER) for case in CASES for number in ('sg', 'pl')]


def _item(surface, **kw):
    item = {'surface': surface, 'compact': True}
    item.update(kw)
    return item


# ----------------------------------------------------------------------
# 動詞

def _stem_variants(stem):
    """接頭辞の後ろの語幹の書き方: آ で始まる語幹は بیا / نیامد のように ی + ا (آمد → یامد)"""
    stem = script.key(stem)
    out = [stem]
    if stem.startswith('آ'):
        out.append('یا' + stem[1:])
        out.append('ا' + stem[1:])
    return out


@functools.lru_cache(maxsize=20000)
def _verbs_by_stem(stem, kind):
    """語幹 → 動詞の項目 (複合動詞 کار کردن は除く。名詞と軽動詞は文の解析でまとめる)"""
    return [e for e in dictionary.verbs_by_stem(stem, kind) if ' ' not in e['word']]


def _stem_roman(entry, stem, kind):
    if kind == 'past':
        past = entry.get('past')
        if past and past[1]:
            return past[1]
        roman = _roman(entry)
        return roman[:-2] if roman.endswith('an') else script.rough_translit(stem)
    for s, r in entry.get('present') or []:
        if script.key(s) == script.key(stem) and r:
            return r
    return script.rough_translit(stem)


def _verb_item(surface, entry, kind, stem_roman, prefix_roman, ending, negative, prefix_kind, tense_kind):
    """動詞の項目。tense_kind: 'present' / 'past' / 'perfect' / 'imperative' / 'participle'"""
    ja, gloss_lang = _gloss(entry)
    _, ending_roman, person, number = ending
    roman = prefix_roman + stem_roman + ending_roman
    item = _item(surface, pos='verb', pres1sg=script.normalize(entry['word']), lemma=script.normalize(entry['word']),
                 base='%s %s' % (_roman(entry), script.isolate(entry['word'])), ja=ja, gloss_lang=gloss_lang,
                 roman=roman, voice='active', person=person, number=number, main=True, stem_kind=kind,
                 stem=stem_roman, prefix=prefix_kind)
    if negative:
        item['negative'] = True
    if tense_kind == 'imperative':
        item.update(mood='imperative', tense='present', form='命令形')
    elif tense_kind == 'perfect':
        item.update(mood='indicative', tense='perfect', form='現在完了 (過去分詞 + 繋辞)')
    elif tense_kind == 'past':
        if prefix_kind == 'mi':
            item.update(mood='indicative', tense='imperfect', form='過去進行・習慣 (mi- + 過去語幹)')
        else:
            item.update(mood='indicative', tense='perfect', form='単純過去 (過去語幹)')
    else:
        if prefix_kind == 'be':
            item.update(mood='indicative', tense='present', form='接続法現在 (be- + 現在語幹)', subjunctive=True)
        elif prefix_kind == 'mi':
            item.update(mood='indicative', tense='present', form='現在 (mi- + 現在語幹)')
        else:
            item.update(mood='indicative', tense='present', form='現在 (現在語幹)')
    if script.key(entry['word']) == script.key(COPULA):
        item['existential'] = True
    return item


def verb_analyses(token):
    """動詞として読む候補"""
    word = script.key(token)
    out = []
    for preverb, preverb_roman in [('', '')] + PREVERBS:
        if not word.startswith(preverb):
            continue
        rest0 = word[len(preverb):]
        for prefix, prefix_roman, negative, prefix_kind in VERB_PREFIXES:
            if not rest0.startswith(prefix):
                continue
            rest = rest0[len(prefix):]
            if not rest:
                continue
            for k in range(len(rest), 0, -1):
                stem_written, tail = rest[:k], rest[k:]
                for kind in ('present', 'past'):
                    for stem in {stem_written, 'آ' + stem_written[2:] if stem_written.startswith('یا') else None,
                                 'آ' + stem_written[1:] if stem_written.startswith('ا') and prefix else None} - {None}:
                        entries = _verbs_by_stem(preverb + stem, kind) if preverb else _verbs_by_stem(stem, kind)
                        if not entries:
                            continue
                        out += _with_endings(token, entries, preverb + stem, kind, tail, preverb_roman,
                                             prefix, prefix_roman, negative, prefix_kind)
    return out


def _verb_priority(entry, stem, kind):
    """同じ語幹の動詞のうちどれを取るか: 手で訳語を決めた基本の動詞 (کن は کردن「する」で کندن「掘る」でない)、
    過去語幹 + ن が不定形のもの、語義の多いもの"""
    key = script.key(entry['word'])
    return (any(script.key(w) == key for w in GLOSSES), kind == 'past' and key == script.key(stem) + 'ن',
            entry['senses'] or 0)


def _with_endings(token, entries, stem, kind, tail, preverb_roman, prefix, prefix_roman, negative, prefix_kind):
    out = []
    entry = max(entries, key=lambda e: _verb_priority(e, stem, kind))
    stem_roman = _stem_roman(entry, stem, kind)
    if preverb_roman and stem_roman.startswith(preverb_roman):
        stem_roman = stem_roman[len(preverb_roman):]
    if prefix_kind == 'be' and stem_roman.startswith('â'):
        prefix_roman = 'biy'
    elif negative and prefix_kind == '' and stem_roman.startswith('â'):
        prefix_roman = 'nay'
    full_prefix = preverb_roman + prefix_roman
    if kind == 'present':
        # 母音で終わる語幹 (â, gu) は語尾の前に y を入れる (می‌آید mi-â-yad, می‌آیید mi-â-yid)
        endings = GLIDE_ENDINGS if stem_roman[-1:] in 'aeiouâ' else PRESENT_ENDINGS
        for ending in endings:
            if tail == ending[0]:
                if prefix_kind == '' and not negative and script.key(entry['word']) not in BARE_PRESENT:
                    score = 0.3  # mi- / be- の無い現在形は داشتن・خواستن など一部の動詞だけ
                else:
                    score = 1.0
                out.append(Analysis(score, [(token, _verb_item(token, entry, kind, stem_roman, full_prefix, ending,
                                                              negative, prefix_kind, 'present'))], 'verb'))
        if tail in ('', 'ید') and prefix_kind in ('be', '') and (prefix_kind == 'be' or negative):
            ending = ('', '', 2, 'sg') if tail == '' else ('ید', 'id', 2, 'pl')
            out.append(Analysis(0.9, [(token, _verb_item(token, entry, kind, stem_roman, full_prefix, ending,
                                                         negative, prefix_kind, 'imperative'))], 'verb'))
    else:
        for ending in PAST_ENDINGS:
            if tail == ending[0] and prefix_kind != 'be':
                score = 1.0 if prefix_kind or negative or ending[0] else 0.9
                out.append(Analysis(score, [(token, _verb_item(token, entry, kind, stem_roman, full_prefix, ending,
                                                              negative, prefix_kind, 'past'))], 'verb'))
        for written, roman, person, number in PERFECT_ENDINGS:
            if tail == 'ه' + written and prefix_kind in ('', ) and (written or True):
                ending = (written, ('e-' + roman) if roman else 'e', person, number)
                tense = 'perfect' if written else 'participle'
                item = _verb_item(token, entry, kind, stem_roman, full_prefix, ending, negative, prefix_kind,
                                  'perfect')
                if not written:
                    # 過去分詞 (رفته「行った」)。完了・受動 (نوشته شد) の組み立てに使う
                    item.update(participle=True, form='過去分詞 (過去語幹 + -e)')
                score = 0.9 if written else 0.6
                if written and any(e['pos'] in ('adj', 'noun') for e in dictionary.lemmas(stem + 'ه')):
                    score -= 0.4  # خسته‌ام は「私は疲れている」(形容詞 + 繋辞) を先に
                out.append(Analysis(score, [(token, item)], 'verb'))
    return out


# 接頭辞の無い現在形を使う動詞 (دارم「持っている」、خواهم (未来の助動詞))
BARE_PRESENT = {script.key(w) for w in ('داشتن', 'خواستن', 'بودن', 'توانستن')}


# ----------------------------------------------------------------------
# 名詞類

def _nominal_entries(base):
    found = [e for e in dictionary.lemmas(base) if e['pos'] in ('noun', 'name', 'adj', 'pronoun', 'num', 'det')]
    if found:
        return found
    # 不規則な複数形 (کتب kotob) など
    out = []
    for lemma, tag in dictionary.forms(base):
        for e in dictionary.lemmas(lemma):
            if e['pos'] in ('noun', 'adj'):
                out.append(dict(e, form_tag=tag, form_word=base))
    return out


def _suffix_chains(base_final):
    """名詞類の後ろに付く接尾辞の並び [(書かれた形, [(種類, 転写, 書かれた形, 人称, 数)])]"""
    chains = [('', [])]
    plurals = [('', None)] + [(w, (('plural', r, w, None, 'pl'))) for w, r in PLURALS]
    for pw, plural in plurals:
        final = (pw or base_final)[-1:] if (pw or base_final) else ''
        vowel = final in 'او' or (pw == '' and final == 'ه')
        head = [plural] if plural else []
        if pw:
            chains.append((pw, head))
        # 不定の -i
        for w, r in ([('ی', 'i')] if not vowel else [('یی', 'yi'), ('ای', "'i")]):
            chains.append((pw + w, head + [('indefinite', r, w, None, None)]))
        # 書かれたエザーフェ (母音で終わる語: دانشجوی dânešju-ye、خانه‌ی xâne-ye)
        if vowel or pw == 'ها':
            chains.append((pw + 'ی', head + [('ezafe', '-ye', 'ی', None, None)]))
        # 人称の接語 (所有「私の」)
        for w, r, person, number in POSSESSIVE:
            if vowel and final in 'او':
                w2, r2 = 'ی' + w, 'y' + (r if r[0] == 'a' else r[1:])
            elif vowel:
                w2, r2 = ('ا' + w if r[0] == 'a' else w), ("'" + r if r[0] == 'a' else r)
            else:
                w2, r2 = w, r
            chains.append((pw + w2, head + [('possessive', r2, w2, person, number)]))
        # 繋辞の接語 (خوبم xub-am「私は良い」)
        for w, r, person, number in COPULA_CLITICS:
            if vowel and w not in ('ست', 'است'):
                w2, r2 = 'ا' + w if final == 'ه' else 'ی' + w, ("'" if final == 'ه' else 'y') + r
            else:
                w2, r2 = w, r
            chains.append((pw + w2, head + [('copula', r2, w2, person, number)]))
    return chains


def relational_adjective(token):
    """関係形容詞 (名詞 + -i「〜の」: جهانی jahâni「世界の」、ملی melli「国の」) を作る。辞書に無くてもよい"""
    word = script.key(token)
    if not word.endswith('ی') or len(word) < 3:
        return None
    if any(e['pos'] in ('noun', 'adj') and e['gloss_lang'] == 'ja' for e in dictionary.lemmas(word)) or \
            any(script.key(w) == word for w in GLOSSES):
        return None  # 語全体に日本語の訳語がある (فارسی「ペルシア語」)
    base = word[:-1]
    if base.endswith('ی'):  # 母音で終わる語 + -yi (آسیایی)
        base = base[:-1]
    nouns = [e for e in dictionary.lemmas(base) if e['pos'] in ('noun', 'name')]
    if not nouns:
        return None
    entry = max(nouns, key=lambda e: e['senses'] or 0)
    ja, gloss_lang = _gloss(entry)
    roman = _roman(entry)
    roman = roman + ('yi' if roman[-1:] in 'aâeiuo' else 'i')
    gloss = ja.split(',')[0] + 'の' if gloss_lang == 'ja' else 'of ' + ja.split(',')[0]
    item = _item(word, pos='adj', base='%s %s' % (roman, script.isolate(word)), ja=gloss, gloss_lang=gloss_lang,
                 roman=roman, lemma=word, main=True, relational=entry['word'], adjective=True, _=_adj_cngs())
    return Analysis(0.8, [(word, item)], 'nominal')


def nominal_analyses(token):
    word = script.key(token)
    if word in {script.key(w) for w in ADJECTIVES}:
        roman, ja = next(v for w, v in ADJECTIVES.items() if script.key(w) == word)
        return [Analysis(1.1, [(word, _item(word, pos='adj', base='%s %s' % (roman, script.isolate(word)), ja=ja,
                                            gloss_lang='ja', roman=roman, lemma=word, main=True, adjective=True,
                                            _=_adj_cngs()))], 'nominal')] + _nominal_analyses(token)
    relational = relational_adjective(token)
    return ([relational] if relational else []) + _nominal_analyses(token)


def _nominal_analyses(token):
    word = script.key(token)
    # ZWNJ (半スペース) の前までが語の本体であることが多い (گل‌های = گل + های、نامه‌ای = نامه + ای)
    zwnj = len(token.split(script.ZWNJ)[0]) if script.ZWNJ in token else None
    out = []
    for k in range(len(word), 0, -1):
        base, rest = word[:k], word[k:]
        entries = None
        for written, chain in _suffix_chains(base):
            if written != rest:
                continue
            if entries is None:
                entries = _nominal_entries(base)
            if not entries:
                break
            for entry in entries[:3]:
                analysis = _nominal_analysis(token, base, entry, chain)
                if zwnj is not None and chain:
                    analysis.score += 0.3 if len(base) == zwnj else -0.3
                out.append(analysis)
    return out


POS_MAP = {'noun': 'noun', 'name': 'noun', 'adj': 'adj', 'pronoun': 'pronoun', 'num': 'adj', 'det': 'adj'}


def _form_roman(entry, form):
    """変化形の転写: 規則的な複数形 (دانشجویان) は見出し語の転写 + 語尾、それ以外は大まかな転写"""
    lemma = script.key(entry['word'])
    rest = script.key(form)[len(lemma):] if script.key(form).startswith(lemma) else None
    for w, r in PLURALS:
        if rest == w:
            return _roman(entry) + r
    return script.rough_translit(form)


def _nominal_analysis(token, base, entry, chain):
    ja, gloss_lang = _gloss(entry)
    pos = POS_MAP[entry['pos']]
    number = 'pl' if any(c[0] == 'plural' for c in chain) or entry.get('form_tag') == 'plural' else 'sg'
    roman = _roman(entry) if not entry.get('form_word') else _form_roman(entry, base)
    tails = ''.join(c[1] if c[0] != 'ezafe' else '' for c in chain if c[0] not in ('possessive', 'copula'))
    main = _item(base, pos=pos, base='%s %s' % (_roman(entry), script.isolate(entry['word'])), ja=ja,
                 gloss_lang=gloss_lang, roman=roman + tails, lemma=script.normalize(entry['word']), main=True,
                 _=_adj_cngs() if pos == 'adj' else _nominal_cngs(number))
    if entry['pos'] == 'name':
        # 固有名詞の訳語は転写 (Wiktionary の英語の説明 'male given name' は使わない)。手で決めた訳語 (テヘラン) はそれを
        main['proper'] = True
        if gloss_lang != 'ja':
            main.update(ja=_roman(entry)[:1].upper() + _roman(entry)[1:], gloss_lang='en')
    if pos == 'adj' and entry['pos'] == 'adj':
        main['adjective'] = True
    if any(c[0] == 'indefinite' for c in chain):
        main.update(indefinite=True, ja=ja.split(',')[0] + ',' + ja if False else ja)
    if any(c[0] == 'ezafe' for c in chain):
        main['ezafe_written'] = True
    if any(c[0] == 'plural' for c in chain):
        main['plural_suffix'] = next(c[1] for c in chain if c[0] == 'plural')
    segments = [(base, main)]
    score = 1.0 - 0.15 * len(chain)
    if len(base) <= 2 and chain:
        score -= 0.2  # 短い語 + 接語 (رفت を رف「棚」+ -at と読まない)
    if pos == 'adj' and any(c[0] == 'possessive' for c in chain):
        score -= 0.3  # 形容詞 + -am は「私は〜だ」(繋辞) を先に
    if pos == 'adj' and any(c[0] == 'copula' for c in chain):
        score += 0.2
    if entry['pos'] == 'adj' and not chain and base.endswith('ی') and \
            any(e['pos'] == 'noun' for e in dictionary.lemmas(base[:-1])):
        score -= 0.25  # کتابی は「本の (形容詞)」より「ある本」(不定の -i) を先に
    for kind, r, written, person, number2 in chain:
        if kind == 'possessive':
            main['roman'] = main['roman'] + ('-' if False else '')
            segments.append((written, _item(written, pos='noun', base=written, ja=PERSONAL[(person, number2)],
                                            gloss_lang='ja', roman=r, suffix=True, person=person,
                                            _=[('Gen', number2, GENDER)])))
        elif kind == 'copula':
            segments.append((written, copula_item(written, r, person, number2, False, clitic=True)))
            score -= 0.2
    if entry.get('form_tag'):
        score -= 0.05
    return Analysis(score, segments, 'nominal')


def copula_item(surface, roman, person, number, negative, clitic=False):
    item = _item(surface, pos='verb', pres1sg=COPULA, lemma=COPULA, base='budan %s' % script.isolate(COPULA),
                 ja='ある,いる,〜である', gloss_lang='ja', roman=roman, voice='active', mood='indicative',
                 tense='present', person=person, number=number, main=True, existential=True,
                 form='繋辞の接語' if clitic else '繋辞 (現在)')
    if negative:
        item['negative'] = True
    if clitic:
        item['clitic'] = True
    return item


# ----------------------------------------------------------------------

@functools.lru_cache(maxsize=50000)
def analyses(token):
    """語 → [Analysis] (点数の高い順)"""
    word = script.normalize(token)
    key = script.key(token)
    out = []
    function = FUNCTION_WORDS.get(word) or FUNCTION_WORDS.get(key)
    if function:
        pos, roman, ja, extra = function
        item = _item(word, pos=pos, base=roman, ja=ja, gloss_lang='ja', roman=roman, main=True, **extra)
        if pos == 'preposition':
            item['dominates'] = 'Gen'  # 前置詞の目的語 (エザーフェでつながった名詞と同じく、文の解析で属格に絞る)
        out.append(Analysis(2.0, [(word, item)], 'function'))
    if key in {script.key(w) for w in PRONOUNS}:
        roman, person, number = next(v for w, v in PRONOUNS.items() if script.key(w) == key)
        out.append(Analysis(2.0, [(word, _item(word, pos='pronoun', base=roman, ja=PRONOUN_GLOSSES.get(word) or
                                                PERSONAL[(person, number)], gloss_lang='ja', roman=roman, main=True,
                                                person=person, _=_nominal_cngs(number)))], 'pronoun'))
    if key in DEMONSTRATIVES:
        roman, adj, pron = DEMONSTRATIVES[key]
        out.append(Analysis(2.0, [(word, _item(word, pos='adj', base=roman, ja=adj, ja_pronoun=pron,
                                                gloss_lang='ja', roman=roman, main=True, demonstrative=True,
                                                _=_adj_cngs()))], 'demonstrative'))
    if key in COPULA_FORMS:
        roman, person, number, negative = COPULA_FORMS[key]
        out.append(Analysis(2.0, [(word, copula_item(word, roman, person, number, negative))], 'copula'))
    verbs = verb_analyses(word)
    if any(not a.main.get('negative') and not a.main.get('prefix') for a in verbs):
        for a in verbs:
            if a.main.get('negative') and not a.main.get('prefix'):
                a.score *= 0.6  # نوشت は「書いた」で、na- + وشت ではない
    for a in verbs:
        if any(script.key(w) == script.key(a.main['lemma']) for w in GLOSSES):
            a.score += 0.05  # 同点なら基本の動詞 (می‌کند は کردن「する」で、کندن「掘る」の過去でない)
    out += verbs
    nominals = nominal_analyses(word)
    curated = any(a.main.get('gloss_lang') == 'ja' and not a.main.get('proper') for a in nominals)
    for a in nominals:
        if a.main.get('proper') and not curated:
            a.score += 0.05  # علی は形容詞「高い」(英語の訳語) より人名。زیبا「美しい」は人名にしない
    out += nominals
    if not out:
        out.append(Analysis(0.0, [(word, _item(word, pos='noun', base=word, ja=script.rough_translit(word),
                                                gloss_lang='en', roman=script.rough_translit(word), main=True,
                                                unknown=True, _=_nominal_cngs('sg')))], 'unknown'))
    return sorted(out, key=lambda a: -a.score)
