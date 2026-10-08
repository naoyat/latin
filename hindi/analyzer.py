#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ヒンディー語の文の解析
#
# 語を Wiktionary の変化表 (hindi/morphology.py) で引き、読みを文脈で選んでから、並列・係り先・後置詞句・格の枠・
# 日本語訳を共通の解析器 (core/analyzer.py) をヒンディー語の設定 (HINDI) で使う:
#   - 動詞は節の終わりに来る (主語-目的語-動詞)。動詞と助動詞・補助動詞の並びを1つの動詞にまとめる:
#     पढ़ता है「読む」(習慣)、पढ़ रहा है「読んでいる」(進行)、पढ़ा「読んだ」(完了)、पढ़ा था (過去完了)、
#     पढ़ेगा「読むだろう」(未来)、पढ़ सकता है「読める」、पढ़ा जाता है「読まれる」(受動)、पढ़ लिया (複合動詞)
#   - 後置詞は前の名詞 (斜格) に掛かる: ने → 主語 (能格。完了形の他動詞)、को → 目的語「〜を」か与格「〜に」、
#     का / की / के → 属格「〜の」(後ろの名詞に掛かる)、में・से・पर など → 後置詞句 (共通の解析器の前置詞句にするため、
#     名詞句の前に移す)。के लिए「〜のために」のような複合後置詞は1語にまとめる
#   - 主語: ने の付いた名詞句、無ければ動詞と人称・性・数の合う直格の名詞句。残りの直格の名詞句は目的語
#
import re

from core import analyzer as common
from core import language
from core.Word import Word
from . import dictionary, morphology, script

PUNCTUATION = {'।': 'period', '॥': 'period', '.': 'period', '!': 'period', '?': 'question', ',': 'comma',
               ';': 'comma', ':': 'comma', '"': None, '“': None, '”': None, "'": None, '(': 'comma', ')': 'comma',
               '-': 'comma', '–': 'comma', '—': 'comma'}
TOKEN = re.compile('[ऀ-ॣ०-ॿ‌‍]+|[0-9]+|[।॥.!?,;:"“”\'()\\-–—]')
HELPERS = {'रहना', 'सकना', 'चुकना', 'जाना', 'लेना', 'देना', 'डालना', 'पड़ना', 'बैठना', 'उठना', 'होना', 'चाहना',
           'पाना', 'लगना'}
STEM_HELPERS = {'रहना', 'सकना', 'चुकना', 'लेना', 'देना', 'डालना', 'पड़ना', 'बैठना', 'उठना', 'पाना'}
MOTION_VERBS = {'जाना', 'आना', 'पहुँचना', 'लौटना', 'भेजना'}
DEMONSTRATIVE_PRONOUNS = {'यह': ('この', 'is'), 'वह': ('その,あの', 'us'), 'ये': ('これらの', 'in'), 'वे': ('それらの', 'un'),
                          'इस': ('この', 'is'), 'उस': ('その,あの', 'us'), 'इन': ('これらの', 'in'), 'उन': ('それらの', 'un')}
NOUN_POSTPOSITIONS = {'पास': '〜のところに,〜のそばに', 'लिए': '〜のために', 'लिये': '〜のために', 'साथ': '〜とともに',
                      'बाद': '〜の後で', 'ऊपर': '〜の上に', 'सामने': '〜の前に', 'पीछे': '〜の後ろに', 'अंदर': '〜の中に',
                      'बिना': '〜なしで', 'बारे': '〜について'}
VECTORS = {'लेना', 'देना', 'जाना', 'डालना', 'पड़ना', 'बैठना', 'उठना'}
LIGHT_VERBS = {'करना', 'कराना', 'होना', 'देना', 'लेना', 'रखना', 'लगना', 'लगाना'}
DATIVE_VERBS = {'देना', 'कहना', 'बताना', 'दिखाना', 'भेजना', 'मिलना', 'सिखाना', 'समझाना', 'पूछना', 'लिखना'}


class KeySet(frozenset):
    def __new__(cls, words):
        return super().__new__(cls, {script.key(w) for w in words})

    def __contains__(self, word):
        return isinstance(word, str) and super().__contains__(script.key(word))


def _root_items(lemma):
    return [{'pos': 'verb', 'ja': l['ja'], 'gloss_lang': l['gloss_lang']}
            for l in dictionary.lemmas(lemma) if l['pos'] == 'verb']


HINDI = language.Language(
    name='hi',
    and_words=('और', 'तथा', 'एवं'),
    or_words=('या',),
    copulas=KeySet({'होना'}),
    negations=KeySet(morphology.NEGATIONS),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Dat': 'に', 'Gen': 'の', 'Voc': 'よ', 'Obl': 'に'},  # 後置詞の無い斜格は時の副詞 (इस साल「今年」)
    absolute_case=None,
    lookup=_root_items,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_precedes_head=True,
    possessor_cases=('Dat',),
)


def tokens(text):
    return TOKEN.findall(text)


COMPOUND_KEYS = {tuple(script.key(w) for w in k) for k in morphology.COMPOUND_POSTPOSITIONS}


def _alts(token):
    """語の位置の候補 (ヒンディー語は1つ。ウルドゥー語の入口は綴りの骨組みの合うデーヴァナーガリーの形の組)"""
    return token if isinstance(token, tuple) else (token,)


def group_tokens(surfaces):
    """語の列 → [(語 (候補の組のこともある), 元の位置のタプル)]。複合後置詞 (के लिए) は1語にまとめる"""
    import itertools
    out = []
    i = 0
    while i < len(surfaces):
        for n in (3, 2):
            window = surfaces[i:i + n]
            if len(window) < n:
                continue
            combo = next((c for c in itertools.product(*[_alts(t) for t in window])
                          if tuple(script.key(t) for t in c) in COMPOUND_KEYS), None)
            if combo:
                out.append((' '.join(combo), tuple(range(i, i + n))))
                i += n
                break
        else:
            out.append((surfaces[i], (i,)))
            i += 1
    return out


def sentences(text):
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


# ----------------------------------------------------------------------
# 読みの選択

def _compound_postposition(token):
    key = tuple(script.key(t) for t in token.split())
    for k, (roman, ja) in morphology.COMPOUND_POSTPOSITIONS.items():
        if tuple(script.key(w) for w in k) == key:
            return {'surface': token, 'pos': 'postposition', 'base': roman, 'ja': ja, 'gloss_lang': 'ja',
                    'roman': roman, 'compact': True, 'postposition': token, 'compound_postposition': True}
    return None


def _items(token):
    """語 (候補の組でもよい) → 項目のリスト。候補の組なら、どの形から来たかを 'dev' に"""
    out = []
    for k, alt in enumerate(_alts(token)):
        if ' ' in alt:
            found = _compound_postposition(alt)
            if found:
                out.append(dict(found, dev=alt))
                continue
        out += [dict(i, dev=alt, alt_rank=k) for i in morphology.analyses(alt)]
    return out


def _keys(token):
    return {script.key(t) for t in _alts(token)} if token is not None else set()


def _is_postposition(token):
    return token is not None and any(i['pos'] == 'postposition' for i in _items(token))


def _is_verbal_helper(token):
    return token is not None and any(i['pos'] == 'verb' and i.get('lemma') in HELPERS for i in _items(token))


def choose_items(surfaces):
    """語ごとに1つの項目を選ぶ"""
    out = []
    for i, token in enumerate(surfaces):
        if not isinstance(token, tuple) and token in PUNCTUATION:
            out.append(None)
            continue
        items = _items(token)
        nxt = surfaces[i + 1] if i + 1 < len(surfaces) else None
        prev_item = out[-1] if out else None
        before_postposition = _is_postposition(nxt)
        nxt_punct = nxt is not None and not isinstance(nxt, tuple) and nxt in PUNCTUATION
        verbal_position = nxt is None or nxt_punct or _is_verbal_helper(nxt) or \
            _keys(nxt) & {'और', 'कि', 'तो', 'लेकिन', 'पर'} and not before_postposition

        has_verb = any(i['pos'] == 'verb' for i in items)
        before_helper = nxt is not None and any(i['pos'] == 'verb' and i.get('lemma') in STEM_HELPERS
                                                for i in _items(nxt))

        def score(item):
            s = 0.97 ** item.get('alt_rank', 0)  # 候補の組では先の候補を少し先に (ウルドゥー語の入口)
            if item.get('unknown'):
                return 0.0
            if item['pos'] == 'conj' and item.get('dev') in ('या', 'और', 'तथा') and i == 0:
                s *= 0.3  # 文頭の「または・と」は無い (ウルドゥー語の یہ は यह で या でない)
            if item['pos'] == 'postposition' and (prev_item is None or prev_item['pos'] not in ('noun', 'pronoun', 'adj')):
                s *= 0.1  # 前に名詞の無い後置詞は無い (文頭の میں は मैं「私」で में「〜で」でない)
            if item['pos'] == 'verb' and item.get('form') == 'infinitive' and item.get('lemma') != script.key(item['dev']) \
                    and not before_postposition:
                s *= 0.3  # 女性・複数の不定詞 (पानी を पाना の不定詞と読まない)
            if item.get('lemma') in morphology.GLOSSES and item['pos'] != 'verb':
                s *= 1.25 if item['pos'] == 'noun' else 1.2  # 手で訳語を決めた基本語 (हिंदी「ヒンディー語」は名詞を先に)
            if item['pos'] in ('adv', 'conj', 'postposition') or item.get('possessive'):
                s *= 1.3  # 機能語の表の読み (कल「昨日・明日」、बहुत「とても」) を辞書の形容詞より先に
            if item['pos'] == 'postposition' and has_verb and (_is_verbal_helper(nxt) or verbal_position and nxt_punct):
                s *= 0.2  # की・के の後ろが助動詞・文末なら करना の完了分詞 (स्थापित की गई「設置された」)
            if item['pos'] == 'verb' and item.get('form') == 'stem' and before_helper:
                s *= 3  # रहा・सकता などの前は語幹 (पी रही है「飲んでいる」)
            if item['pos'] == 'verb':
                kind = item.get('form')
                if before_postposition and kind != 'infinitive':
                    s *= 0.2
                if verbal_position:
                    s *= 1.5
                if kind == 'stem' and not _is_verbal_helper(nxt):
                    s *= 0.3
                if kind == 'conjunctive':
                    s *= 0.4
                if prev_item is not None and prev_item['pos'] == 'verb' and item.get('lemma') in HELPERS:
                    s *= 2
            elif item['pos'] in ('noun', 'adj', 'pronoun'):
                cases = {c[0] for c in item.get('_') or []}
                if before_postposition:
                    s *= 1.5 if 'Obl' in cases else 0.3
                elif cases == {'Obl'}:
                    s *= 0.5
                if item.get('proper'):
                    s *= 0.9
                if item['pos'] == 'adj' and nxt is not None and not before_postposition and \
                        any(i['pos'] == 'noun' and not i.get('unknown') for i in _items(nxt)):
                    s *= 1.1  # 名詞の前の形容詞
            return s
        best = max(items, key=score)
        if best['pos'] in ('noun', 'adj', 'pronoun') and best.get('_'):
            if before_postposition and any(c[0] == 'Obl' for c in best['_']):
                best['_'] = [c for c in best['_'] if c[0] == 'Obl']
            elif not before_postposition and any(c[0] != 'Obl' for c in best['_']) and best['pos'] != 'adj':
                best['_'] = [c for c in best['_'] if c[0] != 'Obl']  # 形容詞は後ろの名詞に合わせる (पिछले साल में)
        out.append(best)
    return out


def _item(word):
    return word.items[0] if isinstance(word, Word) and word.items else None


def _pos(word):
    item = _item(word)
    return item.pos if item is not None else None


def _restrict(word, cases):
    for item in word.items or []:
        if item._:
            kept = [c for c in item._ if c[0] in cases]
            if kept:
                item._ = kept


def _recase(word, case):
    """斜格の読みを別の格に読み替える (ने の前の名詞 → 主格、का の前 → 属格)"""
    item = _item(word)
    if item is None or not item._:
        return
    source = [c for c in item._ if c[0] == 'Obl'] or [c for c in item._ if c[0] in ('Nom', 'Acc', 'Dat')]
    new = [(case,) + tuple(c[1:]) for c in source]  # 後置詞の前は斜格の読みだけ (लड़के ने は単数)
    item._ = list(dict.fromkeys(new)) or item._


def mark_demonstratives(words):
    """यह / वह (इस / उस) のすぐ後ろが名詞なら指示の形容詞「この / その」(यह किताब「この本」)"""
    for i, word in enumerate(words[:-1]):
        item, nxt = _item(word), _item(words[i + 1])
        if item is None or item.pos != 'pronoun' or script.key(word.surface) not in \
                {script.key(w) for w in DEMONSTRATIVE_PRONOUNS} or nxt is None or nxt.pos not in ('noun', 'adj'):
            continue
        if item.attrib('pronoun_case') == 'direct' and i + 2 < len(words) and _pos(words[i + 2]) == 'postposition':
            continue  # वह घर में है「彼は家にいる」(指示の形容詞なら斜格の उस घर में)
        ja = next(v for w, v in DEMONSTRATIVE_PRONOUNS.items() if script.key(w) == script.key(word.surface))[0]
        cases = {c[0] for c in item._ or []}
        if cases == {'Obl'}:
            # 斜格の指示詞 (इस, उस) の後ろの名詞も斜格 (इस साल「今年」、इस बार「今回」。後置詞が無ければ時の副詞)
            noun = words[i + 1]
            _recase(noun, 'Obl')
        cngs = [(c, n, g) for c in cases for n in ('sg', 'pl') for g in ('m', 'f')]
        word.items = [type(item)(dict(item.item, pos='adj', ja=ja, demonstrative=True, _=cngs))]


def mark_indefinite(words):
    """एक「一つの、ある」が名詞 (間に形容詞があってもよい) の前にあれば、不定の印として名詞に付ける (訳には出さない)"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or script.key(word.surface) != script.key('एक'):
            continue
        j = i + 1
        while j < len(words) and _pos(words[j]) == 'adj':
            j += 1
        if j < len(words) and _pos(words[j]) == 'noun':
            word.items = [type(item)(dict(item.item, pos='article', ja=' ※不定の ek「ある〜、一つの〜」', gloss_lang='ja'))]
            words[j].add_modifier(word)


def mark_possessive_postpositions(words):
    """所有の形容詞 + 名詞由来の後置詞 (मेरे पास「私のところに」、उसके लिए「彼のために」): 所有の形容詞を代名詞の斜格に、
    後ろの語を後置詞にする"""
    for i, word in enumerate(words[:-1]):
        item, nxt = _item(word), words[i + 1]
        key = script.key(nxt.surface)
        if item is None or not item.attrib('possessive') or key not in {script.key(w) for w in NOUN_POSTPOSITIONS}:
            continue
        ja = next(v for w, v in NOUN_POSTPOSITIONS.items() if script.key(w) == key)
        oblique = (item.attrib('lemma') or '')[:-1] + 'े'  # 後置詞の前は -e の形 (मेरे पास)
        word.items = [type(item)(dict(item.item, pos='pronoun', ja=item.ja.rstrip('の').split(',')[0],
                                      roman=script.translit(oblique), _=[('Obl', 'sg', 'm'), ('Obl', 'sg', 'f')]))]
        nitem = _item(nxt)
        data = {'surface': nxt.surface, 'pos': 'postposition', 'base': script.translit(nxt.surface), 'ja': ja,
                'gloss_lang': 'ja', 'roman': script.translit(nxt.surface), 'compact': True,
                'postposition': nxt.surface}
        nxt.items = [type(item)(data)] if nitem is None else [type(nitem)(data)]


# ----------------------------------------------------------------------
# 動詞の並び

def merge_verb_groups(words):
    """本動詞 + 補助動詞・助動詞を1つの動詞にまとめる"""
    out = []
    i = 0
    while i < len(words):
        item = _item(words[i])
        if item is None or item.pos != 'verb':
            out.append(words[i])
            i += 1
            continue
        group = [words[i]]
        j = i + 1
        negation = None
        while j < len(words):
            nitem = _item(words[j])
            if nitem is not None and nitem.pos == 'verb' and nitem.attrib('lemma') in HELPERS:
                group.append(words[j])
                j += 1
            elif nitem is not None and words[j].surface in morphology.NEGATIONS and j + 1 < len(words) and \
                    _item(words[j + 1]) is not None and _item(words[j + 1]).attrib('lemma') in HELPERS:
                negation = words[j]  # पढ़ नहीं सकता: 否定は動詞の並びの前へ
                j += 1
            else:
                break
        if negation is not None:
            out.append(negation)
        out.append(_merge(group) if len(group) > 1 else _single(group[0]))
        i = j
    return out


def _single(word):
    """1語の動詞: 未完了分詞だけ (否定の नहीं पढ़ता) は現在、完了分詞は過去"""
    item = _item(word)
    kind = item.attrib('form')
    if kind == 'habitual':
        item.item['tense'] = 'present'
    return word


def _merge(group):
    main = _item(group[0])
    helpers = [_item(w) for w in group[1:]]
    aux = helpers[-1] if helpers[-1].attrib('lemma') == 'होना' and helpers[-1].attrib('form') in ('present', 'past',
                                                                                                  'subjunctive', 'future') else None
    data = dict(main.item)
    kind = main.attrib('form')
    lemmas = [h.attrib('lemma') for h in helpers]
    aux_tense = aux.attrib('form') if aux is not None else None
    ja = main.ja
    form = kind
    if 'रहना' in lemmas and kind == 'stem':
        tense = 'imperfect' if aux_tense == 'past' else 'progressive'
        form = '進行 (語幹 + rahnā)'
    elif 'सकना' in lemmas and kind == 'stem':
        ja = main.ja.split(',')[0] + 'ことができる'
        sak = helpers[lemmas.index('सकना')]
        tense = {'perfective': 'perfect', 'future': 'future'}.get(sak.attrib('form'), 'present')
        if aux_tense == 'past':
            tense = 'imperfect'
        form = '可能 (語幹 + saknā)'
    elif 'चुकना' in lemmas and kind == 'stem':
        tense = 'perfect'
        form = '完了 (語幹 + cuknā「〜し終えた」)'
    elif kind == 'perfective' and 'जाना' in lemmas:
        ja_form = helpers[lemmas.index('जाना')].attrib('form')
        data['voice'] = 'passive'
        tense = {'perfective': 'perfect', 'future': 'future', 'habitual': 'present'}.get(ja_form, 'present')
        if aux_tense == 'past':
            tense = 'imperfect' if ja_form == 'habitual' else 'pluperfect'
        form = '受動 (完了分詞 + jānā)'
    elif kind == 'stem' and any(l in VECTORS for l in lemmas):
        vector = helpers[next(k for k, l in enumerate(lemmas) if l in VECTORS)]
        vform = vector.attrib('form')
        tense = {'perfective': 'perfect', 'future': 'future', 'habitual': 'present', 'imperative': 'present',
                 'subjunctive': 'present'}.get(vform, 'present')
        if vform == 'imperative':
            data['mood'] = 'imperative'
        if aux_tense == 'past':
            tense = 'imperfect' if vform == 'habitual' else 'pluperfect'
        form = '複合動詞 (語幹 + %s)' % vector.attrib('lemma')
    elif kind == 'infinitive' and ('होना' in lemmas or 'चाहना' in lemmas):
        ja = main.ja.split(',')[0] + ('べきだ' if 'चाहना' in lemmas else 'なければならない')
        tense = 'imperfect' if aux_tense == 'past' else 'present'
        form = '義務 (不定詞 + %s)' % ('cāhie' if 'चाहना' in lemmas else 'honā')
    elif kind == 'habitual':
        tense = 'imperfect' if aux_tense == 'past' else 'present'
        form = '習慣 (未完了分詞 + honā)'
    elif kind == 'perfective':
        tense = 'pluperfect' if aux_tense == 'past' else 'perfect'
        form = '完了 (完了分詞 + honā)'
    else:
        tense = data.get('tense', 'present')
    data.update(tense=tense, ja=ja, form=form, surface=' '.join(w.surface for w in group),
                roman=' '.join(_item(w).attrib('roman') or w.surface for w in group), mood=data.get('mood') if
                data.get('mood') == 'imperative' else 'indicative', merged=True)
    last = helpers[-1]
    if aux is not None:
        data.update(person=aux.attrib('person'), number=aux.attrib('number') or data.get('number'),
                    persons=aux.attrib('persons'))
    elif last.attrib('persons'):
        data.update(person=last.attrib('person'), persons=last.attrib('persons'))  # 未来・接続法の補助動詞
    else:
        data['persons'] = []  # 分詞で終わる並び (नहीं बोल सकता): 人称は分からない
    data.update(number=last.attrib('number') or data.get('number'), gender=last.attrib('gender') or data.get('gender'))
    word = Word(data['surface'], [data])
    word.token_ix = group[0].token_ix
    word.token_ixs = tuple(i for w in group for i in (getattr(w, 'token_ixs', None) or (w.token_ix,)))
    return word


# ----------------------------------------------------------------------
# 後置詞

def mark_postpositions(words):
    """後置詞の働き: ने → 主語、को → 目的語・与格、का/की/के → 属格、ほかは後置詞句 (名詞句の前に移す)"""
    out = list(words)
    for word in list(out):
        item = _item(word)
        if item is None or item.pos != 'postposition':
            continue
        i = out.index(word)
        head = out[i - 1] if i > 0 else None
        if head is None or _pos(head) not in ('noun', 'pronoun', 'adj'):
            continue
        post = script.key(item.attrib('postposition') or word.surface)
        # 名詞句の中の形容詞 (後置詞の前の名詞に掛かるもの) も斜格に
        k = i - 2
        while k >= 0 and _pos(out[k]) == 'adj':
            _restrict(out[k], ('Obl',))
            k -= 1
        if post == script.key('ने'):
            _recase(head, 'Nom')
            head.ergative = True
            _make_marker(word, head)
        elif post == script.key('को'):
            _recase(head, 'Acc')
            head.ko = True
            _make_marker(word, head)
        elif post in (script.key('का'), script.key('की'), script.key('के')):
            _recase(head, 'Gen')
            _make_marker(word, head)
        else:
            # 後置詞句: 名詞句の頭 (前の形容詞・属格の句) まで戻り、その前に後置詞を移す
            start = i - 1
            while start > 0 and _np_continues(out[start - 1]):
                start -= 1
            _restrict(head, ('Obl',))
            data = dict(item.item, pos='preposition', dominates='Obl')
            word.items = [type(item)(data)]
            out.remove(word)
            out.insert(start, word)
    return out


def _np_continues(word):
    """名詞句の中の前の語か (形容詞・所有の形容詞・属格の名詞・属格の後置詞)"""
    item = _item(word)
    if item is None:
        return False
    if item.pos == 'adj':
        return True
    if item.pos == 'article':
        return True
    if item.pos in ('noun', 'pronoun') and item._ and all(c[0] == 'Gen' for c in item._):
        return True
    return False


def _make_marker(word, head):
    item = _item(word)
    word.items = [type(item)(dict(item.item, pos='article'))]
    head.add_modifier(word)


# ----------------------------------------------------------------------
# 主語・目的語

def _finite(item):
    return item is not None and item.pos == 'verb' and item.attrib('mood') in ('indicative', 'imperative')


def choose_subject(words):
    start = 0
    for i, word in enumerate(words):
        item = _item(word)
        if word.items is None or (item is not None and item.pos == 'conj' and word.surface not in HINDI.and_words):
            start = i + 1
            continue
        if not _finite(item):
            continue
        clause = [w for w in words[start:i] if _pos(w) in ('noun', 'pronoun')]
        start = i + 1
        direct = [w for w in clause if not getattr(w, 'ergative', False) and not getattr(w, 'ko', False) and
                  _item(w)._ and any(c[0] in ('Nom', 'Acc') for c in _item(w)._)]
        ergative = [w for w in clause if getattr(w, 'ergative', False)]
        dative = [w for w in clause if getattr(w, 'ko', False) or (_item(w).attrib('pronoun_case') == 'dative')]
        copula = HINDI.is_copula(item.attrib('pres1sg'))
        subject = ergative[0] if ergative else None
        transitive_perfective = not ergative and item.attrib('tense') in ('perfect', 'pluperfect') and \
            item.attrib('voice') != 'passive' and _transitive(item.attrib('lemma'))
        if transitive_perfective:
            subject = None  # 完了形の他動詞で ने の句が無い: 主語は省かれていて、直格の名詞句は目的語 (動詞はこれに一致)
        elif subject is None:
            person, number, gender = item.attrib('person'), item.attrib('number'), item.attrib('gender')

            def agrees(w):
                it = _item(w)
                if it.pos == 'pronoun' and it.attrib('person') is not None:
                    if not item.attrib('persons'):
                        return True  # 人称の分からない分詞で終わる動詞 (नहीं बोलता, नहीं बोल सकता)
                    return it.attrib('person') == person
                return any(c[0] == 'Nom' and (number is None or c[1] == number) and (gender is None or c[2] == gender)
                           for c in it._)
            subject = next((w for w in direct if agrees(w)), direct[0] if direct and (copula or not dative) else None)
        for w in direct:
            if w is subject:
                _restrict(w, ('Nom',))
            elif copula:
                _restrict(w, ('Nom',))
            elif item.attrib('lemma') in MOTION_VERBS and _pos(w) == 'noun':
                _recase(w, 'Dat')  # 移動の動詞の、後置詞の無い行き先 (स्कूल जाता हूँ「学校に行く」)
            else:
                _restrict(w, ('Acc',))
        # 動詞の直前の名詞は複合動詞の一部 (स्नान कराना「沐浴させる」) とみなし、को の句を与格にする目的語に数えない
        light = item.attrib('lemma') in LIGHT_VERBS
        has_object = any(w is not subject and not (light and words.index(w) == i - 1) for w in direct) and not copula
        for w in dative:
            if w is subject:
                continue
            if has_object or item.attrib('lemma') in DATIVE_VERBS or copula:
                _restrict_or_recase(w, 'Dat')
            else:
                _restrict_or_recase(w, 'Acc')


def _transitive(lemma):
    return any(e.get('transitivity') in ('transitive', 'ambitransitive') for e in dictionary.lemmas(lemma or '')
               if e['pos'] == 'verb')


def _restrict_or_recase(word, case):
    it = _item(word)
    if any(c[0] == case for c in it._ or []):
        _restrict(word, (case,))
    else:
        _recase(word, case)


# ----------------------------------------------------------------------

def lookup_all(surfaces):
    grouped = group_tokens(surfaces)
    items = choose_items([g for g, _ in grouped])
    words = []
    for (token, ixs), item in zip(grouped, items):
        if item is not None:
            token = item.get('dev', token)  # 候補の組から選んだデーヴァナーガリーの形
        word = Word(token, None if item is None else [item])
        word.token_ix = ixs[0]
        if len(ixs) > 1:
            word.token_ixs = ixs
        words.append(word)
    mark_demonstratives(words)
    mark_indefinite(words)
    mark_possessive_postpositions(words)
    words = merge_verb_groups(words)
    words = mark_postpositions(words)
    choose_subject(words)
    for i, word in enumerate(words):
        word.index = i
    return words


def sentence_text(surfaces, romans=None):
    """(文, 転写の文)。romans は語ごとの転写 (辞書の語は Wiktionary の転写から。無ければ規則で)"""
    text, latin = '', ''
    for k, s in enumerate(surfaces):
        if s in PUNCTUATION:
            text += s
            latin += '.' if s in '।॥' else s
        else:
            text += (' ' if text else '') + s
            latin += (' ' if latin else '') + ((romans or {}).get(k) or script.translit(s))
    return text, latin


def _romans(words):
    """元の語の位置 → 選んだ読みの転写"""
    out = {}
    for word in words:
        item = _item(word)
        ixs = getattr(word, 'token_ixs', None) or (getattr(word, 'token_ix', None),)
        if item is None or ixs[0] is None:
            continue
        parts = (item.attrib('roman') or '').split()
        if len(parts) == len(ixs):
            out.update(zip(ixs, parts))
        elif len(ixs) == 1:
            out[ixs[0]] = item.attrib('roman')
    return out


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(HINDI):
        analysis = common.analyze_words([w.surface for w in words], words, word_details, [])
    analysis.forms_text = sentence_text(surfaces, _romans(words))
    return analysis


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
