#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) からインドネシア語の文を作る
#
#   語形変化は無い。動詞の派生の接辞と語順・機能語で組み立てる
#   動詞: 語は語根 (baca「読む」) で引き、目的語があれば meN- 形 (membaca)、受動は di- 形 (dibaca) + oleh 動作主。
#         目的語の無い動詞は辞書に ber- 形 (bernyanyi) があればそれ。派生形は辞書 (id/wiktionary.sqlite の active / passive)
#         を先に、無ければ鼻音の交替の規則で (tulis → menulis、pakai → memakai、kirim → mengirim、sapu → menyapu)
#   時制: 語形は変えず副詞で (完了 telah、未来 akan。未完了過去・現在は印なし)。否定 tidak (名詞の述語は bukan)
#   繋辞: 形容詞の述語は無し (Gadis itu cantik)、名詞の述語は adalah
#   語順: 主語 - (副詞) - 動詞 - 目的語 - kepada 受け手 - 前置詞句。名詞の後ろに形容詞・属格・ini / itu
#   複数: 重複 (anak-anak)。関係節: yang + 節 (目的語の空所は di- 受動: buku yang dibaca guru、1・2人称は yang saya baca)
#
import functools
import os
import sqlite3

from dragoman.core import paths
from . import transfer, english
from .frame import Lex, NP

PRONOUNS = {('ego', 'sg'): 'saya', ('ego', 'pl'): 'kami', ('tū', 'sg'): 'kamu', ('tū', 'pl'): 'kalian',
            ('is', 'sg'): 'dia', ('is', 'pl'): 'mereka', ('sē', 'sg'): 'dirinya', ('sē', 'pl'): 'diri mereka',
            ('quis', 'sg'): 'siapa', ('quis', 'pl'): 'siapa', ('quid', 'sg'): 'apa', ('quid', 'pl'): 'apa',
            ('nēmō', 'sg'): 'tidak seorang pun', ('nihil', 'sg'): 'tidak ada apa-apa',
            ('ipse', 'sg'): 'dia sendiri', ('ipse', 'pl'): 'mereka sendiri', ('alius', 'sg'): 'yang lain',
            ('alius', 'pl'): 'yang lain', ('alter', 'sg'): 'yang lain', ('īdem', 'sg'): 'yang sama',
            ('īdem', 'pl'): 'yang sama'}
# 語ごとに決まった訳 (人称代名詞を含む副詞 sēcum「自分と一緒に」など)
WORDS = {'sēcum': 'bersamanya', 'mēcum': 'bersamaku', 'tēcum': 'bersamamu', 'nōbīscum': 'bersama kami',
         'magnopere': 'sangat', 'frūstrā': 'sia-sia', 'libenter': 'dengan senang hati', 'longē': 'jauh',
         'graviter': 'dengan berat', 'benignē': 'dengan ramah', 'aliter': 'kalau tidak', 'umquam': 'pernah',
         'numquam': 'tidak pernah', 'semper': 'selalu', 'saepe': 'sering', 'statim': 'segera', 'mox': 'segera',
         'posteā': 'kemudian', 'tandem': 'akhirnya', 'iterum': 'lagi', 'ibi': 'di sana', 'hīc': 'di sini',
         'nōn': 'tidak', 'etiam': 'juga', 'quoque': 'juga', 'sīc': 'begitu', 'ita': 'begitu', 'tam': 'begitu',
         'valdē': 'sangat', 'postrīdiē': 'keesokan harinya', 'hodiē': 'hari ini', 'crās': 'besok', 'heri': 'kemarin',
         'nunc': 'sekarang', 'tunc': 'lalu', 'diū': 'lama', 'paene': 'hampir', 'sōlum': 'hanya',
         'Graecus': 'Yunani', 'centaurus': 'kentaur', 'cyclōps': 'kiklops', 'Cyclōps': 'kiklops'}
DEMONSTRATIVES = {'hic': 'ini', 'hīc': 'ini', 'ille': 'itu', 'is': 'itu', 'iste': 'itu'}
POSSESSIVES = {'meus': 'saya', 'tuus': 'kamu', 'suus': 'nya', 'noster': 'kami', 'vester': 'kalian'}
# ラテン語の前置詞 + 格 → インドネシア語の前置詞
PREPOSITIONS = {('in', 'Abl'): 'di', ('in', 'Acc'): 'ke', ('ad', 'Acc'): 'ke', ('ex', 'Abl'): 'dari', ('ē', 'Abl'): 'dari',
                ('ab', 'Abl'): 'dari', ('ā', 'Abl'): 'dari', ('cum', 'Abl'): 'dengan', ('dē', 'Abl'): 'tentang',
                ('sine', 'Abl'): 'tanpa', ('per', 'Acc'): 'melalui', ('propter', 'Acc'): 'karena', ('ob', 'Acc'): 'karena',
                ('post', 'Acc'): 'setelah', ('ante', 'Acc'): 'sebelum', ('sub', 'Abl'): 'di bawah',
                ('sub', 'Acc'): 'ke bawah', ('super', 'Acc'): 'di atas', ('apud', 'Acc'): 'di', ('prō', 'Abl'): 'untuk',
                ('contrā', 'Acc'): 'melawan', ('inter', 'Acc'): 'di antara', ('prope', 'Acc'): 'dekat',
                ('trāns', 'Acc'): 'di seberang', ('circum', 'Acc'): 'di sekitar', ('ante', 'Abl'): 'di depan'}
ROLE_PREPOSITIONS = {'recipient': 'kepada', 'means': 'dengan', 'place': 'di', 'source': 'dari'}
ASPECTS = {'perfect': 'telah', 'past-perfect': 'telah', 'future': 'akan', 'future-perfect': 'akan telah'}
CONNECTIVES = {'et': 'dan', 'que': 'dan', 'atque': 'dan', 'ac': 'dan', 'sed': 'tetapi', 'at': 'tetapi',
               'autem': 'lalu', 'enim': 'karena', 'nam': 'karena', 'igitur': 'jadi', 'itaque': 'maka',
               'tamen': 'namun', 'neque': 'dan tidak', 'nec': 'dan tidak', 'tum': 'lalu', 'deinde': 'kemudian',
               'ubi': 'ketika', 'cum': 'ketika', 'postquam': 'setelah', 'dum': 'sementara', 'quod': 'karena',
               'quia': 'karena', 'sī': 'jika', 'nisi': 'kecuali jika', 'ut': 'supaya', 'nē': 'supaya tidak',
               'quamquam': 'meskipun', 'etsī': 'meskipun', 'simul': 'begitu', 'priusquam': 'sebelum',
               'antequam': 'sebelum', 'iam': 'sudah', 'aut': 'atau', 'vel': 'atau'}
ADVERB_CONNECTIVES = {'tum', 'deinde', 'iam'}
QUESTION_WORDS = {'cūr': 'mengapa', 'quārē': 'mengapa', 'quōmodo': 'bagaimana', 'quemadmodum': 'bagaimana',
                  'ubi': 'di mana', 'quō': 'ke mana', 'unde': 'dari mana', 'quandō': 'kapan', 'num': 'apakah',
                  'utrum': 'apakah', 'quantus': 'seberapa besar', 'quālis': 'seperti apa', 'quot': 'berapa'}
NUMERALS = {'ūnus': 'satu', 'duo': 'dua', 'trēs': 'tiga', 'quattuor': 'empat', 'quīnque': 'lima', 'sex': 'enam',
            'septem': 'tujuh', 'octō': 'delapan', 'novem': 'sembilan', 'decem': 'sepuluh', 'ūndecim': 'sebelas',
            'duodecim': 'dua belas', 'vīgintī': 'dua puluh', 'centum': 'seratus', 'mīlle': 'seribu',
            'prīmus': 'pertama', 'secundus': 'kedua', 'tertius': 'ketiga'}
QUANTIFIERS = {'omnis': 'semua', 'multus': 'banyak', 'nūllus': 'tidak ada', 'paucī': 'sedikit', 'aliquis': 'seorang',
               'quīdam': 'seorang', 'alius': 'lain', 'tōtus': 'seluruh', 'cēterī': 'yang lain'}
VOWELS = 'aeiou'
# 接辞を付けずに使う動詞 (tahu「知っている」、ingin「〜したい」、tidur「眠る」…)
BARE_VERBS = {'tahu', 'ingin', 'mau', 'suka', 'tidur', 'mati', 'pergi', 'datang', 'tinggal', 'pulang', 'masuk',
              'keluar', 'duduk', 'tiba', 'ada', 'bisa', 'percaya', 'lupa', 'ingat', 'hidup', 'jatuh', 'naik', 'turun',
              'takut', 'senang', 'marah', 'sakit', 'lapar', 'haus'}


def available():
    return transfer.available('id')


@functools.lru_cache(maxsize=1)
def _db():
    path = paths.data('id', 'wiktionary.sqlite')
    return sqlite3.connect(path, check_same_thread=False) if os.path.exists(path) else None


@functools.lru_cache(maxsize=5000)
def derived(root, link):
    """辞書の派生形 (root の active: memberi、passive: diberi)。-kan・-i の付かない短い形を先に"""
    db = _db()
    if db is None:
        return []
    rows = db.execute("SELECT key FROM lemmas WHERE target = ? AND link = ? AND lang = 'id'", (root, link)).fetchall()
    forms = sorted({k for (k,) in rows if ' ' not in k}, key=lambda k: (k.endswith(('kan', 'i')), len(k)))
    return forms


@functools.lru_cache(maxsize=20000)
def _known(word):
    db = _db()
    return db is not None and db.execute("SELECT 1 FROM lemmas WHERE key = ? AND lang = 'id' LIMIT 1",
                                         (word,)).fetchone() is not None


def men(root):
    """meN- + 語根 (鼻音の交替の規則)"""
    if root.startswith(('me', 'ber', 'ter', 'di')) and affixed(root):
        return root   # すでに派生形
    if sum(c in VOWELS for c in root) == 1:
        return 'menge' + root                                 # cat → mengecat
    head = root[0]
    if head in VOWELS:
        return 'meng' + root                                  # ambil → mengambil
    if root.startswith(('sy', 'kh')):
        return ('meny' if root[0] == 's' else 'meng') + root
    if head == 'p':
        return 'mem' + root[1:]                               # pakai → memakai
    if head in 'bfv':
        return 'mem' + root                                   # baca → membaca
    if head == 't':
        return 'men' + root[1:]                               # tulis → menulis
    if head in 'dcjz':
        return 'men' + root                                   # dengar → mendengar
    if head == 's':
        return 'meny' + root[1:]                              # sapu → menyapu
    if head == 'k':
        return 'meng' + root[1:]                              # kirim → mengirim
    if head in 'gh':
        return 'meng' + root                                  # gambar → menggambar
    return 'me' + root                                        # lihat → melihat、rasa → merasa


@functools.lru_cache(maxsize=5000)
def root_of(form):
    """派生形 (menukil、memiliki) の語根。辞書の active / passive の対応から。派生形でなければそのまま"""
    db = _db()
    if db is None:
        return form
    row = db.execute("SELECT target FROM lemmas WHERE key = ? AND link IN ('active', 'passive') AND lang = 'id' "
                     "AND target != '' LIMIT 1", (form,)).fetchone()
    return row[0] if row else form


def _stem_known(stem):
    """語幹 (接尾辞 -i・-kan が付いていてもよい) が辞書の語か"""
    if _known(stem):
        return True
    for suffix in ('kan', 'i'):
        if stem.endswith(suffix) and len(stem) - len(suffix) >= 3 and _known(stem[:-len(suffix)]):
            return True
    return False


@functools.lru_cache(maxsize=5000)
def split_prefix(form):
    """接頭辞の付いた派生形 → (接頭辞, 語幹)。memiliki → ('meN', 'miliki')、berkata → ('ber', 'kata')。違えば None"""
    if not _known(form):
        return None
    if form.startswith(('ber', 'ter')) and len(form) >= 6 and _stem_known(form[3:]):
        return form[:3], form[3:]
    if form.startswith('me'):
        from dragoman.indonesian.morphology import _men_roots
        for stem in _men_roots(form[2:]):
            if len(stem) >= 3 and _stem_known(stem):
                return 'meN', stem
    return None


def affixed(form):
    """接頭辞の付いた派生形か (berkata、memiliki、tertawa。beri・meja は違う)"""
    return root_of(form) != form or split_prefix(form) is not None


def active(root):
    if root in BARE_VERBS or (root.startswith(('me', 'ber')) and affixed(root)):
        return root   # 接辞を付けない動詞 (tahu)、辞書の派生形 (memiliki、berkata)
    found = [f for f in derived(root, 'active') if f.startswith('me')]
    return found[0] if found else men(root)


def intransitive(root):
    """目的語の無い動詞: 辞書に ber- 形があればそれ (nyanyi → bernyanyi)、無ければ meN- 形の辞書の形、無ければ語根"""
    if root in BARE_VERBS or (root.startswith(('ber', 'me', 'ter')) and affixed(root)):
        return root
    for form in derived(root, 'active'):
        if form.startswith('ber'):
            return form
    if _known('ber' + root):
        return 'ber' + root
    found = [f for f in derived(root, 'active') if f.startswith('me')]
    if found:
        return found[0]
    if _known(men(root)) or not _known(root):
        return men(root)   # tangis → menangis (辞書にある meN- 形)
    return root if root in BARE_VERBS or ' ' in root else men(root)   # kurung → mengurung


def passive(root):
    split = split_prefix(root)
    if split and split[0] in ('ber', 'ter'):
        return root   # 自動詞は受動にならない
    root = root_of(root) if root_of(root) != root else (split[1] if split else root)   # memiliki → miliki
    found = derived(root, 'passive')
    return found[0] if found else 'di' + root


# ----------------------------------------------------------------------
# 語

def to_indonesian(lex, pos=None):
    pos = pos or {'participle': 'verb', 'name': 'noun'}.get(lex.pos, lex.pos)
    if lex.lemma in WORDS and lex.lang in ('', 'la'):
        return WORDS[lex.lemma]
    if lex.lemma in NUMERALS and lex.lang in ('', 'la'):
        return NUMERALS[lex.lemma]
    if lex.proper:
        return lex.lemma
    if lex.lang == 'id':
        return lex.lemma
    target = transfer.best(lex, 'id', pos)
    return target.lemma if target else None


def word(lex, pos=None):
    found = to_indonesian(lex, pos)
    return found if found else '[%s]' % english.word(lex)


def noun_phrase(np):
    if np.members:
        conj = 'atau' if np.conj in ('aut', 'vel') else 'dan'
        parts = [noun_phrase(m) for m in np.members]
        return ', '.join(parts[:-1]) + ' ' + conj + ' ' + parts[-1] if len(parts) > 2 else (' %s ' % conj).join(parts)
    head = np.head
    if head is None:
        return ''
    before, after = [], []
    if head.pos == 'pronoun':
        lemma = 'quid' if head.lemma == 'quis' and np.gender == 'n' else head.lemma
        if (lemma, np.number) in PRONOUNS:
            main = PRONOUNS[(lemma, np.number)]
        elif lemma in DEMONSTRATIVES:
            main = DEMONSTRATIVES[lemma] if not np.relatives else ('mereka' if np.number == 'pl' else
                                                                   'orang' if np.animate else 'apa')
        else:
            main = word(head)
    else:
        main = word(head, 'noun')
        if np.number == 'pl' and ' ' not in main and not main.startswith('[') and not head.proper and \
                not any(_is_quantifier(m) for m in np.modifiers if not isinstance(m, NP)):
            main = main + '-' + main   # 重複で複数 (anak-anak)
    for m in np.modifiers:
        if isinstance(m, NP):
            after.append(' dan '.join(_adjective(x.head) for x in m.members))
        elif m.pos == 'pronoun' and m.lemma in DEMONSTRATIVES:
            after.append(DEMONSTRATIVES[m.lemma])
        elif m.lemma in POSSESSIVES:
            after.append(POSSESSIVES[m.lemma])
        elif m.lemma in NUMERALS or m.lemma in QUANTIFIERS:
            q = NUMERALS.get(m.lemma) or QUANTIFIERS[m.lemma]
            (after if q in ('lain', 'seluruh') else before).append(q)
        else:
            after.append(_adjective(m))
    text = ' '.join(before + [main] + [a for a in after if a]).replace(' nya', 'nya')   # pancarnya
    if after and any(a in ('ini', 'itu') for a in after):   # 指示詞は句の最後 (rumah besar itu)
        demos = [a for a in after if a in ('ini', 'itu')]
        text = ' '.join(before + [main] + [a for a in after if a not in ('ini', 'itu')] + demos).replace(' nya', 'nya')
    for g in np.genitives:
        text += ' ' + noun_phrase(g)
    for r in np.relatives:
        text += ' ' + relative_clause(r)
    return text


def _is_quantifier(m):
    return m.lemma in NUMERALS or m.lemma in QUANTIFIERS


def _adjective(lex):
    if lex.pos == 'pronoun' and lex.lemma in DEMONSTRATIVES:
        return DEMONSTRATIVES[lex.lemma]
    if lex.lemma in ('ipse',):
        return 'sendiri'
    positive = english._positive(lex) if lex.lang in ('', 'la') else None
    degree = lex.degree or ('++' if positive is not None else '')
    if degree in ('+', '++'):   # 比較級 lebih besar、最上級 paling besar
        import dataclasses
        base = _adjective(positive or dataclasses.replace(lex, degree=''))
        return ('lebih ' if degree == '+' else 'paling ') + base
    if lex.pos == 'participle' and lex.verb:
        root = to_indonesian(Lex(lex.verb, 'verb', lex.verb_ja, lang=lex.lang), 'verb')
        if root:
            return 'yang ' + (passive(root) if lex.ptense in ('past', 'perfect') else active(root))
    found = to_indonesian(lex, 'adj')
    if found is None and lex.pos == 'participle':
        found = to_indonesian(lex, 'verb')
    return found or '[%s]' % english.word(lex)


def prepositional(np, passive_clause=False):
    if passive_clause and np.prep.lemma in ('ā', 'ab'):
        prep = 'oleh'   # 受動の動作主
    elif np.prep.lang == 'id' and np.prep.surface:
        prep = np.prep.surface
    else:
        prep = PREPOSITIONS.get((np.prep.lemma, np.case), 'di')
    import dataclasses
    return prep + ' ' + noun_phrase(dataclasses.replace(np, prep=None))


def relative_clause(r):
    """yang + 節。目的語の空所は受動 (3人称の動作主: yang dibaca oleh guru) か、1・2人称なら語根 (yang saya baca)"""
    import dataclasses
    if r.gap == 'object':
        subjects = r.role('subject')
        root = to_indonesian(r.verb, 'verb') if not r.copula else None
        if root:
            rest = [(role, np) for role, np in r.args if role != 'subject']
            body = realize(dataclasses.replace(r, args=rest), verb_override=passive(root), finite=True)
            if subjects:
                s = subjects[0]
                personal = s.head is not None and s.head.pos == 'pronoun' and s.head.lemma in ('ego', 'tū')
                if personal:   # yang telah kamu lihat (時の副詞は代名詞の前)
                    body = realize(dataclasses.replace(r, args=rest), verb_override=root, finite=True, aspect=False)
                    return ' '.join(w for w in ('yang', ASPECTS.get(r.tense, ''), noun_phrase(s), body) if w)
                return 'yang ' + body + ' oleh ' + noun_phrase(s)
            if r.person in (1, 2):
                pronoun = PRONOUNS[('ego' if r.person == 1 else 'tū', r.number)]
                body = realize(dataclasses.replace(r, args=rest), verb_override=root, finite=True, aspect=False)
                return ' '.join(w for w in ('yang', ASPECTS.get(r.tense, ''), pronoun, body) if w)
            return 'yang ' + body
    if r.gap == 'prep' and r.gap_prep:
        prep = PREPOSITIONS.get((r.gap_prep[0].lemma, r.gap_prep[1]), 'di')
        word_ = 'tempat' if prep in ('di', 'ke', 'dari') else 'yang'
        return ('%s %s' % (word_, realize(r, finite=True))) if word_ == 'tempat' else \
            'yang ' + prep + ' ' + 'nya ' + realize(r, finite=True)
    if r.gap == 'place':
        return 'tempat ' + realize(r, finite=True)
    if r.gap in ('possessor',):
        return 'yang ' + realize(r, finite=True)
    return 'yang ' + realize(r, finite=True)


# ----------------------------------------------------------------------
# 節

def _subject_np(clause):
    subjects = clause.role('subject')
    return subjects[0] if subjects else None


def realize(clause, verb_override=None, finite=False, aspect=True):
    """節 → インドネシア語の語の列。verb_override は動詞の形を決めて渡すとき (関係節の受動など)"""
    from .frame import lexical_negation, periphrastic
    clause = lexical_negation(periphrastic(clause))
    out = []
    for p in clause.adjuncts:
        if p.kind == 'absolute':
            out.append(_absolute(p) + ',')
    subjects = clause.role('subject')
    for np in subjects:
        out.append(noun_phrase(np))
    if not subjects and clause.mood not in ('infinitive', 'imperative') and not verb_override:
        if clause.person in (1, 2) or (clause.person == 3 and not clause.copula and not finite):
            key = {1: 'ego', 2: 'tū', 3: 'is'}[clause.person]
            out.append(PRONOUNS[(key, clause.number)])
    if aspect and clause.mood != 'infinitive' and clause.tense in ASPECTS and not clause.copula and \
            not (clause.subordinator in ('postquam', 'ubi', 'cum') and clause.tense != 'future'):
        out.append(ASPECTS[clause.tense])   # setelah raja datang (従属節の時は主節で分かる)
    if clause.copula:
        complements = clause.role('complement') + clause.role('object')   # 不定詞の繋辞の対格の補語 (puerum esse bonum)
        noun = any(np.head is not None and np.head.pos in ('noun', 'pronoun') for np in complements)
        if clause.negated:
            out.append('bukan' if noun else 'tidak')
        elif noun:
            out.append('adalah')
        for np in complements:
            if np.head is not None and np.head.pos in ('adj', 'participle') and not np.members:
                out.append(_adjective(np.head))
            else:
                out.append(noun_phrase(np))
        if not complements:
            out.append('ada')   # 存在 (est「ある」)
    else:
        if clause.negated:
            out.append('tidak')
        for adv in clause.adverbs:
            out.append(word(adv, 'adv'))
        out.append(verb_override or _verb(clause))
        for np in clause.role('object'):
            out.append(noun_phrase(np))
        for np in clause.role('recipient'):
            out.append('kepada ' + noun_phrase(np))
    for inner in clause.infinitives:
        out.append(_infinitive(inner))
    for inner in clause.questions:
        out.append(_question(inner))
    for role, np in clause.args:
        if role in ('subject', 'object', 'recipient', 'complement'):
            continue
        if role == 'prep':
            out.append(prepositional(np, clause.voice == 'passive'))
        else:
            prep = 'kepada' if role == 'means' and np.animate else ROLE_PREPOSITIONS.get(role)   # 与格と奪格の同形
            out.append(prep + ' ' + noun_phrase(np) if prep else noun_phrase(np))
    if clause.copula and clause.adverbs:
        out += [word(adv, 'adv') for adv in clause.adverbs]
    return ' '.join(w.strip() for w in out if w and w.strip())


def _verb(clause):
    root = to_indonesian(clause.verb, 'verb')
    if root is None:
        return '[%s]' % english.word(clause.verb)
    if clause.verb.lang == 'id':
        return root
    if clause.voice == 'passive':
        return passive(root)
    if clause.mood == 'imperative':
        return root   # 命令は語根 (Baca!)
    if clause.questions and not clause.role('object') and intransitive(root).startswith('ber'):
        return intransitive(root)   # bertanya siapa …
    if clause.role('object') or clause.questions or any(i.infinitive_kind in ('saying', 'perception')
                                                        for i in clause.infinitives):
        return active(root)
    return intransitive(root)


def _infinitive(inner):
    """不定詞句: 言う・知覚の動詞の後ろは bahwa + 節、ほかは動詞をそのまま (ingin bernyanyi)"""
    import dataclasses
    if inner.infinitive_kind in ('saying', 'perception') and inner.role('subject'):
        finite = dataclasses.replace(inner, mood='indicative', infinitive_kind='')
        return 'bahwa ' + realize(finite, finite=True)
    rest = dataclasses.replace(inner, args=[(r, np) for r, np in inner.args if r != 'subject'],
                               mood='infinitive')
    return realize(rest, finite=True)


def _question(inner):
    """間接疑問: siapa yang … (主語の疑問)、apa yang … (目的語)、疑問の副詞 + 節"""
    import dataclasses
    from .frame import interrogative_np, without_interrogative
    owner, role, wh = interrogative_np(inner)
    finite = dataclasses.replace(inner, mood='indicative', question_word='')
    if wh is None:
        word_ = QUESTION_WORDS.get(inner.question_word, inner.question_word)
        return word_ + ' ' + realize(finite, finite=True)
    pronoun = 'siapa' if inner.question_word in ('quis', 'quem', 'cui', 'cūius', 'cuius') and wh.gender != 'n' \
        else 'apa'
    rest = without_interrogative(finite)
    if role == 'subject':
        return pronoun + ' yang ' + realize(rest, finite=True)
    root = to_indonesian(inner.verb, 'verb')
    if role == 'object' and root:   # apa yang ditulis anak itu
        subjects = rest.role('subject')
        body = dataclasses.replace(rest, args=[(r, np) for r, np in rest.args if r != 'subject'])
        text = pronoun + ' yang ' + realize(body, verb_override=passive(root), finite=True)
        return text + (' ' + noun_phrase(subjects[0]) if subjects else '')
    return pronoun + ' ' + realize(rest, finite=True)


def _absolute(p):
    """独立奪格・属格独立: 過去の分詞は setelah + 受動の節 (setelah kota direbut)、現在は ketika + 節"""
    subject = noun_phrase(p.subject) if p.subject is not None else ''
    root = to_indonesian(Lex(p.verb.verb, 'verb', p.verb.verb_ja, lang=p.verb.lang), 'verb') if p.verb.verb else None
    if root is None:
        found = to_indonesian(p.verb, 'adj')
        return 'ketika ' + subject + ' ' + (found or '[%s]' % english.word(p.verb))
    if p.tense != 'present':
        verb = passive(root) if p.voice == 'passive' else intransitive(root)
        return 'setelah ' + subject + ' ' + verb
    return 'ketika ' + subject + ' ' + intransitive(root)


def wrap(text, clause):
    words = []
    for key in clause.connectives + ([clause.subordinator] if clause.subordinator else []):
        w = CONNECTIVES.get(key)
        if w:
            words.append(w)
    return ' '.join(words + [text]) if words else text


def sentence(clauses):
    if not clauses:
        return ''
    texts = []
    for c in clauses:
        text = wrap(realize(c), c)
        texts.append(text)
    out = ', '.join(texts)
    return out[:1].upper() + out[1:] + '.'
