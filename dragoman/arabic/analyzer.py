#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア語 (現代標準アラビア語) の文の解析
#
# 語を CAMeL Tools の解析で切れ目 (接続詞 wa-/fa-、前置詞 bi-/li-/ka-、本体、人称接尾辞) ごとの語に分け、
# 読みと格を文脈で絞ってから、並列・係り先・前置詞句・格の枠・日本語訳を共通の解析器 (core/analyzer.py) を
# アラビア語の設定 (ARABIC) で使う:
#   - 語の読み (見出し語・品詞) は曖昧性解消の点数に、前後の語の手がかりを掛けて選ぶ
#     (لم・لن・قد・سوف の後ろは動詞、前置詞の後ろは名詞、إن の後ろが名詞なら inna「実に」)
#   - 前置詞の後ろの名詞は属格。連語 (iḍāfa: 定冠詞の無い名詞 + 名詞) の後ろの名詞も属格「〜の」
#     (كِتابُ الوَلَدِ「少年の本」)。名詞の人称接尾辞は属格、動詞の人称接尾辞は対格
#   - 動詞文 (動詞-主語-目的語) の主語は、動詞の後ろの性の合う名詞。動詞が前にあれば、主語が複数でも
#     動詞は単数 (ذَهَبَ الطُّلّابُ「学生たちは行った」)
#   - 形容詞は定冠詞の有無が名詞と合うときだけ名詞に掛ける。合わなければ述語 (الوَلَدُ كَبِيرٌ「少年は大きい」)
#   - 動詞の無い文 (名詞文) には見えない繋辞を補う。inna とその姉妹 (إِنَّ) の後ろの名詞は主語、
#     لَيْسَ は否定の繋辞「〜でない」
#   - لَمْ + 未完了 (要求法) は過去の否定「〜しなかった」、لَنْ + 未完了 (接続法) は未来の否定「〜しないだろう」
#
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.core.Word import Word
from . import dictionary, morphology, script

PUNCTUATION = {'.': 'period', '!': 'period', '?': 'question', '؟': 'question', '،': 'comma', ',': 'comma',
               '؛': 'comma', ';': 'comma', ':': 'comma', '«': None, '»': None, '"': None, '(': 'comma', ')': 'comma',
               '-': 'comma', '–': 'comma', '—': 'comma'}
TOKEN = re.compile('[ء-غـ-ٰٟٱ]+|[0-9٠-٩]+|[.!?؟،,؛;:«»"()\\-–—]')


class BareSet(frozenset):
    """母音記号を除いた形で比べる集合 (لَمْ と لم を同じ語に)"""
    def __new__(cls, words):
        return super().__new__(cls, {script.bare(w) for w in words})

    def __contains__(self, word):
        return isinstance(word, str) and super().__contains__(script.bare(word))


def _root_items(lemma):
    return [{'pos': 'verb', 'ja': l['ja'], 'gloss_lang': l['gloss_lang']}
            for l in dictionary.lemmas(lemma) if l['pos'] == 'verb']


def _definite(word):
    """定まった名詞類か (定冠詞、固有名詞、人称接尾辞の付いた名詞、定まった名詞と連語になった名詞)"""
    if not isinstance(word, Word) or not word.items:
        return False
    item = word.items[0]
    return bool(item.attrib('definite')) or item.pos == 'pronoun'


def predicative_adjective(adj, noun):
    """定冠詞の有無が名詞と合わない形容詞は名詞に掛けない (述語: الوَلَدُ كَبِيرٌ「少年は大きい」)。
    指示詞は定まった名詞に掛かる (هٰذا الكِتابُ「この本」)"""
    if not isinstance(adj, Word) or not isinstance(noun, Word):
        return False
    if adj.items and adj.items[0].attrib('demonstrative'):
        return not _definite(noun)
    return _definite(adj) != _definite(noun)


AND = 'وَ'
ARABIC = language.Language(
    name='ar',
    and_words=(AND,),
    or_words=('أَوْ', 'أَو'),
    copulas=BareSet({'كان'}),
    negations=BareSet({'لا', 'لم', 'لن', 'ما', 'ليس', 'غير'}),
    vocative_particles=BareSet({'يا'}),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の', 'Voc': 'よ'},
    absolute_case=None,
    lookup=_root_items,
    predicative_adjective=predicative_adjective,
    dictionary=dictionary,
    pronoun_subject=True,
    genitive_follows_head=True,
    objects_follow_verb=True,
    possessor_cases=(),
)


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


# 語の読みを選ぶ文脈の手がかり (前の語の母音記号を除いた形 → 後ろの語の読みに掛ける点数の関数)
VERBAL_TRIGGERS = {'لم', 'لن', 'قد', 'سوف', 'لا', 'كي', 'لكي', 'حتى'}
NOMINAL_TRIGGERS = {'إن', 'أن', 'لأن', 'لكن', 'كأن', 'ليت', 'لعل'}
NOMINAL = {'noun', 'noun_prop', 'noun_num', 'noun_quant', 'adj', 'adj_comp', 'adj_num', 'pron', 'pron_dem'}


def _context_score(reading, prev, nxt):
    """前後の語の読みから、この読みに掛ける点数"""
    pos = reading.pos
    score = 1.0
    if prev is not None:
        prev_bare = script.bare(prev.main['diac']).replace('ٱ', 'ا')
        prev_pos = prev.pos
        if prev_bare in ('لم', 'لن', 'قد', 'سوف') or prev_pos == 'part_neg' and prev_bare in ('لم', 'لن'):
            score *= 4 if pos == 'verb' else 0.2
            if prev_bare == 'لم' and pos == 'verb' and reading.feature('asp') != 'i':
                score *= 0.2
        elif prev_bare in ('أن', 'كي', 'لكي') and prev.lex in ('أَنْ', 'أَن', 'كَي', 'كَيْ', 'لِكَي'):
            score *= 3 if pos == 'verb' and reading.feature('asp') == 'i' else 0.5
        elif prev_pos == 'prep' or prev.main.get('prc1') in ('bi_prep', 'li_prep', 'ka_prep') \
                and prev.pos not in NOMINAL | {'verb'}:
            score *= 2 if pos in NOMINAL - {'adj'} else 1 if pos == 'adj' else 0.3  # فِي العامِ「その年に」
        elif prev_pos == 'verb_pseudo':
            score *= 2 if pos in NOMINAL else 0.5
        elif prev_pos == 'pron' and prev.main.get('enc0') in (None, '0', 'na'):
            score *= 1.5 if pos in NOMINAL else 0.7  # هُوَ طالِبٌ「彼は学生だ」
    if morphology.is_function_word(reading):
        score *= 2  # 前置詞・機能語の読み (عِنْدَ「〜のところに」、أَيْنَ「どこに」) を先に
    if pos == 'noun_prop':
        score *= 0.5  # 固有名詞は、ほかの読みが近い点数なら使わない (أَبِيهِ「彼の父」を人名 Abbe に読まない)
    if pos == 'verb' and nxt is not None and (prev is None or prev.pos in ('conj', 'punc')
                                               or prev.main.get('prc2') in ('wa_conj', 'fa_conj')) \
            and nxt.main.get('prc0') == 'Al_det':
        score *= 2  # 節の頭の動詞 + 定冠詞付きの名詞 (أَكَلَ الوَلَدُ「少年は食べた」)
    if nxt is not None and pos in ('conj_sub', 'verb_pseudo'):
        bare = script.bare(reading.main['diac'])
        nxt_nominal = nxt.pos in NOMINAL and nxt.main.get('prc0') == 'Al_det' or nxt.pos in ('pron', 'noun_prop')
        if bare in ('إن', 'أن', 'لأن', 'لكن'):
            # إن / أن の後ろが名詞なら inna / anna (後ろが動詞なら in「もし」/ an「〜すること」)
            if reading.lex in ('إِنَّ', 'أَنَّ') or pos == 'verb_pseudo':
                score *= 3 if nxt_nominal else 0.5
            elif nxt.pos == 'verb':
                score *= 2
    return score


def choose_readings(surfaces):
    """語ごとの読み (Reading) を選ぶ。前の語の読みが決まってから次の語を選ぶ (2回まわして後ろの語も見る)"""
    candidates = [morphology.readings(s) if s not in PUNCTUATION else [] for s in surfaces]
    chosen = [c[0] if c else None for c in candidates]
    for _ in range(2):
        for i, cands in enumerate(candidates):
            if len(cands) < 2:
                continue
            prev = chosen[i - 1] if i > 0 else None
            nxt = chosen[i + 1] if i + 1 < len(chosen) else None
            chosen[i] = max(cands, key=lambda r: r.score * _context_score(r, prev, nxt))
    return chosen


def _words(token, reading, ix):
    if token in PUNCTUATION:
        word = Word(token, None)
        word.token_ix = ix
        return [word]
    if reading is None:
        word = Word(token, [])
        word.token_ix = ix
        return [word]
    out = []
    for surface, item in morphology.segments(reading):
        if item.get('proclitic', '').startswith('wa_'):
            surface = item['surface'] = AND  # 並列の接続詞は綴りをそろえる (core の並列の検出)
        word = Word(surface, [item])
        word.token_ix = ix
        word.original = token
        if 'lex' in item and not item.get('suffix'):
            word.reading = reading  # 本体: 解析の後で格の語尾を付けた形を作るのに使う
        out.append(word)
    return out


def _item(word):
    return word.items[0] if word.items else None


def _pos(word):
    item = _item(word)
    return item.pos if item is not None else None


def _nominal(word):
    return bool(word.items) and word.items[0].pos in ('noun', 'pronoun', 'adj')


def _restrict(word, cases):
    for item in word.items or []:
        if item._:
            kept = [c for c in item._ if c[0] in cases]
            if kept:
                item._ = kept


def mark_construct(words):
    """連語 (iḍāfa): 定冠詞・人称接尾辞の無い名詞のすぐ後ろの名詞 (形容詞でないもの) を属格「〜の」に
    (كِتابُ الوَلَدِ「少年の本」、بَيْتُ رَجُلٍ「ある男の家」)。後ろが定まった名詞なら前の名詞も定まる。
    人称接尾辞は、名詞に付けば属格 (所有)、動詞に付けば対格 (目的語)、前置詞に付けば属格 (前置詞の目的語)"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None:
            continue
        if item.attrib('suffix'):
            host = _item(words[i - 1]) if i > 0 else None
            if host is not None and host.pos in ('noun', 'adj'):
                _restrict(word, ('Gen',))
                # 所有の人称接尾辞は名詞として扱い、前の名詞の属格にする (كِتابُهُ「彼の本」)
                word.items = [type(item)(dict(item.item, pos='noun'))]
                host.item['definite'] = True
                host.item['construct_with'] = ('suffix', word.surface, item.ja)
            elif host is not None and host.attrib('inna'):
                # inna とその姉妹の人称接尾辞は文の主語 (إِنَّهُ「実に彼は」、أَنَّها「彼女が〜ということ」)
                item._ = [('Nom',) + tuple(c[1:]) for c in item._ if c[0] == 'Gen'] or item._
                item.item['inna_subject'] = True
                host.item['inna_suffix'] = True
            elif host is not None and host.pos == 'verb':
                _restrict(word, ('Acc',))
            continue
        if item.pos != 'noun' or item.attrib('definite') or item.attrib('proper'):
            continue
        states = item.attrib('states') or []
        if states and 'c' not in states and 'u' not in states:
            continue  # 母音記号で非限定 (tanwīn) と決まった名詞
        nxt = words[i + 1] if i + 1 < len(words) else None
        nxt_item = _item(nxt) if nxt is not None else None
        if nxt_item is None or nxt_item.attrib('suffix') or nxt_item.pos not in ('noun', 'pronoun'):
            continue
        if any(c[0] == 'Gen' for c in nxt_item._ or []):
            _restrict(nxt, ('Gen',))
            item.item['construct_with'] = ('noun', nxt.surface, (nxt_item.ja or '').split(',')[0])
            if nxt_item.attrib('definite'):
                item.item['definite'] = True
    # 連語の連なり (كِتابُ ابْنِ الرَّجُلِ) の定まり方は後ろから決まるので、もう一度後ろから
    for i in range(len(words) - 2, -1, -1):
        item = _item(words[i])
        if item is not None and item.attrib('construct_with') and item.attrib('construct_with')[0] == 'noun':
            nxt = _item(words[i + 1])
            if nxt is not None and nxt.attrib('definite'):
                item.item['definite'] = True


def _finite(item):
    return item is not None and item.pos == 'verb' and item.attrib('mood') in ('indicative', 'imperative')


def _free_nominals(words):
    """前置詞の目的語・属格・人称接尾辞を除いた名詞類の位置"""
    out = []
    after_preposition = False
    for i, word in enumerate(words):
        item = _item(word)
        if item is None:
            after_preposition = False
            continue
        if item.pos == 'preposition':
            after_preposition = True
            continue
        if item.pos in ('noun', 'pronoun') and not item.attrib('suffix'):
            if not after_preposition and not all(c[0] == 'Gen' for c in item._ or [('Gen',)]):
                out.append(i)
            after_preposition = False
        elif item.pos != 'adj':
            after_preposition = False
    return out


def negate_verbs(words):
    """لَمْ + 未完了は過去の否定 (لَمْ يَذْهَبْ「行かなかった」)、لَنْ + 未完了は未来の否定 (لَنْ يَذْهَبَ「行かないだろう」)。
    لَيْسَ「〜でない」は否定の語と繋辞に分ける"""
    out = []
    for i, word in enumerate(words):
        item = _item(word)
        if item is not None and item.pos == 'verb' and script.bare(item.attrib('lex') or '') == 'ليس':
            negation = Word(word.surface, [dict(item.item, pos='adv', ja='〜ない', gloss_lang='ja', particle='ليس',
                                                desc='否定の繋辞 laysa「〜でない」')])
            negation.token_ix = getattr(word, 'token_ix', None)
            copula = Word('(كان)', [dict(COPULA, surface='(كان)', person=item.attrib('person'),
                                         number=item.attrib('number'), gender=item.attrib('gender'))])
            out += [negation, copula]
            continue
        out.append(word)
        if item is None or item.pos != 'adv':
            continue
        particle = script.bare(item.attrib('particle') or '')
        nxt = next((w for w in words[i + 1:i + 3] if _item(w) is not None and _item(w).pos == 'verb'), None)
        if nxt is None:
            continue
        verb = _item(nxt)
        if particle == 'لم' and verb.attrib('tense') == 'present':
            verb.item.update(tense='perfect', verb_mood='jussive')
        elif particle == 'لن':
            verb.item.update(tense='future', verb_mood='subjunctive')
        elif particle == 'لا' and verb.attrib('verb_mood') == 'jussive' and verb.attrib('person') == 2:
            verb.item['mood'] = 'imperative'  # 禁止「〜するな」
    return out


def choose_subject(words):
    """3人称の定動詞の主語: 動詞の後ろ (無ければ前) の、性が合い、属格に決まっていない最初の名詞類を主格に。
    動詞が前にあれば数は合わなくてよい (動詞は単数のまま)。主語の後ろの名詞類は目的語 (対格) に。
    1・2人称の動詞の節の名詞は目的語"""
    free = _free_nominals(words)
    last_subject = None  # 前の動詞の主語 (性・数)
    for i, word in enumerate(words):
        verb = _item(word)
        if not _finite(verb) or verb.attrib('person') is None:
            continue
        nxt = next((j for j in range(i + 1, len(words)) if _finite(_item(words[j])) or words[j].items is None
                    or (_pos(words[j]) == 'conj' and words[j].surface != AND)), len(words))
        prv = next((j for j in range(i - 1, -1, -1) if _finite(_item(words[j])) or words[j].items is None
                    or _pos(words[j]) == 'conj'), -1)
        after = [j for j in free if i < j < nxt]
        before = [j for j in reversed(free) if prv < j < i]
        copula = ARABIC.is_copula(verb.attrib('pres1sg'))
        # 動詞の後ろに目的語の人称接尾辞があれば、名詞は主語から
        if verb.attrib('person') != 3:
            for j in after:
                if not copula:
                    _restrict(words[j], ('Acc',))
            continue
        gender, number = verb.attrib('gender'), verb.attrib('number')

        def agrees(c, following):
            if c[0] != 'Nom' or (gender and c[2] and c[2] != gender and not (c[1] == 'pl' and following)):
                return False
            return following or c[1] == number  # 前の主語には数も合わせる
        subject = None
        # wa- でつながった2つ目の動詞が前の主語と性・数が合い、後ろの名詞類が1つだけなら、主語は前と同じで
        # その名詞類は目的語 (أَكَلَ الوَلَدُ الخُبْزَ وَشَرِبَ الماءَ「少年はパンを食べ、水を飲んだ」)
        shared = i > 0 and words[i - 1].surface == AND and last_subject == (gender, number) and len(after) == 1 \
            and not copula
        # 節の頭の定まった名詞が性・数とも動詞と合えば、それが主語 (名詞-動詞の順。見出しに多い:
        # الكَنِيسَةُ المِصْرِيَّةُ تَبْحَثُ「エジプトの教会は探している」)
        if before and not shared:
            j = before[-1]
            item = _item(words[j])
            if (_definite(words[j]) or item.attrib('proper')) and any(agrees(c, False) for c in item._ or []):
                subject = j
        for j in after if not shared and subject is None else []:
            if any(agrees(c, True) for c in _item(words[j])._ or []):
                subject = j
                break
        if subject is None:
            for j in before:
                if any(agrees(c, False) for c in _item(words[j])._ or []):
                    subject = j
                    break
        if subject is not None:
            item = _item(words[subject])
            item._ = [c for c in item._ if agrees(c, subject > i)]
            last_subject = (gender, number)
        elif not shared:
            last_subject = None
        if copula:
            continue
        for j in after:
            if j != subject and (subject is None or j > subject):
                _restrict(words[j], ('Acc',))


COPULA = {'pos': 'verb', 'pres1sg': 'كان', 'lex': 'كان', 'base': 'كان', 'ja': 'ある,いる', 'gloss_lang': 'ja',
          'voice': 'active', 'mood': 'indicative', 'tense': 'present', 'person': 3, 'number': 'sg',
          'desc': '名詞文 (繋辞なし)'}


def mark_inna(words):
    """inna とその姉妹 (إِنَّ, أَنَّ, لٰكِنَّ) の後ろの名詞 (形は対格) は文の主語。訳では主語 (主格) として扱う"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('inna') or item.attrib('inna_suffix'):
            continue  # 人称接尾辞の付いた inna (إِنَّهُ) は接尾辞が主語
        nxt = next((w for w in words[i + 1:i + 3] if _nominal(w)), None)
        if nxt is not None:
            _restrict(nxt, ('Nom',))
            nxt.items[0].item['inna_subject'] = True


def supply_copula(words):
    """動詞の無い節 (名詞文) に見えない繋辞を補う。節は句読点・接続詞で区切る"""
    out, clause = [], []
    for i, word in enumerate(words):
        nxt = words[i + 1] if i + 1 < len(words) else None
        # wa- の後ろに定まった名詞が来て、前の節に名詞類が2つ以上あれば、wa- で節を分ける
        # (المَدِينَةُ كَبِيرَةٌ وَالشَّوارِعُ واسِعَةٌ「町は大きく、通りは広い」)
        new_clause = word.surface == AND and nxt is not None and _nominal(nxt) and _definite(nxt) and \
            sum(1 for w in clause if _nominal(w)) >= 2
        inna = _item(word) is not None and _item(word).attrib('inna')
        if inna:
            # inna とその姉妹は新しい節の頭 (قالَ إِنَّهُ مَرِيضٌ「彼は病気だと言った」)
            out += _supply_copula(clause)
            clause = [word]
        elif word.items is None or (_pos(word) == 'conj' and word.surface != AND and clause) or new_clause:
            out += _supply_copula(clause) + [word]
            clause = []
        else:
            clause.append(word)
    return out + _supply_copula(clause)


def _supply_copula(words):
    """主語 (定まった名詞・代名詞・固有名詞) の後ろに、述語 (定まらない名詞・形容詞、前置詞句、または代名詞の後ろの名詞) が
    あれば、その間に繋辞を補う (الوَلَدُ كَبِيرٌ「少年は大きい」、هُوَ طالِبٌ「彼は学生だ」、الكِتابُ عَلَى المَكْتَبِ
    「本は机の上にある」)。前置詞句が先で定まらない名詞が後ろなら存在文 (فِي البَيْتِ رَجُلٌ「家に男がいる」)"""
    if any(_finite(_item(w)) for w in words):
        return words
    if len(words) >= 3 and _item(words[0]) is not None and _item(words[0]).attrib('inna') and \
            _item(words[1]) is not None and _item(words[1]).attrib('inna_subject') and \
            any(_nominal(w) or _pos(w) == 'preposition' for w in words[2:]):
        # 人称接尾辞が主語の inna (إِنَّهُ مَرِيضٌ「実に彼は病気だ」): 接尾辞の後ろに
        for w in words[2:]:
            if _nominal(w) and not all(c[0] == 'Gen' for c in _item(w)._ or [('x',)]):
                _restrict(w, ('Nom',))
                break
        return words[:2] + [Word('(كان)', [dict(COPULA, surface='(كان)')])] + words[2:]
    free = _free_nominals(words)
    if not free:
        return words
    first = free[0]
    head = _item(words[first])
    if head.pos == 'pronoun' or _definite(words[first]):
        # 主語の後ろ (掛かる属格・形容詞・人称接尾辞の後ろ) に
        at = first + 1
        while at < len(words) and _item(words[at]) is not None and (
                _item(words[at]).attrib('suffix') or
                all(c[0] == 'Gen' for c in _item(words[at])._ or [('x',)]) or
                (_item(words[at]).pos == 'adj' and _definite(words[at]) == _definite(words[first]))):
            at += 1
        if at >= len(words):
            return words
        rest = words[at:]
        if not any(_item(w) is not None and (_item(w).pos in ('noun', 'adj', 'preposition', 'pronoun')) for w in rest):
            return words
        _restrict(words[first], ('Nom',))
        for w in rest:
            if _nominal(w) and not all(c[0] == 'Gen' for c in _item(w)._ or [('x',)]) and \
                    _item(w).pos != 'pronoun':
                _restrict(w, ('Nom',))
                break
        copula = Word('(كان)', [dict(COPULA, surface='(كان)')])
        return words[:at] + [copula] + words[at:]
    # 前置詞句 + 定まらない名詞 (存在文)
    preposition = next((i for i, w in enumerate(words[:first]) if _item(w) is not None
                        and _item(w).pos == 'preposition'), None)
    if preposition is not None and not _definite(words[first]):
        _restrict(words[first], ('Nom',))
        copula = Word('(كان)', [dict(COPULA, surface='(كان)')])
        return words[:first] + [copula] + words[first:]
    return words


def mark_prepositions(words):
    """前置詞の後ろの名詞類 (指示詞 + 名詞は両方) を属格に (فِي مِصْرَ「エジプトで」、فِي هٰذا العامِ「この年に」)"""
    for i, word in enumerate(words):
        if _pos(word) != 'preposition':
            continue
        for nxt in words[i + 1:i + 3]:
            if not _nominal(nxt) or _item(nxt).attrib('suffix') and _pos(nxt) != 'pronoun':
                break
            _restrict(nxt, ('Gen',))
            if not _item(nxt).attrib('demonstrative'):
                break


def agree_adjectives(words):
    """解析の後で、名詞に掛かった形容詞の格を名詞の格にそろえる (母音記号の無い形容詞は格が決まらないので)"""
    for word in words:
        item = _item(word)
        if item is None or not item._ or not getattr(word, 'modifiers', None):
            continue
        case = item._[0][0]
        for mod in word.modifiers:
            if isinstance(mod, Word) and _pos(mod) == 'adj':
                _restrict(mod, (case,))


def mark_demonstratives(words):
    """指示詞は、すぐ後ろが定冠詞付きの名詞なら「この」(هٰذا الكِتابُ「この本」)、そうでなければ代名詞「これ」
    (هٰذا كِتابٌ「これは本だ」)"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('demonstrative'):
            continue
        adjective, pronoun = (item.ja.split(',') + [item.ja])[:2]
        nxt = _item(words[i + 1]) if i + 1 < len(words) else None
        if nxt is not None and nxt.pos == 'noun' and nxt.attrib('definite') and not nxt.attrib('construct_with'):
            item.item['ja'] = adjective
        else:
            item.item.update(ja=pronoun, pos='pronoun', demonstrative=False)
        word.items = [type(item)(item.item)]


def lookup_all(surfaces):
    readings = choose_readings(surfaces)
    words = [w for ix, (s, r) in enumerate(zip(surfaces, readings)) for w in _words(s, r, ix)]
    words = negate_verbs(words)
    mark_construct(words)
    mark_prepositions(words)
    mark_demonstratives(words)
    mark_inna(words)
    words = supply_copula(words)
    choose_subject(words)
    for i, word in enumerate(words):
        word.index = i
    return words


CASE_CODES = {'Nom': 'n', 'Acc': 'a', 'Gen': 'g'}
MOOD_CODES = {'jussive': 'j', 'subjunctive': 's'}


def word_form(word):
    """解析の後の語の形 (母音記号付き): 名詞類は選んだ格と状態 (定・非限定・連語形) の語尾、動詞は法の語尾を付ける
    (الوَلَد → الوَلَدُ (主格)、رِسالَة → رِسالَةً (対格・非限定)、لَمْ يَذْهَب → يَذْهَبْ (要求法))"""
    item = _item(word)
    reading = getattr(word, 'reading', None)
    if item is None or reading is None:
        return word.surface
    analyses = reading.analyses
    if item.pos == 'verb':
        mood = MOOD_CODES.get(item.attrib('verb_mood'), 'i')
        found = [a for a in analyses if a.get('mod') == mood]
        if item.attrib('aspect') == 'i':
            return mood_ending(morphology.split(found[0])[1] if found else word.surface, mood)
    elif item._:
        # inna の主語は訳では主語 (主格) として扱うが、形は対格 (إِنَّ الطّالِباتِ)
        case = 'a' if item.attrib('inna_subject') else CASE_CODES.get(item._[0][0])
        if reading.main.get('enc0') not in (None, '0', 'na') or item.attrib('construct_with'):
            state = 'c'
        elif reading.main.get('prc0') == 'Al_det':
            state = 'd'
        else:
            state = 'i'
        found = [a for a in analyses if a.get('cas') == case and a.get('stt') == state] or \
            [a for a in analyses if a.get('cas') == case]
    else:
        found = []
    if not found:
        return word.surface
    return morphology.split(found[0])[1]


def mood_ending(form, mood):
    """未完了形の法の語尾を付ける: 直説法 -u (يَذْهَبُ)、接続法 -a (يَذْهَبَ)、要求法 -∅ (يَذْهَبْ)。
    -ūna / -īna / -āni の形は、接続法・要求法で -na / -ni が落ちる (يَكْتُبُونَ → يَكْتُبُوا)"""
    bare = script.bare(form)
    if bare.endswith(('ون', 'ين', 'ان')) and len(bare) > 3:
        if mood == 'i':
            return form
        stem = form[:form.rfind('ن')]
        return stem + ('ا' if bare.endswith('ون') else '')
    if script.has_diacritics(form[-1:]) or bare[-1:] in 'اويى':
        return form  # 語尾の母音が書かれているもの、弱い語末 (يَمْشِي) はそのまま
    return form + {'i': script.DAMMA, 's': script.FATHA, 'j': script.SUKUN}[mood]


def sentence_forms(words):
    """元の語ごとの、母音記号付きの形と転写 [(形, 転写)] (接頭辞はハイフンでつなぐ: wa-bi-l-qalami)"""
    out = []
    current, parts, ix = '', [], None
    for word in words:
        if word.surface.startswith('(') or getattr(word, 'token_ix', None) is None:
            continue
        if word.items is None:
            if current:
                out.append((current, ''.join(parts)))
            out.append((word.surface, word.surface))
            current, parts, ix = '', [], None
            continue
        if word.token_ix != ix and current:
            out.append((current, ''.join(parts)))
            current, parts = '', []
        ix = word.token_ix
        form = script.sun_shadda(word_form(word))
        latin = script.translit(form)
        item = _item(word)
        if parts and parts[-1].endswith('-') and re.match('a[^aeiouāīū-]+-', latin):
            latin = latin[1:]  # wa-l-waladu, bi-š-šamsi (定冠詞の a- は前の接頭辞と続けて落ちる)
        if item is not None and item.attrib('proclitic'):
            latin += '-'
        if script.bare(current).endswith('ل') and current and form.startswith('ال'):
            form = form[1:]  # لِ + الوَزِير → لِلْوَزِير (アリフを書かない)
        current += form
        parts.append(latin)
    if current:
        out.append((current, ''.join(parts)))
    return out


def sentence_text(forms):
    """(母音記号付きの文, 転写の文)。句読点は前の語に付ける"""
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
    with language.using(ARABIC):
        analysis = common.analyze_words([w.surface for w in words], words, word_details, [])
    agree_adjectives(words)
    analysis.forms = sentence_forms(words)  # 格の語尾を付けた形と転写 (見出しの行に使う)
    return analysis


def analyze_text(text):
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
