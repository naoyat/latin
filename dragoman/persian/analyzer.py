#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語の文の解析
#
# 語を規則で解析し (persian/morphology.py)、読みを文脈で選んでから、並列・係り先・前置詞句・格の枠・日本語訳を
# 共通の解析器 (core/analyzer.py) をペルシア語の設定 (PERSIAN) で使う:
#   - 動詞は文 (節) の終わりに来る (主語-目的語-動詞)。節の終わりの語は動詞の読みを先にする
#   - 複数語の動詞をまとめる: 未来 (خواهم رفت xâham raft「行くだろう」)、受動 (نوشته شد nevešte šod「書かれた」)、
#     複合動詞 (名詞 + 軽動詞: کار کردن kâr kardan「働く」。Wiktionary にあるもの)
#   - را (râ) の前の名詞句は目的語 (対格)
#   - エザーフェ (-e。文字には書かれない): 名詞 + 形容詞は修飾 (ketâb-e xub「良い本」)、名詞 + 名詞は属格
#     (ketâb-e Ali「アリの本」)。見出しの行の転写に -e / -ye を補う
#   - 主語は動詞の前の、目的語・属格・前置詞の目的語でない最初の名詞類。代名詞の主語は省かれる (動詞の人称語尾から)
#   - 名詞 + 形容詞 + 繋辞 (است ast) の文は、形容詞を述語にする (این کتاب خوب است「この本は良い」)
#
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.core.Word import Word
from . import dictionary, morphology, script

PUNCTUATION = {'.': 'period', '!': 'period', '?': 'question', '؟': 'question', '،': 'comma', ',': 'comma',
               '؛': 'comma', ';': 'comma', ':': 'comma', '«': None, '»': None, '"': None, '(': 'comma', ')': 'comma',
               '-': 'comma', '–': 'comma', '—': 'comma'}
TOKEN = re.compile('[ء-غف-يً-ٰٟپچژکگیۀ'
                   'آ‌]+|[0-9۰-۹٠-٩]+|[.!?؟،,؛;:«»"()\\-–—]')
LIGHT_VERBS = {script.key(w) for w in ('کردن', 'شدن', 'دادن', 'زدن', 'داشتن', 'گرفتن', 'خوردن', 'آمدن', 'کشیدن',
                                       'آوردن', 'رفتن', 'گشتن', 'ساختن', 'نمودن', 'یافتن', 'گذاشتن', 'بردن')}


class KeySet(frozenset):
    """正規化したキーで比べる集合"""
    def __new__(cls, words):
        return super().__new__(cls, {script.key(w) for w in words})

    def __contains__(self, word):
        return isinstance(word, str) and super().__contains__(script.key(word))


def _root_items(lemma):
    return [{'pos': 'verb', 'ja': l['ja'], 'gloss_lang': l['gloss_lang']}
            for l in dictionary.lemmas(lemma) if l['pos'] == 'verb']


def predicative_adjective(adj, noun):
    """エザーフェで結ばれていない形容詞は名詞に掛けない (述語: این کتاب خوب است「この本は良い」)"""
    if not isinstance(adj, Word) or not isinstance(noun, Word) or not adj.items or not noun.items:
        return False
    if adj.items[0].attrib('demonstrative'):
        return getattr(adj, 'index', 0) > getattr(noun, 'index', 0)  # 指示詞は後ろの名詞にだけ (این کتاب)
    if getattr(adj, 'index', 0) < getattr(noun, 'index', 0):
        # 名詞の前に置く語 (数量詞・最上級・序数: هر کس「誰でも」、اولین بار「初めて」) だけ後ろの名詞に掛ける
        return not prenominal(adj.items[0])
    return not getattr(adj, 'ezafe_from', None) is noun and not getattr(noun, 'ezafe_from', None) is adj


PRENOMINAL = {script.key(w) for w in ('هر', 'هیچ', 'چند', 'همه', 'همهٔ', 'چه', 'کدام', 'بعضی', 'برخی', 'تمام', 'کل',
                                      'فلان', 'چندین', 'نخستین', 'آخرین', 'اولین', 'دومین', 'سومین', 'بیشترین')}


def prenominal(item):
    """名詞の前に置く形容詞類か (数量詞、-in の最上級・序数 بزرگترین, اولین)"""
    lemma = script.key(item.attrib('lemma') or item.surface or '')
    return lemma in PRENOMINAL or script.key(item.surface or '') in PRENOMINAL or \
        (item.attrib('roman') or '').endswith(('tarin', 'omin', 'in')) and lemma.endswith('ین')


AND = 'و'
PERSIAN = language.Language(
    name='fa',
    and_words=(AND,),
    or_words=('یا',),
    copulas=KeySet({morphology.COPULA}),
    negations=KeySet({'نه'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の'},
    absolute_case=None,
    lookup=_root_items,
    predicative_adjective=predicative_adjective,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_follows_head=True,
    possessor_cases=(),
)


def tokens(text):
    """語の列。離して書いた می / نمی は後ろの動詞に付ける (می روم → می‌روم)"""
    out = []
    for token in TOKEN.findall(script.normalize(text)):
        if out and script.key(out[-1]) in ('می', 'نمی'):
            out[-1] = out[-1] + script.ZWNJ + token
            continue
        out.append(token)
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

def _is_boundary(token):
    return token is None or token in PUNCTUATION or script.key(token) in ('و', 'که', 'اما', 'ولی', 'تا', 'اگر', 'چون')


def choose_analyses(surfaces):
    """語ごとの解析を選ぶ: 節の終わり (句読点・接続詞の前) の語は動詞の読みを先に、それ以外は名詞類を先に"""
    out = []
    for i, token in enumerate(surfaces):
        if token in PUNCTUATION:
            out.append(None)
            continue
        cands = morphology.analyses(token)
        nxt = surfaces[i + 1] if i + 1 < len(surfaces) else None
        final = _is_boundary(nxt)
        nxt_verbal = nxt is not None and any(a.kind in ('verb', 'copula') and a.score >= 0.9
                                             for a in morphology.analyses(nxt)) if nxt not in PUNCTUATION and nxt else False

        def score(a):
            s = a.score
            if a.kind == 'verb':
                item = a.main
                if final:
                    s *= 1.5
                elif not item.get('prefix') and not item.get('negative') and not item.get('participle'):
                    s *= 0.6  # 節の途中の接頭辞の無い過去形 (کرد) は名詞の読みもある
                if item.get('participle') and nxt is not None and script.key(nxt)[:2] in ('شد', 'شو', 'بو', 'می', 'نش', 'نم'):
                    s = s * 2 + 0.5  # 過去分詞 + شد (受動) / بود (過去完了)
            elif a.kind == 'nominal' and final and len(a.segments) == 1:
                s *= 0.8
            return s
        out.append(max(cands, key=score))
    return prefer_adjectives(surfaces, out)


def _main_pos(analysis):
    return analysis.main.get('pos') if analysis is not None and analysis.kind == 'nominal' else None


def prefer_adjectives(surfaces, chosen):
    """名詞の後ろの語は形容詞の読みを先にする (میراث فرهنگی: farhangi「文化の」で、farhang + 不定の -i ではない。
    خودکار قرمز: 「赤いペン」)。点数の近い (0.35 以内) 形容詞の読みがあれば取り替える"""
    for i in range(1, len(chosen)):
        prev, cur = chosen[i - 1], chosen[i]
        if cur is None or cur.kind != 'nominal' or _main_pos(prev) != 'noun' or _main_pos(cur) == 'adj':
            continue
        if len(prev.segments) > 1:
            continue  # 人称の接語の付いた名詞の後ろ (پدرم) にはエザーフェが付かない
        if (i == 1 or _is_boundary(surfaces[i - 2])) and i + 1 < len(surfaces) and \
                script.key(surfaces[i + 1]) == 'را' and _main_pos(cur) == 'noun':
            continue  # 節の頭の名詞 + 名詞 + را: 主語 + 目的語 (دانشجویان فارسی را می‌خوانند)
        adjs = [a for a in morphology.analyses(surfaces[i]) if _main_pos(a) == 'adj'
                and not a.main.get('demonstrative') and a.score >= cur.score - 0.35
                and not (cur.main.get('proper') and a.main.get('gloss_lang') != 'ja' and not a.main.get('relational'))]
        if adjs:
            chosen[i] = max(adjs, key=lambda a: a.score)
    # 名詞と形容詞のどちらにも読める語が、形容詞の前にあれば名詞に (خودکار قرمز の خودکار)
    for i in range(len(chosen) - 1):
        cur, nxt = chosen[i], chosen[i + 1]
        if cur is None or _main_pos(cur) != 'adj' or _main_pos(nxt) != 'adj' or cur.main.get('demonstrative'):
            continue
        if i > 0 and _main_pos(chosen[i - 1]) == 'noun':
            continue
        nouns = [a for a in morphology.analyses(surfaces[i]) if _main_pos(a) == 'noun' and a.score >= cur.score - 0.35]
        if nouns:
            chosen[i] = max(nouns, key=lambda a: a.score)
    return chosen


def _words(token, analysis, ix):
    if token in PUNCTUATION or analysis is None:
        word = Word(token, None)
        word.token_ix = ix
        return [word]
    out = []
    for surface, item in analysis.segments:
        word = Word(surface, [dict(item)])
        word.token_ix = ix
        word.original = token
        out.append(word)
    return out


def _item(word):
    return word.items[0] if isinstance(word, Word) and word.items else None


def _pos(word):
    item = _item(word)
    return item.pos if item is not None else None


def _nominal(word):
    return _pos(word) in ('noun', 'pronoun', 'adj')


def _restrict(word, cases):
    for item in word.items or []:
        if item._:
            kept = [c for c in item._ if c[0] in cases]
            if kept:
                item._ = kept


def _rebuild(word, **changes):
    item = _item(word)
    data = dict(item.item, **changes)
    word.items = [type(item)(data)]
    return word.items[0]


# ----------------------------------------------------------------------
# 複数語の動詞

def merge_verbs(words):
    """未来 (خواهم رفت)、受動 (نوشته شد)、過去完了 (رفته بود)、複合動詞 (کار کرد) を1語の動詞にまとめる"""
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        item = _item(word)
        nxt = words[i + 1] if i + 1 < len(words) else None
        nitem = _item(nxt) if nxt is not None else None
        # 未来: خواستن の現在形 (接頭辞なし) + 過去語幹 (人称語尾なし)
        if item is not None and item.pos == 'verb' and script.key(item.attrib('lemma') or '') == script.key('خواستن') \
                and not item.attrib('prefix') and nxt is not None:
            stem = _past_stem_verb(nxt.surface)
            if stem is not None:
                merged = dict(stem, surface=word.surface + ' ' + nxt.surface, person=item.attrib('person'),
                              number=item.attrib('number'), tense='future', mood='indicative',
                              roman=item.attrib('roman') + ' ' + stem['roman'],
                              form='未来 (xâstan の現在形 + 過去語幹)', negative=item.attrib('negative'))
                out.append(_merged(word, nxt, merged))
                i += 2
                continue
        # 過去分詞 + شدن (受動) / بودن (過去完了)
        if item is not None and item.attrib('participle') and nitem is not None and nitem.pos == 'verb':
            aux = script.key(nitem.attrib('lemma') or '')
            if aux in (script.key('شدن'), script.key(morphology.COPULA)):
                passive = aux == script.key('شدن')
                merged = dict(item.item, surface=word.surface + ' ' + nxt.surface, person=nitem.attrib('person'),
                              number=nitem.attrib('number'), roman=item.attrib('roman') + ' ' + nitem.attrib('roman'),
                              negative=nitem.attrib('negative'), participle=False)
                if passive:
                    merged.update(voice='passive', tense=nitem.attrib('tense'), mood=nitem.attrib('mood'),
                                  form='受動 (過去分詞 + šodan)')
                else:
                    merged.update(tense='pluperfect' if nitem.attrib('tense') != 'present' else 'perfect',
                                  form='過去完了 (過去分詞 + budan)')
                out.append(_merged(word, nxt, merged))
                i += 2
                continue
        # 複合動詞: 名詞・形容詞 + 軽動詞 (Wiktionary に「X kardan」があるもの)
        if item is not None and item.pos in ('noun', 'adj') and nitem is not None and nitem.pos == 'verb' and \
                script.key(nitem.attrib('lemma') or '') in LIGHT_VERBS and not item.attrib('suffix'):
            compound = [e for e in dictionary.lemmas(item.attrib('lemma', '') + ' ' + nitem.attrib('lemma', ''))
                        if e['pos'] == 'verb']
            if compound:
                entry = compound[0]
                ja, gloss_lang = morphology._gloss(entry)
                merged = dict(nitem.item, surface=word.surface + ' ' + nxt.surface, ja=ja, gloss_lang=gloss_lang,
                              base='%s %s' % (entry.get('roman') or '', script.isolate(entry['word'])),
                              lemma=entry['word'], pres1sg=entry['word'],
                              roman=item.attrib('roman') + ' ' + nitem.attrib('roman'), compound=True,
                              light_verb=nitem.attrib('lemma'))
                out.append(_merged(word, nxt, merged))
                i += 2
                continue
        out.append(word)
        i += 1
    return out


def _merged(first, second, item):
    word = Word(item['surface'], [item])
    word.token_ix = first.token_ix
    word.token_ixs = (first.token_ix, second.token_ix)
    return word


def _past_stem_verb(token):
    """人称語尾の無い過去語幹 (未来の رفت) の動詞の項目"""
    for a in morphology.verb_analyses(script.normalize(token)):
        item = a.main
        if item.get('stem_kind') == 'past' and item.get('person') == 3 and item.get('number') == 'sg' and \
                not item.get('prefix') and not item.get('participle') and item.get('tense') == 'perfect':
            return item
    return None


# ----------------------------------------------------------------------
# 名詞句

def mark_ezafe(words):
    """エザーフェで名詞句をつなぐ: 名詞 + 形容詞 (修飾)、名詞 + 名詞・代名詞 (属格「〜の」)。
    つないだ語には ezafe_from (前の語) を書き、前の語の転写に -e / -ye を付ける"""
    for i in range(len(words) - 1):
        word, nxt = words[i], words[i + 1]
        item, nitem = _item(word), _item(nxt)
        if item is None or nitem is None or item.pos not in ('noun', 'adj') or item.attrib('suffix'):
            continue
        if item.attrib('proper') or item.attrib('demonstrative') or nitem.attrib('suffix') or \
                nitem.pos == 'verb':
            continue
        if item.attrib('indefinite') and not item.attrib('ezafe_written'):
            continue  # 不定の -i の後ろにはエザーフェが付かない (ふつう)
        # 次の語の後ろの語 (述語の形容詞の判定)
        after = words[i + 2] if i + 2 < len(words) else None
        aitem = _item(after)
        if nitem.pos == 'adj' and not nitem.attrib('demonstrative'):
            # 名詞 + 形容詞 + 繋辞 (節の終わり) は述語「〜は…だ」
            if aitem is not None and aitem.pos == 'verb' and PERSIAN.is_copula(aitem.attrib('pres1sg')) and \
                    not item.attrib('ezafe_written'):
                continue
            if item.pos == 'adj' and not getattr(word, 'ezafe_from', None):
                continue  # 形容詞 + 形容詞 は前の形容詞が名詞に掛かっているときだけ
            nxt.ezafe_from = word
            _set_ezafe(word)
        elif nitem.pos in ('noun', 'pronoun') and item.pos == 'noun':
            # 名詞 + 名詞: 後ろの名詞が節の終わりの動詞の直前の目的語 (مرد کتاب خرید) のこともあるが、属格を先に
            if aitem is not None and aitem.pos == 'verb' and i == 0 and not item.attrib('ezafe_written') and \
                    nitem.pos == 'noun' and not nitem.attrib('proper'):
                continue  # 文頭の名詞 + 名詞 + 動詞: 主語 + 目的語
            if aitem is not None and aitem.pos == 'verb' and script.key(aitem.attrib('lemma') or '') in LIGHT_VERBS \
                    and not item.attrib('ezafe_written'):
                continue  # 名詞 + 名詞 + 軽動詞: 後ろの名詞は複合動詞の一部 (نقش ایفا کرد)
            if _clause_initial(words, i) and not item.attrib('ezafe_written') and _np_before_ra(words, i + 1):
                continue  # 節の頭の名詞 + را の付いた名詞句: 主語 + 目的語 (ملت تلاش زیادی را آغاز کرد)
            nxt.ezafe_from = word
            _set_ezafe(word)
            _restrict(nxt, ('Gen',))
            item.item['construct_with'] = ('noun', nxt.surface, (nitem.ja or '').split(',')[0])


def _clause_initial(words, i):
    return i == 0 or words[i - 1].items is None or _pos(words[i - 1]) == 'conj'


def _np_before_ra(words, j):
    """j の語から名詞句 (名詞・形容詞・数) が続いて را で終わるか"""
    for k in range(j, min(j + 5, len(words))):
        item = _item(words[k])
        if item is None:
            return False
        if item.pos == 'postposition':
            return True
        if item.pos not in ('noun', 'adj', 'pronoun'):
            return False
    return False


def _set_ezafe(word):
    item = _item(word)
    if item.attrib('ezafe'):
        return
    roman = item.attrib('roman') or ''
    suffix = '-ye' if roman[-1:] in 'aeiouâ' or item.attrib('ezafe_written') else '-e'
    item.item.update(ezafe=True, roman=roman + suffix)


def mark_suffixes(words):
    """人称の接語: 名詞の後ろは属格「〜の」(所有)、動詞・前置詞の後ろは対格"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('suffix') or i == 0:
            continue
        host = _item(words[i - 1])
        if host is not None and host.pos in ('noun', 'adj'):
            _restrict(word, ('Gen',))
            host.item['construct_with'] = ('suffix', word.surface, item.ja)


def mark_prepositions(words):
    """前置詞の目的語 (すぐ後ろの名詞類。指示詞・前に置く形容詞の後ろの名詞も) を属格に。前置詞の目的語でも
    エザーフェの後ろでもない名詞類からは属格の読みを除く (前置詞句が後ろの目的語まで取り込まないように:
    به او ناهار بدهید「彼に昼食を与えよ」)"""
    governed = set()
    for i, word in enumerate(words):
        if _pos(word) != 'preposition':
            continue
        for j in range(i + 1, min(i + 4, len(words))):
            nxt = words[j]
            if not _nominal(nxt):
                break
            governed.add(id(nxt))
            if _pos(nxt) in ('noun', 'pronoun') and not _item(nxt).attrib('demonstrative'):
                break
    for word in words:
        item = _item(word)
        if item is None or item.pos not in ('noun', 'pronoun') or item.attrib('suffix'):
            continue
        if id(word) in governed:
            _restrict(word, ('Gen',))
        elif getattr(word, 'ezafe_from', None) is None:
            _restrict(word, ('Nom', 'Acc'))


def mark_ra(words):
    """را の前の名詞句 (エザーフェでつながった句の頭の名詞) を対格に。را は頭の名詞の修飾語にして訳に出さない"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or item.pos != 'postposition':
            continue
        j = i - 1
        while j >= 0 and words[j].items is not None and (
                getattr(words[j], 'ezafe_from', None) is not None or _item(words[j]) is not None and
                _item(words[j]).attrib('suffix')):
            j = (words.index(words[j].ezafe_from) if getattr(words[j], 'ezafe_from', None) is not None else j - 1)
        if j < 0 or not _nominal(words[j]):
            continue
        head = words[j]
        if _pos(head) == 'adj' and _item(head).attrib('demonstrative') and j + 1 < i:
            head = words[j + 1]
        _restrict(head, ('Acc',))
        _rebuild(word, pos='article')
        head.add_modifier(word)
        head.ra = True


def mark_demonstratives(words):
    """این / آن: 後ろが名詞なら「この / その」、そうでなければ代名詞「これ / それ」"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('demonstrative'):
            continue
        nxt = _item(words[i + 1]) if i + 1 < len(words) else None
        if nxt is None or nxt.pos not in ('noun', 'adj') or nxt.attrib('suffix'):
            _rebuild(word, pos='pronoun', ja=item.attrib('ja_pronoun') or item.ja, demonstrative=False)


def split_copula_clitics(words):
    """名詞類 + 繋辞の接語 (خوبم xub-am「私は良い」) は、接語を繋辞の動詞として残す (形はすでに別の語)"""
    return words


# ----------------------------------------------------------------------
# 主語

def _finite(item):
    return item is not None and item.pos == 'verb' and item.attrib('mood') in ('indicative', 'imperative') \
        and not item.attrib('participle')


def _free_nominals(words, fr, to):
    """前置詞の目的語・属格・را の付いた語・接語を除いた名詞類の位置"""
    out = []
    after_preposition = False
    for i in range(fr, to):
        word = words[i]
        item = _item(word)
        if item is None:
            after_preposition = False
            continue
        if item.pos == 'preposition':
            after_preposition = True
            continue
        if item.pos in ('noun', 'pronoun') and not item.attrib('suffix'):
            if not after_preposition and getattr(word, 'ezafe_from', None) is None and not getattr(word, 'ra', False):
                out.append(i)
            after_preposition = False
        elif item.pos not in ('adj', 'article'):
            after_preposition = False
    return out


def choose_subject(words):
    """各動詞の節 (前の動詞・句読点・接続詞の後ろから動詞まで) で主語を決める:
    動詞の人称と合う代名詞、3人称なら最初の名詞類を主格に。残りの名詞類は目的語 (را の無い不定の目的語)。
    繋辞の文では残りは補語 (主格のまま)"""
    start = 0
    for i, word in enumerate(words):
        item = _item(word)
        if word.items is None or (item is not None and item.pos == 'conj' and word.surface != AND):
            start = i + 1
            continue
        if not _finite(item):
            continue
        free = _free_nominals(words, start, i)
        start = i + 1
        if not free:
            continue
        person, number = item.attrib('person'), item.attrib('number')
        copula = PERSIAN.is_copula(item.attrib('pres1sg'))
        subject = None
        for j in free:
            fitem = _item(words[j])
            if fitem.pos == 'pronoun' and fitem.attrib('person') is not None:
                if fitem.attrib('person') == person:
                    subject = j
                    break
                continue
            if person == 3:
                subject = j
                break
        for j in free:
            if j == subject:
                _restrict(words[j], ('Nom',))
            elif not copula:
                _restrict(words[j], ('Acc',))
            else:
                _restrict(words[j], ('Nom',))


# ----------------------------------------------------------------------

def lookup_all(surfaces):
    analyses = choose_analyses(surfaces)
    words = [w for ix, (s, a) in enumerate(zip(surfaces, analyses)) for w in _words(s, a, ix)]
    words = merge_verbs(words)
    mark_suffixes(words)
    mark_demonstratives(words)
    mark_ezafe(words)
    mark_prepositions(words)
    mark_ra(words)
    choose_subject(words)
    for i, word in enumerate(words):
        word.index = i
    return words


def sentence_forms(words):
    """元の語ごとの (表記, 転写)。エザーフェの -e、接語は転写に付ける"""
    out = []
    current, roman, ix = None, '', None
    for word in words:
        ixs = getattr(word, 'token_ixs', None) or (getattr(word, 'token_ix', None),)
        if word.items is None:
            if current is not None:
                out.append((current, roman))
            out.append((word.surface, word.surface))
            current, roman, ix = None, '', None
            continue
        item = _item(word)
        r = item.attrib('roman') if item is not None else word.surface
        if ixs[0] != ix or current is None:
            if current is not None:
                out.append((current, roman))
            current, roman = getattr(word, 'original', word.surface), r or ''
        else:
            roman += r or ''
        ix = ixs[-1]
        if len(ixs) > 1:
            current = word.surface
    if current is not None:
        out.append((current, roman))
    return out


def sentence_text(forms):
    """(文, 転写の文)。句読点は前の語に付ける"""
    text, latin = '', ''
    for form, roman in forms:
        if form in PUNCTUATION:
            text += form
            latin += {'،': ',', '؟': '?', '؛': ';'}.get(form, form)
        else:
            text += (' ' if text else '') + form
            latin += (' ' if latin else '') + roman
    return text, latin


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(PERSIAN):
        analysis = common.analyze_words([w.surface for w in words], words, word_details, [])
    analysis.forms = sentence_forms(words)
    return analysis


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
