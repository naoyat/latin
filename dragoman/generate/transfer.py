#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 語の置き換え: 元の言語の語 (Lex) → 作る言語の見出し語
#
#   英語を仲立ちにする: 元の語の英語の訳語の候補 (english.candidates。解析の日本語に合うものが先頭) と、
#   作る言語の見出し語の英語の訳語 ($DRAGOMAN_DATA/<lang>/en-index.tsv。tools/build_english_index.py) を突き合わせる。
#   どちらの訳語の並びでも前にあるほど、語義の多い (よく使う) 語ほど良い。さらに、作る言語の辞書の日本語の訳語
#   (<lang>/wiktionary.sqlite。無ければ英語の訳語を英語 → 日本語の表で) が元の語の日本語の訳語と合えば良くする
#     rēx「王」→ sa: rAjan (君主,王,…) を sTapati より先に
#     puella (girl, lass, maiden …) → ru: девочка (girl, little girl)、sa: kanyA (maiden, daughter …)
#
import csv
import functools
import math
import os
import re
import sqlite3
from dataclasses import dataclass

from dragoman.core import paths, en_ja
from . import english


@dataclass(frozen=True)
class Target:
    lemma: str
    pos: str
    english: tuple
    gender: str = ''
    gana: str = ''     # サンスクリットの動詞の類
    senses: int = 1


# 英語 → 見出し語の表: Wiktionary 由来 (tools/build_english_index.py) と、サンスクリットは Apte の英梵辞典
# (tools/build_sanskrit_apte.py。7列目に英語の見出しの中での候補の順位)
INDEX_FILES = {'sa': ('en-index.tsv', 'en-index-apte.tsv')}


@functools.lru_cache(maxsize=4)
def _index(lang):
    """英語 → [(訳語の中の順位, Target)]"""
    if lang == 'la':
        return _latin_index()
    index = {}
    for name in INDEX_FILES.get(lang, ('en-index.tsv',)):
        path = paths.data(lang, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            for row in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                if len(row) not in (6, 7):
                    continue
                lemma, pos, en, gender, gana, senses = row[:6]
                glosses = tuple(g.strip() for g in en.split(',') if g.strip())
                target = Target(lemma, pos, glosses, gender, gana, int(senses))
                if len(row) == 7:   # 英梵辞典: 見出しの英語ひとつ (chest=box は chest で引き、box で日本語と照らす)
                    key, _, ref = en.partition('=')
                    target = Target(lemma, pos, (ref or key,), gender, gana, int(senses))
                    index.setdefault(key.lower(), []).append((int(row[6]), target))
                    continue
                for rank, g in enumerate(glosses):
                    index.setdefault(g.lower(), []).append((rank, target))
    return index


@functools.lru_cache(maxsize=1)
def _latin_index():
    """ラテン語を作るとき: 英語 → ラテン語の見出し (la-en.tsv。english._table を逆に)"""
    table, _ = english._table()
    index = {}
    for (lemma, pos), entries in table.items():
        for glosses in entries:
            target = Target(lemma, pos, tuple(glosses), '', '', len(glosses))
            for rank, g in enumerate(glosses):
                index.setdefault(g.lower(), []).append((rank, target))
    return index


@functools.lru_cache(maxsize=4)
def _by_lemma(lang):
    """見出し → [英語] (ロシア語・サンスクリットの語の英語の訳語。en-index.tsv を見出しで)"""
    out = {}
    for name in INDEX_FILES.get(lang, ('en-index.tsv',))[:1]:
        path = paths.data(lang, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            for row in csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
                if len(row) >= 6:
                    out.setdefault((row[0], row[1]), []).extend(g.strip() for g in row[2].split(',') if g.strip())
    return out


def _in_hand_dictionary(lemma):
    from . import latin
    return lemma in latin._hand_index()


def source_key(lang, lemma):
    """元の言語の見出しを表の形に (サンスクリットは IAST → SLP1)"""
    if lang == 'sa':
        from dragoman.sanskrit import script
        return script.to_slp1(lemma.replace('-', ''))   # 複合語・語根の切れ目 (rāma-lakṣmaṇa、ud-i) は除く
    if lang == 'ru':
        from dragoman.russian import script
        return script.key(lemma)
    return lemma


def english_glosses(lang, lemma, pos):
    """元の言語の語の英語の訳語 (表から)"""
    pos = {'participle': 'verb', 'name': 'noun'}.get(pos, pos)
    return list(dict.fromkeys(_by_lemma(lang).get((source_key(lang, lemma), pos), [])))


def available(lang):
    return bool(_index(lang))


@functools.lru_cache(maxsize=4)
def _db(lang):
    path = paths.data(lang, 'wiktionary.sqlite')
    return sqlite3.connect(path, check_same_thread=False) if os.path.exists(path) else None


@functools.lru_cache(maxsize=50000)
def japanese(lang, target):
    """作る言語の見出し語の日本語の訳語 (の集合)"""
    out = set()
    if lang == 'la':   # ラテン語の辞書 (手作りの辞書・Wiktionary) の項目の訳語
        from . import latin
        from .ja_lexicon import _keys
        for _, item in latin._forms(target.lemma, target.pos)[:20]:
            out.update(_keys(item.get('ja')))
        return frozenset(out)
    db = _db(lang) if lang != 'grc' else None   # ギリシア語の辞書は lemmas.info (JSON) だけで日本語の訳語の列が無い
    if db is not None:
        pos = 'root' if target.pos == 'verb' and lang == 'sa' else target.pos
        for ja, gloss_lang in db.execute('SELECT ja, gloss_lang FROM lemmas WHERE key = ? AND pos IN (?, ?)',
                                         (target.lemma, pos, target.pos)):
            if gloss_lang == 'ja':
                out.update(j.strip() for j in ja.split(','))
    for en in target.english[:2]:
        out.update(en_ja.lookup(en, target.pos))
    return frozenset(out)


# 基本の語は、教科書でよく使う語を先に (英語の訳語の表と語義の数だけでは、девушка / kanyakA のような語が先に来る)。
# (英語, 品詞) → (見出し語, 性または語根の類)
PREFERRED = {
    'ru': {('girl', 'noun'): ('девочка', 'f'), ('book', 'noun'): ('книга', 'f'), ('king', 'noun'): ('царь', 'm'),
           ('farmer', 'noun'): ('крестьянин', 'm'), ('sailor', 'noun'): ('моряк', 'm'),
           ('slave', 'noun'): ('раб', 'm'), ('lord', 'noun'): ('господин', 'm'), ('master', 'noun'): ('господин', 'm'),
           ('teacher', 'noun'): ('учитель', 'm'), ('letter', 'noun'): ('письмо', 'n'),
           ('walk', 'verb'): ('гулять', ''), ('love', 'verb'): ('любить', ''), ('sing', 'verb'): ('петь', ''),
           ('praise', 'verb'): ('хвалить', ''), ('see', 'verb'): ('видеть', ''), ('give', 'verb'): ('давать', ''),
           ('carry', 'verb'): ('нести', ''), ('convey', 'verb'): ('нести', ''), ('say', 'verb'): ('говорить', ''),
           ('beautiful', 'adj'): ('красивый', ''), ('great', 'adj'): ('великий', ''),
           ('good', 'adj'): ('хороший', ''), ('long', 'adj'): ('длинный', ''), ('city', 'noun'): ('город', 'm'),
           ('town', 'noun'): ('город', 'm'), ('road', 'noun'): ('дорога', 'f'), ('forest', 'noun'): ('лес', 'm'),
           ('field', 'noun'): ('поле', 'n'), ('flower', 'noun'): ('цветок', 'm'), ('friend', 'noun'): ('друг', 'm'),
           ('male friend', 'noun'): ('друг', 'm'), ('man', 'noun'): ('мужчина', 'm'),
           ('people', 'noun'): ('народ', 'm'), ('queen', 'noun'): ('царица', 'f'), ('mother', 'noun'): ('мать', 'f'),
           ('soldier', 'noun'): ('солдат', 'm'), ('enemy', 'noun'): ('враг', 'm'), ('sword', 'noun'): ('меч', 'm'),
           ('thing', 'noun'): ('дело', 'n'), ('camp', 'noun'): ('лагерь', 'm'), ('word', 'noun'): ('слово', 'n'),
           ('messenger', 'noun'): ('вестник', 'm'), ('life', 'noun'): ('жизнь', 'f'), ('temple', 'noun'): ('храм', 'm'),
           ('think', 'verb'): ('думать', ''), ('consider', 'verb'): ('думать', ''), ('come', 'verb'): ('приходить', ''),
           ('weep', 'verb'): ('плакать', ''), ('laugh', 'verb'): ('смеяться', ''), ('sleep', 'verb'): ('спать', ''),
           ('wait', 'verb'): ('ждать', ''), ('fear', 'verb'): ('бояться', ''), ('fight', 'verb'): ('сражаться', ''),
           ('take', 'verb'): ('брать', ''), ('capture', 'verb'): ('брать', ''), ('move', 'verb'): ('двигать', ''),
           ('pluck', 'verb'): ('рвать', ''), ('learn', 'verb'): ('узнавать', ''), ('know', 'verb'): ('знать', ''),
           ('play', 'verb'): ('играть', ''), ('labor', 'verb'): ('трудиться', ''), ('work', 'verb'): ('работать', ''),
           ('order', 'verb'): ('велеть', ''), ('command', 'verb'): ('велеть', ''), ('read', 'verb'): ('читать', ''),
           ('crowd', 'noun'): ('народ', 'm'), ('die', 'verb'): ('умирать', ''), ('kill', 'verb'): ('убивать', ''),
           ('brother', 'noun'): ('брат', 'm'),
           ('receive', 'verb'): ('получать', ''), ('ask', 'verb'): ('спрашивать', ''),
           ('want', 'verb'): ('хотеть', ''), ('wish', 'verb'): ('хотеть', ''), ('greatly', 'adv'): ('очень', ''), ('suddenly', 'adv'): ('вдруг', ''),
           ('willingly', 'adv'): ('охотно', ''), ('gladly', 'adv'): ('охотно', ''), ('uselessly', 'adv'): ('напрасно', ''),
           ('in vain', 'adv'): ('напрасно', ''), ('heavily', 'adv'): ('тяжело', ''), ('by chance', 'adv'): ('случайно', ''),
           ('kindly', 'adv'): ('ласково', ''), ('everywhere', 'adv'): ('везде', ''),
           ('golden', 'adj'): ('золотой', ''), ('happy', 'adj'): ('счастливый', ''), ('glad', 'adj'): ('радостный', '')},
    'la': {('see', 'verb'): ('videō', ''), ('rejoice', 'verb'): ('gaudeō', ''), ('be happy', 'verb'): ('gaudeō', ''), ('die', 'verb'): ('morior', ''), ('give', 'verb'): ('dō', ''),
           ('love', 'verb'): ('amō', ''), ('like', 'verb'): ('amō', ''), ('praise', 'verb'): ('laudō', ''),
           ('read', 'verb'): ('legō', ''), ('weep', 'verb'): ('fleō', ''), ('cry', 'verb'): ('fleō', ''),
           ('boy', 'noun'): ('puer', 'm'), ('girl', 'noun'): ('puella', 'f'), ('teacher', 'noun'): ('magister', 'm'),
           ('book', 'noun'): ('liber', 'm'), ('king', 'noun'): ('rēx', 'm'), ('tsar', 'noun'): ('rēx', 'm'),
           ('people', 'noun'): ('populus', 'm'), ('garden', 'noun'): ('hortus', 'm'), ('winter', 'noun'): ('hiems', 'f'),
           ('say', 'verb'): ('dīcō', ''), ('come', 'verb'): ('veniō', ''), ('go', 'verb'): ('eō', ''),
           ('know', 'verb'): ('sciō', ''), ('want', 'verb'): ('volō', ''), ('sing', 'verb'): ('cantō', ''),
           ('write', 'verb'): ('scrībō', ''), ('live', 'verb'): ('vīvō', ''), ('city', 'noun'): ('urbs', 'f'),
           ('house', 'noun'): ('domus', 'f'), ('water', 'noun'): ('aqua', 'f'), ('man', 'noun'): ('vir', 'm'),
           ('woman', 'noun'): ('fēmina', 'f'), ('mother', 'noun'): ('māter', 'f'), ('father', 'noun'): ('pater', 'm')},
    'sa': {('girl', 'noun'): ('bAlikA', 'f'), ('boy', 'noun'): ('bAlaka', 'm'), ('king', 'noun'): ('nfpa', 'm'),
           ('book', 'noun'): ('pustaka', 'n'), ('farmer', 'noun'): ('kfzaka', 'm'), ('slave', 'noun'): ('dAsa', 'm'),
           ('lord', 'noun'): ('svAmin', 'm'), ('master', 'noun'): ('svAmin', 'm'),
           ('teacher', 'noun'): ('aDyApaka', 'm'), ('friend', 'noun'): ('mitra', 'm'),
           ('city', 'noun'): ('nagara', 'n'), ('town', 'noun'): ('nagara', 'n'), ('garden', 'noun'): ('udyAna', 'n'),
           ('forest', 'noun'): ('vana', 'n'), ('field', 'noun'): ('kzetra', 'n'), ('sea', 'noun'): ('samudra', 'm'),
           ('flower', 'noun'): ('puzpa', 'n'), ('sailor', 'noun'): ('nAvika', 'm'), ('letter', 'noun'): ('patra', 'n'),
           ('sing', 'verb'): ('gE', '1'), ('love', 'verb'): ('snih', '4'), ('say', 'verb'): ('vad', '1'),
           ('speak', 'verb'): ('vad', '1'), ('see', 'verb'): ('dfS', '1'), ('give', 'verb'): ('dA', '3'),
           ('praise', 'verb'): ('praSaMs', '1'), ('walk', 'verb'): ('cal', '1'), ('carry', 'verb'): ('vah', '1'),
           ('convey', 'verb'): ('vah', '1'), ('live', 'verb'): ('jIv', '1'), ('reside', 'verb'): ('vas', '1'),
           ('beautiful', 'adj'): ('sundara', ''), ('great', 'adj'): ('viSAla', ''), ('good', 'adj'): ('sADu', ''),
           ('daughter', 'noun'): ('duhitf', 'f'), ('man', 'noun'): ('nara', 'm'), ('road', 'noun'): ('mArga', 'm'),
           ('mother', 'noun'): ('mAtf', 'f'), ('queen', 'noun'): ('rAjYI', 'f'), ('word', 'noun'): ('vacana', 'n'),
           ('soldier', 'noun'): ('sEnika', 'm'), ('people', 'noun'): ('jana', 'm'), ('crowd', 'noun'): ('jana', 'm'),
           ('temple', 'noun'): ('mandira', 'n'), ('enemy', 'noun'): ('ari', 'm'), ('sword', 'noun'): ('Kaqga', 'm'),
           ('thing', 'noun'): ('vastu', 'n'), ('life', 'noun'): ('jIvana', 'n'), ('messenger', 'noun'): ('dUta', 'm'),
           ('happy', 'adj'): ('prasanna', ''), ('glad', 'adj'): ('prasanna', ''),
           ('labor', 'verb'): ('Sram', '4'), ('work', 'verb'): ('Sram', '4'), ('leave', 'verb'): ('nirgam', '1'),
           ('depart', 'verb'): ('nirgam', '1'), ('wait', 'verb'): ('pratiIkz', '1'), ('fear', 'verb'): ('BI', '3'),
           ('think', 'verb'): ('cint', '10'), ('consider', 'verb'): ('cint', '10'), ('learn', 'verb'): ('jYA', '9'),
           ('know', 'verb'): ('jYA', '9'), ('command', 'verb'): ('AdiS', '6'), ('order', 'verb'): ('AdiS', '6'),
           ('move', 'verb'): ('cal', '1'), ('fight', 'verb'): ('yuD', '4'), ('die', 'verb'): ('mf', '6'),
           ('weep', 'verb'): ('rud', '2'), ('laugh', 'verb'): ('has', '1'), ('sleep', 'verb'): ('svap', '2'),
           ('play', 'verb'): ('krIq', '1'), ('read', 'verb'): ('paW', '1'), ('come', 'verb'): ('Agam', '1'),
           ('receive', 'verb'): ('grah', '9'), ('greatly', 'adv'): ('atIva', ''), ('suddenly', 'adv'): ('sahasA', ''),
           ('willingly', 'adv'): ('sAnandam', ''), ('gladly', 'adv'): ('sAnandam', ''), ('uselessly', 'adv'): ('vfTA', ''),
           ('in vain', 'adv'): ('vfTA', ''), ('heavily', 'adv'): ('BfSam', ''), ('by chance', 'adv'): ('daivAt', ''),
           ('kindly', 'adv'): ('snehena', ''), ('everywhere', 'adv'): ('sarvatra', ''),
           ('place', 'noun'): ('sTAna', 'n'), ('kill', 'verb'): ('han', '2'), ('slay', 'verb'): ('han', '2'), ('reply', 'verb'): ('prativac', '2'),
           ('answer', 'verb'): ('prativac', '2'), ('stretch', 'verb'): ('tan', '8'), ('greek', 'adj'): ('yavana', ''),
           ('greek', 'noun'): ('yavana', 'm'), ('flee', 'verb'): ('palAy', '1'),
           ('ask', 'verb'): ('praC', '6'), ('begin', 'verb'): ('Arab', '1'), ('seize', 'verb'): ('grah', '9'),
           ('drag', 'verb'): ('kfz', '1'), ('climb up', 'verb'): ('Aruh', '1'), ('climb', 'verb'): ('Aruh', '1'),
           ('carefully', 'adv'): ('yatnena', ''), ('centaur', 'noun'): ('kinnara', 'm'),
           ('boat', 'noun'): ('nOkA', 'f'), ('ship', 'noun'): ('nO', 'f'), ('cattle', 'noun'): ('go', 'm'),
           ('fruit', 'noun'): ('Pala', 'n'), ('priestess', 'noun'): ('tApasI', 'f'), ('victim', 'noun'): ('paSu', 'm')},
    'grc': {('girl', 'noun'): ('κόρη', 'f'), ('boy', 'noun'): ('παῖς', 'm'), ('child', 'noun'): ('παῖς', 'm'),
            ('king', 'noun'): ('βασιλεύς', 'm'), ('queen', 'noun'): ('βασίλεια', 'f'), ('book', 'noun'): ('βιβλίον', 'n'),
            ('teacher', 'noun'): ('διδάσκαλος', 'm'), ('master', 'noun'): ('δεσπότης', 'm'),
            ('lord', 'noun'): ('δεσπότης', 'm'), ('slave', 'noun'): ('δοῦλος', 'm'), ('sailor', 'noun'): ('ναύτης', 'm'),
            ('farmer', 'noun'): ('γεωργός', 'm'), ('man', 'noun'): ('ἀνήρ', 'm'), ('woman', 'noun'): ('γυνή', 'f'),
            ('city', 'noun'): ('πόλις', 'f'), ('god', 'noun'): ('θεός', 'm'), ('goddess', 'noun'): ('θεά', 'f'),
            ('war', 'noun'): ('πόλεμος', 'm'), ('letter', 'noun'): ('ἐπιστολή', 'f'), ('word', 'noun'): ('λόγος', 'm'),
            ('road', 'noun'): ('ὁδός', 'f'), ('way', 'noun'): ('ὁδός', 'f'), ('house', 'noun'): ('οἰκία', 'f'),
            ('friend', 'noun'): ('φίλος', 'm'), ('soldier', 'noun'): ('στρατιώτης', 'm'), ('ship', 'noun'): ('ναῦς', 'f'),
            ('island', 'noun'): ('νῆσος', 'f'), ('horse', 'noun'): ('ἵππος', 'm'), ('sea', 'noun'): ('θάλαττα', 'f'),
            ('land', 'noun'): ('γῆ', 'f'), ('earth', 'noun'): ('γῆ', 'f'), ('water', 'noun'): ('ὕδωρ', 'n'),
            ('see', 'verb'): ('ὁράω', ''), ('praise', 'verb'): ('ἐπαινέω', ''), ('give', 'verb'): ('δίδωμι', ''),
            ('love', 'verb'): ('φιλέω', ''), ('say', 'verb'): ('λέγω', ''), ('have', 'verb'): ('ἔχω', ''),
            ('write', 'verb'): ('γράφω', ''), ('carry', 'verb'): ('φέρω', ''), ('bear', 'verb'): ('φέρω', ''),
            ('lead', 'verb'): ('ἄγω', ''), ('come', 'verb'): ('ἔρχομαι', ''), ('go', 'verb'): ('ἔρχομαι', ''),
            ('send', 'verb'): ('πέμπω', ''), ('teach', 'verb'): ('διδάσκω', ''), ('hear', 'verb'): ('ἀκούω', ''),
            ('sing', 'verb'): ('ᾄδω', ''), ('walk', 'verb'): ('βαδίζω', ''), ('fight', 'verb'): ('μάχομαι', ''),
            ('kill', 'verb'): ('ἀποκτείνω', ''), ('take', 'verb'): ('λαμβάνω', ''), ('know', 'verb'): ('γιγνώσκω', ''),
            ('beautiful', 'adj'): ('καλός', ''), ('good', 'adj'): ('ἀγαθός', ''), ('bad', 'adj'): ('κακός', ''),
            ('evil', 'adj'): ('κακός', ''), ('great', 'adj'): ('μέγας', ''), ('big', 'adj'): ('μέγας', ''),
            ('large', 'adj'): ('μέγας', ''), ('small', 'adj'): ('μικρός', ''), ('long', 'adj'): ('μακρός', ''),
            ('wise', 'adj'): ('σοφός', ''), ('brave', 'adj'): ('ἀνδρεῖος', ''), ('new', 'adj'): ('νέος', ''),
            ('old', 'adj'): ('παλαιός', ''), ('many', 'adj'): ('πολύς', ''), ('dear', 'adj'): ('φίλος', '')},
}


PARTICLES = ('to', 'as', 'at', 'on', 'for', 'with', 'into', 'upon', 'in', 'from', 'of', 'out', 'up', 'away',
             'off', 'down', 'by')


def _variants(sources):
    """英語の訳語と、その簡単な形 (順位は少し下げる): drive or move to → drive, move;
    address as → address; look at → look; put together → put"""
    out = []
    for i, en in enumerate(sources):
        out.append((i, en))
        m = re.match(r'^(?:any |a )?(?:head|heads|type|kind|sort|piece|species) of (.+)$', en)
        if m:
            out.append((i + 0.3, m.group(1)))   # head of cattle → cattle, any type of fruit → fruit
        elif ' of ' in en and not en.startswith('of '):
            out.append((i + 0.6, en.split(' of ')[0]))   # priestess of Pythian Apollo → priestess
        if en.startswith('of '):
            out.append((i + 0.6, en[3:].split(' ')[0]))   # of such size → such
        words = en.split()
        if 1 < len(words) <= 3 and ' of ' not in en and ' or ' not in en:
            out.append((i + 0.8, words[-1]))   # sacrificial victim → victim, light boat → boat (名詞の頭)
        for part in en.split(' or '):
            words = part.split()
            while len(words) > 1 and words[-1] in PARTICLES:
                words = words[:-1]
            simple = ' '.join(words)
            if simple and simple != en:
                out.append((i + 0.5, simple))
            if len(words) > 1 and part != en:
                out.append((i + 0.7, words[0]))
    return out


def candidates(lex, lang, pos=None):
    """Lex → [(点, Target)] (点の小さいほうが良い)。元の言語と作る言語が同じなら置き換えない"""
    pos = pos or {'participle': 'verb'}.get(lex.pos, lex.pos)
    if (lex.lang or 'la') == lang:
        return [(-1000, Target(source_key(lang, lex.lemma), pos, (), '', '', 1))]
    sources = english.candidates(lex) or ([e for e in lex.en.split(',') if e] if lex.en else [])
    for en in sources[:1] + [e.replace(' for', '') for e in sources[:1] if e.endswith(' for')]:   # wait for → wait
        words = en.lower().split(' ')
        preferred = PREFERRED.get(lang, {}).get((en.lower(), pos)) or \
            PREFERRED.get(lang, {}).get((words[-1], pos)) or \
            (PREFERRED.get(lang, {}).get((words[0], pos)) if pos == 'verb' else None)   # die of … → die
        if preferred:
            lemma, extra = preferred
            gender, gana = (extra, '') if pos != 'verb' else ('', extra)
            return [(-100, Target(lemma, pos, (en,), gender, gana))]
    wanted = [j.strip() for j in (lex.ja or '').split(',') if j.strip()]
    scored, matched = {}, {}
    for i, en in _variants(sources[:6]):
        for j, target in _index(lang).get(en.lower(), []):
            if target.pos != pos or j > 5:
                continue
            score = 3 * i + j - math.log(1 + target.senses)
            if lang == 'la' and _in_hand_dictionary(target.lemma):
                score -= 3   # 手作りの辞書にある (よく使う) ラテン語の語 (hortus を gardīnum より)
            ja = japanese(lang, target)
            if wanted and wanted[0] in ja:
                score -= 3     # 日本語の一番の訳語が合う
            elif any(w in ja for w in wanted):
                score -= 2
            matched.setdefault((target.lemma, target.pos), set()).add(int(i))
            if target not in scored or score < scored[target]:
                scored[target] = score
    # 元の語の英語の訳語の複数に合う語を良くする (arca: chest, box → 「胸」の uras より、chest と box の両方にある「箱」)
    best_by_lemma = {}
    for target, score in scored.items():
        score -= 2 * (len(matched[(target.lemma, target.pos)]) - 1)
        key = (target.lemma, target.pos)
        if key not in best_by_lemma or score < best_by_lemma[key][0]:
            best_by_lemma[key] = (score, target)
    return sorted(best_by_lemma.values(), key=lambda st: st[0])


def by_english(words, lang, pos):
    """英語の語の列 (前ほど良い) → 作る言語の見出し語の候補 (分詞の英語の訳語から動詞を引く)"""
    scored = {}
    for i, en in _variants(list(words)[:8]):
        for j, target in _index(lang).get(en.lower(), []):
            if target.pos == pos and j <= 5:
                score = 3 * i + j - math.log(1 + target.senses)
                key = (target.lemma, target.gana)
                if key not in scored or score < scored[key][0]:
                    scored[key] = (score, target)
    return sorted(scored.values(), key=lambda st: st[0])


def best(lex, lang, pos=None):
    found = candidates(lex, lang, pos)
    return found[0][1] if found else None
