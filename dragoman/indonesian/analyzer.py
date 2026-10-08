#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# インドネシア語・マレー語の文の解析
#
# 語を解析し (indonesian/morphology.py)、文の中での働きを決めてから、並列・係り先・前置詞句・格の枠・日本語訳は
# 共通の解析器 (core/analyzer.py) をインドネシア語の設定 (INDONESIAN) で使う:
#   - 語順は 主語-動詞-目的語。動詞の前の、前置詞の目的語でない最初の名詞類が主語、動詞の後ろの名詞類が目的語
#   - di- の受動 (Buku itu ditulis oleh Ali「その本はアリによって書かれた」): 前の名詞が主語 (受け手)、oleh が動作主
#   - 修飾語・属格・指示詞は名詞の後ろ (buku besar「大きい本」、rumah ayah「父の家」、buku ini「この本」)。
#     指示詞の後ろの形容詞は述語 (Buku itu besar「その本は大きい」)
#   - 時制・相の副詞 (sudah / telah → 過去、akan → 未来、sedang → 進行) は後ろの動詞の時制に
#   - 接語 -nya / -ku / -mu は前の名詞の所有者 (bukunya「彼の本」)
#
import re

from dragoman.core import analyzer as common
from dragoman.core import language
from dragoman.core.Word import Word
from . import dictionary, morphology

PUNCTUATION = {'.': 'period', '!': 'period', '?': 'question', ',': 'comma', ';': 'comma', ':': 'comma',
               '"': None, '“': None, '”': None, '(': 'comma', ')': 'comma', '–': 'comma', '—': 'comma'}
TOKEN = re.compile(r"[A-Za-zÀ-ÿ']+(?:-[A-Za-zÀ-ÿ']+)*|[0-9]+(?:[.,][0-9]+)*|[.!?,;:\"“”()–—]")
LANG = 'id'


def _root_items(lemma):
    return [{'pos': 'verb', 'ja': l['en'], 'gloss_lang': 'en'} for l in dictionary.lemmas(lemma, LANG)
            if l['pos'] == 'verb' and l['en']]


def predicative_adjective(adj, noun):
    """名詞に掛けない形容詞: 名詞の前にある形容詞 (数量詞の他)、指示詞 (ini / itu) の後ろの形容詞 (述語)"""
    if not isinstance(adj, Word) or not isinstance(noun, Word) or not adj.items or not noun.items:
        return False
    a, n = getattr(adj, 'index', 0), getattr(noun, 'index', 0)
    item = adj.items[0]
    if item.attrib('prenominal'):
        return a > n  # 数量詞は後ろの名詞にだけ (semua orang)
    if a < n:
        return True   # 形容詞は名詞の後ろ
    if item.attrib('demonstrative'):
        return False
    return bool(getattr(adj, 'after_demonstrative', False))


INDONESIAN = language.Language(
    name='id',
    and_words=('dan', 'serta'),
    or_words=('atau',),
    copulas=frozenset({'adalah'}),
    negations=frozenset(morphology.NEGATIONS),
    case_particles={'Nom': 'が', 'Acc': 'を', 'Gen': 'の'},
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


LINE_BREAKS = False  # 改行も文の区切りにする (--sentence-per-line。歌詞・詩の行。行末がカンマなら次の行に続ける)


def sentences(text):
    """文に分ける: 句点・疑問符。LINE_BREAKS なら改行でも"""
    current = []
    for line in text.splitlines():
        for token in tokens(line):
            current.append(token)
            if PUNCTUATION.get(token) in ('period', 'question'):
                yield current
                current = []
        if LINE_BREAKS and current and current[-1] not in (',', ';', ':'):
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


def _choose(items, token, prev_items, next_items):
    """読みの選択: me- / di- / ber- の語は動詞を先に。前が冠詞的な語 (ini, itu, 前置詞) なら名詞を先に"""
    def score(item):
        s = 0
        if item['pos'] == 'verb' and token.lower().startswith(('me', 'di', 'ber', 'ter')):
            s -= 2
        if prev_items and (prev_items[0]['pos'] == 'preposition' or prev_items[0]['pos'] == 'adj' and
                           not prev_items[0].get('demonstrative')) and item['pos'] in ('noun', 'pronoun'):
            s -= 1
        if item.get('unknown'):
            s += 5
        return s
    return sorted(items, key=score)


def _merge_tokens(surfaces):
    """場所の前置詞の組 (di atas → 1語)"""
    out = []
    i = 0
    while i < len(surfaces):
        pair = (surfaces[i].lower(), surfaces[i + 1].lower()) if i + 1 < len(surfaces) else None
        if pair and ' '.join(pair) in morphology.GLOSSES:
            out.append(surfaces[i] + ' ' + surfaces[i + 1])  # 2語の見出し (rumah sakit「病院」)
            i += 2
            continue
        if pair in morphology.COMPOUND_PREPOSITIONS:
            out.append(surfaces[i] + ' ' + surfaces[i + 1])
            i += 2
            continue
        out.append(surfaces[i])
        i += 1
    return out


def _words(surfaces):
    surfaces = _merge_tokens(surfaces)
    out = []
    analyses = []
    for token in surfaces:
        if token in PUNCTUATION:
            analyses.append((None, None))
            continue
        if ' ' in token and tuple(token.lower().split()) in morphology.COMPOUND_PREPOSITIONS:
            ja = morphology.COMPOUND_PREPOSITIONS[tuple(token.lower().split())]
            analyses.append(([morphology._item(token, pos='preposition', base=token, ja=ja, gloss_lang='ja',
                                               dominates='Gen')], None))
            continue
        analyses.append(morphology.analyze(token.lower(), LANG))
    for ix, token in enumerate(surfaces):
        items, clitic = analyses[ix]
        if items is None:
            word = Word(token, None)
            word.token_ix = ix
            out.append(word)
            continue
        prev = analyses[ix - 1][0] if ix > 0 else None
        nxt = analyses[ix + 1][0] if ix + 1 < len(analyses) else None
        items = [dict(i, surface=token if not clitic else token[:-len(clitic)]) for i in _choose(items, token, prev, nxt)]
        word = Word(items[0]['surface'], items[:1])  # 読みは1つに (動詞と名詞の両方を渡すと動詞を見つけられない)
        word.alternatives = items[1:]
        word.token_ix = ix
        out.append(word)
        if clitic in morphology.CLITICS and items[0]['pos'] in ('noun', 'adj'):
            # 名詞の所有の接語は訳語に直接付ける (anaknya → 彼の子供)
            ja = morphology.CLITICS[clitic][0]
            data = dict(word.items[0].item, ja=ja + (word.items[0].ja or '').split(',')[0], gloss_lang='ja',
                        possessor=clitic)
            word.items = [type(word.items[0])(data)]
        elif clitic in morphology.CLITICS:
            ja, person = morphology.CLITICS[clitic]
            suffix = Word('-' + clitic, [morphology._item('-' + clitic, pos='pronoun', base='-' + clitic, ja=ja.rstrip('の'),
                                                          gloss_lang='ja', person=person,
                                                          _=[('Acc', 'sg', morphology.GENDER)])])  # 動詞の目的語
            suffix.token_ix = ix
            out.append(suffix)
        elif clitic in morphology.PARTICLE_CLITICS and morphology.PARTICLE_CLITICS[clitic]:
            particle = Word('-' + clitic, [morphology._item('-' + clitic, pos='adv', base='-' + clitic,
                                                            ja=morphology.PARTICLE_CLITICS[clitic], gloss_lang='ja')])
            particle.token_ix = ix
            out.append(particle)
    return out


TIME_TENSES = {'kemarin': 'perfect', 'tadi': 'perfect', 'dulu': 'perfect', 'dahulu': 'perfect', 'semalam': 'perfect',
               'besok': 'future', 'nanti': 'future', 'lusa': 'future', 'esok': 'future'}


def ensure_verbs(words):
    """動詞の無い節 (句読点・接続詞で区切る) で、名詞類の後ろにある、動詞にも読める語を動詞に (kehilangan「失う」)"""
    clause = []
    for word in words + [None]:
        if word is None or word.items is None or _pos(word) in ('conj', 'relative'):
            if clause and not any(_pos(w) in ('verb',) for w in clause):
                for k, w in enumerate(clause[1:], 1):
                    alt = next((a for a in getattr(w, 'alternatives', []) if a['pos'] == 'verb'), None)
                    if alt is not None and _pos(w) == 'noun' and \
                            _pos(clause[k - 1]) in ('noun', 'pronoun', 'adj', 'adv', 'aspect'):
                        w.items = [type(w.items[0])(alt)]
                        break
            clause = []
        else:
            clause.append(word)


def apply_time_words(words):
    """時の副詞 (kemarin「昨日」→ 過去、besok「明日」→ 未来) で、相の語の無い動詞の時制を決める"""
    tense = next((TIME_TENSES[w.surface.lower()] for w in words if w.surface.lower() in TIME_TENSES), None)
    if tense is None:
        return
    for word in words:
        for it in word.items or []:
            if it.pos == 'verb' and it.attrib('tense') == 'present' and not it.attrib('copula'):
                it.item['tense'] = tense


def mark_reporting(words):
    """引用の後の報告の動詞 (句読点・引用符の後ろの kata / ujar …) を動詞にし、後ろの名詞類を倒置した主語に"""
    for i, word in enumerate(words):
        key = word.surface.lower()
        if key not in morphology.REPORTING or i == 0 or words[i - 1].items is not None:
            continue
        item = morphology._item(word.surface, pos='verb', pres1sg=key, lemma=key, base=key, ja=morphology.REPORTING[key],
                                gloss_lang='ja', voice='active', mood='indicative', tense='perfect', person=None,
                                number=None, main=True, reporting=True)
        word.items = [type(word.items[0])(item)] if word.items else word.items
        for j in range(i + 1, min(i + 4, len(words))):
            nxt = _item(words[j])
            if nxt is None:
                break
            if nxt.pos in ('noun', 'pronoun'):
                words[j].inverted_subject = True
                break


def _modal_form(verb, modal):
    from dragoman.kobun.modernize import Modern
    try:
        if modal == 'want':
            return Modern.masu_stem(verb) + 'たい'
        if modal == 'can':
            return verb + 'ことができる'
        if modal == 'must':
            return Modern.neg_stem(verb) + 'なければならない'
        if modal == 'may':
            return Modern.te(verb) + 'もよい'
        if modal == 'need':
            return verb + '必要がある'
    except Exception:
        pass
    return verb


def apply_modals(words):
    """助動詞的な語 + 動詞 → 1つの述語 (ingin belajar → 勉強したい)。助動詞的な語は訳に出さない"""
    from dragoman.core import en_ja
    out = []
    pending = None
    for word in words:
        item = _item(word)
        if item is not None and item.pos == 'modal':
            pending = item.attrib('modal')
            continue
        if pending and item is not None and item.pos == 'verb':
            ja = (item.ja or '').split(',')[0]
            if item.attrib('gloss_lang') == 'en' or re.search('[a-z]', ja):
                ja = (en_ja.translate(item.ja or '', 'verb') or ja).split(',')[0]
            data = dict(item.item, ja=_modal_form(ja, pending), gloss_lang='ja', modal=pending)
            word.items = [type(item)(data)]
            pending = None
        elif item is not None and item.pos not in ('adv', 'aspect'):
            pending = None
        out.append(word)
    return out


def apply_aspects(words):
    """sudah / telah / akan / sedang → 後ろの動詞の時制。相の語は訳に出さない"""
    out = []
    pending = None
    for word in words:
        item = _item(word)
        if item is not None and item.pos == 'aspect':
            pending = item.attrib('aspect')
            continue
        if pending and item is not None and item.pos in ('verb', 'adj'):
            tense = {'perfect': 'perfect', 'future': 'future', 'progressive': 'progressive'}.get(pending)
            if tense and item.pos == 'verb':
                for it in word.items:
                    if it.pos == 'verb':
                        it.item['tense'] = tense
                        it.tense = tense
            pending = None
        elif item is not None and item.pos not in ('adv',):
            pending = None
        out.append(word)
    return out


def mark_demonstratives(words):
    """ini / itu: 前が名詞なら「この / その」(名詞に掛ける)。後ろの形容詞は述語。前が名詞でなければ代名詞「これ / それ」"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('demonstrative'):
            continue
        prev = _item(words[i - 1]) if i > 0 else None
        if prev is None or prev.pos not in ('noun', 'adj', 'pronoun'):
            data = dict(item.item, pos='pronoun', ja=item.attrib('ja_pronoun'), demonstrative=False,
                        _=morphology._nominal_cngs())
            word.items = [type(item)(data)]
            continue
        for j in range(i + 1, min(i + 3, len(words))):
            nxt = _item(words[j])
            if nxt is not None and nxt.pos == 'adj':
                words[j].after_demonstrative = True
            elif nxt is not None and nxt.pos == 'adv':
                continue
            break


def mark_suffixes(words):
    """所有の接語 (-nya, -ku, -mu): 前の名詞の所有者「彼の・私の・あなたの」"""
    for i, word in enumerate(words):
        item = _item(word)
        if item is None or not item.attrib('suffix') or i == 0:
            continue
        host = _item(words[i - 1])
        if host is not None and host.pos in ('noun', 'adj'):
            host.item['construct_with'] = ('suffix', word.surface, item.ja)


def merge_possessors(words):
    """名詞 + 所有者 (名詞・代名詞・固有名詞): 所有者を属格の名詞にして残す (共通の解析器が前の名詞に掛ける:
    kucing saya → 私の猫、pemerintah Indonesia → インドネシアの政府)。bahasa + 国名は1語に (bahasa Jepang → 日本語)"""
    out = []
    for word in words:
        item = _item(word)
        prev = out[-1] if out else None
        pitem = _item(prev) if prev is not None else None
        if item is not None and pitem is not None and pitem.pos == 'noun' and not getattr(word, 'inverted_subject', False) \
                and item.pos in ('noun', 'pronoun') and not item.attrib('demonstrative') and not pitem.attrib('relative'):
            if pitem.attrib('lemma') == 'bahasa' and word.surface.lower() in morphology.NAMES:
                ja = morphology.LANGUAGE_NAMES.get(word.surface.lower(), (item.ja or '').split(',')[0]) + '語'
                prev.items = [type(pitem)(dict(pitem.item, ja=ja, gloss_lang='ja'))]
                prev.surface = prev.surface + ' ' + word.surface
                continue
            # 所有者は属格の名詞に (代名詞も名詞として掛ける)
            data = dict(item.item, pos='noun', _=[('Gen', 'sg', morphology.GENDER)], possessor=True)
            word.items = [type(item)(data)]
        out.append(word)
    return out


def mark_prepositions(words):
    """前置詞の目的語 (すぐ後ろの名詞類) を属格 (前置詞句) に。ほかの名詞類からは属格を除く (前置詞句の外)"""
    governed = set()
    for i, word in enumerate(words):
        if _pos(word) != 'preposition':
            continue
        for j in range(i + 1, min(i + 4, len(words))):
            nxt = words[j]
            if _pos(nxt) not in ('noun', 'pronoun', 'adj'):
                break
            governed.add(id(nxt))
            if _pos(nxt) in ('noun', 'pronoun'):
                break
    previous_noun = False
    for word in words:
        item = _item(word)
        if item is None or item.pos not in ('noun', 'pronoun'):
            previous_noun = False
            continue
        if id(word) in governed or item.attrib('suffix') or item.attrib('possessor'):
            _restrict(word, ('Gen',))
        elif previous_noun and item.pos == 'pronoun' and not item.attrib('demonstrative'):
            _restrict(word, ('Gen',))  # 名詞 + 代名詞 (guru saya「私の先生」)
        elif previous_noun and not item.attrib('demonstrative'):
            _restrict(word, ('Gen', 'Nom', 'Acc'))  # 名詞 + 名詞 (rumah ayah「父の家」)
        else:
            _restrict(word, ('Nom', 'Acc'))
        previous_noun = id(word) not in governed


def choose_subject(words):
    """節 (接続詞・句読点で区切る) ごとに: 動詞の前の自由な名詞類の最初を主語 (主格)、動詞の後ろの名詞類を目的語
    (対格。受動・自動詞・繋辞なら主格)"""
    start = 0
    for i, word in enumerate(words + [None]):
        item = _item(word) if word is not None else None
        boundary = word is None or word.items is None or (item is not None and item.pos in ('conj', 'relative'))
        if not boundary:
            continue
        clause = words[start:i]
        start = i + 1
        verb_ix = next((k for k, w in enumerate(clause) if _pos(w) == 'verb'), None)
        participle_ix = [k for k, w in enumerate(clause) if _pos(w) == 'participle']
        free = [k for k, w in enumerate(clause) if _pos(w) in ('noun', 'pronoun') and
                _item(w)._ and all(c[0] != 'Gen' for c in _item(w)._) and not _item(w).attrib('suffix')]
        if verb_ix is None:
            if free:
                _restrict(clause[free[0]], ('Nom',))
            continue
        verb = _item(clause[verb_ix])
        if verb.attrib('reporting'):
            inverted = [k for k in free if k > verb_ix]
            if inverted:
                _restrict(clause[inverted[0]], ('Nom',))
            continue
        before = [k for k in free if k < verb_ix]
        after = [k for k in free if k > verb_ix]
        if before:
            _restrict(clause[before[0]], ('Nom',))
        # 動詞の後ろの名詞は目的語 (自動詞の表の動詞・受動・繋辞を除く: belajar bahasa「言語を学ぶ」)
        transitive = verb.attrib('voice') == 'active' and not verb.attrib('copula') and \
            verb.attrib('lemma') not in INTRANSITIVE and verb.attrib('pres1sg') not in INTRANSITIVE
        for k in after:
            if any(p < k for p in participle_ix) and not any(p < k < verb_ix for p in participle_ix) and k > verb_ix:
                pass
            _restrict(clause[k], ('Acc',) if transitive else ('Nom',))
        for p in participle_ix:
            # 関係節の目的語 (分詞の後ろの名詞): 対格
            for k in free:
                if p < k < (verb_ix if verb_ix > p else len(clause)):
                    _restrict(clause[k], ('Acc',))
                    break


INTRANSITIVE = {'pergi', 'datang', 'tidur', 'duduk', 'berdiri', 'tinggal', 'lari', 'jatuh', 'mati', 'hidup', 'naik',
                'turun', 'masuk', 'keluar', 'pulang', 'tiba', 'menjadi', 'adalah', 'ada', 'bekerja', 'berjalan',
                'bermain', 'main', 'tertawa', 'menangis', 'datang', 'muncul', 'terjadi', 'berangkat', 'kembali'}
TRANSITIVE = {'makan', 'minum', 'baca', 'tulis', 'lihat', 'beri', 'punya', 'tahu', 'cari', 'beli', 'jual', 'bawa',
              'buat', 'pakai', 'suka', 'cinta', 'kenal', 'dengar', 'tanya', 'jawab', 'ambil', 'kirim', 'pukul'}


COPULA = {'pos': 'verb', 'pres1sg': 'adalah', 'lemma': 'adalah', 'base': '(繋辞なし)', 'ja': 'である', 'gloss_lang': 'ja',
          'voice': 'active', 'mood': 'indicative', 'tense': 'present', 'person': None, 'number': None, 'copula': True,
          'surface': '(adalah)'}


def supply_copula(words):
    global _sentence_has_verb
    _sentence_has_verb = any(_pos(w) == 'verb' for w in words)
    return _supply_copula_clauses(words)


_sentence_has_verb = False


def _supply_copula_clauses(words):
    """動詞の無い節に見えない繋辞を補う: 主語 (指示詞 ini / itu で閉じた名詞句、または代名詞・固有名詞) の後ろに
    述語 (形容詞・名詞・前置詞句) が続けば、その間に (Rumah itu besar「その家は大きい」、Dia guru「彼は先生だ」)"""
    out, clause = [], []
    for word in words + [None]:
        if word is None or word.items is None or _pos(word) in ('conj', 'relative'):
            out += _supply_copula(clause) + ([word] if word is not None else [])
            clause = []
        else:
            clause.append(word)
    return out


def _supply_copula(clause):
    if not clause or any(_pos(w) == 'verb' for w in clause):
        return clause
    content = [w for w in clause if _pos(w) not in ('adv', 'aspect')]
    if not _sentence_has_verb and len(content) >= 2 and _pos(content[-1]) == 'adj' and \
            _pos(content[-2]) in ('noun', 'pronoun') and \
            not _item(content[-1]).attrib('demonstrative') and not _item(content[-1]).attrib('prenominal'):
        # 名詞 + 形容詞で終わる節は形容詞が述語 (Harga minyak tinggi「石油の価格は高い」)
        k = clause.index(content[-1])
        while k > 0 and _pos(clause[k - 1]) in ('adv',):
            k -= 1  # sangat tinggi
        clause[clause.index(content[-1])].after_demonstrative = True
        copula = Word('(adalah)', [dict(COPULA)])
        copula.token_ix = getattr(clause[k], 'token_ix', None)
        return clause[:k] + [copula] + clause[k:]
    for k, w in enumerate(clause[:-1]):
        item = _item(w)
        closes = item is not None and (item.attrib('demonstrative') or
                                       (item.pos == 'pronoun' and k == 0) or item.attrib('proper') and k == 0)
        nxt = _item(clause[k + 1])
        if closes and nxt is not None and nxt.pos in ('adj', 'noun', 'preposition', 'adv') and \
                not nxt.attrib('demonstrative'):
            if nxt.pos == 'noun':
                _restrict(clause[k + 1], ('Nom',))
            copula = Word('(adalah)', [dict(COPULA)])
            copula.token_ix = getattr(clause[k + 1], 'token_ix', None)
            return clause[:k + 1] + [copula] + clause[k + 1:]
    return clause


def _ja(item, pos):
    """項目の日本語の訳語 (最初の1つ。英語なら英語 → 日本語の表で)"""
    from dragoman.core import en_ja
    ja = (item.ja or '').split(',')[0]
    if item.attrib('gloss_lang') == 'en' or re.search('[a-z]', ja):
        ja = (en_ja.translate(item.attrib('ja') or item.ja or '', pos) or ja).split(',')[0]
    return ja


def mark_relatives(words):
    """yang + 動詞 (+ 目的語) / 形容詞: 前の名詞に連体節として掛ける (orang yang membaca buku「本を読む人」、
    rumah yang besar「大きい家」)。連体節は名詞の訳語に付け、yang と節の語は除く。節の終わりの指示詞 (itu / ini) は名詞に"""
    from dragoman.core.japanese import JaVerb
    from dragoman.core import verb_flags as V
    out = []
    i = 0
    while i < len(words):
        word = words[i]
        item = _item(word)
        if item is None or item.pos != 'relative':
            out.append(word)
            i += 1
            continue
        head = next((w for w in reversed(out) if _pos(w) in ('noun', 'pronoun')), None)
        j = i + 1
        span = []
        while j < len(words) and words[j].items is not None and _pos(words[j]) not in ('conj', 'relative') and \
                not (span and _pos(words[j]) == 'verb') and not (_item(words[j]).attrib('copula')):
            span.append(words[j])
            j += 1
            if _item(span[-1]).attrib('demonstrative'):
                break  # 指示詞で名詞句が閉じる (… yang ditulis oleh guru itu | bagus)
        demonstrative = span[-1] if span and _item(span[-1]).attrib('demonstrative') else None
        if demonstrative is not None:
            span = span[:-1]
        if head is None or not span:
            i += 1
            continue
        first = _item(span[0])
        if first.pos == 'verb':
            verb = _ja(first, 'verb') or first.attrib('pres1sg')
            if first.attrib('voice') == 'passive':
                try:
                    verb = JaVerb(verb).form(V.INDICATIVE | V.PASSIVE, False)
                except Exception:
                    pass
            parts, prep = [], None
            for w in span[1:]:
                if _pos(w) == 'preposition':
                    prep = _item(w).ja
                elif _pos(w) in ('noun', 'pronoun'):
                    particle = prep if prep else ('が' if first.attrib('voice') == 'passive' else 'を')
                    parts.append(_ja(_item(w), 'noun') + particle)
                    prep = None
            clause = ''.join(parts) + verb  # 本を読む、先生によって書かれる
        else:
            clause = ''.join(_ja(_item(w), 'adj' if _pos(w) == 'adj' else 'noun') for w in span)
            clause = clause if clause.endswith(('い', 'な')) else clause + 'の'
        hitem = _item(head)
        data = dict(hitem.item, ja=clause + (hitem.ja or '').split(',')[0], gloss_lang='ja',
                    relative='yang ' + ' '.join(w.surface for w in span))
        head.items = [type(hitem)(data)]
        if demonstrative is not None:
            out.append(demonstrative)
        i = j
    return out


def lookup_all(surfaces):
    words = _words(surfaces)
    mark_reporting(words)
    ensure_verbs(words)
    words = apply_aspects(words)
    words = apply_modals(words)
    apply_time_words(words)
    for i, word in enumerate(words):
        word.index = i
    words = merge_possessors(words)
    for i, word in enumerate(words):
        word.index = i
    mark_demonstratives(words)
    mark_suffixes(words)
    words = mark_relatives(words)
    for i, word in enumerate(words):
        word.index = i
    mark_prepositions(words)
    words = supply_copula(words)
    for i, word in enumerate(words):
        word.index = i
    choose_subject(words)
    for i, word in enumerate(words):
        word.index = i
    return words


def analyze_sentence(surfaces):
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    with language.using(INDONESIAN):
        analysis = common.analyze_words([w.surface for w in words], words, word_details, [])
    analysis.original = list(surfaces)  # 見出しの行・音読は元の文 (関係節・所有でまとめた語を含む)
    return analysis


def set_lang(lang):
    """辞書で先に引く言語 (id: インドネシア語、ms: マレー語)"""
    global LANG
    LANG = lang


def analyze_text(text, lang=None):
    if lang:
        set_lang(lang)
    for surfaces in sentences(text):
        yield analyze_sentence(surfaces)
