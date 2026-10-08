#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語の語形の解析
#
# 動詞は、どの名詞を ang で目立たせるか (焦点) を接辞で示し、アスペクトを重複と -in- で示す:
#   行為者焦点  -um-  bumili (完了・不定) / bumibili (進行) / bibili (未然)
#              mag-  nagsulat (完了) / nagsusulat (進行) / magsusulat (未然) / magsulat (不定)
#   対象焦点    -in   binili (完了) / binibili (進行) / bibilhin (未然) / bilhin (不定)
#   場所焦点    -an   binilhan / binibilhan / bibilhan / bilhan
#   移動物焦点  i-    isinulat / isinusulat / isusulat / isulat
#   状態・可能  ma-   nakita (完了) / nakikita (進行) / makikita (未然) / makita (不定)
# 辞書 (Wiktionary) の語形の表にある形はそこから、無ければ接辞と重複を外して語根を引き、その語根の動詞の見出し
# (sumulat, sulatin, isulat …) の訳語を使う。
#   名詞の前の標識: ang / si (焦点)、ng / ni (焦点でない中心の参与者)、sa / kay (場所・受け手)。複数は mga / sina …
#   代名詞は形で標識が決まる (ako「私 (ang)」、ko「私 (ng)」、akin「私 (sa)」)
#   繋ぎ (linker): na / -ng (magandang bahay「美しい家」、bahay na maganda)
#
import functools
import re

from . import dictionary, script

GENDER = 'c'
CASES = ('Nom', 'Acc', 'Gen', 'Dat')
ASPECT_TENSES = {'completive': 'perfect', 'progressive': 'progressive', 'contemplative': 'future',
                 'infinitive': 'present', None: 'present'}
ASPECT_NAMES = {'completive': '完了', 'progressive': '進行', 'contemplative': '未然', 'infinitive': '不定'}
VOICE_NAMES = {'actor': '行為者焦点', 'object': '対象焦点', 'locative': '場所焦点', 'conveyance': '移動物・受益者焦点'}

# 標識: 語 → (種類, 複数)
MARKERS = {'ang': ('ang', False), 'si': ('ang', False), 'sina': ('ang', True), 'ng': ('ng', False),
           'ni': ('ng', False), 'nina': ('ng', True), 'sa': ('sa', False), 'kay': ('sa', False),
           'kina': ('sa', True), 'ang mga': ('ang', True), 'ng mga': ('ng', True), 'sa mga': ('sa', True)}
# 代名詞: 語 → (訳, 標識の種類, 人称, 数)
PRONOUNS = {
    'ako': ('私', 'ang', 1, 'sg'), 'ko': ('私', 'ng', 1, 'sg'), 'akin': ('私', 'sa', 1, 'sg'),
    'ikaw': ('あなた', 'ang', 2, 'sg'), 'ka': ('あなた', 'ang', 2, 'sg'), 'mo': ('あなた', 'ng', 2, 'sg'),
    'iyo': ('あなた', 'sa', 2, 'sg'), 'siya': ('彼', 'ang', 3, 'sg'), 'niya': ('彼', 'ng', 3, 'sg'),
    'kaniya': ('彼', 'sa', 3, 'sg'), 'kanya': ('彼', 'sa', 3, 'sg'), 'kami': ('私たち', 'ang', 1, 'pl'),
    'namin': ('私たち', 'ng', 1, 'pl'), 'amin': ('私たち', 'sa', 1, 'pl'), 'tayo': ('私たち', 'ang', 1, 'pl'),
    'natin': ('私たち', 'ng', 1, 'pl'), 'atin': ('私たち', 'sa', 1, 'pl'), 'kayo': ('あなたたち', 'ang', 2, 'pl'),
    'ninyo': ('あなたたち', 'ng', 2, 'pl'), 'inyo': ('あなたたち', 'sa', 2, 'pl'), 'sila': ('彼ら', 'ang', 3, 'pl'),
    'nila': ('彼ら', 'ng', 3, 'pl'), 'kanila': ('彼ら', 'sa', 3, 'pl'),
    'ito': ('これ', 'ang', 3, 'sg'), 'iyan': ('それ', 'ang', 3, 'sg'), 'iyon': ('あれ', 'ang', 3, 'sg'),
    'nito': ('これ', 'ng', 3, 'sg'), 'niyan': ('それ', 'ng', 3, 'sg'), 'niyon': ('あれ', 'ng', 3, 'sg'),
    'noon': ('あれ', 'ng', 3, 'sg'), 'dito': ('ここ', 'sa', 3, 'sg'), 'diyan': ('そこ', 'sa', 3, 'sg'),
    'doon': ('あそこ', 'sa', 3, 'sg'), 'sino': ('誰', 'ang', 3, 'sg'), 'ano': ('何', 'ang', 3, 'sg'),
}
# sa の形の代名詞は所有にも使う (sa akin「私の」、akin + -ng)
NEGATIONS = {'hindi': '〜ない', "'di": '〜ない', 'di': '〜ない', 'huwag': '〜するな'}
EXISTENTIALS = {'may': 'ある', 'mayroon': 'ある', 'meron': 'ある', 'wala': 'ない'}
CONJUNCTIONS = {'at': 'そして,〜と', 'o': 'または', 'pero': 'しかし', 'ngunit': 'しかし', 'subalit': 'しかし',
                'kung': 'もし', 'kapag': '〜するとき', 'dahil': '〜なので', 'sapagkat': '〜なので', 'kaya': 'だから',
                'habang': '〜する間', 'nang': '〜したとき', 'upang': '〜するために', 'para': '〜のために',
                'kaya naman': 'だから', 'bago': '〜する前に', 'pagkatapos': '〜した後で'}
# 第2位の接語 (後ろに付く小辞)
ENCLITICS = {'na': ('もう', 'adv'), 'pa': ('まだ', 'adv'), 'ba': ('か', 'question'), 'daw': ('〜そうだ', 'adv'),
             'raw': ('〜そうだ', 'adv'), 'din': ('〜も', 'adv'), 'rin': ('〜も', 'adv'), 'lang': ('〜だけ', 'adv'),
             'lamang': ('〜だけ', 'adv'), 'naman': ('', 'adv'), 'po': ('', 'polite'), 'ho': ('', 'polite'),
             'nga': ('本当に', 'adv'), 'pala': ('なんと', 'adv'), 'kasi': ('〜なので', 'adv'), 'yata': ('たぶん', 'adv'),
             'sana': ('〜ならいいのに', 'adv'), 'muna': ('まず', 'adv'), 'man': ('〜でも', 'adv')}
# 訳語を決めておく語 (Wiktionary の最初の語義が外れるもの)
GLOSSES = {'bata': ('子供', 'noun'), 'lalaki': ('男', 'noun'), 'babae': ('女', 'noun'), 'isda': ('魚', 'noun'),
           'bahay': ('家', 'noun'), 'aso': ('犬', 'noun'), 'pusa': ('猫', 'noun'), 'libro': ('本', 'noun'),
           'aklat': ('本', 'noun'), 'tindahan': ('店', 'noun'), 'paaralan': ('学校', 'noun'), 'guro': ('先生', 'noun'),
           'estudyante': ('学生', 'noun'), 'tubig': ('水', 'noun'), 'kanin': ('ご飯', 'noun'), 'pera': ('お金', 'noun'),
           'sulat': ('手紙', 'noun'), 'liham': ('手紙', 'noun'), 'nanay': ('母', 'noun'), 'tatay': ('父', 'noun'),
           'ina': ('母', 'noun'), 'ama': ('父', 'noun'), 'kaibigan': ('友達', 'noun'), 'mesa': ('机', 'noun'),
           'lungsod': ('町', 'noun'), 'bayan': ('町,国', 'noun'), 'araw': ('日', 'noun'), 'gabi': ('夜', 'noun'),
           'ingay': ('騒音', 'noun'), 'maganda': ('美しい', 'adj'), 'malaki': ('大きい', 'adj'),
           'maliit': ('小さい', 'adj'), 'mabuti': ('良い', 'adj'), 'masarap': ('おいしい', 'adj'),
           'mainit': ('暑い', 'adj'), 'malamig': ('寒い', 'adj'), 'bago': ('新しい', 'adj'), 'luma': ('古い', 'adj'),
           'matanda': ('年老いた', 'adj'), 'mataas': ('高い', 'adj'), 'masaya': ('楽しい', 'adj'),
           'pagkain': ('食べ物', 'noun'), 'trabaho': ('仕事', 'noun'), 'wika': ('言語', 'noun'),
           'tao': ('人', 'noun'), 'mga': ('〜たち', 'plural'), 'naturan': ('前述の', 'adj'), 'marami': ('多くの', 'adj'),
           'iba': ('他の', 'adj'), 'bawat': ('それぞれの', 'adj'), 'lahat': ('すべて', 'noun'), 'isa': ('一つ', 'noun'),
           'dalawa': ('二つ', 'noun'), 'tatlo': ('三つ', 'noun'), 'pamahalaan': ('政府', 'noun'), 'bansa': ('国', 'noun'),
           'kahapon': ('昨日', 'adv'), 'ngayon': ('今', 'adv'), 'mamaya': ('後で', 'adv'), 'noon': ('その時', 'adv'),
           'palagi': ('いつも', 'adv'), 'lagi': ('いつも', 'adv'), 'sobra': ('とても', 'adv'), 'talaga': ('本当に', 'adv'),
           'lamang': ('〜だけ', 'adv'), 'muli': ('再び', 'adv'), 'agad': ('すぐに', 'adv')}
# 動詞の訳語を決めておく見出し (態ごとの見出しの訳語が外れるもの)
VERB_GLOSSES = {'bili': '買う', 'kain': '食べる', 'inom': '飲む', 'sulat': '書く', 'basa': '読む', 'bigay': '与える',
                'kita': '見る', 'gising': '起きる', 'tulog': '眠る', 'punta': '行く', 'alis': '出発する', 'dating': '着く',
                'luto': '料理する', 'linis': '掃除する', 'aral': '勉強する', 'turo': '教える', 'tawag': '呼ぶ',
                'sabi': '言う', 'gawa': '作る', 'dala': '持って行く', 'kuha': '取る', 'bukas': '開ける',
                'sara': '閉める', 'hanap': '探す', 'tulong': '助ける', 'lakad': '歩く', 'takbo': '走る',
                'upo': '座る', 'tayo': '立つ', 'laro': '遊ぶ', 'sayaw': '踊る', 'kanta': '歌う', 'dinig': '聞く',
                'rinig': '聞く', 'alam': '知る', 'gusto': '好む', 'mahal': '愛する', 'uwi': '帰る', 'balik': '戻る',
                'isip': '思う', 'ikot': '回る', 'hinto': '止まる', 'tanto': '悟る', 'sagot': '答える', 'iyak': '泣く',
                'tawa': '笑う', 'ngiti': '微笑む', 'hintay': '待つ', 'alala': '思い出す', 'limot': '忘れる',
                'damdam': '感じる', 'patak': '滴る', 'pangarap': '夢見る', 'ngarap': '夢見る', 'kilala': '知る',
                'sama': '一緒に行く', 'tagpo': '出会う', 'kita': '見る', 'hanga': '感心する', 'asa': '期待する',
                'tingin': '見る', 'titig': '見つめる', 'yakap': '抱きしめる', 'halik': 'キスする', 'awit': '歌う',
                'sigaw': '叫ぶ', 'takot': '恐れる', 'saya': '楽しむ', 'lungkot': '悲しむ', 'ibig': '愛する'}
# 対象焦点・場所焦点で訳語の変わる語根 (gumising「起きる」/ ginising「起こす」)
TRANSITIVE_GLOSSES = {'gising': '起こす', 'tulog': '寝かせる', 'balik': '返す', 'uwi': '持ち帰る', 'labas': '出す',
                      'pasok': '入れる', 'alis': '取り除く', 'upo': '座らせる', 'tayo': '立てる'}
LINKER = 'linker'

VOWELS = 'aeiou'


def _item(surface, **kw):
    item = {'surface': surface, 'compact': True}
    item.update(kw)
    return item


def _nominal_cngs(number='sg'):
    return [(case, number, GENDER) for case in CASES]


def _adj_cngs():
    return [(case, number, GENDER) for case in CASES for number in ('sg', 'pl')]


# ----------------------------------------------------------------------
# 接辞と重複を外す (語根, 態, アスペクト)

def _redup(rest):
    """語頭の CV の重複 (bibili → bili、susulat → sulat、aalis → alis)。外せなければ None"""
    if len(rest) >= 4 and rest[0] in VOWELS and rest[1] == rest[0]:
        return rest[1:]
    if len(rest) >= 5 and rest[0] not in VOWELS and rest[1] in VOWELS and rest[2:4] == rest[0:2]:
        return rest[2:]
    return None


def _strip_in_suffix(stem):
    """-in / -hin / -an / -han を外した語根の候補 (bilhin → bili は辞書の語形の表で、ここは規則どおりのもの)"""
    out = []
    for suffix in ('hin', 'nin', 'in'):
        if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
            root = stem[:-len(suffix)]
            out.append(root)
            if root.endswith('u'):
                out.append(root[:-1] + 'o')   # inumin ← inom (o → u)
            out += _unsyncope(stem[:-len(suffix) + (1 if suffix == 'hin' else 0)] if suffix == 'hin' else root)
    return out


def _unsyncope(stem):
    """母音の脱落を戻す (bilh-in ← bili、kun-in ← kuha は規則外): 子音 + h で終われば、h の前に母音を補う"""
    if len(stem) >= 3 and stem.endswith('h') and stem[-2] not in VOWELS:
        return [stem[:-1] + v for v in 'iaou']
    return []


def _strip_an_suffix(stem):
    out = []
    for suffix in ('han', 'nan', 'an'):
        if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
            root = stem[:-len(suffix)]
            out.append(root)
            if root.endswith('u'):
                out.append(root[:-1] + 'o')
            if suffix == 'han':
                out += _unsyncope(stem[:-2])                # bilhan ← bili
    return out


def _uninfix(word, infix):
    """-um- / -in- を外す (bumili → bili、binili → bili、母音で始まる語根は語頭: umalis → alis、inalis → alis)"""
    if word.startswith(infix) and len(word) > 4:
        return word[2:]
    if len(word) > 4 and word[0] not in VOWELS and word[1:3] == infix:
        return word[0] + word[3:]
    return None


@functools.lru_cache(maxsize=50000)
def candidates(word):
    """動詞の語形 → [(語根, 態, アスペクト)] (可能性のあるものをすべて)"""
    out = []

    def add(root, voice, aspect):
        if root and len(root) >= 2 and (root, voice, aspect) not in out:
            out.append((root, voice, aspect))

    # 行為者焦点 mag- / nag- / mang- / nang- / maka- / naka-
    for prefix, aspect_plain, aspect_redup in (('nag', 'completive', 'progressive'), ('mag', 'infinitive', 'contemplative'),
                                               ('naka', 'completive', 'progressive'), ('maka', 'infinitive', 'contemplative'),
                                               ('nakapag', 'completive', 'progressive'),
                                               ('nagpa', 'completive', 'progressive'), ('magpa', 'infinitive', 'contemplative'),
                                               ('nakiki', 'progressive', 'progressive'), ('naki', 'completive', 'progressive'),
                                               ('maki', 'infinitive', 'contemplative')):
        if word.startswith(prefix) and len(word) > len(prefix) + 2:
            rest = word[len(prefix):].lstrip('-')
            redup = _redup(rest)
            if redup:
                add(redup, 'actor', aspect_redup)
            add(rest, 'actor', aspect_plain)
    for prefix, aspect_plain, aspect_redup in (('nang', 'completive', 'progressive'), ('mang', 'infinitive', 'contemplative'),
                                               ('nam', 'completive', 'progressive'), ('mam', 'infinitive', 'contemplative'),
                                               ('nan', 'completive', 'progressive'), ('man', 'infinitive', 'contemplative')):
        if word.startswith(prefix) and len(word) > len(prefix) + 2:
            rest = word[len(prefix):]
            for root in (rest, 'p' + rest, 'b' + rest, 't' + rest, 's' + rest, 'k' + rest):
                add(_redup(root) or root, 'actor', aspect_redup if _redup(root) else aspect_plain)
    # 状態・可能 ma- / na- (対象焦点が多い: nakita ko「私が見た」)
    for prefix, aspect_plain, aspect_redup in (('na', 'completive', 'progressive'), ('ma', 'infinitive', 'contemplative')):
        if word.startswith(prefix) and len(word) > 4:
            rest = word[2:]
            redup = _redup(rest)
            if redup:
                add(redup, 'stative', aspect_redup)
            add(rest, 'stative', aspect_plain)
    # i- (移動物・受益者焦点): isinulat / isinusulat / isusulat / isulat
    if word.startswith('i') and len(word) > 4 and word[1] not in VOWELS:
        rest = word[1:]
        root = _uninfix(rest, 'in')
        if root:
            add(_redup(root) or root, 'conveyance', 'progressive' if _redup(root) else 'completive')
        add(_redup(rest) or rest, 'conveyance', 'contemplative' if _redup(rest) else 'infinitive')
    # -an (場所焦点)
    for stem in _strip_an_suffix(word):
        root = _uninfix(stem, 'in')
        if root:
            add(_redup(root) or root, 'locative', 'progressive' if _redup(root) else 'completive')
        add(_redup(stem) or stem, 'locative', 'contemplative' if _redup(stem) else 'infinitive')
    # -in- / -in (対象焦点)
    root = _uninfix(word, 'in')
    if root:
        add(_redup(root) or root, 'object', 'progressive' if _redup(root) else 'completive')
    for stem in _strip_in_suffix(word):
        add(_redup(stem) or stem, 'object', 'contemplative' if _redup(stem) else 'infinitive')
    # -um- (行為者焦点)
    root = _uninfix(word, 'um')
    if root:
        add(_redup(root) or root, 'actor', 'progressive' if _redup(root) else 'completive')
    # 重複だけ (未然の行為者焦点: bibili ← bili)
    redup = _redup(word)
    if redup:
        add(redup, 'actor', 'contemplative')
    return out


# ----------------------------------------------------------------------
# 訳語

def _english(key, pos=None):
    rows = [r for r in dictionary.lemmas(key) if r['en'] and (pos is None or r['pos'] == pos)]
    return rows[0]['en'] if rows else None


def _verb_lemma_gloss(root, voice):
    """語根と態から、その態の動詞の見出しを探して訳語を返す (sulat + actor → sumulat「書く」)"""
    if root in VERB_GLOSSES:
        return VERB_GLOSSES[root], 'ja'
    um = root[0] + 'um' + root[1:] if root[0] not in VOWELS else 'um' + root
    forms = {'actor': [um, 'mag' + root, 'mang' + root], 'object': [root + 'in', root + 'hin'],
             'locative': [root + 'an', root + 'han'], 'conveyance': ['i' + root],
             'stative': ['ma' + root]}.get(voice, [])
    for form in forms + [um, 'mag' + root, root + 'in', 'i' + root]:
        en = _english(form, 'verb')
        if en:
            return en, 'en'
    en = _english(root)
    return (en, 'en') if en else (root, 'en')


def _verb_item(surface, root, voice, aspect, lemma=None, en=None):
    if en is None:
        ja, gloss_lang = _verb_lemma_gloss(root, voice)
    else:
        ja, gloss_lang = (VERB_GLOSSES[root], 'ja') if root in VERB_GLOSSES else (en, 'en')
    if root in VERB_GLOSSES:
        ja, gloss_lang = VERB_GLOSSES[root], 'ja'
    if root in TRANSITIVE_GLOSSES and voice in ('object', 'locative', 'conveyance'):
        ja, gloss_lang = TRANSITIVE_GLOSSES[root], 'ja'
    if voice == 'stative':
        voice = 'object' if re.match(r'^(be |get |happen to |be able to )', ja or '') or root in ('kita', 'rinig', 'dinig', 'alam') \
            else 'actor'
    return _item(surface, pos='verb', pres1sg=lemma or root, lemma=lemma or root, root=root,
                 base='%s (%s・%s)' % (root, VOICE_NAMES.get(voice, voice or '?'), ASPECT_NAMES.get(aspect, '?')),
                 ja=ja, gloss_lang=gloss_lang, voice='active', focus=voice, aspect=aspect,
                 mood='indicative', tense=ASPECT_TENSES.get(aspect, 'present'), person=None, number=None, main=True)


def _root_of(lemma):
    """動詞の見出しの語根 (bumili → bili、bilhin → bili)。訳語を決めてある語根を先に"""
    found = [root for root, voice, aspect in candidates(lemma) if dictionary.lemmas(root) or root in VERB_GLOSSES]
    return next((r for r in found if r in VERB_GLOSSES), found[0] if found else lemma)


def _function_word(word):
    if word in PRONOUNS:
        ja, marker, person, number = PRONOUNS[word]
        return _item(word, pos='pronoun', base=word, ja=ja, gloss_lang='ja', marker=marker, person=person,
                     _=_nominal_cngs(number))
    if word in MARKERS:
        kind, plural = MARKERS[word]
        return _item(word, pos='marker', base=word, ja='', gloss_lang='ja', marker=kind, plural=plural)
    if word in NEGATIONS:
        return _item(word, pos='adv', base=word, ja=NEGATIONS[word], gloss_lang='ja', negation=True)
    if word in EXISTENTIALS:
        return _item(word, pos='verb', pres1sg='may', lemma=word, base=word, ja=EXISTENTIALS[word], gloss_lang='ja',
                     voice='active', focus='existential', mood='indicative', tense='present', person=None,
                     number=None, main=True, existential=True)
    if word == 'ay':
        return _item(word, pos='ay', base=word, ja='', gloss_lang='ja')
    if word == 'mga':
        return _item(word, pos='plural', base=word, ja='', gloss_lang='ja')
    if word in CONJUNCTIONS:
        return _item(word, pos='conj', base=word, ja=CONJUNCTIONS[word], gloss_lang='ja')
    if word in ENCLITICS:
        ja, kind = ENCLITICS[word]
        return _item(word, pos='enclitic', base=word, ja=ja, gloss_lang='ja', enclitic=kind)
    return None


@functools.lru_cache(maxsize=50000)
def analyze(word):
    """語 (照合用の形) → ([項目 (良いものから)], 繋ぎ -ng が付いていたか)"""
    function = _function_word(word)
    if function:
        return [function], False
    items = []
    # 辞書の語形の表 (bumibili → bumili の進行)
    variant = lambda lemma: any(re.match(r'^(apheretic|alternative|syncopic|obsolete|dialectal)', r['en'] or '')
                                for r in dictionary.lemmas(lemma))
    for lemma, aspect in sorted(dictionary.forms(word), key=lambda f: variant(f[0])):
        rows = [r for r in dictionary.lemmas(lemma) if r['pos'] == 'verb' and r['en']]
        if rows:
            root = _root_of(lemma)
            items.append(_verb_item(word, root, rows[0]['voice'], aspect, lemma=lemma, en=rows[0]['en']))
            break
    for row in dictionary.lemmas(word):
        if row['pos'] == 'verb' and row['en'] and not items:
            root = _root_of(word)
            items.append(_verb_item(word, root, row['voice'], 'infinitive', lemma=word, en=row['en']))
        elif row['pos'] == 'verb' and not row['en'] and row['target'] and not items:
            target = [r for r in dictionary.lemmas(row['target']) if r['pos'] == 'verb' and r['en']]
            if target:
                items.append(_verb_item(word, _root_of(row['target']), target[0]['voice'], None, lemma=row['target'],
                                        en=target[0]['en']))
        elif row['pos'] in ('noun', 'name', 'adj', 'num', 'adv', 'intj') and row['en'] and \
                row['pos'] not in [i.get('kind') for i in items]:
            pos = {'name': 'noun', 'num': 'noun', 'intj': 'adv'}.get(row['pos'], row['pos'])
            fixed = GLOSSES.get(word)
            ja, lang = (fixed[0], 'ja') if fixed and fixed[1] == pos else (row['en'], 'en')
            if row['pos'] == 'name':
                ja, lang = word[:1].upper() + word[1:], 'en'
            item = _item(word, pos=pos, base=word, ja=ja, gloss_lang=lang, kind=row['pos'], proper=row['pos'] == 'name',
                         _=_adj_cngs() if pos == 'adj' else _nominal_cngs() if pos == 'noun' else None)
            items.append(item)
    if word in GLOSSES:
        pos = GLOSSES[word][1]
        items = [i for i in items if i['pos'] != pos]
        items.insert(0, _item(word, pos=pos, base=word, ja=GLOSSES[word][0], gloss_lang='ja',
                              _=_adj_cngs() if pos == 'adj' else _nominal_cngs()))
    if any(i.get('kind') == 'noun' for i in items):
        items = [i for i in items if not i.get('proper')]  # isda: 名詞「魚」があれば固有名詞「うお座」は除く
    if not items and '-' in word:
        # 部分的な重複 (iniisip-isip、pinangarap-ngarap、paikot-ikot): 後ろの繰り返しを除いて引き、「何度も」
        first, second = word.rsplit('-', 1)
        if len(second) >= 3 and (first.endswith(second) or first.endswith(second[1:]) or second in first):
            base, linked = analyze(first)
            if base and not base[0].get('unknown'):
                return [dict(base[0], surface=word, base=base[0]['base'] + ' (重複: 繰り返し)', repeated=True)], linked
    if not items:
        # 動名詞 pag- / pagka- / pang- (pagpatak「(しずくが) 落ちること」、pag-ikot「回ること」)
        m = re.match(r'^(pagka|pag|pang|pan|pam)-?(.{3,})$', word)
        if m and (dictionary.lemmas(m.group(2)) or m.group(2) in VERB_GLOSSES):
            root = m.group(2)
            ja, lang = _verb_lemma_gloss(root, 'actor')
            if lang == 'ja':
                ja = ja + 'こと'
            return [_item(word, pos='noun', base='%s (動名詞 %s-)' % (root, m.group(1)), ja=ja, gloss_lang=lang,
                          gerund=True, _=_nominal_cngs())], False
    if not items:
        # 繋ぎ -ng / -g (magandang → maganda + ng、mabuting → mabuti + ng)
        for stem in ([word[:-2]] if word.endswith('ng') else []) + ([word[:-1]] if word.endswith('g') else []):
            if len(stem) >= 2 and (dictionary.lemmas(stem) or stem in GLOSSES or stem in PRONOUNS):
                base, _ = analyze(stem)
                if base and not base[0].get('unknown'):
                    return base, True
        # ma- の形容詞の複数 (matataas ← mataas、magagaling ← magaling)
        if word.startswith('ma') and _redup(word[2:]):
            adj = 'ma' + _redup(word[2:])
            base, _ = analyze(adj)
            if base and base[0]['pos'] == 'adj':
                return [dict(base[0], surface=word, base=adj + ' (複数)', _=_adj_cngs())], False
        for root, voice, aspect in candidates(word):
            if voice == 'stative' and root not in VERB_GLOSSES and \
                    not any(r['pos'] == 'verb' for r in dictionary.lemmas('ma' + root)) and \
                    not any(r['pos'] in ('verb', 'noun') and r['en'] for r in dictionary.lemmas(root)):
                continue  # ma- / na- の動詞は、その動詞か語根が辞書にあるときだけ (naturang を動詞にしない)
            if dictionary.lemmas(root) or root in VERB_GLOSSES:
                items.append(_verb_item(word, root, voice, aspect))
                break
    if not items:
        # 接辞 + ハイフン + 英語などの語根 (mag-operate、na-recover、i-post): 語根を英語の訳語として動詞に
        m = re.match(r"^(nag|mag|nakapag|makapag|naka|maka|na|ma|i|ipina|ipinag|pinag|pina|in|um|nagpa|magpa)-(.+)$", word)
        if m:
            prefix = m.group(1)
            voice = 'actor' if prefix in ('nag', 'mag', 'nakapag', 'makapag', 'naka', 'maka', 'um', 'nagpa', 'magpa') \
                else 'conveyance' if prefix.startswith('i') else 'object'
            aspect = 'completive' if prefix.startswith(('nag', 'naka', 'na', 'in', 'ipina', 'pinag', 'pina', 'um')) \
                else 'infinitive'
            items = [_verb_item(word, m.group(2), voice, aspect, en=m.group(2))]
    if not items:
        # 辞書に無いが、動詞の接辞の形をしている語 (lansagin、naipatupad) は動詞 (語根の訳語は分からない)
        for root, voice, aspect in candidates(word):
            if voice != 'stative' and len(root) >= 3 and re.match(r'^(nag|mag|naka|maka|nakapag|ipina|ipinag|pinag|'
                                                                  r'ina|naipa|maipa|nai|mai|in|um|[^aeiou](um|in))', word):
                items = [_item(word, pos='verb', pres1sg=root, lemma=root, root=root, ja=root, gloss_lang='en',
                               base='%s (%s・%s)' % (root, VOICE_NAMES.get(voice, voice), ASPECT_NAMES.get(aspect, '?')),
                               voice='active', focus=voice, aspect=aspect, mood='indicative',
                               tense=ASPECT_TENSES.get(aspect, 'present'), person=None, number=None, main=True,
                               unknown=True)]
                break
    if not items:
        items = [_item(word, pos='noun', base=word, ja=word, gloss_lang='en', unknown=True, _=_nominal_cngs())]
    # 名詞と動詞の両方に読める語は、動詞の読みを後ろに (文の頭では解析器が選び直す)
    return items, False
