#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文と文をつなぐ語 (et, autem, igitur …) と従属節の接続詞 (ubi, postquam, dum …)
#
#   kind: coord (等位: 節の頭) / post (後置: 節の2語目。autem, enim, igitur …) / sub (従属節を導く) /
#         adv (文の副詞: tum, tandem …。節の頭)
#   en / ru / sa: 各言語の語。sa の (語, 相関語) は、従属節の yadA に主節の tadA を対にするもの
#   sa_enclitic: サンスクリットで節の最初の語の後ろに置く語 (ca, tu, hi)
#
CONNECTIVES = {
    'et': ('coord', 'and', 'и', 'ca'),
    'atque': ('coord', 'and', 'и', 'ca'),
    'ac': ('coord', 'and', 'и', 'ca'),
    'que': ('coord', 'and', 'и', 'ca'),
    'neque': ('coord', 'and not', 'и не', 'na ca'),
    'nec': ('coord', 'and not', 'и не', 'na ca'),
    'sed': ('coord', 'but', 'но', 'kintu'),
    'at': ('coord', 'but', 'но', 'kintu'),
    'autem': ('post', 'however', 'же', 'tu'),
    'enim': ('post', 'for', 'ведь', 'hi'),
    'nam': ('coord', 'for', 'ведь', 'hi'),
    'namque': ('coord', 'for', 'ведь', 'hi'),
    'igitur': ('post', 'therefore', 'поэтому', 'ataH'),
    'itaque': ('coord', 'therefore', 'поэтому', 'ataH'),
    'tamen': ('post', 'nevertheless', 'однако', 'taTApi'),
    'vērō': ('post', 'indeed', 'же', 'tu'),
    'quoque': ('post', 'also', 'тоже', 'api'),
    'tum': ('adv', 'then', 'тогда', 'tadA'),
    'deinde': ('adv', 'then', 'затем', 'tataH'),
    'tandem': ('adv', 'at last', 'наконец', 'ante'),
    'statim': ('adv', 'immediately', 'сразу', 'sadyaH'),
    'diū': ('adv', 'for a long time', 'долго', 'cirAt'),
    'iam': ('adv', 'already', 'уже', 'eva'),
    'ita': ('adv', 'so', 'так', 'evam'),
    'sīc': ('adv', 'thus', 'так', 'evam'),
    'ut': ('sub', 'so that', 'чтобы', ('yena', '')),
    'nē': ('sub', 'so that not', 'чтобы не', ('yena na', '')),
    'etsī': ('sub', 'although', 'хотя', ('yadyapi', 'taTApi')),
    'quoniam': ('sub', 'since', 'так как', ('yataH', 'ataH')),
    'sīve': ('coord', 'or', 'или', 'vA'),
    'seu': ('coord', 'or', 'или', 'vA'),
    'ubi': ('sub', 'when', 'когда', ('yadA', 'tadA')),
    'cum': ('sub', 'when', 'когда', ('yadA', 'tadA')),   # 接続詞の cum (解析で中身の無い前置詞句になったもの)
    'postquam': ('sub', 'after', 'после того как', ('yadA', 'tadA')),
    'dum': ('sub', 'while', 'пока', ('yAvat', 'tAvat')),
    'quod': ('sub', 'because', 'потому что', ('yataH', 'ataH')),
    'quia': ('sub', 'because', 'потому что', ('yataH', 'ataH')),
    'sī': ('sub', 'if', 'если', ('yadi', 'tarhi')),
    'nisi': ('sub', 'unless', 'если не', ('yadi na', 'tarhi')),
    'antequam': ('sub', 'before', 'прежде чем', ('prAk', '')),
    'priusquam': ('sub', 'before', 'прежде чем', ('prAk', '')),
    'quamquam': ('sub', 'although', 'хотя', ('yadyapi', 'taTApi')),
    'simul': ('sub', 'as soon as', 'как только', ('yadA eva', 'tadA')),   # simul atque「〜するとすぐに」
}
# 従属節の後ろに来たときの読み (ubi「〜するところの」: ad eum locum vēnit ubi Medūsa dormiēbat)
AFTER_MAIN = {'ubi': ('where', 'где', ('yatra', ''))}
SA_ENCLITIC = {'ca', 'tu', 'hi', 'api'}


def lookup(word):
    from .english import _flat
    key = word.lower()
    return CONNECTIVES.get(key) or CONNECTIVES.get(_flat(key))


def is_connective(word):
    return lookup(word) is not None


def key(word):
    """表の見出し (マクロンの有無を問わない)"""
    from .english import _flat
    lower = word.lower()
    if lower in CONNECTIVES:
        return lower
    flat = _flat(lower)
    return next((k for k in CONNECTIVES if _flat(k) == flat), lower)


LANG_INDEX = {'en': 1, 'ru': 2, 'sa': 3}


def _word(key, lang, after_main=False):
    entry = AFTER_MAIN[key] if after_main and key in AFTER_MAIN else CONNECTIVES[key][1:]
    if lang == 'la':
        return key
    return entry[LANG_INDEX[lang] - 1]


def wrap(text, clause, lang, previous=None):
    """節の文につなぎの語を付ける。previous は一つ前の節 (サンスクリットの相関語 tadA を付けるため)"""
    if not text:
        return text
    front, second = [], []
    for key in clause.connectives:
        kind = CONNECTIVES[key][0]
        word = _word(key, lang)
        if lang == 'la' and key == 'que':
            second.append('que')
        elif (lang == 'la' and kind == 'post') or (lang == 'ru' and word == 'же') or \
                (lang == 'sa' and word in SA_ENCLITIC):
            second.append(word)
        elif lang == 'sa' and word == 'na ca':
            front.append('na')
            second.append('ca')
        else:
            front.append(word)
    if clause.subordinator:
        word = _word(clause.subordinator, lang, clause.after_main)
        front.append(word[0] if isinstance(word, tuple) else word)
    elif lang == 'sa' and previous is not None and previous.subordinator and not previous.after_main:
        correlative = _word(previous.subordinator, 'sa')[1]
        if correlative:
            front.append(correlative)   # yadA … tadA …
    if lang == 'en' and front and any(CONNECTIVES[k][0] == 'post' for k in clause.connectives):
        front[-1] += ','   # However, …
    if front:
        text = ' '.join(front) + ' ' + text
    if second:   # 後置の語は (前置の語も含めて) 最初の語の後ろ: yadA ca …、postquam autem …
        head, _, rest = text.partition(' ')
        if second == ['que']:
            text = head + 'que' + (' ' + rest if rest else '')
        else:
            text = head + ' ' + ' '.join(second) + (' ' + rest if rest else '')
    return text


def join(clauses, texts, lang):
    """節の文をつなぐ: 従属節 (前置) の後ろと、つなぎの語のある節の前は読点、ほかは ; (英語・ロシア語)"""
    out = ''
    for i, (clause, text) in enumerate(zip(clauses, texts)):
        text = wrap(text, clause, lang, clauses[i - 1] if i else None)
        if i == 0:
            out = text
            continue
        prev = clauses[i - 1]
        joined_by_comma = (prev.subordinator and not prev.after_main) or clause.connectives or clause.subordinator
        if lang == 'sa':
            out += ' ' + text
        elif lang == 'la' or joined_by_comma:
            out += ', ' + text
        else:
            out += '; ' + text
    return out
