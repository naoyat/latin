#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語の文の解析
#
# 語を解析し (tagalog/morphology.py)、名詞句の標識と動詞の焦点から格を決めてから、並列・係り先・格の枠・日本語訳は
# 共通の解析器 (core/analyzer.py) をタガログ語の設定 (TAGALOG) で使う:
#   - 名詞句の標識: ang / si (焦点)、ng / ni (焦点でない中心の参与者)、sa / kay (場所・受け手: 「に」「で」)。
#     代名詞は形で決まる (ako / ko / akin)。標識の語は訳に出さない
#   - 動詞の焦点 (接辞) で ang と ng の役割が決まる:
#       行為者焦点 (-um-, mag-)  ang = 動作主 (主格)、ng = 対象 (対格)   Bumili ang lalaki ng isda「男は魚を買った」
#       対象焦点 (-in, i-, ma-)  ang = 対象 (対格)、ng = 動作主 (主格)   Binili ng lalaki ang isda「魚は男が買った」
#       場所焦点 (-an)           ang = 場所・受け手 (与格)、ng = 動作主・対象
#     焦点の名詞 (ang) は日本語では主題「は」にする (Language.particle)
#   - 名詞の後ろの ng 名詞句・ng の代名詞は所有 (bahay ng lalaki「男の家」、bahay ko「私の家」)
#   - 繋ぎ (na / -ng) でつながった形容詞は名詞に掛ける (magandang bahay「美しい家」)。名詞 + 繋ぎ + 動詞は関係節
#     (lalaking bumili ng isda「魚を買った男」)
#   - ay の倒置 (Ang bata ay kumain「子供は食べた」)、動詞の無い文 (Maganda ang bahay「家は美しい」) には見えない繋辞
#
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.core.Word import Word
from . import dictionary, morphology, script

PUNCTUATION = {'.': 'period', '!': 'period', '?': 'question', ',': 'comma', ';': 'comma', ':': 'comma',
               '"': None, '“': None, '”': None, '(': 'comma', ')': 'comma', '–': 'comma', '—': 'comma'}
TOKEN = re.compile(r"[A-Za-zÀ-ÿñÑ']+(?:-[A-Za-zÀ-ÿñÑ']+)*|[0-9]+(?:[.,][0-9]+)*|[.!?,;:\"“”()–—]")
FOCUS_PARTICLES = {'Nom': 'は', 'Acc': 'は', 'Dat': 'には'}


def particle(case, obj, pred):
    """焦点の名詞 (ang) は主題「は」"""
    if isinstance(obj, Word) and getattr(obj, 'focus', False):
        return FOCUS_PARTICLES.get(case)
    return None


def predicative_adjective(adj, noun):
    """繋ぎ (na / -ng) でつながった形容詞だけを名詞に掛ける。ほかは述語 (Maganda ang bahay)"""
    if not isinstance(adj, Word) or not isinstance(noun, Word):
        return False
    return getattr(adj, 'linked_to', None) is not noun


def _root_items(lemma):
    return []


TAGALOG = language.Language(
    name='tl',
    and_words=('at',),
    or_words=('o',),
    copulas=frozenset({'ay'}),
    negations=frozenset({'hindi', 'huwag', 'di', "'di"}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の', 'Dat': 'に'},
    absolute_case=None,
    lookup=_root_items,
    particle=particle,
    predicative_adjective=predicative_adjective,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_follows_head=True,
    objects_follow_verb=True,
    possessor_cases=(),
)

COPULA = {'pos': 'verb', 'pres1sg': 'ay', 'lemma': 'ay', 'base': '(繋辞なし)', 'ja': 'である', 'gloss_lang': 'ja',
          'voice': 'active', 'mood': 'indicative', 'tense': 'present', 'person': None, 'number': None,
          'copula': True, 'surface': '(ay)'}


def tokens(text):
    return TOKEN.findall(text)


def sentences(text):
    current = []
    for token in tokens(text):
        current.append(token)
        if PUNCTUATION.get(token) in ('period', 'question'):
            yield current
            current = []
    if current:
        yield current


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


def _rebuild(word, **changes):
    item = _item(word)
    word.items = [type(item)(dict(item.item, **changes))]
    return word.items[0]


# ----------------------------------------------------------------------
# 語

def _choose(items, prev, first):
    """読みの選択: 標識・繋ぎ・形容詞の後ろは名詞類、文頭・否定の後ろは動詞を先に"""
    def score(item):
        s = 0
        if prev in ('marker', 'plural', 'linker', 'adj') and item['pos'] in ('noun', 'adj', 'pronoun'):
            s -= 2
        if (first or prev in ('negation', 'enclitic', 'ay')) and item['pos'] == 'verb':
            s -= 1
        if item.get('unknown'):
            s += 5
        return s
    return sorted(items, key=score)


def _words(surfaces):
    out = []
    prev = None
    for ix, token in enumerate(surfaces):
        if token in PUNCTUATION:
            word = Word(token, None)
            word.token_ix = ix
            out.append(word)
            prev = None
            continue
        key = script.key(token)
        items, linker = morphology.analyze(key)
        first = not [w for w in out if w.items is not None]
        items = _choose(items, prev, first)
        word = Word(token, [dict(items[0], surface=token)])
        word.alternatives = items[1:]
        word.token_ix = ix
        word.linker = linker
        out.append(word)
        item = items[0]
        prev = ('negation' if item.get('negation') else 'linker' if linker else item['pos'])
    return out


def mark_linkers(words):
    """繋ぎ: 単独の na (名詞類と名詞類・動詞の間) と、語に付いた -ng。形容詞は繋ぎの向こうの名詞に掛ける。
    名詞 + 繋ぎ + 動詞は関係節の印 (relative)。単独の na は除く"""
    out = []
    for i, word in enumerate(words):
        item = _item(word)
        prev = out[-1] if out else None
        nxt = words[i + 1] if i + 1 < len(words) else None
        if item is not None and word.surface.lower() == 'na' and prev is not None and _pos(prev) in ('noun', 'adj', 'pronoun') \
                and nxt is not None and _pos(nxt) in ('noun', 'adj', 'verb'):
            prev.linker = True  # 単独の繋ぎ na (bahay na maganda)
            continue
        out.append(word)
    for i, word in enumerate(out[:-1]):
        if not getattr(word, 'linker', False):
            continue
        nxt = out[i + 1]
        if _pos(word) == 'adj' and _pos(nxt) == 'noun':
            word.linked_to = nxt                    # magandang bahay
        elif _pos(word) == 'noun' and _pos(nxt) == 'adj':
            nxt.linked_to = word                    # bahay na maganda
        elif _pos(word) in ('noun', 'pronoun') and _pos(nxt) == 'verb':
            nxt.relative_head = word                # lalaking bumili …
        elif _pos(word) == 'pronoun' and _item(word).attrib('marker') == 'sa' and _pos(nxt) == 'noun':
            # aking bahay「私の家」(sa の代名詞 + 繋ぎ + 名詞)
            _rebuild(word, pos='noun', _=[('Gen', 'sg', morphology.GENDER)], possessor=True)
    return out


def mark_phrases(words):
    """標識の後ろの名詞句の語に標識の種類 (ang / ng / sa) を付ける。標識の語は句の頭の名詞の修飾語 (訳に出さない) か、
    sa / kay は前置詞 (に)。代名詞は自分の形の標識"""
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        item = _item(word)
        if item is None or item.pos != 'marker':
            if item is not None and item.pos == 'pronoun':
                word.marker = item.attrib('marker')
            out.append(word)
            i += 1
            continue
        kind = item.attrib('marker')
        j = i + 1
        phrase = []
        while j < len(words) and _pos(words[j]) in ('noun', 'adj', 'plural', 'pronoun') and \
                not (_pos(words[j]) == 'pronoun' and phrase):
            phrase.append(words[j])
            j += 1
            if phrase and _pos(phrase[-1]) in ('noun', 'pronoun') and not getattr(phrase[-1], 'linker', False) and \
                    not (j < len(words) and getattr(words[j], 'linked_to', None) is not None):
                break
        heads = [w for w in phrase if _pos(w) in ('noun', 'pronoun')] or [w for w in phrase if _pos(w) == 'adj']
        if not heads:
            i += 1
            continue
        for w in phrase:
            w.marker = kind
            if item.attrib('plural') or any(_pos(p) == 'plural' for p in phrase):
                for it in w.items:
                    if it._:
                        it._ = [(c, 'pl', g) for c, n, g in it._]
        head = heads[-1]
        if kind == 'sa':
            prep = Word(word.surface, [dict(item.item, pos='preposition', ja='に', dominates='Gen')])
            prep.token_ix = word.token_ix
            prep.marker = 'sa'
            out.append(prep)
            for w in phrase:
                _restrict(w, ('Gen',))
        else:
            article = Word(word.surface, [dict(item.item, pos='article')])
            article.token_ix = word.token_ix
            head.add_modifier(article)
        out += [w for w in phrase if _pos(w) != 'plural']
        i = j
    return out


def mark_possessors(words):
    """所有: 名詞の後ろの ng の代名詞 (bahay ko「私の家」)、ng / sa の名詞句の中の名詞の後ろの ng 名詞句
    (sa bahay ng lalaki「男の家で」)、動詞の無い節の名詞の後ろの ng 名詞句 (Maganda ang bahay ng lalaki)。
    動詞の節の ang 名詞句の後ろの ng 名詞句 (Bumili ang lalaki ng isda) は動詞の補語"""
    has_verb = any(_pos(w) == 'verb' for w in words)
    for i, word in enumerate(words):
        if getattr(word, 'marker', None) != 'ng' or i == 0 or _pos(word) not in ('noun', 'pronoun'):
            continue
        prev = words[i - 1]
        if _pos(prev) == 'article':
            continue
        if _pos(prev) != 'noun' or getattr(prev, 'is_possessor', False):
            continue
        pronoun = _pos(word) == 'pronoun' and getattr(word, 'phrase_start', True)
        nested = getattr(prev, 'marker', None) in ('ng', 'sa')
        if pronoun or nested or not has_verb:
            _rebuild(word, pos='noun', _=[('Gen', 'sg', morphology.GENDER)])
            word.is_possessor = True
            word.marker = 'gen'


def mark_relatives(words):
    """名詞 + 繋ぎ + 動詞 (+ 補語): 連体節にして名詞の訳語に付ける (lalaking bumili ng isda → 魚を買った男、
    isdang binili ng lalaki → 男が買った魚)。節の語は除く"""
    from dragoman.core import en_ja
    from dragoman.kobun.modernize import Modern
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        head = getattr(word, 'relative_head', None)
        item = _item(word)
        if head is None or item is None or item.pos != 'verb':
            out.append(word)
            i += 1
            continue
        verb = (item.ja or '').split(',')[0]
        if item.attrib('gloss_lang') == 'en' or re.search('[a-z]', verb):
            verb = (en_ja.translate(item.ja or '', 'verb') or verb).split(',')[0]
        if item.attrib('aspect') == 'completive':
            try:
                verb = Modern.past_form(verb)
            except Exception:
                pass
        elif item.attrib('aspect') == 'progressive':
            try:
                verb = Modern.te(verb) + 'いる'
            except Exception:
                pass
        j = i + 1
        parts = []
        focus = item.attrib('focus')
        while j < len(words) and getattr(words[j], 'marker', None) in ('ng', 'sa') and words[j].items:
            w = words[j]
            if _pos(w) == 'preposition':
                j += 1
                continue
            ja = (_item(w).ja or '').split(',')[0]
            if _item(w).attrib('gloss_lang') == 'en' or re.search('[a-z]', ja):
                ja = (en_ja.translate(_item(w).ja or '', 'noun') or ja).split(',')[0]
            if w.marker == 'sa':
                parts.append(ja + 'に')
            else:
                parts.append(ja + ('を' if focus == 'actor' else 'が'))
            j += 1
        hitem = _item(head)
        hja = (hitem.ja or '').split(',')[0]
        head.items = [type(hitem)(dict(hitem.item, ja=''.join(parts) + verb + hja, gloss_lang='ja',
                                       relative=word.surface))]
        i = j
    return out


def assign_cases(words):
    """節 (動詞から次の動詞・接続詞・句読点まで、前の ay の句を含む) ごとに、焦点から ang / ng の格を決める"""
    clauses, current = [], []
    for word in words + [None]:
        if word is None or word.items is None or _pos(word) == 'conj':
            clauses.append(current)
            current = []
        else:
            current.append(word)
    for clause in clauses:
        verbs = [w for w in clause if _pos(w) == 'verb']
        verb = _item(verbs[0]) if verbs else None
        focus = verb.attrib('focus') if verb is not None else None
        angs = [w for w in clause if getattr(w, 'marker', None) == 'ang' and _pos(w) in ('noun', 'pronoun')]
        ngs = [w for w in clause if getattr(w, 'marker', None) == 'ng' and _pos(w) in ('noun', 'pronoun')]
        if verb is None or verb.attrib('copula'):
            for w in angs:
                _restrict(w, ('Nom',))
                w.focus = True
            continue
        if focus in ('object', 'conveyance'):
            ang_case, ng_cases = 'Acc', ['Nom', 'Nom']
        elif focus == 'locative':
            ang_case, ng_cases = 'Dat', ['Nom', 'Acc']
        elif focus == 'existential':
            ang_case, ng_cases = 'Nom', ['Nom', 'Acc']
        else:
            ang_case, ng_cases = 'Nom', ['Acc', 'Acc']
        for w in angs:
            _restrict(w, (ang_case,))
            w.focus = True
        heads = [w for w in ngs]
        for k, w in enumerate(heads):
            _restrict(w, (ng_cases[min(k, 1)],))
        # 標識の無い名詞 (may の後ろなど) は主格
        if focus == 'existential':
            for w in clause:
                if _pos(w) == 'noun' and getattr(w, 'marker', None) is None:
                    _restrict(w, ('Nom',))


def handle_ay(words):
    """ay の倒置: ay を除く (前の句が主題、後ろが述語)。後ろが名詞類・形容詞だけなら見えない繋辞を補う"""
    out = []
    for i, word in enumerate(words):
        if _pos(word) != 'ay':
            out.append(word)
            continue
        rest = words[i + 1:]
        if not any(_pos(w) == 'verb' for w in rest[:4]):
            copula = Word('(ay)', [dict(COPULA)])
            copula.token_ix = word.token_ix
            out.append(copula)
    return out


def supply_copula(words):
    """動詞の無い節: 述語 (形容詞・名詞) + ang 名詞句 (Maganda ang bahay、Guro si Juan) なら、述語の後ろに繋辞を補う"""
    if any(_pos(w) == 'verb' for w in words):
        return words
    content = [w for w in words if w.items is not None and _pos(w) not in ('enclitic', 'adv')]
    if len(content) >= 2 and getattr(content[0], 'marker', None) is None and _pos(content[0]) in ('adj', 'noun') and \
            any(getattr(w, 'marker', None) == 'ang' for w in content[1:]):
        k = words.index(content[0]) + 1
        copula = Word('(ay)', [dict(COPULA)])
        copula.token_ix = content[0].token_ix
        _restrict(content[0], ('Nom',))
        return words[:k] + [copula] + words[k:]
    return words


def drop_enclitics(words):
    """丁寧の po / ho、疑問の ba などの小辞: 丁寧・疑問は訳に出さない。ほかは副詞 (na「もう」、din「〜も」)"""
    out = []
    for word in words:
        item = _item(word)
        if item is not None and item.pos == 'enclitic':
            if item.attrib('enclitic') in ('polite', 'question') or not item.ja:
                continue
            _rebuild(word, pos='adv')
        out.append(word)
    return out


def lookup_all(surfaces):
    words = _words(surfaces)
    words = mark_linkers(words)
    words = mark_phrases(words)
    mark_possessors(words)
    words = mark_relatives(words)
    words = drop_enclitics(words)
    words = handle_ay(words)
    words = supply_copula(words)
    for i, word in enumerate(words):
        word.index = i
    assign_cases(words)
    return words


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(TAGALOG):
        return common.analyze_words([w.surface for w in words], words, word_details, [])


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
