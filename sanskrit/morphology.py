#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# サンスクリットの語形の解析: vidyut の kosha (パーニニ文法で生成した語形の辞書) の結果を、辞書の項目 (dict) にする
#
# kosha はありうる分析をすべて返す (rāmas に、名詞 rāma の単数主格のほか、語根 ram からの機械的な派生の分析が多数)。
# 見出し語の辞書 (Wiktionary) に載っている語・語根の分析を優先し、よく使われる分詞などを次に、ほかの派生は後ろに回す。
# 不変化詞 (ca, vā, na, eva, iti …) は表で先に決める。
#
# 空白で分かれた語は、語末の連声を戻して引く (rāmo → rāmas, vanaṃ → vanam, …ḥ → …s / …r)。
#
import os

from vidyut import kosha as vidyut_kosha

from . import dictionary, script

CASES = {'praTamA': 'Nom', 'dvitIyA': 'Acc', 'tftIyA': 'Ins', 'caturTI': 'Dat', 'paYcamI': 'Abl', 'zazWI': 'Gen',
         'saptamI': 'Loc', 'samboDanam': 'Voc'}
GENDERS = {'puM': 'm', 'strI': 'f', 'napuMsaka': 'n'}
NUMBERS = {'eka': 'sg', 'dvi': 'du', 'bahu': 'pl'}
PERSONS = {'praTama': 3, 'maDyama': 2, 'uttama': 1}
LAKARAS = {'la~w': ('present', 'indicative'), 'la~N': ('imperfect', 'indicative'), 'li~w': ('perfect', 'indicative'),
           'lu~N': ('aorist', 'indicative'), 'lf~w': ('future', 'indicative'), 'lu~w': ('future', 'indicative'),
           'lo~w': ('present', 'imperative'), 'viDili~N': ('present', 'optative'),
           'ASIrli~N': ('present', 'optative'), 'lf~N': ('future', 'subjunctive')}
VOICES = {'kartari': 'active', 'karmaRi': 'passive', 'BAve': 'passive'}
# よく使われる分詞・不定詞など (krt) → (品詞, 時制, 態)
PARTICIPLES = {'kta': ('participle', 'past', 'passive'), 'ktavatu~': ('participle', 'past', 'active'),
               'Satf~': ('participle', 'present', 'active'), 'SAnac': ('participle', 'present', 'middle'),
               'cAnaS': ('participle', 'present', 'middle'),
               'tavya': ('participle', 'future', 'passive'), 'anIyar': ('participle', 'future', 'passive'),
               'ktvA': ('absolutive', None, None), 'lyap': ('absolutive', None, None),
               'tumu~n': ('infinitive', None, None)}
PRONOUNS = {'tad', 'yad', 'idam', 'adas', 'etad', 'kim', 'asmad', 'yuzmad', 'sarva', 'anya', 'Bavat', 'svayam'}
DETERMINERS = {'tad', 'etad', 'idam', 'adas', 'sarva', 'anya', 'yad', 'kim', 'eka'}
# 代名詞の訳語 (Wiktionary に人称代名詞の見出しが無いので)
PRONOUN_GLOSSES = {'asmad': '私', 'yuzmad': 'あなた', 'tad': 'それ,彼,彼女', 'etad': 'これ', 'idam': 'これ',
                   'adas': 'あれ', 'yad': '〜するところのもの', 'kim': '何,誰', 'Bavat': 'あなた (敬称)', 'svayam': '自ら'}

# 不変化詞 (SLP1) → (品詞, 訳語)
INDECLINABLES = {
    'ca': ('conj', 'そして,〜と'), 'vA': ('conj', 'または'), 'na': ('adv', '〜ない'), 'mA': ('adv', '〜するな'),
    'eva': ('adv', 'まさに,〜だけ'), 'iti': ('conj', '〜と (引用)'), 'api': ('adv', '〜も,さえ'), 'tu': ('conj', 'しかし'),
    'hi': ('conj', 'なぜなら,実に'), 'atha': ('conj', 'さて,そして'), 'iva': ('adv', '〜のように'),
    'yaTA': ('conj', '〜のように'), 'taTA': ('adv', 'そのように'), 'yadA': ('conj', '〜するとき'), 'tadA': ('adv', 'そのとき'),
    'yadi': ('conj', 'もし'), 'tatra': ('adv', 'そこで'), 'atra': ('adv', 'ここで'), 'punar': ('adv', '再び'),
    'ca eva': ('conj', 'そしてまさに'), 'kila': ('adv', '実に,〜だそうだ'), 'nu': ('adv', 'さて,いったい'),
    'saha': ('adv', '〜とともに'), 'vinA': ('adv', '〜なしに'), 'iha': ('adv', 'ここで,この世で'), 'adya': ('adv', '今日'),
    'sadA': ('adv', 'いつも'), 'tatas': ('adv', 'それから'), 'yatas': ('conj', '〜だから'), 'evam': ('adv', 'このように'),
    'kim': ('adv', '〜か (疑問)'), 'kTam': ('adv', 'どのように'), 'katham': ('adv', 'どのように'), 'kva': ('adv', 'どこに'),
    'he': ('adv', 'おお'), 'Bos': ('adv', 'おお'), 'Bo': ('adv', 'おお'),
    'sma': ('adv', '(過去を表す)'), 'vE': ('adv', '実に'), 'u': ('adv', 'そして,また'), 'ha': ('adv', '実に'),
}
COMMON_KRT_RANK = 1
_kosha = None


def available():
    return os.path.isdir(os.path.join(dictionary.VIDYUT_DATA, 'kosha'))


def _get_kosha():
    global _kosha
    if _kosha is None:
        _kosha = vidyut_kosha.Kosha(os.path.join(dictionary.VIDYUT_DATA, 'kosha'))
    return _kosha


def _gloss(key, root=False):
    """見出し語 (SLP1) の訳語と品詞。(訳語, 言語, 品詞)。辞書に無ければ None"""
    lemma = main_lemma([l for l in dictionary.lemmas(key) if root or l['pos'] != 'root'])
    return (lemma['ja'], lemma['gloss_lang'], lemma['pos']) if lemma else None


def main_lemma(lemmas, order=('name', 'noun', 'pronoun', 'adj')):
    """同綴の見出しのうち主なもの: Wiktionary の語義の多いもの (bāhu: 名詞「腕」8 > 固有名詞 4)。
    同じなら order の品詞の順 (rāma: 固有名詞「ラーマ」4 = 名詞「暗闇」4)"""
    rank = {pos: i for i, pos in enumerate(order)}
    return min(lemmas, key=lambda l: (-l.get('senses', 0), rank.get(l['pos'], len(order))), default=None)


GANAS = {name: i + 1 for i, name in enumerate(
    ['Bhvadi', 'Adadi', 'Juhotyadi', 'Divadi', 'Svadi', 'Tudadi', 'Rudhadi', 'Tanadi', 'Kryadi', 'Curadi'])}


PREFIX_FORMS = {'ud': ('ud', 'ut', 'uc', 'uj', 'ul', 'un'), 'nis': ('nis', 'niz', 'nir', 'niH'),
                'dus': ('dus', 'duz', 'dur', 'duH'), 'sam': ('sam', 'saM', 'saN', 'saY', 'san')}


def _root_keys(clean, prefixes, causative):
    """語根を辞書で引くキーの候補。そのまま (utTA) → 使役の語尾 -i を除く (sTApi → sTA) → 接頭辞を除く (udi → i)"""
    keys = [clean]
    if causative and clean.endswith('i'):
        keys += [clean[:-1], clean[:-2]] if clean.endswith('pi') else [clean[:-1]]
    for key in list(keys):
        rest = key
        for prefix in prefixes:
            form = next((f for f in PREFIX_FORMS.get(prefix, (prefix,)) if rest.startswith(f)), None)
            if form is None:
                break
            rest = rest[len(form):]
            if prefix == 'ud' and rest.startswith('T'):
                rest = 's' + rest  # ud + sthā → utthā
        else:
            if rest != key:
                keys.append((rest, tuple(prefixes)))
    return [k if isinstance(k, tuple) else (k, ()) for k in dict.fromkeys(keys) if k]


def _root_gloss(dhatu_entry):
    """語根の訳語。同綴の語根 (pā「飲む」第1類 pibati と pā「守る」第2類 pāti) は、vidyut の類 (gana) と
    使役かどうかが Wiktionary の動詞の見出し (class 1, root पा) と合うものを選ぶ"""
    dhatu = dhatu_entry.dhatu
    gana = GANAS.get(repr(dhatu.gana).split('.')[-1])
    causative = any('Ric' in repr(s) for s in (dhatu.sanadi or []))
    roots = []
    stripped = []
    for key, stripped in _root_keys(dhatu_entry.clean_text, dhatu.prefixes or [], causative):
        roots = [l for l in dictionary.lemmas(key) if l['pos'] in ('root', 'verb')]
        if roots:
            break
    if not roots:
        return None

    def score(l):
        return ((l['causative'] != causative) * 4 + (l['gana'] is not None and l['gana'] != gana) * 2 +
                (l['gana'] is None))
    best = min(roots, key=score)
    # 接頭辞を除いて引いたら、接頭辞を添える (ud-i → ud-行く)
    prefix = ''.join(script.iast(p) + '-' for p in stripped)
    return prefix + best['ja'], best['gloss_lang'], best['pos']


def _subanta(e, surface):
    """名詞類の分析 → (順位, 項目)"""
    p = e.pratipadika_entry
    cng = (CASES.get(str(e.vibhakti)), NUMBERS.get(str(e.vacana)), GENDERS.get(str(e.linga)))
    if not cng[0]:
        return None
    if hasattr(p, 'krt'):
        root = p.dhatu_entry.clean_text
        kind = PARTICIPLES.get(str(p.krt))
        gloss = _root_gloss(p.dhatu_entry)
        if kind is None:
            # そのほかの派生 (ram + kvip など)。辞書に語根があっても後ろに回す
            return 3, {'pos': 'noun', 'base': script.iast(e.lemma), '_': [cng],
                       'ja': gloss[0] if gloss else script.iast(e.lemma), 'gloss_lang': gloss[1] if gloss else 'en'}
        pos, tense, voice = kind
        item = {'pos': 'participle' if pos == 'participle' else 'verb', 'pres1sg': script.iast(root),
                'base': script.iast(root), 'ja': gloss[0] if gloss else script.iast(root),
                'gloss_lang': gloss[1] if gloss else 'en'}
        if pos == 'participle':
            item.update({'tense': tense, 'voice': voice, '_': [cng]})
        elif pos == 'absolutive':
            # 絶対分詞 (gatvā「行って」): 動詞を修飾する副詞として
            item = {'pos': 'adv', 'base': script.iast(root), 'pres1sg': script.iast(root),
                    'ja': _absolutive_gloss(gloss, root)}
        else:
            item.update({'mood': pos})  # 不定詞 (〜するために)
        return (COMMON_KRT_RANK if gloss else 2), item
    text = p.pratipadika.text
    gloss = (PRONOUN_GLOSSES[text], 'ja', 'pronoun') if text in PRONOUN_GLOSSES else _gloss(text)
    pos = 'pronoun' if text in PRONOUNS else (gloss[2] if gloss and gloss[2] in ('noun', 'adj', 'pronoun') else 'noun')
    item = {'pos': pos, 'base': script.iast(text), '_': [cng],
            'ja': gloss[0] if gloss else script.iast(text), 'gloss_lang': gloss[1] if gloss else 'en'}
    if gloss and gloss[2] == 'name':
        item['name'] = True
    if text in DETERMINERS:
        item['desc'] = '指示代名詞'  # 名詞に掛かりうる (sarve janāḥ「すべての人々」, sa rājā「その王」)
    rank = 0 if gloss or text in PRONOUNS else 2
    lemmas = [l for l in dictionary.lemmas(text) if l['pos'] != 'root'] if pos == 'noun' else []
    adj = [l for l in lemmas if l['pos'] == 'adj']
    if adj and gloss[2] != 'name':  # 固有名詞 (rāma) は形容詞「暗い」に読まない
        # 形容詞としても読める名詞 (mahat「偉大な」, viśva「すべての」) は形容詞の読みも (名詞と合えば前に出す)
        return [(rank, item), (rank, dict(item, pos='adj', ja=adj[0]['ja'], gloss_lang=adj[0]['gloss_lang']))]
    return rank, item


def _absolutive_gloss(gloss, root):
    if gloss and gloss[1] == 'ja':
        from core.japanese import JaVerb
        try:
            return JaVerb(gloss[0].split(',')[0]).adverbial_form('active')
        except Exception:
            pass
    return '%s[絶対分詞]' % (gloss[0].split(',')[0] if gloss else script.iast(root))


def _tinanta(e):
    root = e.dhatu_entry.clean_text
    tense, mood = LAKARAS.get(str(e.lakara), ('present', 'indicative'))
    gloss = _root_gloss(e.dhatu_entry)
    return (0 if gloss else 2), {
        'pos': 'verb', 'pres1sg': script.iast(root), 'tense': tense, 'mood': mood,
        'voice': VOICES.get(str(e.prayoga), 'active'), 'person': PERSONS.get(str(e.purusha)),
        'number': NUMBERS.get(str(e.vacana)), 'ja': gloss[0] if gloss else script.iast(root),
        'gloss_lang': gloss[1] if gloss else 'en'}


ENAD = {'enam': [('Acc', 'sg', 'm')], 'enAm': [('Acc', 'sg', 'f')], 'enat': [('Acc', 'sg', 'n')],
        'enO': [('Acc', 'du', 'm'), ('Acc', 'du', 'f'), ('Acc', 'du', 'n')], 'ene': [('Acc', 'du', 'f'), ('Acc', 'du', 'n')],
        'enAn': [('Acc', 'pl', 'm')], 'enAH': [('Acc', 'pl', 'f')], 'enAni': [('Acc', 'pl', 'n')],
        'enena': [('Ins', 'sg', 'm'), ('Ins', 'sg', 'n')], 'enayA': [('Ins', 'sg', 'f')],
        'enayoH': [('Gen', 'du', 'm'), ('Loc', 'du', 'm'), ('Gen', 'du', 'f'), ('Loc', 'du', 'f')]}


def analyze(slp1):
    """語 (SLP1、連声を戻した形) の解析 → 辞書の項目のリスト (良いものから)"""
    if slp1 in ENAD:  # 前方照応の前接代名詞 enad (kosha に無い)
        return [{'surface': script.iast(slp1), 'pos': 'pronoun', 'base': 'enad', '_': list(ENAD[slp1]),
                 'ja': 'それ,彼,彼女', 'gloss_lang': 'ja', 'source': 'table'}]
    if slp1 in INDECLINABLES:
        pos, ja = INDECLINABLES[slp1]
        return [{'surface': script.iast(slp1), 'pos': pos, 'base': script.iast(slp1), 'ja': ja, 'gloss_lang': 'ja'}]
    ranked = []
    for e in _get_kosha().get(slp1):
        try:
            r = _tinanta(e) if hasattr(e, 'dhatu_entry') and hasattr(e, 'purusha') else _subanta(e, slp1)
        except (AttributeError, TypeError):
            r = None
        if r:
            ranked += r if isinstance(r, list) else [r]
    if not ranked:
        return []
    best = min(rank for rank, _ in ranked)
    # 同じ見出し語・品詞の分析は1つの項目にまとめる (格の組を合わせる)
    merged = {}
    for rank, item in sorted(ranked, key=lambda r: r[0]):
        if rank > best + 1 or (rank == 3 and best < 3):
            continue
        sig = tuple((k, str(v)) for k, v in sorted(item.items()) if k != '_')
        if sig in merged:
            for cng in item.get('_', []):
                if cng not in merged[sig]['_']:
                    merged[sig]['_'].append(cng)
        else:
            item['surface'] = script.iast(slp1)
            item['source'] = 'vidyut'
            merged[sig] = item
    # 呼格・双数は後ろに (tat, etat の中性単数は主格・対格・呼格が同形。vane は処格単数か主格・対格の双数)
    for item in merged.values():
        if '_' in item:
            item['_'].sort(key=lambda cng: (cng[0] == 'Voc', cng[1] == 'du'))
    # 代名詞の読みを先に (saḥ「彼」と sas「アナペスト」)。bhavat「あなた」の処格 bhavati は動詞 bhavati「なる」の後
    return sorted(merged.values(), key=lambda item: item['pos'] != 'pronoun' or item['base'] == 'bhavat')


# ----------------------------------------------------------------------
# 語末の連声を戻す (SLP1)

FINAL_SANDHI = [
    ('o', ['as']), ('M', ['m']), ('H', ['s', 'r']), ('A', ['As']), ('a', ['as']), ('e', ['es']),
    ('d', ['t']), ('g', ['k']), ('b', ['p']), ('q', ['w']), ('r', ['s']), ('S', ['s']), ('z', ['s']),
    ('c', ['t']), ('j', ['t']), ('l', ['t']), ('Y', ['n']), ('N', ['n']), ('n', ['t']),
]


def unsandhi_candidates(slp1):
    """語末の連声を戻した形の候補 (元の形を含む)"""
    word = slp1.lstrip("'")  # 語頭の a の省略記号 (ऽ)
    if slp1.startswith("'"):
        word = 'a' + word
    # sa / eṣa は子音の前の saḥ / eṣaḥ (この2語だけの連声)
    candidates = [word + 's', word] if word in ('sa', 'eza') else [word]
    for final, replacements in FINAL_SANDHI:
        if word.endswith(final):
            candidates += [word[:-len(final)] + r for r in replacements]
    return list(dict.fromkeys(candidates))


def lookup(slp1):
    """語末の連声を戻しながら引く。(戻した形, 項目のリスト)。見つからなければ (元の形, [])"""
    found = [(c, items) for c, items in ((c, analyze(c)) for c in unsandhi_candidates(slp1)) if items]
    if not found:
        return slp1, []
    # 呼格だけの読み (sūrya) より、ḥ の落ちた形と見た読み (sūrya ← sūryaḥ 母音の前) を
    vocative_only = lambda items: all(cng[0] == 'Voc' for item in items for cng in item.get('_', [('x',)]))
    if vocative_only(found[0][1]) and slp1.endswith('a'):
        return next(((c, items) for c, items in found if c == slp1 + 's' and not vocative_only(items)), found[0])
    return found[0]
