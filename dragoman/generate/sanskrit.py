#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) からサンスクリットの文を作る
#
#   語は transfer で置き換え (puella → bAlikA)、語形は vidyut (パーニニ文法の生成) で作る (bAlikA → bAlikAm)。
#   格: 主語 → 主格、目的語 → 対格、受け手 → 為格、手段 → 具格、所有者 → 属格、起点 → 奪格、場所 → 処格。
#       ラテン語の前置詞句 → 格 (+ 後置詞): in + 奪格 → 処格、cum + 奪格 → 具格 + saha、sine → 具格 + vinA …
#   動詞: 現在 → laṭ、未完了過去・完了 → laṅ (語りの過去)、未来 → lṛṭ、命令法 → loṭ、接続法 → vidhiliṅ。
#         受動は karmaṇi (動作主は具格)。繋辞 (sum) は現在なら省き、過去は Asīt、未来は bhaviṣyati
#   不定詞句: 言う → 直接話法 + iti (再帰代名詞 sē は 1人称に)、見る → 対格 + 現在分詞の対格 (bAlikAM gAyantIm)、
#             命じる・補足 → 不定詞 -tum (paWituM Saknoti)
#   独立奪格 → 処格独立 (nfpe mfte「王が死んだとき」)、述語的な分詞 → 現在分詞・-tvā の絶対分詞 (uktvA)
#   語順は 主語 - 受け手 - 目的語 - そのほか - 動詞。形容詞・属格は名詞の前。連声 (sandhi) はかけない (語を分けて書く)
#
import functools
import os

from . import transfer, english
from .frame import Lex, NP

try:
    from vidyut import kosha as vidyut_kosha
    from vidyut.prakriya import (Vyakarana, Pada, Pratipadika, Linga, Vibhakti, Vacana, Lakara, Prayoga, Purusha,
                                 Krt)
except ImportError:   # vidyut が無ければサンスクリットは作れない
    vidyut_kosha = None

from dragoman.sanskrit import script
from dragoman.sanskrit.dictionary import VIDYUT_DATA

ROLE_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Ins', 'possessor': 'Gen',
              'place': 'Loc', 'address': 'Voc', 'complement': 'Nom', 'source': 'Abl'}
# ラテン語の前置詞 + 格 → (サンスクリットの格, 後置詞)
PREPOSITIONS = {('in', 'Abl'): ('Loc', None), ('in', 'Acc'): ('Acc', None), ('ad', 'Acc'): ('Acc', None),
                ('cum', 'Abl'): ('Ins', 'saha'), ('ā', 'Abl'): ('Abl', None), ('ab', 'Abl'): ('Abl', None),
                ('ē', 'Abl'): ('Abl', None), ('ex', 'Abl'): ('Abl', None), ('dē', 'Abl'): ('Loc', None),
                ('sine', 'Abl'): ('Ins', 'vinA'), ('prō', 'Abl'): ('Dat', None), ('sub', 'Abl'): ('Gen', 'aDaH'),
                ('sub', 'Acc'): ('Gen', 'aDaH'), ('per', 'Acc'): ('Ins', None), ('post', 'Acc'): ('Abl', 'param'),
                ('ante', 'Acc'): ('Gen', 'puraH'), ('apud', 'Acc'): ('Gen', 'samIpe'), ('inter', 'Acc'): ('Gen', 'maDye'),
                ('trāns', 'Acc'): ('Gen', 'pAre'), ('circum', 'Acc'): ('Acc', 'paritaH'),
                ('prope', 'Acc'): ('Gen', 'samIpe'), ('propter', 'Acc'): ('Abl', None),
                ('contrā', 'Acc'): ('Acc', 'prati'), ('super', 'Acc'): ('Gen', 'upari'), ('ob', 'Acc'): ('Abl', None)}
# ラテン語の代名詞 → サンスクリットの代名詞の語幹
PRONOUNS = {'ego': 'asmad', 'tū': 'yuzmad', 'nōs': 'asmad', 'vōs': 'yuzmad', 'is': 'tad', 'hīc': 'etad',
            'hic': 'etad', 'ille': 'adas', 'quī': 'yad', 'quis': 'kim', 'quid': 'kim', 'īdem': 'tad',
            'meus': 'madIya', 'tuus': 'tvadIya', 'noster': 'asmadIya', 'vester': 'yuzmadIya', 'suus': 'sva',
            'sē': 'Atman', 'alius': 'anya', 'alter': 'anya', 'cēterus': 'anya', 'omnis': 'sarva', 'tōtus': 'sarva',
            'tantus': 'tAvat', 'ūnus': 'eka', 'sōlus': 'eka', 'duo': 'dvi', 'trēs': 'tri', 'quattuor': 'catur',
            'quīnque': 'paYcan', 'sex': 'zaz', 'septem': 'saptan', 'octō': 'azwan', 'novem': 'navan', 'decem': 'daSan',
            'duodecim': 'dvAdaSan', 'centum': 'Sata', 'mīlle': 'sahasra'}
# 不定代名詞: (疑問代名詞, 後ろに付ける語、否定するか) (aliquis → kaScit、nēmō → na kaH api)
INDEFINITES = {'aliquis': ('kim', 'cit', False), 'aliquī': ('kim', 'cit', False), 'quīdam': ('kim', 'cit', False), 'quisquam': ('kim', 'api', False),
               'nēmō': ('kim', 'api', True), 'nihil': ('kim', 'api', True), 'nūllus': ('kim', 'api', True)}
INDECLINABLE = {'ipse': 'svayam'}
CONJUNCTIONS = {'et': 'ca', 'atque': 'ca', 'ac': 'ca', 'que': 'ca', '-que': 'ca', 'aut': 'vA', 'vel': 'vA',
                'neque': 'na', 'nec': 'na', 'sed': 'kintu'}
LINGAS = {'m': 'Pum', 'f': 'Stri', 'n': 'Napumsaka', 'c': 'Pum'}
VIBHAKTIS = {'Nom': 'Prathama', 'Acc': 'Dvitiya', 'Ins': 'Trtiya', 'Dat': 'Caturthi', 'Abl': 'Panchami',
             'Gen': 'Sasthi', 'Loc': 'Saptami', 'Voc': 'Sambodhana'}
GANAS = {'1': 'Bhvadi', '2': 'Adadi', '3': 'Juhotyadi', '4': 'Divadi', '5': 'Svadi', '6': 'Tudadi', '7': 'Rudhadi',
         '8': 'Tanadi', '9': 'Kryadi', '10': 'Curadi'}
LAKARAS = {'present': 'Lat', 'imperfect': 'Lan', 'perfect': 'Lan', 'past-perfect': 'Lan', 'future': 'Lrt',
           'future-perfect': 'Lrt'}
# 数: 'du' は両数 (ラテン語の duo・ambō と一緒の名詞)
VACANAS = {'sg': Vacana.Eka, 'du': Vacana.Dvi, 'pl': Vacana.Bahu} if vidyut_kosha is not None else {}
DUAL_WORDS = {'duo', 'ambō'}
# 動詞の見出しの置き換え (英語の訳語の表に無い語根)
VERBS = {'sum': ('as', '2'), 'possum': ('Sak', '5')}
# 対格でない格を取る動詞 (BI「恐れる」+ 奪格: samudrAt biByati、snih「愛する」+ 処格)
GOVERNMENT = {'BI': 'Abl', 'snih': 'Loc'}


def available():
    return vidyut_kosha is not None and transfer.available('sa') and os.path.exists(VIDYUT_DATA)


@functools.lru_cache(maxsize=1)
def _vyakarana():
    return Vyakarana()


@functools.lru_cache(maxsize=1)
def _dhatus():
    """語根 (SLP1。接頭辞つきも) → [Dhatu]"""
    index = {}
    kosha = vidyut_kosha.Kosha(os.path.join(VIDYUT_DATA, 'kosha'))
    for entry in kosha.dhatus():
        if entry.dhatu.sanadi:
            continue
        index.setdefault(entry.clean_text, []).append(entry.dhatu)
    return index


def _loose(root):
    """綴りの揺れを除いた語根 (Apte の praC / vidyut の pracC、Arab / AraB、palAy / palAay)"""
    root = root.replace('cC', 'c').replace('Aa', 'A')
    return root.translate(str.maketrans('KGCJWQTDPB', 'kgcjwqtdpb'))


@functools.lru_cache(maxsize=1)
def _loose_dhatus():
    index = {}
    for root, found in _dhatus().items():
        index.setdefault(_loose(root), []).extend(found)
    return index


def dhatu(root, gana=''):
    found = _dhatus().get(root, []) or _loose_dhatus().get(_loose(root), [])
    if gana:
        same = [d for d in found if repr(d.gana).endswith('.' + GANAS.get(gana, ''))]
        found = same or found
    found = sorted(found, key=lambda d: d.antargana is not None)
    return found[0] if found else None


def _derive(pada):
    try:
        forms = [p.text for p in _vyakarana().derive(pada)]
    except Exception:
        return None
    # 複数の形があれば、為他言 (parasmaipada。両方とれる語根 dA: dadAti / datte)、語末が -d でない (agacCat / agacCad)、
    # 短いもの (gacCatu / gacCatAt)
    return min(forms, key=lambda f: (isinstance(pada, Pada.Tinanta) and f.endswith(ATMANEPADA), f.endswith('d'),
                                     len(f))) if forms else None


ATMANEPADA = ('te', 'se', 'e', 'ta', 'TAH', 'tAm', 'ntAm', 'sva', 'Dvam', 'mahi', 'vahi', 'mahe', 'vahe')


def subanta(stem, linga, case, number):
    """名詞・形容詞・代名詞の語形 (SLP1)。作れなければ語幹に * を付けて"""
    if stem == 'mahat' and linga == 'm':
        stem = 'mahant'   # vidyut は mahat の男性を mahat (主格) にするので、mahAn・mahAntam になる語幹で
    try:
        if not isinstance(stem, str):
            prat = stem
        elif linga == 'f' and stem.endswith(('A', 'I')):
            prat = Pratipadika.nyap(stem)   # 女性の -ā・-ī 語幹 (bAlikA, nadI)。basic のままだと男性の変化になる
        else:
            prat = Pratipadika.basic(stem)
    except ValueError:   # SLP1 でない語幹 (辞書の見出しの記号など)
        return '*' + str(stem)
    form = _derive(Pada.Subanta(pratipadika=prat, linga=getattr(Linga, LINGAS.get(linga, 'Pum')),
                                vibhakti=getattr(Vibhakti, VIBHAKTIS[case]),
                                vacana=VACANAS.get(number, Vacana.Eka)))
    return form or '*' + (stem if isinstance(stem, str) else '?')


def tinanta(d, tense, mood, voice, person, number):
    lakara = 'Lot' if mood == 'imperative' else 'VidhiLin' if mood == 'subjunctive' else LAKARAS.get(tense, 'Lat')
    return _derive(Pada.Tinanta(dhatu=d, prayoga=Prayoga.Karmani if voice == 'passive' else Prayoga.Kartari,
                                lakara=getattr(Lakara, lakara),
                                purusha={1: Purusha.Uttama, 2: Purusha.Madhyama}.get(person, Purusha.Prathama),
                                vacana=VACANAS.get(number, Vacana.Eka)))


# ----------------------------------------------------------------------
# 語の置き換え

def noun_stem(lex, gender=''):
    """Lex → (語幹, 性)"""
    if lex.pos == 'pronoun' or lex.lemma in PRONOUNS:
        stem = PRONOUNS.get(lex.lemma) or PRONOUNS.get(english._flat(lex.lemma))
        if stem:
            return stem, gender or 'm'
    if lex.proper and lex.lang == 'sa':
        return transfer.source_key('sa', lex.lemma), gender or 'm'   # サンスクリットの名前はそのまま (rāma)
    if lex.proper:
        return name(lex.lemma)
    lex = english.substantive(lex) or lex   # 名詞として辞書にある形 (tālāria)
    target = transfer.best(lex, 'sa', 'noun' if lex.pos not in ('adj', 'participle') else 'adj')
    if target is None:
        return None, gender
    return target.lemma, target.gender or gender or 'm'


def name(latin):
    """ラテン語の固有名詞 → サンスクリットの語幹 (Mārcus → mArka (男性)、Iūlia → yUliyA (女性))"""
    import unicodedata
    # 長音の記号 (マクロン) だけ残し、短音の記号 (Ătlās の ˘)・合字の記号 (Perse͡us) などは除く
    word = ''.join(c for c in unicodedata.normalize('NFD', latin.lower())
                   if not unicodedata.combining(c) or c == '\u0304')
    word = unicodedata.normalize('NFC', ''.join(c for c in word if c.isalpha() or c == '\u0304'))
    long = {'ā': 'A', 'ē': 'e', 'ī': 'I', 'ō': 'o', 'ū': 'U', 'ȳ': 'I'}
    for ending, stem_ending, gender in (('us', 'a', 'm'), ('um', 'a', 'n'), ('a', 'A', 'f'), ('ā', 'A', 'f'),
                                         ('ō', 'a', 'm'), ('o', 'a', 'm')):
        if word.endswith(ending) and len(word) > len(ending) + 1:
            word, tail = word[:-len(ending)], stem_ending
            break
    else:
        tail, gender = 'a', 'm'
    out = ''
    i = 0
    while i < len(word):
        two = word[i:i + 2]
        if two in ('ae', 'oe'):
            out, i = out + 'e', i + 2
            continue
        if two == 'qu':
            out, i = out + 'kv', i + 2
            continue
        if two in ('th', 'ph', 'ch'):
            out, i = out + {'th': 'T', 'ph': 'P', 'ch': 'K'}[two], i + 2   # ギリシア語の有気音 (Thessalia)
            continue
        c = word[i]
        out += long.get(c) or {'c': 'k', 'j': 'y', 'i': 'i', 'x': 'kz', 'h': 'h', 'z': 'j', 'y': 'i'}.get(c, c)
        i += 1
    return out.replace('iu', 'yu').replace('ia', 'iy') + tail, gender


def verb_root(lex):
    """動詞の語根と類。vidyut に無い語根 (rac 第10類) は次の候補に"""
    if lex.lemma in VERBS:
        return VERBS[lex.lemma]
    for _, target in transfer.candidates(lex, 'sa', 'verb')[:8]:
        if dhatu(target.lemma, target.gana) is not None:
            return target.lemma, target.gana
    return None, ''


def _verb_lex(p):
    return Lex(p.verb.verb, 'verb', p.verb.verb_ja, lang=p.verb.lang)


# ----------------------------------------------------------------------
# 名詞句

# 女性形が -ī になる -a 語幹の形容詞 (ほかは -ā: viSAla → viSAlA)
FEMININE_I = {'sundara', 'gOra'}


def participle_root(lex):
    """分詞のもとの動詞の語根: 動詞の見出しがあればそれを置き換え、無ければ (動形容詞 adeundus) 英語の訳語から"""
    if lex.verb:
        root, gana = verb_root(Lex(lex.verb, 'verb', lex.verb_ja, lang=lex.lang))
        if root:
            return dhatu(root, gana)
    for _, target in transfer.by_english(english.verb_bases(lex.en or ''), 'sa', 'verb')[:8]:
        d = dhatu(target.lemma, target.gana)
        if d is not None:
            return d
    return None


def participle_from_lex(lex, linga, case, number):
    """名詞に係る分詞・補語の分詞 (Latin の分詞の Lex): 現在 → śatṛ、完了 → kta (形式受動態は ktavatu、
    prōgressus → pragatavat)、未来 (動形容詞) → tavya (adeundus → abhigantavya)"""
    d = participle_root(lex)
    if d is None:
        return None
    deponent = lex.verb.endswith('r')
    if lex.ptense == 'present':
        krts = ['Satf', 'SAnac']
    elif lex.ptense == 'future':
        krts = ['tavyat']
    else:
        krts = ['ktavatu' if deponent else 'kta']
    for krt in krts:
        stem = Pratipadika.krdanta(d, getattr(Krt, krt))
        if linga == 'f':
            nominative = subanta(stem, 'f', 'Nom', 'sg')
            if nominative.endswith(('I', 'A')):
                stem = nominative   # 女性は -ī・-ā 語幹として (vidyut の分詞の女性の処格の不具合を避ける)
        form = subanta(stem, linga, case, number)
        if not form.startswith('*'):
            return form
    return None


def adjective(lex, linga, case, number):
    if lex.pos == 'participle':
        form = participle_from_lex(lex, linga, case, number)
        if form:
            return form
    if lex.lemma in INDECLINABLE:
        return INDECLINABLE[lex.lemma]   # arcam ipsam → svayam
    if lex.lemma in INDEFINITES:   # rēx quīdam → nfpaH kaScit
        stem, suffix, negative = INDEFINITES[lex.lemma]
        word = subanta(stem, linga, case, number)
        if suffix == 'cit' and word.endswith('H'):
            word = word[:-1] + 'S'
        return ('na ' if negative else '') + word + ('' if suffix == 'cit' else ' ') + suffix
    positive = english._positive(lex)
    degree = lex.degree or ('++' if positive is not None else '')
    lex = positive or lex   # 最上級の見出し (difficillimus) は原級で引いて -tama を付ける
    stem = PRONOUNS.get(lex.lemma)
    pronoun = stem is not None
    if stem is None:
        target = transfer.best(lex, 'sa', 'adj') or transfer.best(lex, 'sa', 'noun')
        stem = target.lemma if target else None
    if stem is None:
        return '[%s]' % english.word(lex)
    if degree and not pronoun:
        stem = stem + ('tara' if degree == '+' else 'tama')   # -tara / -tama (kaWina → kaWinatama)
    if linga == 'f' and stem.endswith('a') and not pronoun and (stem not in FEMININE_I or degree):
        stem = stem[:-1] + 'A'
    return subanta(stem, linga, case, number)


def noun_phrase(np, case):
    """名詞句 (語の列を SLP1 で)"""
    if np.members:
        conj = CONJUNCTIONS.get(np.conj, 'ca')
        parts = [noun_phrase(m, case) for m in np.members]
        if conj == 'na':
            return ' '.join('na ' + p for p in parts)
        if conj == 'ca':
            return ' '.join(p + ' ca' for p in parts) if np.correlative else ' '.join(parts) + ' ca'   # A B ca
        return ' '.join(parts) + ' ' + conj
    head = np.head
    if head.lemma in INDEFINITES or head.lemma in INDECLINABLE:
        if head.lemma in INDECLINABLE:
            return INDECLINABLE[head.lemma]
        stem, suffix, negative = INDEFINITES[head.lemma]
        gender = 'n' if head.lemma == 'nihil' else (np.gender or 'm')
        word = subanta(stem, gender, case, np.number)
        if suffix == 'cit' and word.endswith('H'):
            word = word[:-1] + 'S'   # kaH + cit → kaScit
        return ('na ' if negative else '') + word + ('' if suffix == 'cit' else ' ') + suffix
    if (np.dual or any(getattr(m, 'lemma', '') in DUAL_WORDS for m in np.modifiers)) and np.number == 'pl':
        import dataclasses
        np = dataclasses.replace(np, number='du')   # duo frātrēs → dvau BrAtarO (両数)
    stem, gender = noun_stem(head, np.gender)
    if head.pos == 'pronoun' and head.desc == '指示代名詞' and np.modifiers:
        stem = None
    if stem is None and head.pos in ('adj', 'participle') and not english.substantive(head):
        word = adjective(head, np.gender or 'm', case, np.number)
        gender = np.gender or 'm'
    elif stem is None:
        noun = english.substantive(head)
        word = '[%s]' % (english.gloss(noun) if noun is not None else english.word(head))
    else:
        number = np.number
        if stem in ('asmad', 'yuzmad'):
            number = 'pl' if head.lemma in ('nōs', 'vōs') else np.number
        word = subanta(stem, gender, case, number)
    before = [noun_phrase(gen, 'Gen') for gen in np.genitives]
    for mod in np.modifiers:
        if isinstance(mod, NP):   # 並列した形容詞
            before.append(' '.join(adjective(m.head, gender, case, np.number) for m in mod.members) + ' ca')
        else:
            before.append(adjective(mod, gender, case, np.number))
    for p in np.participles:
        before.append(participial_phrase(p, gender, case, np.number))
    if np.relatives:
        # 関係節は相関構文: 関係節 (yad …) を先に、名詞には相関詞 tad を (yam aDyApakaH praSaMsati taM bAlakam)
        relatives = [relative_clause(r, gender, np.number) for r in np.relatives]
        correlative = subanta('tad', gender, case, np.number) \
            if any(r.gap != 'place' for r in np.relatives) and stem not in ('tad', 'etad', 'adas', 'idam') else ''
        return ' '.join(relatives + [w for w in [correlative] + before + [word] if w])
    return ' '.join(before + [word])


GAP_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Ins', 'possessor': 'Gen'}


def relative_clause(r, gender, number):
    """関係節: 関係代名詞 yad を先行詞の性・数と空所の格で (yam …)、場所なら yatra、動詞は直説法"""
    import dataclasses
    post = None
    if r.gap == 'place':
        word = 'yatra'
    else:
        if r.gap == 'prep':
            case, post = PREPOSITIONS.get((r.gap_prep[0].lemma, r.gap_prep[1]), ('Loc', None))
        else:
            case = GAP_CASES.get(r.gap, 'Nom')
        word = subanta('yad', gender, case, number) + (' ' + post if post else '')
    finite = dataclasses.replace(r, mood='indicative') if r.mood == 'subjunctive' else r
    return word + ' ' + realize(finite)


def prepositional(np, passive=False):
    case, post = PREPOSITIONS.get((np.prep.lemma, np.case), ('Loc', None))
    if passive and np.prep.lemma in ('ā', 'ab', 'abs'):
        case, post = 'Ins', None   # 受動の動作主は具格
    import dataclasses
    inner = noun_phrase(dataclasses.replace(np, prep=None), case)
    return inner + (' ' + post if post else '')


# ----------------------------------------------------------------------
# 分詞

def participle_stem(p, krt=None):
    root, gana = verb_root(_verb_lex(p))
    d = dhatu(root, gana) if root else None
    if d is None:
        return None
    if krt is None:
        if p.tense == 'present':
            krt = 'Satf'
        elif p.voice == 'passive':
            krt = 'kta'
        else:
            krt = 'kta'   # 自動詞の -ta は能動の意味 (mfta「死んだ」)
    return Pratipadika.krdanta(d, getattr(Krt, krt))


def participle_word(p, linga, case, number):
    for krt in ([None, 'SAnac'] if p.tense == 'present' else [None]):
        stem = participle_stem(p, krt)
        if stem is not None and linga == 'f':
            # 女性は主格単数 (gAyantI, jYAtA) を -ī・-ā 語幹として変化させる
            # (vidyut の分詞の女性の処格が gAyantyE になるため)
            nominative = subanta(stem, 'f', 'Nom', 'sg')
            if nominative.endswith(('I', 'A')):
                stem = nominative
        if stem is not None:
            form = subanta(stem, linga, case, number)
            if not form.startswith('*'):
                return form
    return '[%s]' % english.word(p.verb)


def adverb(lex):
    """副詞 (変化しない): 文をつなぐ語の表 (tum → tadA) → 置き換えの表 (subitō → sahasA)"""
    from . import connectives
    entry = connectives.lookup(lex.surface or lex.lemma) or connectives.lookup(lex.lemma)
    if entry and isinstance(entry[3], str):
        return entry[3]
    if lex.lang == 'sa':
        return transfer.source_key('sa', lex.lemma)   # yathāśakti (複合語の切れ目を除く)
    target = transfer.best(lex, 'sa', 'adv')
    return target.lemma if target else '[%s]' % english.word(lex)


def _args(p):
    out = []
    for role, np in p.args:
        if role == 'adverb':
            out.append(adverb(np.head))
        elif role == 'prep':
            out.append(prepositional(np, p.voice == 'passive'))
        elif role == 'means' and p.voice == 'passive':
            out.append(noun_phrase(np, 'Ins'))
        else:
            out.append(noun_phrase(np, ROLE_CASES.get(role, 'Acc')))
    return out


def participial_phrase(p, linga, case, number):
    return ' '.join(_args(p) + [participle_word(p, linga, case, number)])


def absolutive(p):
    """-tvā の絶対分詞 (uktvA「言って」)"""
    stem = participle_stem(p, 'ktvA')
    return subanta(stem, 'm', 'Nom', 'sg') if stem is not None else '[%s]' % english.word(p.verb)


def participial(p, subject=None):
    if p.kind == 'absolute' and p.subject is not None:
        # 処格独立: 主語と分詞を処格に (nfpe mfte「王が死んだとき」)
        stem, gender = noun_stem(p.subject.head, p.subject.gender) if not p.subject.members else (None, 'm')
        return ' '.join([noun_phrase(p.subject, 'Loc')] + _args(p) +
                        [participle_word(p, gender or 'm', 'Loc', p.subject.number)])
    if p.voice == 'active' and p.tense != 'present':
        return ' '.join(_args(p) + [absolutive(p)])   # 完了の能動 (locūtus) → -tvā
    gender, number = 'm', 'sg'
    if subject is not None and not subject.members:
        gender = noun_stem(subject.head, subject.gender)[1] or subject.gender or 'm'
        number = subject.number
    return participial_phrase(p, gender, 'Nom', number)


# ----------------------------------------------------------------------
# 節

def _agreement(subject, clause):
    if subject is None:
        return 'm', clause.person, clause.number
    if subject.members:
        return 'm', 3, 'du' if len(subject.members) == 2 else 'pl'   # A ca B → 両数 (gacchataH)
    if subject.dual or clause.dual:
        return noun_stem(subject.head, subject.gender)[1], 3, 'du'
    gender = noun_stem(subject.head, subject.gender)[1] if subject.head is not None else 'm'
    if subject.head.pos == 'pronoun':
        return subject.gender or 'm', clause.person, clause.number
    if subject.number == 'pl' and any(getattr(m, 'lemma', '') in DUAL_WORDS for m in subject.modifiers):
        return gender, 3, 'du'   # 両数の主語には両数の動詞 (dvau BrAtarO AstAm)
    return gender, 3, subject.number


def verb_word(clause, person, number):
    if clause.copula:
        if clause.tense in ('imperfect', 'perfect', 'past-perfect'):
            return tinanta(dhatu('as', '2'), 'imperfect', 'indicative', 'active', person, number)
        if clause.tense in ('future', 'future-perfect'):
            return tinanta(dhatu('BU', '1'), 'future', 'indicative', 'active', person, number)
        if clause.verb.lang == 'sa' and clause.verb.surface:
            return tinanta(dhatu('as', '2'), 'present', 'indicative', 'active', person, number)   # tat tvam asi
        return None
    root, gana = verb_root(clause.verb)
    d = dhatu(root, gana) if root else None
    if clause.verb.lang == 'sa' and clause.verb.surface and root and not gana:
        # 元がサンスクリットなら、元の語形を作る類の語根を選ぶ (adadāt → dā 第3類)
        from dragoman.sanskrit import script
        original = script.to_slp1(clause.verb.surface)
        for candidate in _dhatus().get(root, []) + _loose_dhatus().get(_loose(root), []):
            if tinanta(candidate, clause.tense if clause.tense != 'perfect' else 'imperfect', clause.mood,
                       clause.voice, person, number) == original:
                d = candidate
                break
    if d is None:
        return '[%s]' % english.word(clause.verb)
    if clause.mood == 'infinitive':
        return subanta(Pratipadika.krdanta(d, Krt.tumun), 'm', 'Nom', 'sg')
    return tinanta(d, clause.tense, clause.mood, clause.voice, person, number) or '*' + root


def infinitive_phrase(inner, main_subject):
    import dataclasses
    kind = inner.infinitive_kind
    subjects = inner.role('subject')
    if kind == 'saying' and subjects:
        # 直接話法 + iti。再帰代名詞 (sē) は話し手自身なので 1人称 (「私はバラを愛する」と少女は言う)
        finite = dataclasses.replace(inner, mood='indicative', infinitive_kind='')
        if subjects[0].head is not None and subjects[0].head.lemma == 'sē':
            finite = dataclasses.replace(finite, person=1, number=subjects[0].number,
                                         args=[(r, np) for r, np in finite.args if np is not subjects[0]])
        else:
            finite = dataclasses.replace(finite, person=3, number=subjects[0].number if not subjects[0].members
                                         else 'pl')
        return realize(finite, capitalize=False) + ' iti'
    if kind == 'perception' and subjects:
        # 見る・聞く: 目的語 + 現在分詞の対格 (bAlikAM gAyantIm paSyAmi)
        subject = subjects[0]
        stem, gender = noun_stem(subject.head, subject.gender) if not subject.members else (None, 'm')
        root, gana = verb_root(inner.verb)
        d = dhatu(root, gana) if root else None
        rest = [noun_phrase(np, ROLE_CASES.get(r, 'Acc')) if r != 'prep' else prepositional(np)
                for r, np in inner.args if np is not subject]
        word = subanta(Pratipadika.krdanta(d, Krt.Satf), gender or 'f', 'Acc', subject.number) if d else '?'
        return ' '.join([noun_phrase(subject, 'Acc')] + rest + [word])
    rest = realize(dataclasses.replace(inner, args=[(r, np) for r, np in inner.args if r != 'subject']),
                   capitalize=False)
    if subjects and kind == 'command':
        return noun_phrase(subjects[0], 'Acc') + ' ' + rest
    return rest


def question_phrase(inner):
    """間接疑問: 疑問詞はその場に (疑問代名詞 kim は格変化、疑問の副詞は節の頭)、動詞は直説法、終わりに iti
    (rAjA bAlakaH kimarTam arodIt iti apfcCat)"""
    import dataclasses
    from . import connectives
    from .frame import interrogative_np
    from .frame import question_idiom
    finite = dataclasses.replace(inner, mood='indicative', question_word='')
    idiom, stripped = question_idiom(inner)
    stripped = dataclasses.replace(stripped, mood='indicative', question_word='')
    if idiom:
        return {'where': 'kutra', 'why': 'kimartham', 'how': 'katham', 'when': 'kadA'}[idiom] + ' ' + \
            realize(stripped) + ' iti'
    text = realize(finite)
    if interrogative_np(inner)[2] is None:
        entry = connectives.interrogative(inner.question_word)
        text = (entry[2] if entry else inner.question_word) + ' ' + text
    return text + ' iti'


def realize(clause, capitalize=True):
    from .frame import lexical_negation
    clause = lexical_negation(clause)   # nesciō → na + jYA
    subjects = clause.role('subject')
    subject = subjects[0] if subjects else None
    gender, person, number = _agreement(subject, clause)
    out = []
    possessors = [np for np in clause.role('recipient') if clause.copula and not clause.role('complement')]
    if possessors and subject is not None:
        # 所有の与格 (Liber mihi est) → mama pustakam asti (所有者は属格)
        return ' '.join([noun_phrase(possessors[0], 'Gen'), noun_phrase(subject, 'Nom'),
                         verb_word(clause, 3, subject.number) or tinanta(dhatu('as', '2'), 'present', 'indicative',
                                                                         'active', 3, subject.number)])
    for p in clause.adjuncts:
        if p.kind == 'absolute':
            out.append(participial(p))
    if clause.mood not in ('imperative', 'infinitive') and subject is not None:
        if not (subject.head is not None and subject.head.lemma in ('ego', 'tū', 'nōs', 'vōs')):
            out.append(noun_phrase(subject, 'Nom'))
        for other in subjects[1:]:
            out.append(noun_phrase(other, 'Nom'))
    for p in clause.adjuncts:
        if p.kind != 'absolute':
            out.append(participial(p, subject))
    for np in clause.role('recipient'):
        out.append(noun_phrase(np, 'Dat'))
    root = verb_root(clause.verb)[0] if not clause.copula else None
    for np in clause.role('object'):
        out.append(noun_phrase(np, GOVERNMENT.get(root, 'Acc')))
    for role, np in clause.args:
        if role in ('subject', 'object', 'recipient', 'complement'):
            continue
        out.append(prepositional(np, clause.voice == 'passive') if role == 'prep'
                   else noun_phrase(np, ROLE_CASES.get(role, 'Ins')))
    for inner in clause.infinitives:
        out.append(infinitive_phrase(inner, subject))
    for inner in clause.questions:
        out.append(question_phrase(inner))
    for np in clause.role('complement'):
        if subject is not None and not np.members and np.head.pos in ('adj', 'participle'):
            out.append(adjective(np.head, gender, 'Nom', number))   # 補語の形容詞は主語に一致 (jIvanam alpam)
        elif subject is not None and np.members and all(m.head is not None and m.head.pos in ('adj', 'participle')
                                                        for m in np.members):
            out.append(' '.join(adjective(m.head, gender, 'Nom', number) for m in np.members) + ' ca')
        else:
            out.append(noun_phrase(np, 'Nom'))
    out += [adverb(adv) for adv in clause.adverbs]
    if clause.negated:
        out.append('na')
    verb = verb_word(clause, person, number)
    if verb is None and clause.copula and not clause.role('complement') and len(clause.args) > 1:
        verb = tinanta(dhatu('as', '2'), 'present', 'indicative', 'active', person, number)   # 存在: asti
    if verb:
        out.append(verb)
    return ' '.join(w for w in out if w)


def sentence(clauses):
    """IAST (デーヴァナーガリー)"""
    if not clauses:
        return ''
    import re
    from . import connectives
    slp1 = connectives.join(clauses, [realize(c) for c in clauses], 'sa')
    slp1 = re.sub(r'\[[^\]]*\]', lambda m: m.group(0).replace(' ', '_'), slp1)   # [wait for] を1語に
    words = [w.replace('_', ' ') for w in slp1.split(' ')]
    iast = ' '.join(w if w.startswith(('[', '*')) else script.iast(w) for w in words)
    deva = ' '.join(w if w.startswith(('[', '*')) else script.devanagari(w) for w in words)
    return '%s ।\n            %s ।' % (iast, deva)
