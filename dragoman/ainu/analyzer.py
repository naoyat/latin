#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アイヌ語の解析と日本語訳
#
# 語順は日本語と同じ (主語-目的語-動詞、後置詞、修飾語は名詞の前) なので、チベット語と同じく共通の解析器は通さず、
# 語順のまま日本語にする:
#   1. 語に分ける。決まった言い方 (ruwe ne「〜のだ」、hawe ne、kotom siran「〜のようだ」) は1語に
#   2. 語の働きを決める: 名詞の後ろの後置詞 (ta「で」、un「に」、orowa「から」…)、用言の後ろの助詞 (wa「〜て」、kor「〜ながら」、
#      ko / akusu「〜すると」、ciki「〜たら」、kusu「〜ので」、sekor「〜と」…)、否定 somo、完了の a、繋辞 ne
#   3. 節 (用言 + 助詞まで) ごとに、格の印の無い名詞を「が / を」にする (他動詞で名詞が2つなら が・を、1つなら を、
#      自動詞なら が)。人称の接辞の主語・目的語 (ku= 私が、en= 私を) は、名詞が無ければ補う
#   4. 用言は後ろの助詞で形を変える (wa → 〜て、kor → 〜ながら、ciki → 〜たら …)
#
import re
from dataclasses import dataclass, field

from . import grammar, morphology, script

TOKEN = re.compile(r"[A-Za-zÀ-ÿ'’=\-]+|[.,;:!?“”\"()]")
MULTI = ('ruwe ne', 'siri ne', 'hawe ne', 'kusu ne', 'kotom siran', 'ka somo', 'sekor hawe')
PUNCT = set('.,;:!?“”"()')


@dataclass
class Token:
    surface: str
    key: str
    kind: str = ''        # noun / verb / adj / adv / det / num / pron / postp / particle / neg / aux / copula / punct / unknown
    gloss: str = ''
    morph: object = None
    note: str = ''
    case: str = ''        # 決めた助詞 (が / を)


@dataclass
class AinuAnalysis:
    text: str
    tokens: list = field(default_factory=list)
    japanese: str = ''

    @property
    def kana(self):
        return script.kana(' '.join(t.surface for t in self.tokens if t.kind != 'punct'))


def tokenize(text):
    words = TOKEN.findall(text)
    out = []
    i = 0
    while i < len(words):
        pair = ' '.join(script.key(w) for w in words[i:i + 2])
        if pair in MULTI:
            out.append(words[i] + ' ' + words[i + 1])
            i += 2
            continue
        out.append(words[i])
        i += 1
    return out


NOMINAL = {'noun', 'pron'}
VERBAL = {'verb', 'adj', 'copula'}


def classify(words):
    tokens = []
    for i, w in enumerate(words):
        key = script.key(w) if w not in PUNCT else w
        prev = tokens[-1] if tokens else None
        if w in PUNCT:
            tokens.append(Token(w, key, 'punct'))
            continue
        after_verb = prev is not None and prev.kind in VERBAL | {'neg', 'aux', 'unknown'}
        after_noun = prev is not None and prev.kind in NOMINAL | {'det', 'num', 'unknown'}
        if key in ('ruwe ne', 'siri ne', 'hawe ne', 'kusu ne'):
            tokens.append(Token(w, key, 'particle', grammar.VERB_PARTICLES.get(key, ('final', 'のだ'))[1]))
            continue
        if key == 'kotom siran':
            tokens.append(Token(w, key, 'particle', 'ようだ', note='like'))
            continue
        if after_verb and key in grammar.VERB_PARTICLES:
            kind, ja = grammar.VERB_PARTICLES[key]
            tokens.append(Token(w, key, 'particle', ja, note=kind))
            continue
        if after_verb and key == 'a':
            tokens.append(Token(w, key, 'aux', '', note='完了 (〜した)'))
            continue
        if after_noun and key == 'ne':
            tokens.append(Token(w, key, 'copula', 'である'))
            continue
        if after_noun and key in grammar.POSTPOSITIONS:
            tokens.append(Token(w, key, 'postp', grammar.POSTPOSITIONS[key]))
            continue
        if key in grammar.NEGATIONS:
            tokens.append(Token(w, key, 'neg', 'ない'))
            continue
        if key in grammar.POSTPOSITIONS and key not in grammar.LEXICON:
            tokens.append(Token(w, key, 'postp', grammar.POSTPOSITIONS[key]))  # 行頭・句読点の後ろでも
            continue
        if key in grammar.VERB_PARTICLES and key not in grammar.LEXICON and not after_noun:
            kind, ja = grammar.VERB_PARTICLES[key]
            tokens.append(Token(w, key, 'particle', ja, note=kind))
            continue
        m = morphology.analyze(w)
        kind = {'vi': 'verb', 'vt': 'verb', 'adj': 'adj', 'noun': 'noun', 'pron': 'pron', 'adv': 'adv', 'det': 'det',
                'num': 'num', 'unknown': 'unknown', 'particle': 'particle', 'postp': 'postp'}.get(m.pos, 'noun')
        gloss = m.gloss
        if kind == 'unknown':
            gloss = script.kana(w) or w   # 引けない語 (人名・繰り返し句) はカタカナで
        tokens.append(Token(w, key, kind, gloss, m))
    # 形容詞 (性質の自動詞) の後ろに名詞が来れば修飾 (pirka kotan「美しい村」)
    for i, t in enumerate(tokens[:-1]):
        if t.kind == 'adj' and tokens[i + 1].kind in NOMINAL:
            t.kind = 'attr'
    return tokens


# ----------------------------------------------------------------------
# 日本語

def _verb_forms():
    from dragoman.kobun.modernize import Modern
    return Modern


def _is_verb_ja(ja):
    return bool(ja) and ja[-1] in 'うくぐすつぬぶむる' and not ja.endswith('ようだ')


def conjugate(verb, particle_kind, negated, perfect):
    """日本語の用言を、後ろの助詞の種類で活用させる"""
    M = _verb_forms()
    adjective = verb.endswith('い') and not _is_verb_ja(verb)
    try:
        if not _is_verb_ja(verb) and not adjective:
            base = verb  # 〜ようだ・〜である など
            return base + {'te': 'で', 'while': 'で', 'when': 'と', 'if': 'なら', 'because': 'ので', 'but': 'けれど'}.get(
                particle_kind, '')
        if negated:
            stem = (verb[:-1] + 'く' if adjective else M.neg_stem(verb)) + 'ない'
            verb, adjective = stem, True
        if particle_kind == 'te':
            return verb[:-1] + 'くて' if adjective else M.te(verb)
        if particle_kind == 'while':
            return verb + 'まま' if adjective else M.masu_stem(verb) + 'ながら'
        if particle_kind == 'if':
            return (verb[:-1] + 'かったら') if adjective else M.past_form(verb) + 'ら'
        if particle_kind == 'when':
            return verb + 'と'
        if particle_kind == 'because':
            return verb + 'ので'
        if particle_kind == 'but':
            return verb + 'けれど'
        if perfect:
            return (verb[:-1] + 'かった') if adjective else M.past_form(verb)
    except Exception:
        pass
    return verb


def translate_clause(clause, particle):
    """節 (名詞句・副詞・用言) → 日本語"""
    verbs = [t for t in clause if t.kind in ('verb', 'adj', 'copula')]
    verb = verbs[-1] if verbs else None
    negated = any(t.kind == 'neg' for t in clause)
    perfect = any(t.kind == 'aux' for t in clause)
    transitive = verb is not None and verb.morph is not None and verb.morph.pos == 'vt'
    bare = [t for i, t in enumerate(clause) if t.kind in NOMINAL | {'unknown'} and t is not verb and
            not (i + 1 < len(clause) and clause[i + 1].kind in ('postp', 'copula'))]
    if transitive:
        cases = ['が', 'を'] if len(bare) >= 2 else ['を']
        if verb.morph.object and len(bare) == 1:
            cases = ['が']
    else:
        cases = ['が'] * len(bare)
    for t, case in zip(bare[-len(cases):] if len(bare) > len(cases) else bare, cases[-len(bare):]):
        t.case = case
    out = []
    morph = verb.morph if verb is not None else None
    verb_ja = verb.gloss.split(' (')[0] if verb is not None else ''
    if verb is not None and verb.key.endswith('ki') and morph is not None and morph.parts[-1] == 'ki':
        noun = next((t for t in reversed(bare) if t.key in grammar.KI_COMPOUNDS), None)
        if noun is not None:
            verb_ja = grammar.KI_COMPOUNDS[noun.key]   # rekpo ki「歌をする」→ 歌う
            noun.case = 'を'
    subject = morph.subject if morph is not None and morph.subject and not any(t.case == 'が' for t in bare) else ''
    if subject and subject == _context.get('subject'):
        subject = ''   # 同じ主語は繰り返さない (語りの「私が」)
    elif subject:
        _context['subject'] = subject
    if morph is not None and morph.object and not any(t.case == 'を' for t in bare):
        out.append(morph.object + ('に' if morph.gloss in ('与える',) else 'を'))
    for i, t in enumerate(clause):
        if t is verb or t.kind in ('neg', 'aux') or t.case == 'compound':
            continue
        if t.kind == 'postp':
            out[-1:] = [(out[-1] if out else '') + t.gloss]
            continue
        if t.kind == 'copula' and t is not verb:
            continue
        piece = t.gloss
        if t.case:
            piece += t.case
        out.append(piece)
    if verb is not None:
        if verb.kind == 'copula':
            out[-1:] = [(out[-1] if out else '') + conjugate('である', particle[0] if particle else '', negated, False)]
        else:
            if subject:
                out.append(subject + 'が')   # 人称の接辞の主語は動詞の直前に (という歌を私が歌いながら)
            out.append(conjugate(verb_ja, particle[0] if particle else '', negated, perfect))
    text = ''.join(out)
    if particle and particle[0] == 'like' and text.endswith('である'):
        text = text[:-3] + 'のようだ'  # 〜 ne kotom siran → 〜のようだ
    elif particle and particle[0] in ('quote', 'final', 'purpose', 'until', 'like'):
        text += particle[1]
    return text


_context = {}


def translate(tokens):
    """節ごとに日本語にしてつなぐ。節は用言の後ろの助詞・句読点で切る"""
    out = []
    clause = []
    for t in tokens:
        if t.kind == 'particle':
            out.append(translate_clause(clause, (t.note or 'final', t.gloss)))
            clause = []
            continue
        if t.kind == 'punct':
            if clause:
                out.append(translate_clause(clause, None))
                clause = []
            if t.surface in '.!?':
                out.append('。')
            elif t.surface in ',;:':
                out.append('、')
            elif t.surface in '“”"':
                out.append('「' if t.surface == '“' else '」')
            continue
        clause.append(t)
    if clause:
        out.append(translate_clause(clause, None))
    text = ''.join(out)
    text = re.sub('、+', '、', text).replace('、。', '。')
    return text


def sentences(text):
    """文に分ける (句点・疑問符)。行は続けて読む (ユーカラは行が文の途中で切れる)"""
    buf = []
    words = tokenize(' '.join(text.splitlines()))
    for i, token in enumerate(words):
        buf.append(token)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if token in ('.', '!', '?') and nxt not in ('”', '"'):
            yield buf
            buf = []
        elif token in ('”', '"') and buf[-2:-1] and buf[-2] in ('.', '!', '?'):
            yield buf
            buf = []
    if buf:
        yield buf


def _join(words):
    text = ''
    for w in words:
        if w in PUNCT and w not in '“(':
            text += w
        elif text.endswith(('“', '(')):
            text += w
        else:
            text += (' ' if text else '') + w
    return text


def analyze_sentence(words):
    tokens = classify(words)
    return AinuAnalysis(_join(words), tokens, translate(tokens))


def analyze_text(text):
    _context.clear()   # 文章ごとに、語りの主語を覚え直す
    for words in sentences(text):
        yield analyze_sentence(words)
