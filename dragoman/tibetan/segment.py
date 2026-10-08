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


def _merge_compounds(tokens):
    """botok が分けた複合語をつなぐ (byang chub + sems dpa' → byang chub sems dpa')。つないだ形が Hill & Garrett の
    名詞か、訳語を決めてある語のとき (3語まで)"""
    out = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        for n in (3, 2):
            group = tokens[i:i + n]
            if len(group) < n or any(x.upos in ('PUNCT', 'PART', 'ADP') or x.affix or
                                     x.wylie in ('med', 'min', 'yod', 'yin', 'red', 'ma', 'mi') for x in group):
                continue
            wylie = ' '.join(x.wylie for x in group)
            if wylie in grammar.GLOSSES or any(tag.startswith('n.') for tag in dictionary.tags(wylie)):
                out.append(Token(TSHEG.join(x.text for x in group), wylie, 'NOUN', wylie))
                i += n
                break
        else:
            out.append(t)
            i += 1
    return out


def _join_wylie(tokens):
    out = ''
    for t in tokens:
        out += t.wylie if t.affix else (' ' if out else '') + t.wylie
    return out


def _join_text(tokens):
    out = ''
    for t in tokens:
        out += t.text if t.affix or not out else TSHEG + t.text
    return out


def _merge_terms(tokens):
    """仏教の術語 (grammar.TERMS。助詞をまたぐもの: shes rab kyi pha rol tu phyin pa) を1語にする。長いものから"""
    out = []
    i = 0
    longest = max(len(k.split()) for k in grammar.TERMS) + 3
    while i < len(tokens):
        for n in range(min(longest, len(tokens) - i), 0, -1):
            group = tokens[i:i + n]
            if any(t.upos == 'PUNCT' for t in group) or (n == 1 and ' ' not in group[0].wylie and
                                                          group[0].wylie not in grammar.TERMS):
                continue
            wylie = _join_wylie(group)
            starts = i == 0 or tokens[i - 1].upos == 'PUNCT'  # 文頭の語は助詞ではない (lam med → 道が無い)
            if wylie in grammar.TERMS and (n > 1 or group[0].upos not in ('PART', 'ADP') or starts):
                out.append(Token(_join_text(group), wylie, 'TERM', wylie))
                i += n
                break
            if wylie[-1:] in ('s', 'r') and wylie[:-1] in grammar.TERMS and group[-1].text.endswith(('ས', 'ར')) \
                    and (n > 1 or ' ' in wylie):
                # 術語 + 語に付いた -s (能格) / -r (la don) が1語になったもの (shA ri'i bus、dri zar)
                out.append(Token(_join_text(group)[:-1], wylie[:-1], 'TERM', wylie[:-1]))
                out.append(Token(group[-1].text[-1], wylie[-1], 'PART', 'gis' if wylie[-1] == 's' else 'la', True))
                i += n
                break
        else:
            out.append(tokens[i])
            i += 1
    return out


# サンスクリットにしか使わない字: 長母音 ཱ、ྀ (ṛ)、そり舌音 (ཊ〜ཎ)、ཥ、ཀྵ、有声の有気音 (གྷ དྷ བྷ ཛྷ ཌྷ)、ཾ ྃ、ཛྙ (jñ)
SANSKRIT_MARKS = re.compile('[\u0f71\u0f80\u0f81\u0f4a-\u0f4e\u0f65\u0f69\u0f9a-\u0f9e\u0fb5\u0fb9'
                            '\u0f43\u0f52\u0f57\u0f5c\u0f93\u0fa2\u0fa7\u0fac\u0f7e\u0f83\u0f82]|ཛྙ|ྭྭ')


def is_sanskrit(text):
    """チベット文字で書いたサンスクリットらしい綴り (長母音・そり舌音・インドの重ね字)"""
    return bool(SANSKRIT_MARKS.search(text))


def _sanskrit_chunks(tokens):
    """区切り記号までの句で、音節の多くがサンスクリットの字なら句全体を音写とする (真言: ga te ga te pA ra ga te)"""
    global _previous_sanskrit
    out, chunk = [], []
    previous_sanskrit = _previous_sanskrit  # 前の文 (区切り記号までの句) が音写だったか
    for t in tokens + [None]:
        if t is None or t.upos == 'PUNCT':
            words = [x for x in chunk if x.upos != 'TERM']
            marked = sum(1 for x in words if is_sanskrit(x.text))
            # 前の句が音写なら、サンスクリットの字が1つでもあれば続き (真言の ga te ga te pA ra ga te)
            joined = ''.join(x.wylie for x in chunk).replace(' ', '')
            known = joined.startswith(grammar.MANTRAS)
            if chunk and len(words) == len(chunk) and (known or marked and (marked * 3 >= len(words) or previous_sanskrit)):
                out.append(Token(TSHEG.join(x.text for x in chunk), ' '.join(x.wylie for x in chunk), 'SKT', ''))
                previous_sanskrit = True
            else:
                out += chunk
                previous_sanskrit = previous_sanskrit and not chunk
            chunk = []
            if t is not None:
                out.append(t)
        else:
            chunk.append(t)
    _previous_sanskrit = previous_sanskrit
    return out


_previous_sanskrit = False


def reset():
    """文章の頭で、前の文の状態 (真言の続き) を消す"""
    global _previous_sanskrit
    _previous_sanskrit = False


def _merge_sanskrit(tokens):
    """サンスクリットの音写の連なり (経題・真言) を1語にする。短い音節 (ga, ra, ta) は前後が音写なら含める"""
    out = []
    i = 0
    while i < len(tokens):
        if tokens[i].upos not in ('PUNCT', 'TERM') and is_sanskrit(tokens[i].text):
            j = i
            while j + 1 < len(tokens) and tokens[j + 1].upos not in ('PUNCT', 'TERM') and \
                    (is_sanskrit(tokens[j + 1].text) or
                     (j + 2 < len(tokens) and is_sanskrit(tokens[j + 2].text) and len(tokens[j + 1].text) <= 3)):
                j += 1
            group = tokens[i:j + 1]
            out.append(Token(TSHEG.join(t.text for t in group), ' '.join(t.wylie for t in group), 'SKT', ''))
            i = j + 1
            continue
        out.append(tokens[i])
        i += 1
    return out


def i_next_is_copula(tokens, t):
    i = tokens.index(t)
    return i + 1 < len(tokens) and tokens[i + 1].wylie in ('yin', 'red', 'yod', 'lags')


def _fix(tokens):
    for i, t in enumerate(tokens[:-1]):
        # དཔ + འི → dpa + 'i (botok が切った語末の འ を補って転写する。そのままだと dap)
        nxt = tokens[i + 1]
        if nxt.affix and (nxt.text.startswith('འ') or nxt.wylie in ('s', 'r')) and not t.text.endswith('འ') and \
                t.upos != 'PUNCT':
            # 語に付く助詞 (-s, -r, -'i) は母音で終わる音節に付くので、前の音節は a で終わる (མཐ + ར → mtha + r)
            fixed = _wylie(t.text + 'འ')
            if fixed.endswith("'"):
                t.wylie = t.lemma = fixed[:-1]
    split = []
    for t in tokens:
        # སྣ་མེད → སྣ + མེད (名詞と存在動詞・繋辞を botok が1語にしたもの)
        m = re.match(r"^(.+) (med|min|yod|yin|med pa|min pa)$", t.wylie)
        if m and not t.affix and t.upos != 'PUNCT' and \
                (m.group(1) in grammar.TERMS or not dictionary.tags(t.wylie) and dictionary.is_word(m.group(1))):
            n = len(m.group(2).split())
            parts = t.text.split(TSHEG)
            split.append(Token(TSHEG.join(parts[:-n]), m.group(1), 'NOUN', m.group(1)))
            split.append(Token(TSHEG.join(parts[-n:]), m.group(2), 'VERB', m.group(2)))
            continue
        # གཞན་མ + ཡིན → གཞན + མ (否定) (後ろが繋辞・存在動詞なら、語末の ma は否定)
        if i_next_is_copula(tokens, t) and t.wylie.endswith(' ma') and not t.affix and \
                not dictionary.is_word(t.wylie) and t.wylie not in grammar.GLOSSES:
            parts = t.text.split(TSHEG)
            split.append(Token(TSHEG.join(parts[:-1]), t.wylie[:-3], 'NOUN', t.wylie[:-3]))
            split.append(Token(parts[-1], 'ma', 'PART', 'ma'))
            continue
        # དེ་དེ → དེ + དེ (同じ指示詞の繰り返し: de de bzhin no「それはそのとおりである」)
        if t.wylie in ('de de', "'di 'di"):
            for part in t.text.split(TSHEG):
                split.append(Token(part, t.wylie.split()[0], 'DET', t.wylie.split()[0]))
            continue
        split.append(t)
    tokens = _merge_sanskrit(_sanskrit_chunks(_merge_terms(_merge_compounds(split))))
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
                (t.wylie == 'la' or (t.upos == 'VERB' and dictionary.stems(t.wylie + 's') and
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
