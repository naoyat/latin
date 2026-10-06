#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ロシア語の語形の解析: pymorphy3 (OpenCorpora の辞書) の解析を、解析器 (core/) の項目 (dict) にする。
# 訳語は Wiktionary の辞書 (russian/dictionary.py)、前置詞・代名詞は手作りの表から
#
#   книгу   → noun книга「本」 [Acc.sg.f]
#   прочитал → verb прочитать「読む」 完了体・過去 → 完了 (「読んだ」)
#   читал   → verb читать 不完了体・過去 → 未完了 (「読んでいた」)
#   читая   → 副動詞 → 副詞「読みながら / 読んで」
#
import functools

from . import dictionary, script

CASES = {'nomn': 'Nom', 'gent': 'Gen', 'gen1': 'Gen', 'gen2': 'Gen', 'datv': 'Dat', 'accs': 'Acc', 'acc2': 'Acc',
         'ablt': 'Ins', 'loct': 'Loc', 'loc1': 'Loc', 'loc2': 'Loc', 'voct': 'Voc'}
NUMBERS = {'sing': 'sg', 'plur': 'pl'}
GENDERS = {'masc': 'm', 'femn': 'f', 'neut': 'n'}
PERSONS = {'1per': 1, '2per': 2, '3per': 3}
# 解析の候補は、最も確からしいもの (pymorphy3 の score) の何割以上を残すか
MIN_SCORE_RATIO = 0.05

# 前置詞: 支配する格 → 訳 (ラテン語の前置詞と同じく、支配する格ごとに1項目)
PREPOSITIONS = {
    'в': {'Acc': '〜へ,〜の中へ', 'Loc': '〜で,〜の中で'},
    'на': {'Acc': '〜の上へ,〜へ', 'Loc': '〜の上で,〜で'},
    'с': {'Ins': '〜とともに,〜と', 'Gen': '〜から', 'Acc': '〜ほど'},
    'к': {'Dat': '〜の方へ,〜に'},
    'от': {'Gen': '〜から'},
    'из': {'Gen': '〜から,〜の中から'},
    'у': {'Gen': '〜のところに,〜のそばに'},
    'о': {'Loc': '〜について', 'Acc': '〜にぶつかって'},
    'по': {'Dat': '〜に沿って,〜によって', 'Loc': '〜の後で', 'Acc': '〜まで'},
    'за': {'Acc': '〜の向こうへ,〜のために', 'Ins': '〜の向こうで,〜の後ろで'},
    'под': {'Acc': '〜の下へ', 'Ins': '〜の下で'},
    'над': {'Ins': '〜の上方で'},
    'перед': {'Ins': '〜の前で'},
    'между': {'Ins': '〜の間で'},
    'без': {'Gen': '〜なしで'},
    'для': {'Gen': '〜のために'},
    'до': {'Gen': '〜まで'},
    'после': {'Gen': '〜の後で'},
    'через': {'Acc': '〜を通って,〜後に'},
    'при': {'Loc': '〜のときに,〜のそばで'},
    'про': {'Acc': '〜について'},
    'около': {'Gen': '〜の近くで'},
    'из-за': {'Gen': '〜のせいで,〜の後ろから'},
    'из-под': {'Gen': '〜の下から'},
    'вокруг': {'Gen': '〜の周りに'},
    'против': {'Gen': '〜に反対して'},
    'среди': {'Gen': '〜の中で'},
    'кроме': {'Gen': '〜の他に'},
    'вместо': {'Gen': '〜の代わりに'},
}
PREPOSITION_VARIANTS = {'во': 'в', 'со': 'с', 'ко': 'к', 'ото': 'от', 'изо': 'из', 'об': 'о', 'обо': 'о',
                        'подо': 'под', 'надо': 'над', 'передо': 'перед'}

# 代名詞・代名詞的な形容詞の訳 (Wiktionary の日本語訳は「彼は」のように助詞が付いている)
PRONOUNS = {'я': '私', 'ты': 'あなた', 'он': '彼', 'она': '彼女', 'оно': 'それ', 'мы': '私たち', 'вы': 'あなたたち',
            'они': '彼ら', 'себя': '自分', 'кто': '誰', 'что': '何', 'это': 'これ', 'то': 'それ', 'никто': '誰も',
            'ничто': '何も', 'ничего': '何も', 'всё': 'すべて', 'все': 'みな'}
DETERMINERS = {'мой': '私の', 'твой': 'あなたの', 'наш': '私たちの', 'ваш': 'あなたたちの', 'свой': '自分の',
               'его': '彼の', 'её': '彼女の', 'ее': '彼女の', 'их': '彼らの', 'этот': 'この', 'тот': 'その,あの',
               'весь': 'すべての', 'каждый': 'それぞれの', 'такой': 'そのような', 'какой': 'どのような',
               'который': '〜するところの', 'один': '一つの,ある', 'другой': '別の', 'сам': '自身', 'чей': '誰の'}
FUNCTION_WORDS = {
    'и': ('conj', 'そして,〜と'), 'а': ('conj', 'そして,一方'), 'но': ('conj', 'しかし'), 'или': ('conj', 'または'),
    'ни': ('conj', '〜も…ない'), 'что': ('conj', '〜ということ'), 'чтобы': ('conj', '〜するために'),
    'если': ('conj', 'もし'), 'когда': ('conj', '〜するとき'), 'потому': ('adv', 'それゆえ'), 'как': ('conj', '〜のように'),
    'не': ('adv', '〜ない'), 'нет': ('adv', 'いいえ,〜が無い'), 'да': ('adv', 'はい'), 'уже': ('adv', 'もう'),
    'ещё': ('adv', 'まだ,さらに'), 'еще': ('adv', 'まだ,さらに'), 'тоже': ('adv', '〜も'), 'только': ('adv', '〜だけ'),
    'даже': ('adv', '〜さえ'), 'ли': ('adv', '〜か (疑問)'), 'же': ('adv', '(強め)'), 'вот': ('adv', 'ほら'),
    'здесь': ('adv', 'ここで'), 'там': ('adv', 'そこで'), 'сейчас': ('adv', '今'), 'теперь': ('adv', '今'),
    'очень': ('adv', 'とても'), 'всегда': ('adv', 'いつも'), 'никогда': ('adv', '決して…ない'),
}

_morph = None


def morph():
    global _morph
    if _morph is None:
        import pymorphy3
        _morph = pymorphy3.MorphAnalyzer()
    return _morph


def available():
    try:
        morph()
        return True
    except ImportError:
        return False


def _gloss(lemma, kinds):
    """見出し語の訳語 (訳語, 言語)。kinds は Wiktionary の品詞の候補 (先のものを優先)。無ければ (見出し語, 'en')"""
    lemmas = dictionary.lemmas(lemma)
    for kind in kinds:
        found = [l for l in lemmas if l['pos'] == kind]
        if found:
            best = max(found, key=lambda l: (l['gloss_lang'] == 'ja', l['senses']))
            return best['ja'], best['gloss_lang'], best
    if lemmas:
        return lemmas[0]['ja'], lemmas[0]['gloss_lang'], lemmas[0]
    return lemma, 'en', None


def _cng(tag):
    case = CASES.get(tag.case)
    if not case:
        return None
    return (case, NUMBERS.get(tag.number, 'sg'), GENDERS.get(tag.gender))


def _all_genders(cngs):
    """性の無い形 (形容詞の複数形 германские、数詞) は3つの性のどれとも一致するように展開する"""
    out = []
    for case, number, gender in cngs:
        for g in ((gender,) if gender else ('m', 'f', 'n')):
            if (case, number, g) not in out:
                out.append((case, number, g))
    return out


def _verb_item(parse, tag):
    lemma = parse.normal_form
    ja, gloss_lang, entry = _gloss(lemma, ('verb',))
    aspect = {'perf': 'pf', 'impf': 'impf'}.get(tag.aspect) or (entry or {}).get('aspect')
    item = {'pos': 'verb', 'pres1sg': lemma, 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang, 'aspect': aspect,
            'voice': 'active'}
    if tag.POS == 'INFN':
        item.update(mood='infinitive', tense='present')
        return item
    tense = {'pres': 'present', 'futr': 'future'}.get(tag.tense)
    if tag.tense == 'past':
        # 完了体の過去は「〜した」(完了)、不完了体の過去は「〜していた」(未完了)
        tense = 'perfect' if aspect == 'pf' else 'imperfect'
    item.update(mood='imperative' if tag.mood == 'impr' else 'indicative', tense=tense or 'present',
                person=PERSONS.get(tag.person, 3), number=NUMBERS.get(tag.number, 'sg'))
    if tag.gender:
        item['gender'] = GENDERS.get(tag.gender)
    return item


def _adverbial_gloss(ja, gloss_lang, lemma):
    """副動詞の訳 (読んで / reading)"""
    first = ja.split(',')[0]
    if gloss_lang == 'ja':
        from core.japanese import JaVerb
        try:
            return JaVerb(first).adverbial_form('active')
        except Exception:
            pass
    return '%s[副動詞]' % first


def _item(parse):
    """pymorphy3 の解析1つ → 項目 (dict)。扱わなければ None"""
    tag = parse.tag
    pos = tag.POS
    lemma = parse.normal_form
    word = parse.word
    if pos in ('VERB', 'INFN'):
        return _verb_item(parse, tag)
    if pos == 'PRTS':
        # 短語尾分詞 (прочитана「読まれた」) は受動の完了の動詞として
        item = _verb_item(parse, tag)
        item.update(voice='passive', tense='perfect', mood='indicative', person=3,
                    number=NUMBERS.get(tag.number, 'sg'))
        return item
    if pos == 'PRTF':
        ja, gloss_lang, _ = _gloss(lemma, ('verb',))
        cng = _cng(tag)
        if not cng:
            return None
        return {'pos': 'participle', 'base': lemma, 'pres1sg': lemma, 'ja': ja, 'gloss_lang': gloss_lang,
                'tense': 'present' if tag.tense == 'pres' else 'perfect',
                'voice': 'passive' if tag.voice == 'pssv' else 'active', '_': [cng]}
    if pos == 'GRND':
        ja, gloss_lang, _ = _gloss(lemma, ('verb',))
        return {'pos': 'adv', 'base': lemma, 'pres1sg': lemma, 'ja': _adverbial_gloss(ja, gloss_lang, lemma),
                'gloss_lang': gloss_lang, 'desc': '副動詞'}
    if pos == 'PREP':
        return None  # 前置詞は表から (analyze で)
    if pos in ('NOUN', 'NPRO'):
        cng = _cng(tag)
        if not cng:
            return None
        if pos == 'NPRO' or lemma in PRONOUNS:
            return {'pos': 'pronoun', 'base': lemma, 'ja': PRONOUNS.get(lemma, lemma), 'gloss_lang': 'ja', '_': [cng]}
        ja, gloss_lang, entry = _gloss(lemma, ('noun', 'name'))
        item = {'pos': 'noun', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang, '_': [cng]}
        if tag.animacy == 'anim':
            item['animate'] = True  # 人・動物 (存在の文で「いる」)
        if entry and entry['word'] != lemma:
            item['stressed'] = entry['word']
        return item
    if pos in ('ADJF', 'NUMR'):
        cng = _cng(tag)
        if not cng:
            return None
        if lemma in DETERMINERS or 'Apro' in tag:
            ja = DETERMINERS.get(lemma) or _gloss(lemma, ('pronoun', 'adj'))[0]
            return {'pos': 'adj', 'base': lemma, 'ja': ja, 'gloss_lang': 'ja', '_': [cng], 'desc': '指示代名詞'}
        ja, gloss_lang, _ = _gloss(lemma, ('adj', 'num', 'participle'))
        return {'pos': 'adj', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang, '_': [cng]}
    if pos == 'ADJS':
        # 短語尾形容詞 (красива「美しい」) は述語にだけなる。主格と同じ性・数を持たせる
        ja, gloss_lang, _ = _gloss(lemma, ('adj',))
        return {'pos': 'adj', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang, 'desc': '短語尾',
                '_': [('Nom', NUMBERS.get(tag.number, 'sg'), GENDERS.get(tag.gender))]}
    if pos == 'COMP':
        ja, gloss_lang, _ = _gloss(lemma, ('adj', 'adv'))
        return {'pos': 'adv', 'base': lemma, 'ja': 'より' + ja.split(',')[0], 'gloss_lang': gloss_lang, 'desc': '比較級'}
    if pos in ('ADVB', 'PRED'):
        ja, gloss_lang, _ = _gloss(lemma, ('adv', 'predicative', 'adj'))
        return {'pos': 'adv', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang}
    if pos == 'CONJ':
        ja, gloss_lang, _ = _gloss(lemma, ('conj',))
        return {'pos': 'conj', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang}
    if pos in ('PRCL', 'INTJ'):
        ja, gloss_lang, _ = _gloss(lemma, ('particle', 'intj', 'adv'))
        return {'pos': 'adv', 'base': lemma, 'ja': ja, 'gloss_lang': gloss_lang}
    return None


# 代名詞の読みを先にする語 (pymorphy3 は все を助詞「まだ」、то を接続詞と読むのを一番にする)
NOMINAL_FIRST = {'все', 'всё', 'то', 'это', 'всего', 'всем', 'всех'}
NUMBER_CASES = [(case, number, gender) for case in ('Nom', 'Gen', 'Dat', 'Acc', 'Ins', 'Loc') for number in ('sg', 'pl')
                for gender in ('m', 'f', 'n')]


def _nominal_pronoun(parse):
    return parse.tag.POS == 'NPRO' or (parse.tag.POS == 'ADJF' and 'Apro' in parse.tag)


# есть は быть の現在形「ある」(у меня есть книга) と動詞 есть「食べる」の不定形。pymorphy3 は後者だけを残すので両方を
EST = [{'pos': 'verb', 'pres1sg': 'быть', 'base': 'быть', 'ja': '在る,居る', 'gloss_lang': 'ja', 'aspect': 'impf',
        'voice': 'active', 'mood': 'indicative', 'tense': 'present', 'person': 3, 'number': 'sg', 'existential': True,
        'source': 'table'}]


@functools.lru_cache(maxsize=65536)
def _analyze(key):
    if key == 'есть':
        return EST + [item for item in _analyze('есть ') if item['pos'] == 'verb']
    if key == 'есть ':
        key = 'есть'
    if key.isdigit():
        # 数字 (2012 года) は格の決まらない数詞
        return [{'pos': 'adj', 'base': key, 'ja': key, 'gloss_lang': 'ja', '_': list(NUMBER_CASES), 'desc': '数詞',
                 'source': 'table'}]
    prep = PREPOSITION_VARIANTS.get(key, key)
    if prep in PREPOSITIONS:
        return [{'pos': 'preposition', 'base': prep, 'dominates': case, 'ja': ja, 'gloss_lang': 'ja', 'source': 'table'}
                for case, ja in PREPOSITIONS[prep].items()]
    parses = morph().parse(key)
    table = []
    if key in FUNCTION_WORDS:
        # 手作りの表の読み (что「〜ということ」) を先に、pymorphy3 の代名詞の読み (что「何」) を後ろに
        pos, ja = FUNCTION_WORDS[key]
        table = [{'pos': pos, 'base': key, 'ja': ja, 'gloss_lang': 'ja', 'source': 'table'}]
        parses = [p for p in parses if _nominal_pronoun(p)]
    if not parses:
        return table
    if key in NOMINAL_FIRST:
        parses = sorted(parses, key=lambda p: not _nominal_pronoun(p))
    best = max(p.score for p in parses)
    merged = {}
    for parse in parses:
        if parse.score < best * MIN_SCORE_RATIO and not _nominal_pronoun(parse):
            continue
        item = _item(parse)
        if item is None:
            continue
        # 同じ見出し語・品詞・動詞の形の解析は1つの項目にまとめる (格の組を合わせる)
        sig = tuple((k, str(v)) for k, v in sorted(item.items()) if k != '_')
        if sig in merged:
            for cng in item.get('_', []):
                if cng not in merged[sig]['_']:
                    merged[sig]['_'].append(cng)
        else:
            item['source'] = 'pymorphy3'
            merged[sig] = item
    for item in merged.values():
        if item['pos'] in ('adj', 'participle') and '_' in item:
            item['_'] = _all_genders(item['_'])
    return table + list(merged.values())


def analyze(word):
    """語 (表記どおり) → 項目 (dict) のリスト (確からしいものから)。項目の surface は表記どおり"""
    # pymorphy3 は ё と е を区別する (всё「すべて」/ все「みな」) ので、強勢記号を除いて小文字にするだけ
    return [dict(item, surface=word, _=list(item['_'])) if '_' in item else dict(item, surface=word)
            for item in _analyze(script.strip_stress(word).lower())]


def stressed(word):
    """語形に強勢記号を付けた形 (Wiktionary の変化表から。同じ形で強勢の違うもの (замо́к / за́мок) は最初のもの)"""
    forms = dictionary.stressed_forms(word)
    if not forms:
        return word
    form = forms[0]
    # 大文字・ё を元の表記に合わせる
    if word[:1].isupper():
        form = form[:1].upper() + form[1:]
    return form
