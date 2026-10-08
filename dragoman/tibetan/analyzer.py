#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典チベット語の解析と日本語訳
#
#   1. 語に分ける (segment.py: botok か辞書の最長一致)
#   2. 語の種類を決める: 体言・用言 (動詞の語幹から時制)・形容詞・数詞・指示詞・助詞・否定
#   3. 句にまとめる: 名詞句 = 体言 + 後ろの修飾語 (形容詞・数詞・指示詞・複数) + 格助詞、動詞句 = 否定 + 動詞 + 助詞
#   4. 節ごとに格を決める: 能格 (gis) は人なら「が」、物なら道具の「で」。何も付かない名詞は、能格の名詞があるか
#      動詞が他動詞なら「を」、ほかは「が」。繋辞 (yin) の文は最初の名詞を「は」
#   5. 日本語は語順をほぼそのまま (修飾語だけ名詞の前へ: mi bzang po gsum → 三人の良い人)
#
import re
from dataclasses import dataclass, field

from dragoman.core import animacy
from dragoman.kobun.modernize import Modern, transitive_only
from . import dictionary, grammar, segment, script

SENTENCE_END = re.compile('(?<=[།༎༏༐༑༔])')


@dataclass
class Word:
    token: object
    kind: str                # noun, pron, adj, num, det, plural, verb, cop, exist, neg, part, punct
    en: str = None           # 英語の訳語
    ja: str = None           # 日本語の訳語 (用言は辞書形)
    lemma: str = ''          # 動詞の現在の語幹 (見出し)
    tense: str = ''          # pres / past / fut / imp
    nominal: bool = False    # 動名詞 (+ pa / ba)
    function: str = ''       # 助詞の働き
    note: str = ''           # 品詞分解の注 (格の選び方など)

    @property
    def text(self):
        return self.token.text

    @property
    def wylie(self):
        return self.token.wylie


@dataclass
class Phrase:
    kind: str                # np, vp, punct
    words: list = field(default_factory=list)
    particles: list = field(default_factory=list)
    case_ja: str = None      # 決めた助詞 (名詞句)
    existential_la: bool = False  # 存在の文の la (所有者「〜には」)
    as_complement: bool = False   # 見る動詞の補語 (stong par rnam par lta → 空であると観察する)
    first_person: bool = False   # 節の主語が一人称 (未来は意志「〜しよう」)
    lead: str = ''               # 前の動名詞から (V-par gyur →「〜ように」+ なる)
    replace: str = None          # 前の動名詞と合わせた訳 (V-bar bya → 〜しよう)
    ja: str = ''


@dataclass
class TibetanAnalysis:
    text: str
    words: list = field(default_factory=list)
    phrases: list = field(default_factory=list)
    japanese: str = ''
    notes: list = field(default_factory=list)

    @property
    def wylie(self):
        return script.translit(self.text, dictionary.known())

    def word_texts(self):
        """発音の単位: (綴り, 前の語に付く助詞か)。語に付いた助詞 (-s, -r, -'i) は前の語の最後の音節に含める
        (thos pa'i → tʰø.pɛː、rgyal pos → cɛː.pø)"""
        out = []
        for w in self.words:
            if w.kind == 'punct':
                out.append((w.text, False))
                continue
            if w.token.affix and w.wylie != "'o" and out and not re.fullmatch('[།༎༏༐༑༔ ]+', out[-1][0]):
                out[-1] = (out[-1][0] + w.text, out[-1][1])
                continue
            for k, piece in enumerate(getattr(w, 'pieces', None) or [w.text]):
                out.append((piece, w.kind in ('part', 'plural') or (w.kind == 'cop' and False)))
        return out

    def pronunciation(self, pron='lhasa'):
        from . import phonology
        return phonology.ipa(self.text, pron, words=[u for u in self.word_texts()
                                                    if not re.fullmatch('[།༎༏༐༑༔ ]+', u[0])])


# ----------------------------------------------------------------------
# 語の種類

def _is_verb(wylie):
    return bool(dictionary.stems(wylie)) or dictionary.pos(wylie) == 'verb' or \
        any(t.startswith('v.') for t in dictionary.tags(wylie))


def _gloss(wylie, pos):
    if wylie in grammar.GLOSSES:
        return None, grammar.GLOSSES[wylie]
    return dictionary.gloss(wylie, pos)


def hill_tenses(wylie):
    """Hill & Garrett の印 (v.past, v.fut.v.pres, v.invar) → 時制の集合。不変の動詞は 'invar'"""
    out = set()
    for t in dictionary.tags(wylie):
        if not t.startswith('v.'):
            continue
        for part in t.split('.')[1::2]:
            out.add(part if part in grammar.TENSE_NAMES else 'invar' if part == 'invar' else part)
    return out & (set(grammar.TENSE_NAMES) | {'invar'})


def _verb_word(token, wylie, nominal=False):
    found = dictionary.stems(wylie)
    hill = hill_tenses(wylie)
    if found:
        # 見出しの候補: Hill の時制と合うもの、訳語の決まっているものを先に (bcad → gcod「切る」)
        found = sorted(found, key=lambda r: (r[1] not in hill, r[0] not in grammar.GLOSSES))
    lemma = found[0][0] if found else wylie
    tenses = (hill - {'invar'}) or ({'pres'} if hill else {t for l, t in found if l == lemma})
    en, ja = _gloss(wylie, 'verb') if wylie in grammar.GLOSSES else _gloss(lemma, 'verb')
    if ja is None and lemma != wylie:
        en, ja = _gloss(wylie, 'verb')
    w = Word(token, 'verb', en, ja, lemma, nominal=nominal)
    w.tenses = tenses
    return w


def classify(tokens):
    words = []
    for i, t in enumerate(tokens):
        nxt = next((x for x in tokens[i + 1:] if x.upos != 'PUNCT'), None)
        prev = words[-1] if words else None
        wylie = t.wylie
        if t.upos == 'PUNCT':
            words.append(Word(t, 'punct'))
            continue
        if t.upos == 'TERM' and wylie in grammar.POSTPOSITIONS and prev is not None:
            words.append(Word(t, 'part', ja=grammar.TERMS[wylie][0], lemma=wylie, function='後置詞'))
            continue
        if t.upos == 'TERM':
            ja, skt = grammar.TERMS[wylie]
            if wylie in grammar.TERM_VERBS:
                w = _verb_word(t, wylie.split()[-1])
                w.ja, w.note = ja, '術語「%s」' % ja
                w.term = True
                words.append(w)
                continue
            kind = 'adv' if wylie in grammar.TERM_ADVERBS else 'noun'
            w = Word(t, kind, ja=ja, note='術語「%s」' % ja if skt else '')
            w.term = True
            words.append(w)
            continue
        if t.upos == 'SKT':
            words.append(Word(t, 'noun', ja='〔%s〕' % script.iast(wylie), note='サンスクリットの音写'))
            continue
        lemma = grammar.normalize(wylie) if (t.upos in ('PART', 'ADP') or t.affix) else wylie
        if wylie == 'lo' and prev is not None and prev.wylie.endswith('l') and prev.kind in ('verb', 'noun'):
            if prev.kind == 'noun' and _is_verb(prev.wylie):
                words[-1] = prev = _verb_word(prev.token, prev.wylie)
            if prev.kind == 'verb':
                words.append(Word(t, 'part', lemma='go', function='文末'))  # -l の後ろの lo は文末の 'o ('tshal lo)
                continue
        bare_verb = re.sub(r' (pa|ba)$', '', wylie)
        if len(words) >= 2 and words[-1].kind == 'part' and words[-1].lemma == 'la' and words[-2].kind == 'noun' and \
                grammar.PHRASE_VERBS.get((words[-2].wylie, bare_verb)):
            pieces = [words[-2].text, words[-1].text, t.text]
            verb = _verb_word(t, bare_verb, nominal=bare_verb != wylie)
            verb.ja = grammar.PHRASE_VERBS[(words[-2].wylie, bare_verb)]
            verb.token.text = '་'.join([words[-2].text, words[-1].text, t.text])
            verb.token.wylie = ' '.join([words[-2].wylie, words[-1].wylie, wylie])
            verb.note = '決まった言い方'
            verb.pieces = pieces  # 発音は語ごとに
            words[-2:] = [verb]
            continue
        if prev is not None and prev.kind == 'noun' and grammar.COMPOUND_VERBS.get((prev.wylie, bare_verb)):
            verb = _verb_word(t, bare_verb, nominal=bare_verb != wylie)
            verb.ja = grammar.COMPOUND_VERBS[(prev.wylie, bare_verb)]
            verb.token.text = prev.text + '་' + t.text
            verb.token.wylie = prev.wylie + ' ' + wylie
            verb.note = '名詞 + 動詞の組み合わせ'
            words[-1] = verb
            continue
        after_verb = prev is not None and prev.kind in ('verb', 'cop', 'exist')
        if wylie == 'de' and after_verb and not prev.nominal:
            lemma = 'te'
        if wylie == 'de' and prev is not None and prev.kind == 'noun' and \
                (i + 1 >= len(tokens) or tokens[i + 1].upos == 'PUNCT'):
            words.append(Word(t, 'part', lemma='te', function='接続'))  # 名詞 + de (stong pa nyid de → 空性であって)
            continue
        sentence_end = nxt is None or tokens[i + 1].upos == 'PUNCT'
        if wylie in grammar.NEGATIONS and nxt is not None and (_is_verb(nxt.wylie) or nxt.upos == 'VERB' or
                                                                 _is_verb(re.sub(r' (pa|ba)$', '', nxt.wylie)) or
                                                                 nxt.wylie in grammar.COPULAS or
                                                                 nxt.wylie in grammar.EXISTENTIALS):
            words.append(Word(t, 'neg', function='否定'))
            continue
        if wylie in grammar.COPULAS:
            words.append(Word(t, 'cop', ja=grammar.COPULAS[wylie], function='繋辞'))
            continue
        if wylie in grammar.EXISTENTIALS:
            words.append(Word(t, 'exist', ja=grammar.EXISTENTIALS[wylie], function='存在'))
            continue
        verbal_only = lemma in ('te', 'cing', 'go', 'gam', 'lo') and not t.affix
        if verbal_only and lemma in grammar.PARTICLES and prev is not None and prev.kind == 'noun' and \
                not getattr(prev, 'term', False) and prev.token.upos != 'SKT' and \
                _is_verb(prev.wylie) and (wylie != 'shing' or t.upos == 'PART'):
            # 接続・文末の助詞の前の語は動詞として読み直す (lhags zhing → lhags は動詞)
            words[-1] = prev = _verb_word(prev.token, prev.wylie)
            after_verb = True
        trusted = (lemma in ('go', 'gam', 'lo') and sentence_end) or (lemma in ('te', 'cing') and wylie != 'shing'
                                                                     and t.upos == 'PART')
        if lemma in grammar.PARTICLES and (t.upos in ('PART', 'ADP', 'NO_POS', 'DET') or t.affix or lemma == 'te') and \
                not (lemma in ('dag', 'rnams') and prev is None) and not (verbal_only and not after_verb and not trusted):
            kind = 'plural' if grammar.PARTICLES[lemma][0] == '複数' else 'part'
            words.append(Word(t, kind, lemma=lemma, function=grammar.PARTICLES[lemma][0]))
            continue
        if wylie in ('pa', 'ba', 'po', 'bo') and after_verb:
            prev.nominal = True  # 動詞 + pa (動名詞)
            prev.token.text += '་' + t.text
            continue
        if wylie == 'nyid' and prev is not None and prev.kind in ('noun', 'pron', 'verb'):
            words.append(Word(t, 'emph', ja='そのもの'))  # X nyid → Xそのもの (spyod pa nyid → 行そのもの)
            continue
        if wylie == 'gzhan' and nxt is not None and nxt.wylie in ('ma', 'yin', 'min', 'red'):
            words.append(Word(t, 'noun', ja='別'))  # X gzhan ma yin → X は別ではない
            continue
        if t.upos == 'DET' or wylie in grammar.DETERMINERS and prev is not None and prev.kind in ('noun', 'adj', 'num'):
            words.append(Word(t, 'det', ja=grammar.DETERMINERS.get(wylie) or dictionary.gloss(wylie)[1]))
            continue
        if t.upos == 'PRON' or wylie in grammar.PRONOUNS:
            words.append(Word(t, 'pron', ja=grammar.PRONOUNS.get(wylie) or dictionary.gloss(wylie, 'pronoun')[1]))
            continue
        if t.upos == 'NUM' or wylie in grammar.NUMERALS:
            words.append(Word(t, 'num', ja=grammar.NUMERALS.get(wylie) or dictionary.gloss(wylie, 'num')[1]))
            continue
        root = re.sub(r' (pa|ba)$', '', wylie)
        if root != wylie and wylie in grammar.GLOSSES:
            words.append(Word(t, 'noun', ja=grammar.GLOSSES[wylie]))  # 訳語を決めてある動名詞は名詞 (bde ba「幸せ」)
            continue
        tags = dictionary.tags(wylie)
        verb_only = tags and all(x.startswith('v.') for x in tags)
        nounish = wylie in grammar.GLOSSES and not _is_verb(wylie) or any(x.startswith('n.') for x in tags)
        verb_context = nxt is not None and (grammar.normalize(nxt.wylie) in ('go', 'te', 'cing', 'gam', 'lo') or
                                            (nxt.wylie in grammar.COPULAS or nxt.wylie in grammar.EXISTENTIALS) and
                                            not nounish) or \
            prev is not None and prev.kind == 'neg'
        if t.upos == 'VERB' or verb_only or (t.upos in ('NO_POS', 'NOUN') and _is_verb(wylie) and verb_context):
            if root != wylie and _is_verb(root):
                w = _verb_word(t, root, nominal=True)
            else:
                w = _verb_word(t, wylie)
            if w.ja is None and root != wylie and not any(x.startswith('n.v.') for x in dictionary.tags(wylie)):
                en, ja = _gloss(wylie, 'noun')
                if ja:
                    w = Word(t, 'noun', en, ja)  # 動詞の訳語の無い動名詞は名詞 (bde ba「幸せ」)
            words.append(w)
            continue
        if t.upos == 'ADJ' or dictionary.pos(wylie) == 'adj' and prev is not None and prev.kind in ('noun',):
            en, ja = _gloss(wylie, 'adj')
            words.append(Word(t, 'adj', en, ja))
            continue
        if wylie in grammar.ADVERBS:
            words.append(Word(t, 'adv', ja=grammar.ADVERBS[wylie]))
            continue
        en, ja = _gloss(wylie, 'noun')
        words.append(Word(t, 'noun', en, ja))
    return words


# ----------------------------------------------------------------------
# 句

NP_KINDS = {'noun', 'pron', 'adj', 'num', 'det', 'plural', 'emph'}


def group(words):
    phrases = []
    for w in words:
        last = phrases[-1] if phrases else None
        if w.kind == 'punct':
            phrases.append(Phrase('punct', [w]))
        elif w.kind in NP_KINDS:
            if last is not None and last.kind == 'np' and not last.particles and \
                    (w.kind in ('adj', 'num', 'det', 'plural', 'emph') or
                     w.wylie in grammar.PERSON_TERMS and last.words[-1].wylie in grammar.PERSON_TERMS):
                last.words.append(w)  # 後ろの修飾語、称号 + 名前 (tshe dang ldan pa shA ri'i bu → 具寿舎利子)
            else:
                phrases.append(Phrase('np', [w]))
        elif w.kind in ('verb', 'cop', 'exist', 'neg'):
            if last is not None and last.kind == 'vp' and not last.particles and \
                    (last.words[-1].kind == 'neg' or w.kind in ('cop', 'exist', 'verb')):
                last.words.append(w)  # 否定 + 動詞、動詞 + 補助動詞 (yin, yod, 'dug)
            else:
                phrases.append(Phrase('vp', [w]))
        elif w.kind == 'adv':
            phrases.append(Phrase('adv', [w]))
        elif w.kind == 'part':
            if last is not None and last.kind == 'adv' and w.lemma == 'zhes':
                continue  # 'di skad ces → このように
            if last is not None and last.kind in ('np', 'vp'):
                last.particles.append(w)
            else:
                phrases.append(Phrase('np', [], [w]))
    return phrases


def _head(np):
    nouns = [w for w in np.words if w.kind in ('noun', 'pron')]
    return nouns[0] if nouns else (np.words[0] if np.words else None)


def is_animate(word):
    if word is None:
        return False
    if word.kind == 'pron':
        return word.ja not in ('何', 'これ', 'それ', 'どれ')
    if word.wylie in grammar.HUMANS or word.wylie in grammar.PERSON_TERMS:
        return True
    en = (word.en or '').lower()
    ja = word.ja or ''
    return bool(set(re.findall('[a-z]+', en.split(',')[0])) & animacy.ENGLISH) or \
        ja.split(',')[0] in animacy.JAPANESE_WORDS or ja.split(',')[0].endswith(animacy.JAPANESE_SUFFIXES) or \
        ja.split(',')[0] in animacy.PERSONAL_PRONOUNS


# ----------------------------------------------------------------------
# 格の決定 (節ごと)

def assign_cases(phrases, notes):
    clause = []
    first_person = False
    first = next((p for p in phrases if p.kind != 'punct'), None)
    if first is not None and first.kind == 'np' and not first.particles and len(first.words) == 1 and \
            first.words[0].wylie in grammar.VOCATIVES and phrases.index(first) + 1 < len(phrases) and \
            phrases[phrases.index(first) + 1].kind != 'vp':
        first.case_ja = 'よ、'  # 呼びかけ (shA ri'i bu de lta bas na … → 舎利子よ、それゆえ …)
        first.vocative = True
    for k, p in enumerate(phrases):
        if getattr(p, 'vocative', False):
            continue
        if p.kind == 'np' and any(x.lemma == 'go' for x in p.particles):
            # 名詞 + 文末の 'o は述語 (gzugs stong pa'o → 色は空である): 前の何も付かない名詞を「は」に
            before = [n for n in clause if n.words and not n.particles]
            if before:
                before[-1].case_ja = 'は'
            clause = []
            continue
        if p.kind == 'np' and clause and clause[-1].particles and clause[-1].particles[-1].lemma == 'zhes bya ba':
            clause[-1].genitive_link = True  # 『X』という Y
            clause[-1].case_ja = ''
        if p.kind == 'np' and p.words and p.words[0].wylie in grammar.GENITIVE_HEADS and clause and \
                clause[-1].words and not clause[-1].particles:
            clause[-1].case_ja = 'の'  # 甚深な般若波羅蜜多の行
            clause[-1].genitive_link = True
        if p.kind == 'punct':
            first_person = False
        if p.kind == 'np':
            clause.append(p)
            continue
        if p.kind != 'vp':
            continue
        verb = next((w for w in p.words if w.kind in ('verb', 'cop', 'exist')), None)
        nps = [n for n in clause if n.words]
        ergative = [n for n in nps if any(x.lemma == 'gis' for x in n.particles)]
        bare = [n for n in nps if not [x for x in n.particles if x.lemma in grammar.CASES or x.lemma == 'ni']]
        transitive = verb is not None and verb.kind == 'verb' and verb.ja and transitive_only(verb.ja.split(',')[0])
        for n in ergative:
            head = _head(n)
            if is_animate(head) or not bare and transitive:
                n.case_ja = 'が'
                head.note = '能格 (動作主) →「が」'
            else:
                n.case_ja = 'で'
                head.note = '具格 (道具・手段) →「で」'
        copular = verb is not None and verb.kind == 'cop'
        see = verb is not None and (verb.wylie in grammar.SEE_VERBS or verb.lemma in grammar.SEE_VERBS)
        for n in nps:
            if see and [x.wylie for x in n.particles] == ['r']:
                n.as_complement = True  # X-r lta → Xであると観察する
        if verb is not None and verb.lemma == 'ldan' and nps and any(x.lemma == 'dang' for x in nps[-1].particles):
            nps[-1].case_ja = 'を'  # X dang ldan → X を具える (直前の名詞だけ)
        first_person = first_person or any(_head(n) is not None and _head(n).wylie in grammar.FIRST_PERSON
                                           for n in nps)
        p.first_person = first_person
        if verb is not None and verb.kind == 'exist':
            for n in nps:
                if any(x.lemma == 'la' for x in n.particles) and is_animate(_head(n)):
                    n.existential_la = True
        bare = [n for n in bare if not getattr(n, 'genitive_link', False)]
        for k, n in enumerate(bare):
            if any(x.lemma == 'gi' for x in n.particles):
                continue
            head = _head(n)
            if copular:
                n.case_ja = 'は' if k == 0 and len(bare) > 1 else ''
            elif ergative or (transitive and (k > 0 or not is_animate(head))):
                n.case_ja = 'を'
                if head is not None:
                    head.note = '絶対格 (目的語) →「を」'
            else:
                n.case_ja = 'が'
                if head is not None:
                    head.note = '絶対格 (主語) →「が」'
        clause = []


# ----------------------------------------------------------------------
# 日本語

def np_japanese(np):
    dets = [w.ja for w in np.words if w.kind == 'det' and w.ja]
    nums = [w.ja for w in np.words if w.kind == 'num' and w.ja]
    adjs = [_adj(w) for w in np.words if w.kind == 'adj']
    nouns = [_noun(w) for w in np.words if w.kind in ('noun', 'pron')]
    plural = 'たち' if any(w.kind == 'plural' for w in np.words) and nouns else ''
    plural += 'そのもの' if any(w.kind == 'emph' for w in np.words) and nouns else ''
    if not nouns and dets and not nums and not adjs:
        person = any(x.lemma == 'gis' for x in np.particles)
        nouns, dets = [{'この': 'これ', 'その': 'その者' if person else 'それ', 'それらの': 'それら',
                        'これらの': 'これら'}.get(dets[-1], dets[-1])], dets[:-1]  # 指示詞だけ (V-pa de → 〜するそれ)
    if not nouns and nums:
        nouns, nums = nums, []
    elif not nouns and adjs:
        nouns, adjs = [adjs[-1].rstrip('の')], adjs[:-1]
    counter = '人の' if is_animate(_head(np)) else 'つの'
    if nums == ['一'] and nouns:
        nums_text = 'ある'  # gcig: ある〜 (dus gcig na → ある時に)
    else:
        nums_text = ''.join(n + counter if len(n) == 1 else n + 'の' for n in nums)
    text = ''.join(dets) + nums_text + ''.join(adjs) + ''.join(nouns) + plural
    previous = None
    for part in np.particles:
        if part.lemma == 'gi' and previous == 'zhes bya ba':
            previous = part.lemma
            continue  # X zhes bya ba'i Y → Xという Y
        previous = part.lemma
        if part.lemma in grammar.POSTPOSITIONS:
            if text.endswith('の') and part.ja in ('まで', 'という'):
                text = text[:-1]  # X kyi bar du → Xまで
            text += part.ja
            continue
        text += _np_particle(np, part)
    if np.case_ja and not [x for x in np.particles if x.lemma in grammar.CASES or
                           x.lemma in ('gam', 'kyang', 'ni', 'te', 'cing')]:
        if np.particles and np.particles[-1].lemma == 'zhes bya ba':
            text += '言葉'  # legs so zhes bya ba byin → 善哉という言葉を与え
        text += np.case_ja
    if np.as_complement and text.endswith('に'):
        text = text[:-1] + 'であると'
    if np.existential_la and text.endswith('に'):
        text += 'は'  # 所有 (ང་ལ་དངུལ་མེད → 私にはお金がない)
    return text


def _first(ja):
    return (ja or '').split(',')[0]


def _noun(w):
    return _first(w.ja) or '〔%s〕' % w.wylie


def _adj(w):
    ja = _first(w.ja)
    if not ja:
        return '〔%s〕' % w.wylie
    return ja if ja.endswith(('い', 'な')) else ja + 'の'


def _np_particle(np, part):
    lemma = part.lemma
    if lemma == 'gis':
        return np.case_ja or 'が'
    if lemma == 'dang' and np.case_ja:
        return np.case_ja
    if lemma == 'cig':
        return ''
    if lemma == 'go':
        return 'である'  # 名詞 + 文末の 'o (stong pa nyid do → 空性である)
    if lemma in ('te', 'cing'):
        return 'であって'
    if lemma == 'na' and _first(_head(np).ja if _head(np) else '') in grammar.TIME_NOUNS:
        return 'に'  # 時の「に」(dus gcig na → ある時に)
    info = grammar.PARTICLES.get(lemma)
    return info[1] if info and info[1] is not None else ''


def vp_japanese(vp, nxt):
    words = vp.words
    negated = any(w.kind == 'neg' for w in words)
    neg = next((w for w in words if w.kind == 'neg'), None)
    main = next((w for w in words if w.kind in ('verb', 'cop', 'exist')), None)
    aux = [w for w in words if w.kind in ('cop', 'exist') and w is not main]
    parts = [p.lemma for p in vp.particles]
    if main is None:
        return ''
    if main.kind == 'verb':
        verb = _first(main.ja) or 'する'
        tense = choose_tense(main, neg, parts)
        main.tense = tense
        if negated and tense == 'imp':
            return verb + 'な' + _vp_tail(parts, final=True)
        if 'cig' in parts and main.lemma in ('gyur', "'gyur"):
            return Modern.masu_stem(verb) + 'ますように' + _vp_tail(parts, final=True)  # 祈願 (gyur cig)
        if tense == 'imp' or 'cig' in parts:
            return Modern.masu_stem(verb) + 'なさい' + _vp_tail(parts, final=True)
        if main.nominal and aux and aux[0].kind == 'exist':
            # V-pa med → 〜することが無い (bral ba med pa → 離れることがない)
            exist = aux[0].ja
            if parts[:1] in (['nas'], ['las']):
                return verb + 'ことが' + exist + 'ことから' + _vp_tail(parts[1:])
            if exist == 'ない' and parts and parts[0] in ('te', 'cing', 'la'):
                exist = 'なく'
            return verb + 'ことが' + exist + _vp_tail([p for p in parts if p not in ('te', 'cing', 'la')])
        if main.nominal:
            if 'past' in getattr(main, 'tenses', ()) and neg is None and 'gi' in parts:
                tense = main.tense = 'past'  # 連体の動名詞は過去を先に (thos pa'i dus → 聞いた時)
            form = Modern.past_form(verb) if tense == 'past' else verb
            if negated:
                form = Modern.neg_stem(verb) + 'ない'  # ma skyes pa → 生じない
            return _nominal(form, vp, nxt)
        purpose = [x for x in vp.particles if x.lemma == 'la' and x.wylie in ('du', 'tu', 'r')]
        if purpose and not negated and nxt is not None and nxt.kind == 'vp' and \
                any(w.wylie in grammar.MOTION_VERBS or w.lemma in grammar.MOTION_VERBS for w in nxt.words):
            return Modern.masu_stem(verb) + 'に'  # 目的 (chu len du song → 水を取りに行った)
        if any(p in ('te', 'cing', 'la') for p in parts):
            form = Modern.te(verb) if not negated else Modern.neg_stem(verb) + 'ないで'
            return form + _vp_tail([p for p in parts if p not in ('te', 'cing', 'la')])
        if 'nas' in parts or 'las' in parts:
            return Modern.te(verb) + 'から' + _vp_tail([p for p in parts if p not in ('nas', 'las')])
        if 'kyang' in parts:
            return Modern.te(verb) + 'も' + _vp_tail([p for p in parts if p != 'kyang'])
        if negated:
            form = Modern.neg_stem(verb) + ('なかった' if tense == 'past' else 'ない')
        elif tense == 'past':
            form = Modern.past_form(verb)
        elif tense == 'fut':
            form = Modern.volitional(verb) if vp.first_person else verb + 'だろう'
        else:
            form = verb
        if aux:
            form = _aux(form, aux[0], negated)
        return form + _vp_tail(parts)
    # 繋辞・存在
    ja = main.ja
    if negated:
        ja = {'である': 'ではない', 'ある': 'ない', 'いらっしゃる': 'いらっしゃらない'}.get(ja, ja)
    if any(p in ('te', 'cing', 'la') for p in parts):
        # 接続: ない → なく、ある → あって、である → であって
        ja = {'ない': 'なく', 'ではない': 'ではなく', 'ある': 'あって', 'である': 'であって',
              'いらっしゃる': 'いらっしゃって'}.get(ja, ja)
        return ja + _vp_tail([p for p in parts if p not in ('te', 'cing', 'la')])
    if 'gi' in parts:
        return ja + ''.join(grammar.TERMS[p][0] for p in parts if p in grammar.POSTPOSITIONS)
    if parts[:1] in (['nas'], ['las']):
        return ja + 'ことから' + _vp_tail(parts[1:])  # med pa nas → 無いことから
    return ja + _vp_tail(parts)


def _volitional(verb):
    if verb.endswith('ずる'):
        return verb[:-2] + 'じよう'  # 行ずる → 行じよう
    return Modern.volitional(verb)


def _aux(form, aux, negated):
    """動詞 + yin / yod / 'dug (〜したのである・〜している)"""
    if aux.kind == 'cop':
        return form + 'のである'
    return form


def _nominal(form, vp, nxt):
    """動名詞 (+ pa) の後ろ: 属格なら連体形で名詞に掛ける、格助詞なら「〜こと + 助詞」"""
    parts = [p.lemma for p in vp.particles]
    post = ''.join(grammar.TERMS[p][0] for p in parts if p in grammar.POSTPOSITIONS)
    if 'gi' in parts:
        rest = parts[parts.index('gi') + 1:]
        tail = ''.join((grammar.PARTICLES[p][1] or '') for p in rest if p in grammar.PARTICLES and p != 'gi')
        return form + post + tail  # 連体 (thos pa'i dus → 聞いた時、med pa'i phyir → 無いために)
    if parts[:1] == ['dang']:
        main = next(w for w in vp.words if w.kind == 'verb')
        return (_first(main.ja) or 'する') + 'と'  # V-pa dang → 〜すると (smras pa dang → 言うと)
    if [x.wylie for x in vp.particles] in (['r'], ['du'], ['tu']) and nxt is not None and nxt.kind == 'vp':
        aux = next((w for w in nxt.words if w.kind == 'verb'), None)
        main = next(w for w in vp.words if w.kind == 'verb')
        verb = _first(main.ja) or 'する'
        if aux is not None and aux.lemma in ('gyur', "'gyur"):
            nxt.lead = verb + 'ように'   # V-par gyur → 〜するようになる
            return ''
        if aux is not None and aux.lemma == "'dod" or aux is not None and aux.wylie in ("'dod", "'dod pa"):
            nxt.lead = _volitional(verb) + 'と'   # V-par 'dod → 〜しようと欲する
            return ''
        if aux is not None and aux.lemma == 'byed' and aux.wylie not in ('bya', 'bgyi'):
            nxt.replace = grammar.CAUSATIVES.get(verb, verb)  # V-par byed → V する (zhi bar byed → 鎮める)
            return ''
        if aux is not None and aux.wylie in ('bya', 'bgyi'):
            nxt.replace = Modern.volitional(verb) if nxt.first_person else verb + 'べきだ'  # V-bar bya → 〜しよう
            return ''
    if not parts:
        if nxt is not None and nxt.kind == 'vp' and nxt.words[0].kind == 'cop':
            return form + 'の'
        if nxt is not None and nxt.kind == 'vp' and any(w.kind == 'exist' for w in nxt.words):
            return form + 'ことが'  # V-pa med → 〜することが無い (skrag pa med → 恐れることが無い)
        if nxt is not None and nxt.kind == 'np' and nxt.words and nxt.words[0].kind == 'det':
            return form  # V-pa de → 〜するそれ (関係節)
        if nxt is not None and nxt.kind == 'np' and nxt.words and _first(nxt.words[0].ja) in grammar.TIME_NOUNS:
            main = next(w for w in vp.words if w.kind == 'verb')
            verb = _first(main.ja) or 'する'
            return Modern.past_form(verb) if 'past' in getattr(main, 'tenses', ()) else verb  # thos pa dus → 聞いた時
        if nxt is None or nxt.kind == 'punct':
            return form  # 文末の動名詞は言い切り (bka' stsal pa → おっしゃった)
        return form + 'こと'
    out = form + ('の' if parts[0] in ('ni', 'kyang') else 'こと')
    for p in parts:
        info = grammar.PARTICLES.get(p)
        out += info[1] if info and info[1] else ''
    return out


def _vp_tail(parts, final=False):
    out = ''
    for p in parts:
        if p in ('go', 'cig'):
            continue
        info = grammar.PARTICLES.get(p)
        if info:
            out += info[2]
    return out


def choose_tense(verb, neg, parts):
    tenses = getattr(verb, 'tenses', set())
    if 'cig' in parts and 'imp' in tenses:
        return 'imp'
    if neg is not None and neg.wylie == 'ma':
        return 'imp' if tenses == {'imp'} else 'past'
    if neg is not None and neg.wylie == 'mi':
        return 'fut' if tenses == {'fut'} else 'pres'
    for t in ('past', 'pres', 'fut'):
        if tenses == {t}:
            return t
    if 'past' in tenses and 'pres' not in tenses:
        return 'past'
    if 'pres' in tenses:
        return 'pres'
    if tenses == {'imp'}:
        return 'imp'
    return 'pres' if not tenses else sorted(tenses)[0]


def japanese(phrases):
    out = ''
    for i, p in enumerate(phrases):
        nxt = phrases[i + 1] if i + 1 < len(phrases) else None
        if p.kind == 'np':
            p.ja = np_japanese(p)
        elif p.kind == 'vp':
            p.ja = vp_japanese(p, nxt)
            if p.replace is not None:
                parts = [x.lemma for x in p.particles]
                tail = '' if 'gi' in parts else _vp_tail(parts)  # 属格なら連体 (… zhi bar byed pa'i sngags → 鎮める呪)
                p.ja = (p.replace + tail).replace('だて', 'で')
            p.ja = p.lead + p.ja
        elif p.kind == 'adv':
            p.ja = p.words[0].ja
        else:
            p.ja = '、' if p.words[0].wylie.strip() in ('|', ';') else '。'
            before = phrases[i - 1] if i > 0 else None
            last = before.particles[-1].lemma if before is not None and before.particles else ''
            if last == 'dang' and i + 1 < len(phrases):
                p.ja = ''      # A dang། B dang། … (列挙)
            elif last in ('te', 'cing', 'la', 'nas') and i + 1 < len(phrases):
                p.ja = '、'    # 接続の後の区切り
            if out.endswith(('。', '、')):
                p.ja = ''
        out += p.ja
    words = [w for p in phrases for w in p.words]
    correlative = any(w.wylie in ('de bzhin', 'de bzhin du', 'de ltar') for w in words)  # ji ltar … de bzhin du
    if not correlative and any(w.wylie in grammar.QUESTION_WORDS for w in words) and out.rstrip('。、').endswith(('だ', 'る', 'う', 'た', 'い')):
        out = re.sub('だ$', '', out.rstrip('。')) + 'か'  # 疑問詞の文 (ji ltar bslab par bya → どのように学ぶべきか)
    if out and not out.endswith('。'):
        out += '。'
    return out


def sanskrit_notes(words, wylie_text=''):
    """サンスクリットの原語の注: 仏典の定型句 (漢訳つき) と、語ごとの原語 (Mahāvyutpatti・Hopkins)"""
    notes = []
    text = ' ' + re.sub(r'[/|;]', ' ', wylie_text) + ' '
    text = re.sub(' +', ' ', text)
    used = []
    for pattern, skt, kanyaku in grammar.FORMULAS:
        if ' %s' % pattern in text and not any(pattern in u for u in used):
            used.append(pattern)
            notes.append('梵語の定型句: %s → %s (%s)' % (pattern, skt, kanyaku))
    seen = set()
    for w in words:
        if w.kind not in ('noun', 'verb', 'adj', 'adv') or w.wylie in seen:
            continue
        seen.add(w.wylie)
        if any((' ' + w.wylie + ' ') in (' ' + u + ' ') for u in used):
            continue  # 定型句に含まれる語
        if getattr(w, 'term', False):
            ja, skt = grammar.TERMS[w.wylie]
            if skt:
                notes.append('梵語: %s → %s (%s)' % (w.wylie, skt, ja))
            continue
        if w.token.upos == 'SKT':
            continue
        keys = [w.wylie] + ([w.lemma] if w.kind == 'verb' and w.lemma and w.lemma != w.wylie else [])
        if getattr(w, 'pieces', None):
            keys += [_pieces_wylie(p) for p in w.pieces]
        found = []
        for key in keys:
            if key in grammar.SANSKRIT:
                found = [grammar.SANSKRIT[key]]
                break
            found = list(dictionary.sanskrit_all(key))
            if found:
                break
        if found and found[0] != 'na':
            notes.append('梵語: %s → %s' % (w.wylie, ', '.join(found)))
    return notes


def _pieces_wylie(text):
    return script.word_translit(text, dictionary.known())


# ----------------------------------------------------------------------

def sentences(text):
    """文に分ける: シャド (།) の連なりまでを1文 (། ། も前の文に含める)。接続の助詞 (dang, te, cing …) の後の
    シャドでは切らない (tshor ba dang། 'du shes dang། … stong pa'o།)"""
    for line in text.splitlines():
        buf = ''
        for m in re.finditer(r'[^།༎༏༐༑༔]+[།༎༏༐༑༔\s]*', line):
            piece = m.group(0)
            buf += piece
            last = re.split('[་ ]+', re.sub('[་།༎༏༐༑༔\\s]+$', '', piece).strip())[-1:]
            if last and script.translit(last[0]) in grammar.CONTINUING and '༎' not in piece and \
                    piece.count('།') < 2:
                continue
            if script.is_tibetan(buf):
                yield buf.strip()
            buf = ''
        if buf.strip() and script.is_tibetan(buf):
            yield buf.strip()


def analyze_sentence(text):
    tokens = segment.tokenize(text)
    words = classify(tokens)
    phrases = group(words)
    notes = []
    assign_cases(phrases, notes)
    ja = japanese(phrases)
    notes += sanskrit_notes(words, script.translit(text, dictionary.known()))
    return TibetanAnalysis(text, words, phrases, ja, notes)


def analyze_text(text):
    segment.reset()
    for s in sentences(text):
        yield analyze_sentence(s)
