#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# チベット文字の文を語に分ける
#
# botok (OpenPecha、Apache-2.0。辞書パックは $DRAGOMAN_DATA/bo/botok/ に初回に自動でダウンロードされる) があれば
# それで分け、語に付いた格助詞 (རྒྱལ་པོས → རྒྱལ་པོ + ས) も切り離す。無ければ、辞書の見出し語で最長一致を取る。
# botok の誤りのうち、規則で直せるものを直す (རྟ་ལས「馬から」が རྟ་ལ + ས になるもの)。
#
import functools
import re
import warnings
from dataclasses import dataclass

from dragoman.core import paths
from . import dictionary, grammar, script

TSHEG = '་'
SHAD = re.compile('[།༎༏༐༑༔]')


@dataclass
class Token:
    text: str           # チベット文字 (語末のツェクは除く)
    wylie: str          # ワイリー式
    upos: str           # botok の品詞 (NOUN, VERB, PART, ADP …)。区切り記号は PUNCT
    lemma: str = ''     # 代表の形 (助詞の異形 → 代表の形、ワイリー式)
    affix: bool = False  # 前の語に付いた助詞 (-s, -r, -'i …)


def _wylie(text):
    return script.word_translit(text, dictionary.known())


@functools.lru_cache(maxsize=1)
def _botok():
    try:
        from botok import WordTokenizer
        from botok.config import Config
    except ImportError:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        config = Config(dialect_name='general', base_path=paths.data('bo', 'botok'))
        return WordTokenizer(config=config)


def available():
    return _botok() is not None


def tokenize(text):
    wt = _botok()
    tokens = _tokenize_botok(wt, text) if wt is not None else _tokenize_dictionary(text)
    return _fix(tokens)


def _tokenize_botok(wt, text):
    out = []
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        raw = wt.tokenize(text, split_affixes=True)
    for t in raw:
        if t.chunk_type == 'PUNCT' or not script.is_tibetan(t.text):
            if t.text.strip():
                out.append(Token(t.text.strip(), script.translit(t.text.strip()), 'PUNCT'))
            continue
        surface = t.text.strip().rstrip(TSHEG)
        wylie = AFFIX_TEXTS.get(surface, _wylie(surface)) if t.affix else _wylie(surface)
        if t.affix:
            lemma = grammar.normalize(wylie.lstrip())
        else:
            lemma = grammar.normalize(wylie) if t.pos in ('PART', 'ADP') else wylie
        out.append(Token(surface, wylie, t.pos or 'NO_POS', lemma, bool(t.affix)))
    return out


AFFIXES = ("'i", "'o", "'am", "'ang", "'u")
AFFIX_TEXTS = {'ས': 's', 'ར': 'r', 'འི': "'i", 'འོ': "'o", 'འམ': "'am", 'འང': "'ang", 'འུ': "'u"}


def _tokenize_dictionary(text):
    """botok が無いとき: 音節を語の見出しで最長一致 (4音節まで)。語末の音節に付いた助詞 (-s, -r, -'i …) は切り離す"""
    out = []
    for chunk in re.split('(%s+)' % SHAD.pattern, text):
        if not chunk.strip():
            continue
        if SHAD.match(chunk.strip()):
            out.append(Token(chunk.strip(), script.translit(chunk.strip()), 'PUNCT'))
            continue
        syllables = [s for s in re.split('[་ ]+', chunk) if s]
        i = 0
        while i < len(syllables):
            if grammar.particle(_wylie(syllables[i])) or _wylie(syllables[i]) in grammar.NEGATIONS:
                wylie = _wylie(syllables[i])
                upos = 'PART' if grammar.particle(wylie) else 'PART'
                out.append(Token(syllables[i], wylie, upos, grammar.normalize(wylie)))
                i += 1
                continue
            match = None
            for n in range(min(4, len(syllables) - i), 0, -1):
                surface = TSHEG.join(syllables[i:i + n])
                wylie = _wylie(surface)
                last = _wylie(syllables[i + n - 1])
                ends_in_case = n > 1 and grammar.particle(last) is not None  # 句末の助詞まで1語にしない
                if (dictionary.is_word(wylie) and not ends_in_case) or (n > 1 and wylie in grammar.ADVERBS):
                    match = (n, surface, wylie, None)
                    break
                for affix_text, affix in sorted(AFFIX_TEXTS.items(), key=lambda x: -len(x[0])):
                    host = _wylie(surface[:-len(affix_text)])
                    if surface.endswith(affix_text) and len(syllables[i + n - 1]) > len(affix_text) and \
                            dictionary.is_word(host) and not (n > 1 and grammar.particle(host.split()[-1])):
                        match = (n, surface[:-len(affix_text)], _wylie(surface[:-len(affix_text)]), affix_text)
                        break
                if match:
                    break
            if match is None:
                match = (1, syllables[i], _wylie(syllables[i]), None)
            n, surface, wylie, affix_text = match
            upos = 'VERB' if dictionary.stems(wylie) and dictionary.pos(wylie) == 'verb' else 'NO_POS'
            out.append(Token(surface, wylie, upos, wylie))
            if affix_text:
                affix = AFFIX_TEXTS[affix_text]
                out.append(Token(affix_text, affix, 'PART', grammar.normalize(affix), True))
            i += n
    return out


def _fix(tokens):
    out = []
    for i, t in enumerate(tokens):
        if t is None:
            continue
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        # རྟ་ལ + ས → རྟ + ལས (奪格の las・nas を、語の一部と取り違えたもの)
        if nxt is not None and nxt.affix and nxt.wylie == 's' and t.wylie.endswith((' la', ' na')) and \
                (t.upos == 'NO_POS' or not dictionary.entries(t.wylie)) and dictionary.entries(t.wylie[:-3]):
            host_text = t.text.rsplit(TSHEG, 1)[0]
            out.append(Token(host_text, t.wylie[:-3], 'NOUN', t.wylie[:-3]))
            part = t.wylie[-2:] + 's'
            out.append(Token(t.text.rsplit(TSHEG, 1)[1] + nxt.text, part, 'ADP', part))
            tokens[i + 1] = None
            continue
        # སྨྲ + ས → སྨྲས (動詞の過去の語幹の -s を、格助詞として切ったもの)、ལ + ས → ལས
        if nxt is not None and nxt.affix and nxt.wylie == 's' and \
                (t.wylie == 'la' or (dictionary.stems(t.wylie + 's') and
                                     any(x.startswith('v.') for x in dictionary.tags(t.wylie + 's')))):
            merged = t.wylie + 's'
            out.append(Token(t.text + nxt.text, merged, 'ADP' if merged == 'las' else 'VERB', merged))
            tokens[i + 1] = None
            continue
        # བསྒོའོ → བསྒོ + འོ (文末の 'o が付いたまま)
        if not t.affix and t.wylie.endswith("'o") and len(t.wylie) > 2 and t.text.endswith('འོ') and \
                not dictionary.entries(t.wylie):
            host = t.wylie[:-2]
            out.append(Token(t.text[:-2], host, 'VERB' if dictionary.stems(host) else t.upos, host))
            out.append(Token('འོ', "'o", 'PART', 'go', True))
            continue
        # གྱུར་ཅིག → གྱུར + ཅིག (動詞に命令・祈願の cig が付いたまま)
        m = re.match(r"^(.+) (cig|zhig|shig)$", t.wylie)
        if m and not t.affix and dictionary.stems(m.group(1)):
            host_text, last = t.text.rsplit(TSHEG, 1)
            out.append(Token(host_text, m.group(1), 'VERB', m.group(1)))
            out.append(Token(last, m.group(2), 'PART', 'cig'))
            continue
        # ཁོས → ཁོ + ས (代名詞に付いた能格を botok が切らないもの)
        if not t.affix and t.wylie.endswith('s') and t.wylie[:-1] in grammar.PRONOUNS and \
                t.wylie not in grammar.PRONOUNS and t.text.endswith('ས'):
            out.append(Token(t.text[:-1], t.wylie[:-1], 'PRON', t.wylie[:-1]))
            out.append(Token('ས', 's', 'PART', 'gis', True))
            continue
        out.append(t)
    return out
