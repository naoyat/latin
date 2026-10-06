#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 複合語 (samāsa) の分解
#
#   rAjaputraH  → rāja + putraḥ       (前の語は語幹、最後の語だけが格変化する)
#   nIlotpalam  → nīla + utpalam      (a + u → o の連声を戻す)
#   mahAbAhuH   → mahat + bāhuḥ       (mahat は複合語の前では mahā)
#
# 前の語は Vidyut の kosha の語幹 (prātipadika) の一覧にあるもの、最後の語は kosha で格変化形として引けるもの。
# 語の境目の連声は Vidyut の連声の規則 (sandhi/rules.csv: 前の語の末尾, 後ろの語の頭, 結果) を逆にたどって戻す
#
import csv
import functools
import os

from . import dictionary

MAX_MEMBERS = 5
MIN_MEMBER = 2  # 1文字の語幹 (a「否定」を除く) は分けすぎになりやすい

# 複合語の前で形が変わる語幹 (後ろに付く形 → 語幹)
COMPOUND_FORMS = {'mahA': 'mahat', 'a': 'a', 'an': 'a', 'sa': 'sa', 'su': 'su', 'dur': 'dus', 'duz': 'dus',
                  'nir': 'nis', 'niz': 'nis'}

# 格語尾と同じ形の語 (mahākavi-byas と分けない)
ENDINGS = {'Byas', 'Bis', 'Byam', 'ByAm', 'syas', 'sya', 'nAm', 'Am', 'os', 'zu', 'su', 'ena', 'Aya', 'At'}

_stems = None
_rules = None


def stems():
    """kosha の語幹 (派生でない基本の語幹) の集合 (SLP1)"""
    global _stems
    if _stems is None:
        from .morphology import _get_kosha
        _stems = {p.pratipadika.text for p in _get_kosha().pratipadikas() if hasattr(p, 'pratipadika')}
    return _stems


def rules():
    """連声の結果 (空白を除いた形) → [(前の語の末尾, 後ろの語の頭)]"""
    global _rules
    if _rules is None:
        _rules = {}
        path = os.path.join(dictionary.VIDYUT_DATA, 'sandhi', 'rules.csv')
        with open(path, encoding='utf-8') as fp:
            for row in csv.DictReader(fp):
                result = row['result'].replace(' ', '')
                _rules.setdefault(result, []).append((row['first'], row['second']))
    return _rules


# 語末の子音の形 (pada の形) → 語幹の末尾の子音の候補 (vaṇik ← vaṇij, tad → tat / tan)
FINAL_CONSONANTS = {'k': 'cjSzh', 'g': 'cjSzhk', 'w': 'zSq', 'q': 'zSw', 't': 'dDT', 'd': 'tDT', 'n': 'td',
                    'p': 'bB', 'b': 'pB', 'N': 'k', 'M': 'm'}
PRONOUN_FORMS = {'mat': 'asmad', 'mad': 'asmad', 'asmat': 'asmad', 'asmad': 'asmad', 'tvat': 'yuzmad',
                 'tvad': 'yuzmad', 'yuzmat': 'yuzmad', 'yuzmad': 'yuzmad'}


# 動詞の接頭辞 (upasarga)。anu-cita, abhi-mata, sam-bhoga は派生語なので複合語の語として分けない
UPASARGAS = {'pra', 'parA', 'apa', 'sam', 'anu', 'ava', 'nis', 'nir', 'dus', 'dur', 'vi', 'AN', 'A', 'ni', 'aDi',
             'api', 'ati', 'su', 'ud', 'aBi', 'prati', 'pari', 'upa', 'saM', 'ut', 'ava'}


def _stem_of(member, first=False):
    """前の語の形 → 語幹 (無ければ None)。first: 複合語の最初の語 (否定の a- は最初だけ)"""
    if member in ('a', 'an'):
        return 'a' if first else None
    if member in UPASARGAS and member not in ('su',):
        return None
    if member in COMPOUND_FORMS:
        return COMPOUND_FORMS[member]
    if member in PRONOUN_FORMS:
        return PRONOUN_FORMS[member]
    if len(member) < MIN_MEMBER:
        return None
    if member in stems() or _is_participle_stem(member):
        return member
    for c in FINAL_CONSONANTS.get(member[-1], ''):
        if member[:-1] + c in stems():
            return member[:-1] + c
    return None


@functools.lru_cache(maxsize=65536)
def _is_participle_stem(member):
    """kosha の基本の語幹に無い分詞の語幹 (labdha, paricita, kalita)。中性単数主格 -m の形を kosha で引いて確かめる"""
    if not member.endswith(('ta', 'na', 'Da', 'Ta', 'wa', 'qa')):
        return False
    from .morphology import _get_kosha
    return any(hasattr(e, 'pratipadika_entry') and hasattr(e.pratipadika_entry, 'krt')
               for e in _get_kosha().get(member + 'm'))


NASALS = {'k': 'N', 'K': 'N', 'g': 'N', 'G': 'N', 'c': 'Y', 'C': 'Y', 'j': 'Y', 'J': 'Y', 'w': 'R', 'W': 'R',
          'q': 'R', 'Q': 'R', 't': 'n', 'T': 'n', 'd': 'n', 'D': 'n', 'p': 'm', 'P': 'm', 'b': 'm', 'B': 'm'}


def normalize_anusvara(word):
    """語中の破裂音の前の ṃ を同じ調音位置の鼻音に (bhāṃḍa → bhāṇḍa, saṃjīvaka → sañjīvaka)"""
    return ''.join(NASALS.get(word[i + 1], 'M') if c == 'M' and i + 1 < len(word) else c
                   for i, c in enumerate(word))


def _joints(word):
    """前の語と後ろの残りに分ける候補 [(前の語, 後ろの残り)]。連声の無いもの (位置 i で切る) と、
    連声の結果 (nīl[o]tpala の o = a + u) を規則で戻したもの"""
    out = []
    for i in range(1, len(word)):
        out.append((word[:i], word[i:]))
        for length in (1, 2, 3):
            result = word[i:i + length]
            if len(result) < length:
                break
            for first, second in rules().get(result, ()):
                out.append((word[:i] + first, second + word[i + length:]))
    return list(dict.fromkeys(out))


@functools.lru_cache(maxsize=4096)
def split(word, final_lookup=None):
    """複合語 (SLP1) → 分け方の候補 [(語幹のタプル, 最後の語)]。良いものから。分けられなければ []"""
    from .morphology import lookup
    final_lookup = final_lookup or lookup
    results = []

    def walk(rest, members):
        if len(members) >= MAX_MEMBERS:
            return
        for left, right in _joints(rest):
            stem = _stem_of(left, first=not members)
            if stem is None or len(right) < MIN_MEMBER:
                continue
            key, items = final_lookup(right)
            if items:
                results.append((tuple(members + [stem]), key, _known(items)))
            walk(right, members + [stem])

    walk(word, [])
    if 'M' in word[:-1]:
        word = normalize_anusvara(word)
        walk(word, [])

    # 語の数が少なく、辞書 (Wiktionary) に訳語のある語の多いもの。同じなら前の語が長く (rāja-putra と rāj-aputra)、
    # 最後の語が短いもの (mahā-rāja の ā を前の語に含める) を先に
    def score(r):
        members, final, final_known = r
        unknown = sum(not _known_stem(m) for m in members) + (not final_known)
        short = len(final) < 4 or final in ENDINGS  # 語尾だけのような短い語 (-byas, -syas) は分けすぎ
        tiny = sum(len(m) <= 2 and m != 'su' for m in members)
        # 辞書に訳語の無い語幹 (kosha にだけある複合語 sarvaguṇa) は、訳語のある語幹 (sarva-guṇa) に分けたほうを
        return (unknown + short + tiny + len(members) / 2, len(members), -len(members[0]), len(final))
    return [(members, final) for members, final, _ in sorted(dict.fromkeys(results), key=score)]


def _known_stem(stem):
    """辞書 (Wiktionary) にある語幹か。-an の語幹は複合語の前で n が落ちる (rāja ← rājan)"""
    return bool(dictionary.lemmas(stem) or (stem.endswith(('a', 'i')) and dictionary.lemmas(stem + 'n')))


def _known(items):
    return any(item.get('ja') and item.get('ja') != item.get('base') for item in items)


# ----------------------------------------------------------------------
# 複合語の種類 (六合釈) と訳
#
#   依主釈 tatpuruṣa     rāja-putra「王の息子」        前の語が後ろの語に格の関係で掛かる (訳は「〜の」で代表させる)
#   持業釈 karmadhāraya  nīla-utpala「青い蓮」         前の語が後ろの語を形容する
#   帯数釈 dvigu         tri-loka「三つの世界」         前の語が数詞
#   相違釈 dvandva       rāma-lakṣmaṇau「ラーマとラクシュマナ」  並列 (語の数と双数・複数が合う)
#   有財釈 bahuvrīhi     pīta-ambaraḥ「黄色い衣を持つ (者)」   全体が形容詞として別の名詞に掛かる
#   隣近釈 avyayībhāva   yathā-śakti「力に応じて」     前の語が不変化詞で、全体が副詞
#
NUMERALS = {'eka': '一つの', 'dvi': '二つの', 'tri': '三つの', 'catur': '四つの', 'paYca': '五つの', 'paYcan': '五つの',
            'zaz': '六つの', 'sapta': '七つの', 'saptan': '七つの', 'azwa': '八つの', 'azwan': '八つの',
            'nava': '九つの', 'navan': '九つの', 'daSa': '十の', 'daSan': '十の', 'Sata': '百の', 'sahasra': '千の'}
AVYAYA_FIRST = {'yaTA': '〜に応じて', 'prati': '〜ごとに', 'upa': '〜の近くで', 'anu': '〜に従って',
                'yAvat': '〜の限り', 'sa': '〜とともに', 'aDi': '〜について'}
ADJECTIVE_FIRST = {'mahat': '偉大な', 'su': '良い', 'dus': '悪い', 'sarva': 'すべての', 'para': '最高の'}
LABELS = {'tatpurusa': '依主釈', 'karmadharaya': '持業釈', 'dvigu': '帯数釈', 'dvandva': '相違釈',
          'bahuvrihi': '有財釈', 'avyayibhava': '隣近釈', 'negation': '否定'}


def _short(gloss):
    return gloss.split(',')[0].strip() if gloss else gloss


def _member(stem):
    """語幹の (訳語, 品詞)。訳語は最初の1つ"""
    for key in (stem, stem + 'n') if stem.endswith(('a', 'i')) else (stem,):
        lemmas = [l for l in dictionary.lemmas(key) if l['pos'] != 'root']
        if lemmas:
            from .morphology import main_lemma
            # 前の語は形容詞としても読む (pīta「黄色い」-ambara)。語義の数が同じなら固有名詞、形容詞、名詞の順
            first = main_lemma(lemmas, order=('name', 'adj', 'noun', 'pronoun'))
            return _short(first['ja']), first['pos'], any(l['pos'] == 'adj' for l in lemmas)
    if _is_participle_stem(stem):
        return _iast(stem), 'participle', True
    return _iast(stem), 'noun', False


def _iast(slp1):
    from . import script
    return script.iast(slp1)


def _modify(adj, noun):
    """形容する語 + 名詞 (大きい神、{blue}蓮)"""
    if adj.endswith(('い', 'な', 'の', 'た', 'る')):
        return adj + noun
    if any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿' for c in adj):
        return adj + 'の' + noun
    return '{%s}%s' % (adj, noun)


def _lexical_genders(final_key, stem):
    """最後の語の語幹の本来の性 (kosha の語幹の性の一覧)"""
    from .morphology import _get_kosha, GENDERS
    genders = set()
    for e in _get_kosha().get(final_key):
        p = getattr(e, 'pratipadika_entry', None)
        if p is not None and hasattr(p, 'pratipadika') and p.pratipadika.text == stem:
            genders |= {GENDERS.get(str(l)) for l in (p.lingas or [])}
    return genders


def classify(members, final_items):
    """(種類, 前の語の情報のリスト)。種類は LABELS のキー"""
    infos = [_member(m) for m in members]
    first = members[0]
    final = final_items[0]
    numbers = {cng[1] for cng in final.get('_', [])}
    if first == 'a':
        return 'negation', infos
    if first in AVYAYA_FIRST and len(members) == 1:
        return 'avyayibhava', infos
    if first in NUMERALS:
        return 'dvigu', infos
    names = [i for i in infos if i[1] == 'name']
    parts = len(members) + 1
    # 2語の双数で固有名詞を含む (candra-ādityau「月と太陽」)、3語以上の複数ですべて名詞・固有名詞 (並べ挙げ)
    final_name = final.get('name', False)
    if ('du' in numbers and parts == 2 and (names or final_name)) or \
            ('pl' in numbers and parts > 2 and names and all(i[1] in ('name', 'noun') for i in infos)):
        return 'dvandva', infos
    if first in ADJECTIVE_FIRST or infos[0][1] in ('adj', 'participle'):
        return 'karmadharaya', infos
    return 'tatpurusa', infos


def gloss(kind, members, infos, final_gloss):
    words = [ADJECTIVE_FIRST.get(m) or i[0] for m, i in zip(members, infos)]
    head = _short(final_gloss)
    if kind == 'negation':
        rest = gloss(*_inner(members[1:], final_gloss)) if len(members) > 1 else head
        return '非' + rest if any('一' <= c <= '鿿' or '぀' <= c <= 'ヿ' for c in rest) \
            else 'not-' + rest
    if kind == 'avyayibhava':
        return AVYAYA_FIRST[members[0]].replace('〜', head)
    if kind == 'dvigu':
        return NUMERALS[members[0]] + (''.join(words[1:]) + 'の' if len(words) > 1 else '') + head
    if kind == 'dvandva':
        return 'と'.join(words + [head])
    if kind == 'karmadharaya':
        out = head
        for word in reversed(words):
            out = _modify(word, out)
        return out
    # 依主釈: A-B-C → AのBのC
    return 'の'.join(words + [head])


def _inner(members, final_gloss):
    kind, infos = classify(members, [{'_': []}])
    return kind, members, infos, final_gloss


def annotate(items):
    """辞書にある複合語 (rājaputra「王子」) の項目に、成り立ち (rāja-putra 依主釈) を書き添える"""
    from . import script
    for item in items:
        base = item.get('base') or ''
        if item['pos'] not in ('noun', 'adj') or ' ' in base or len(base) < 5:
            continue
        stem = script.to_slp1(base)
        candidates = split(stem + 'm') or split(stem + 's')  # 語幹そのものは変化形でないので、単数の形で分ける
        if not candidates:
            continue
        members, final = candidates[0]
        if not all(_known_stem(m) for m in members):
            continue
        kind, _ = classify(members, [item])
        if kind in ('tatpurusa', 'karmadharaya', 'dvigu', 'dvandva', 'negation'):
            from .morphology import lookup
            final_stem = next((i['base'] for i in lookup(final)[1] if i.get('base')), None)
            if final_stem:
                item['base'] = '%s = %s-%s %s' % (base, '-'.join(_iast(m) for m in members), final_stem, LABELS[kind])
    return items


def _a_stem_final(final, items):
    """複合語の最後で a で終わる語幹になる語 (mahā-rāja: rājan → rāja) は kosha に変化形が無いので、
    deva の変化形から類推して読む (rājaḥ → rāja 単数主格)"""
    from .morphology import analyze as analyze_form
    for n in range(len(final) - 1, 2, -1):
        stem = final[:n]
        if stem.endswith('a') and stem in stems() and not any(i.get('base') == _iast(stem) for i in items):
            analogues = [dict(i, base=_iast(stem), surface=_iast(final), ja=_member(stem)[0])
                         for i in analyze_form('deva' + final[n:]) if i.get('base') == 'deva']
            if analogues:
                return analogues + items
    return items


def analyze(word):
    """複合語 (SLP1) を分けて、辞書の項目のリストにする。分けられなければ []。
    項目の base は「語幹-語幹 種類」(rāja-putra 依主釈)、ja は合成した訳"""
    from .morphology import lookup
    candidates = split(word)
    if not candidates:
        return []
    members, final = candidates[0]
    _, items = lookup(final)
    items = _a_stem_final(final, items)
    nominal = [item for item in items if item['pos'] in ('noun', 'adj', 'participle', 'pronoun')]
    if not nominal:
        return []
    kind, infos = classify(members, nominal)
    out = []
    for item in nominal:
        stem = item['base']
        base = '-'.join(_iast(m) for m in members) + '-' + stem
        compound = dict(item, surface=_iast(word), base='%s %s' % (base, LABELS[kind]),
                        ja=gloss(kind, members, infos, item['ja']), compound=kind)
        if kind == 'avyayibhava':
            compound.update(pos='adv')
            compound.pop('_', None)
        out.append(compound)
        # 最後の語の本来の性と合わない (pīta-ambaraḥ: ambara は中性) か、隣の名詞に掛かれば有財釈
        if kind in ('tatpurusa', 'karmadharaya', 'dvigu') and item['pos'] == 'noun':
            from . import script
            lexical = _lexical_genders(final, script.to_slp1(stem))
            bahuvrihi = dict(compound, pos='adj', base='%s %s' % (base, LABELS['bahuvrihi']),
                             ja=compound['ja'] + 'を持つ', compound='bahuvrihi')
            genders = {cng[2] for cng in item.get('_', [])}
            if lexical and not genders & lexical:
                out.insert(len(out) - 1, bahuvrihi)
            else:
                out.append(bahuvrihi)
    return out
