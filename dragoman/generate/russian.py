#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) からロシア語の文を作る
#
#   語は transfer で置き換え (puella → девочка)、語形は pymorphy3 で作る (девочка → девочку)。
#   格: 主語 → 主格、目的語 → 対格 (活動体は生格と同じ形。pymorphy3 が選ぶ)、受け手 → 与格、手段 → 造格、
#       所有者 → 生格、前置詞句 → ロシア語の前置詞 + 格 (in + 奪格 → в + 前置格、ad + 対格 → к + 与格 …)
#   動詞: 現在 → 不完了体の現在、未完了過去 → 不完了体の過去、完了 → 完了体の過去 (видеть / увидеть)、
#         未来 → будет + 不完了体の不定形。過去形は主語の性・数に一致 (видела, видели)
#   受動: 現在 → 不完了体 + -ся、完了 → был + 完了体の短語尾受動分詞 (был похвален)。動作主は造格
#   繋辞 (sum): 現在は省く (Жизнь коротка → Жизнь короткая)、過去 был、未来 будет。所有の与格 → у + 生格 + есть
#   不定詞句: 言う → что + 節、見る → как + 節、命じる → 与格 + 不定形、補足 → 不定形
#   独立奪格 → когда + 節、述語的な分詞 → 副動詞 (срывая, сказав)
#
import functools

from . import transfer, english
from .frame import Lex, NP

try:
    import pymorphy3
except ImportError:   # pymorphy3 が無ければロシア語は作れない
    pymorphy3 = None

CASES = {'Nom': 'nomn', 'Acc': 'accs', 'Gen': 'gent', 'Dat': 'datv', 'Ins': 'ablt', 'Loc': 'loct'}
ROLE_CASES = {'subject': 'Nom', 'object': 'Acc', 'recipient': 'Dat', 'means': 'Ins', 'possessor': 'Gen',
              'place': 'Loc', 'address': 'Nom', 'complement': 'Nom', 'source': 'Gen'}
# ラテン語の前置詞 + 格 → (ロシア語の前置詞, 格)
PREPOSITIONS = {('in', 'Abl'): ('в', 'Loc'), ('in', 'Acc'): ('в', 'Acc'), ('ad', 'Acc'): ('к', 'Dat'),
                ('cum', 'Abl'): ('с', 'Ins'), ('ā', 'Abl'): ('от', 'Gen'), ('ab', 'Abl'): ('от', 'Gen'),
                ('ē', 'Abl'): ('из', 'Gen'), ('ex', 'Abl'): ('из', 'Gen'), ('dē', 'Abl'): ('о', 'Loc'),
                ('sine', 'Abl'): ('без', 'Gen'), ('prō', 'Abl'): ('за', 'Acc'), ('sub', 'Abl'): ('под', 'Ins'),
                ('sub', 'Acc'): ('под', 'Acc'), ('per', 'Acc'): ('через', 'Acc'), ('post', 'Acc'): ('после', 'Gen'),
                ('ante', 'Acc'): ('перед', 'Ins'), ('apud', 'Acc'): ('у', 'Gen'), ('inter', 'Acc'): ('между', 'Ins'),
                ('trāns', 'Acc'): ('через', 'Acc'), ('circum', 'Acc'): ('вокруг', 'Gen'),
                ('prope', 'Acc'): ('около', 'Gen'), ('propter', 'Acc'): ('из-за', 'Gen'),
                ('contrā', 'Acc'): ('против', 'Gen'), ('super', 'Acc'): ('над', 'Ins'), ('ob', 'Acc'): ('из-за', 'Gen')}
# ラテン語の代名詞 → ロシア語の代名詞 (見出し)
PRONOUNS = {'ego': 'я', 'tū': 'ты', 'nōs': 'мы', 'vōs': 'вы', 'is': 'он', 'sē': 'себя', 'hīc': 'этот', 'hic': 'этот',
            'ille': 'тот', 'ipse': 'сам', 'īdem': 'тот же', 'quī': 'который', 'quis': 'кто',
            'meus': 'мой', 'tuus': 'твой', 'noster': 'наш', 'vester': 'ваш', 'suus': 'свой',
            'quid': 'что', 'aliquis': 'кто-то', 'aliquī': 'какой-то', 'nēmō': 'никто', 'nihil': 'ничто', 'quīdam': 'некий', 'quisquam': 'кто-либо',
            'quisque': 'каждый', 'alius': 'другой', 'alter': 'другой', 'omnis': 'весь', 'tōtus': 'весь',
            'nūllus': 'никакой', 'cēterus': 'остальной', 'tantus': 'такой', 'tālis': 'такой', 'sōlus': 'один',
            'ūnus': 'один', 'duo': 'два', 'trēs': 'три', 'quattuor': 'четыре', 'quīnque': 'пять', 'sex': 'шесть',
            'septem': 'семь', 'octō': 'восемь', 'novem': 'девять', 'decem': 'десять', 'duodecim': 'двенадцать',
            'centum': 'сто', 'mīlle': 'тысяча'}
NUMERALS = {'два': 2, 'три': 3, 'четыре': 4, 'пять': 5, 'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9,
            'десять': 10, 'двенадцать': 12, 'сто': 100}
NEGATIVE_PRONOUNS = {'никто', 'ничто', 'никакой'}   # これがあれば動詞にも не (никто не вернулся)
# 固有名詞: ロシア語で決まった形のあるもの
NAMES = {'Roma': 'Рим', 'Caesar': 'Цезарь', 'Cicero': 'Цицерон', 'Pompeius': 'Помпей', 'Iulia': 'Юлия',
         'Iuno': 'Юнона', 'Iason': 'Ясон', 'Medea': 'Медея', 'Hercules': 'Геракл', 'Perseus': 'Персей',
         'Ulixes': 'Улисс', 'Circe': 'Цирцея', 'Pelias': 'Пелий', 'Aeetes': 'Ээт', 'Andromeda': 'Андромеда',
         'Medusa': 'Медуза', 'Minerva': 'Минерва', 'Apollo': 'Аполлон', 'Neptunus': 'Нептун', 'Iuppiter': 'Юпитер', 'Romulus': 'Ромул', 'Graecia': 'Греция', 'Italia': 'Италия'}  # マクロン無しで
# 対格でなく生格を取る動詞 (бояться моря)、与格を取る動詞
GOVERNMENT = {'бояться': 'Gen', 'испугаться': 'Gen', 'ждать': 'Gen', 'помогать': 'Dat', 'помочь': 'Dat'}
# 複数で別の語になる名詞 (цветок → цветы)
PLURALS = {'цветок': 'цветы'}
PERSONAL = {(1, 'sg'): 'я', (2, 'sg'): 'ты', (3, 'sg'): 'он', (1, 'pl'): 'мы', (2, 'pl'): 'вы', (3, 'pl'): 'они'}
CONJUNCTIONS = {'et': 'и', 'atque': 'и', 'ac': 'и', 'que': 'и', '-que': 'и', 'aut': 'или', 'vel': 'или',
                'neque': 'ни', 'nec': 'ни', 'sed': 'но'}
# 不完了体 → 完了体 (完了の時制に)
PERFECTIVES = {'давать': 'дать', 'видеть': 'увидеть', 'хвалить': 'похвалить', 'петь': 'спеть', 'нести': 'понести',
               'говорить': 'сказать', 'любить': 'полюбить', 'гулять': 'погулять', 'читать': 'прочитать',
               'писать': 'написать', 'делать': 'сделать', 'брать': 'взять', 'приходить': 'прийти',
               'плакать': 'заплакать', 'смеяться': 'засмеяться', 'строить': 'построить', 'ранить': 'ранить',
               'уходить': 'уйти', 'бояться': 'испугаться', 'узнавать': 'узнать', 'двигать': 'двинуть',
               'умирать': 'умереть', 'трогать': 'тронуть', 'убивать': 'убить', 'встречать': 'встретить',
               'находить': 'найти', 'спрашивать': 'спросить', 'хотеть': 'захотеть', 'получать': 'получить', 'бросать': 'бросить', 'отправляться': 'отправиться'}
GENDERS = {'m': 'masc', 'f': 'femn', 'n': 'neut'}
# в / на + 第二前置格 (-у) を取るよく使う名詞 (pymorphy3 の loc2 は дом → дому のような形も返すので、名詞を限る)
LOCATIVE2 = {'сад', 'лес', 'берег', 'мост', 'угол', 'пол', 'шкаф', 'глаз', 'нос', 'рот', 'снег', 'порт', 'год',
             'край', 'луг', 'бой', 'плен', 'ряд', 'час', 'круг', 'пруд', 'дуб', 'мёд', 'лёд', 'бал', 'век', 'дым'}


@functools.lru_cache(maxsize=1)
def _morph():
    return pymorphy3.MorphAnalyzer()


def available():
    return pymorphy3 is not None and transfer.available('ru')


@functools.lru_cache(maxsize=5000)
def _parse(lemma, pos):
    """見出し語の解析 (pymorphy3)。pos: NOUN / ADJF / INFN / NPRO。人名 (Роза) でない解析を先に"""
    key = lemma.lower().replace('ё', 'е')   # pymorphy3 の見出しは ё で書く (мудрёный)
    parses = [p for p in _morph().parse(lemma) if p.normal_form.replace('ё', 'е') == key and p.tag.POS == pos]
    parses.sort(key=lambda p: any(g in p.tag for g in ('Name', 'Surn', 'Patr', 'Geox')))
    return parses[0] if parses else None


def _inflect(lemma, pos, grammemes):
    parse = _parse(lemma, pos)
    if parse is None:
        return lemma
    form = parse.inflect(set(g for g in grammemes if g))
    return form.word if form is not None else lemma


# ----------------------------------------------------------------------
# 語の置き換え

def noun_lemma(lex):
    if lex.pos == 'pronoun':
        pronoun = PRONOUNS.get(lex.lemma) or PRONOUNS.get(english._flat(lex.lemma))
        if pronoun:
            return pronoun, 'm'
        target = transfer.best(lex, 'ru', 'adj') or transfer.best(lex, 'ru', 'pronoun')   # ūnus, tōtus …
        return (target.lemma, '') if target else ('[%s]' % english.word(lex), '')
    if lex.proper:
        lemma = NAMES.get(english._flat(lex.lemma)) or name(lex.lemma)
        return lemma, ''
    lex = english.substantive(lex) or lex   # 名詞として辞書にある形 (tālāria)
    target = transfer.best(lex, 'ru')
    return (target.lemma, target.gender) if target else ('[%s]' % english.word(lex), '')


def name(latin):
    """ラテン語の固有名詞 → ロシア語の綴り (語尾 -us を除いてキリル文字に: Mārcus → Марк)"""
    word = english._flat(latin)
    for ending in ('us', 'um'):
        if word.endswith(ending) and len(word) > 4:
            word = word[:-len(ending)]
    table = [('ch', 'х'), ('ph', 'ф'), ('th', 'т'), ('qu', 'кв'), ('ae', 'е'), ('oe', 'е'), ('iu', 'ю'), ('ia', 'ия'),
             ('a', 'а'), ('b', 'б'), ('c', 'ц'), ('d', 'д'), ('e', 'е'), ('f', 'ф'), ('g', 'г'), ('h', 'г'),
             ('i', 'и'), ('j', 'й'), ('k', 'к'), ('l', 'л'), ('m', 'м'), ('n', 'н'), ('o', 'о'), ('p', 'п'),
             ('r', 'р'), ('s', 'с'), ('t', 'т'), ('u', 'у'), ('v', 'в'), ('x', 'кс'), ('y', 'и'), ('z', 'з')]
    out, i, lower = '', 0, word.lower()
    while i < len(lower):
        for latin_letters, cyrillic in table:
            if lower.startswith(latin_letters, i):
                if latin_letters == 'c' and lower[i + 1:i + 2] not in ('e', 'i', 'y') and \
                        lower[i + 1:i + 3] not in ('ae', 'oe'):
                    cyrillic = 'к'   # c は e, i の前だけ ц (Cicerō → Цицерон は例外として扱わない)
                out += cyrillic
                i += len(latin_letters)
                break
        else:
            out += lower[i]
            i += 1
    return out[:1].upper() + out[1:]


def verb_lemma(lex, aspect='impf', transitive=False):
    if lex.lemma == 'sum':
        return 'быть'
    found = transfer.candidates(lex, 'ru')
    if transitive:   # 受動分詞を作るので、-ся の動詞 (тронуться) を除く
        found = [(s, t) for s, t in found if not t.lemma.endswith(('ся', 'сь'))] or found
    if not found:
        return None
    lemma = found[0][1].lemma
    if aspect == 'perf':
        if lemma in PERFECTIVES:
            return PERFECTIVES[lemma]
        for _, target in found[:8]:
            parse = _parse(target.lemma, 'INFN')
            if parse is not None and 'perf' in parse.tag:
                return target.lemma
    elif _parse(lemma, 'INFN') is not None and 'perf' in _parse(lemma, 'INFN').tag:
        for imperfective, perfective in PERFECTIVES.items():
            if perfective == lemma:
                return imperfective
        for _, target in found[:8]:
            parse = _parse(target.lemma, 'INFN')
            if parse is not None and 'impf' in parse.tag:
                return target.lemma
    return lemma


# ----------------------------------------------------------------------
# 名詞句

def _gender_of(lemma, gender):
    parse = _parse(lemma, 'NOUN')
    if parse is not None:
        for g in ('masc', 'femn', 'neut'):
            if g in parse.tag:
                return g
    return GENDERS.get(gender, 'masc')


def _animate(lemma):
    parse = _parse(lemma, 'NOUN')
    return parse is not None and 'anim' in parse.tag


def adjective(lex, case, number, gender, animate):
    positive = english._positive(lex)
    degree = lex.degree or ('++' if positive is not None else '')
    lex = positive or lex   # 最上級の見出し (difficillimus) は原級 (difficilis) で引いて самый を付ける
    lemma = PRONOUNS.get(lex.lemma)   # 代名詞的な形容詞 (suus → свой, hic → этот)
    if lex.lemma == 'is':
        lemma = 'тот'   # 名詞に係る is (eum locum「その場所」)
    if lemma is None:
        target = transfer.best(lex, 'ru', 'adj')
        lemma = target.lemma if target else None
    if lemma is None:
        return '[%s]' % english.word(lex)
    grammemes = {CASES[case], 'plur' if number == 'pl' else 'sing'}
    if number != 'pl':
        grammemes.add(gender)
    if case == 'Acc' and animate and (number == 'pl' or gender == 'masc'):
        grammemes = (grammemes - {'accs'}) | {'gent'}   # 活動体の対格は生格と同じ (красивого мальчика)
    elif case == 'Acc' and (number == 'pl' or gender == 'masc'):
        grammemes.add('inan')   # 不活動体の対格は主格と同じ (красивые розы)
    form = next((_inflect(lemma, pos, grammemes if pos != 'NUMR' else {CASES[case]})
                 for pos in ('ADJF', 'NPRO', 'NUMR') if _parse(lemma, pos) is not None), lemma)
    if degree == '+':
        return 'более ' + form   # 比較級: более трудный
    if degree == '++':
        return _inflect('самый', 'ADJF', grammemes) + ' ' + form   # 最上級: самый трудный
    return form


def noun_phrase(np, case):
    """名詞句 (case は格の名前 Nom / Acc / Gen / Dat / Ins / Loc)"""
    if np.members:
        conj = CONJUNCTIONS.get(np.conj, 'и')
        parts = [noun_phrase(m, case) for m in np.members]
        if conj == 'ни' or np.correlative:
            return ' '.join(conj + ' ' + p for p in parts)
        return (' %s ' % conj).join(parts)
    head = np.head
    lemma, gender = noun_lemma(head)
    number = 'plur' if np.number == 'pl' else 'sing'
    if head.pos == 'pronoun':
        if lemma in ('он',) and np.gender == 'f':
            lemma = 'она'
        if lemma == 'он' and np.number == 'pl':
            lemma = 'они'
        word = next((_inflect(lemma, pos, {CASES[case]}) for pos in ('NPRO', 'ADJF', 'NUMR') if _parse(lemma, pos)),
                    lemma)
        if head.desc == '指示代名詞' and head.lemma == 'ille' and not np.modifiers:
            personal = 'она' if np.gender == 'f' else 'они' if np.number == 'pl' else 'он'   # 単独の ille → он
            word = _inflect(personal, 'NPRO', {CASES[case]})
        elif head.desc == '指示代名詞':
            word = adjective(head, case, np.number, GENDERS.get(np.gender, 'masc'), False) \
                if np.modifiers else _inflect('это', 'NPRO', {CASES[case]})
    elif head.pos in ('adj', 'participle') and not english.substantive(head):
        word = adjective(head, case, np.number, GENDERS.get(np.gender, 'masc'), False)
    elif head.proper:
        word = _inflect(lemma, 'NOUN', {CASES[case], number}) if _parse(lemma, 'NOUN') else lemma
        word = word[:1].upper() + word[1:]   # pymorphy3 は小文字で返す (Ясона)
    elif number == 'plur' and lemma in PLURALS:
        word = _inflect(PLURALS[lemma], 'NOUN', {CASES[case], number})
    else:
        word = _inflect(lemma, 'NOUN', {CASES[case], number})
    g = _gender_of(lemma, gender or np.gender)
    animate = _animate(lemma)
    before = []
    for mod in np.modifiers:
        if isinstance(mod, NP):   # 並列した形容詞
            conj = CONJUNCTIONS.get(mod.conj, 'и')
            before.append((' %s ' % conj).join(adjective(m.head, case, np.number, g, animate) for m in mod.members))
        else:
            before.append(adjective(mod, case, np.number, g, animate))
    numeral = next((PRONOUNS[m.lemma] for m in np.modifiers if not isinstance(m, NP) and
                    PRONOUNS.get(m.lemma) in NUMERALS), None)
    if numeral and (case == 'Nom' or case == 'Acc' and not animate):
        # 数詞の格支配: 2〜4 は名詞が生格単数 (три стула)、5 以上は生格複数 (пять стульев)。形容詞は生格複数
        noun_case = {'sing'} if NUMERALS[numeral] < 5 else {'plur'}
        word = _inflect(lemma, 'NOUN', {'gent'} | noun_case)
        before = [_inflect(PRONOUNS[m.lemma], 'NUMR', {'nomn'}) if PRONOUNS.get(m.lemma) == numeral
                  else adjective(m, 'Gen', 'pl', g, animate) for m in np.modifiers if not isinstance(m, NP)]
        before.sort(key=lambda w: w != _inflect(numeral, 'NUMR', {'nomn'}))   # 数詞を先頭に
    after = [noun_phrase(gen, 'Gen') for gen in np.genitives]
    for p in np.participles:
        if p.args:
            after.append(participle_form(p, case, np.number, g, animate))
        else:
            before.append(participle_form(p, case, np.number, g, animate))   # бегущего врага
    return ' '.join(before + [word] + after)


def prepositional(np, passive=False):
    prep, case = PREPOSITIONS.get((np.prep.lemma, np.case), (None, None))
    if passive and np.prep.lemma in ('ā', 'ab', 'abs'):
        return noun_phrase(np, 'Ins')   # 受動の動作主は造格 (учителем)
    if prep is None:
        return '[%s] %s' % (np.prep.lemma, noun_phrase(np, 'Loc'))
    inner = noun_phrase(_without_prep(np), case)
    if prep in ('в', 'на') and case == 'Loc' and np.number != 'pl' and not np.members:
        lemma = noun_lemma(np.head)[0]
        if lemma in LOCATIVE2:
            word = _inflect(lemma, 'NOUN', {'loc2', 'sing'})
            inner = inner.replace(_inflect(lemma, 'NOUN', {'loct', 'sing'}), word, 1)   # в саду, в лесу
    if prep == 'в' and inner[:1].lower() in 'вф' and inner[1:2].lower() not in 'аеёиоуыэюя':
        prep = 'во'
    if prep == 'с' and inner[:1].lower() in 'сз' and inner[1:2].lower() not in 'аеёиоуыэюя':
        prep = 'со'
    return prep + ' ' + inner


def _without_prep(np):
    import dataclasses
    return dataclasses.replace(np, prep=None)


# ----------------------------------------------------------------------
# 動詞

def _person(person):
    return {1: '1per', 2: '2per', 3: '3per'}.get(person, '3per')


def verb_form(clause, gender, person, number):
    """述語動詞の形 (語の列)"""
    tense, voice, mood = clause.tense, clause.voice, clause.mood
    num = 'plur' if number == 'pl' else 'sing'
    past = {'past', num} | ({gender} if number != 'pl' else set())
    perfective = tense in ('perfect', 'past-perfect', 'future-perfect')
    if clause.copula:
        if tense in ('imperfect', 'perfect', 'past-perfect'):
            return [_inflect('быть', 'INFN', past)]
        if tense in ('future', 'future-perfect'):
            return [_inflect('быть', 'INFN', {'futr', _person(person), num})]
        return []
    lemma = verb_lemma(clause.verb, 'perf' if perfective or voice == 'passive' and tense != 'present' else 'impf',
                       transitive=voice == 'passive' and tense != 'present')
    if lemma is None:
        return ['[%s]' % english.word(clause.verb)]
    if mood == 'infinitive':
        return [lemma]
    if mood == 'imperative':
        return [_inflect(lemma, 'INFN', {'impr', num})]
    if voice == 'passive':
        if tense == 'present':
            form = _inflect(lemma, 'INFN', {'pres', _person(person), num})
            return [form + ('сь' if form[-1:] in 'аеёиоуыэюя' else 'ся')]   # хвалится
        if tense == 'imperfect' or _short_participle(lemma, gender, number) == lemma:
            # 未完了過去の受動、短語尾受動分詞の無い動詞: 不完了体の過去 + -ся (назывался)
            impf = verb_lemma(clause.verb, 'impf')
            form = _inflect(impf, 'INFN', past)
            if form.endswith(('ся', 'сь')):
                return [form]
            return [form + ('сь' if form[-1:] in 'аеёиоуыэюя' else 'ся')]
        short = _short_participle(lemma, gender, number)
        be = _inflect('быть', 'INFN', past if tense != 'future' else {'futr', _person(person), num})
        return [be, short]
    if tense in ('imperfect', 'perfect', 'past-perfect'):
        return [_inflect(lemma, 'INFN', past)]
    if tense == 'future':
        return [_inflect('быть', 'INFN', {'futr', _person(person), num}), lemma]
    if tense == 'future-perfect':
        return [_inflect(lemma, 'INFN', {'futr', _person(person), num})]
    if mood == 'subjunctive':
        return [_inflect(lemma, 'INFN', past), 'бы']
    return [_inflect(lemma, 'INFN', {'pres', _person(person), num})]


def _short_participle(lemma, gender, number):
    parse = _parse(lemma, 'INFN')
    if parse is None:
        return lemma
    for form in parse.lexeme:
        if 'PRTS' in form.tag and 'pssv' in form.tag and \
                (('plur' in form.tag) if number == 'pl' else (gender in form.tag and 'sing' in form.tag)):
            return form.word
    return lemma


def participle_form(p, case, number, gender, animate):
    """名詞に係る分詞 (hostem fugientem → бегущего врага の бегущего)。形動詞 (PRTF)"""
    lemma = verb_lemma(Lex(p.verb.verb, 'verb', p.verb.verb_ja), 'impf' if p.tense == 'present' else 'perf',
                       transitive=p.voice == 'passive') if p.verb.verb else None
    parse = _parse(lemma, 'INFN') if lemma else None
    if parse is None:
        return '[%s]' % english.word(p.verb)
    tense = 'pres' if p.tense == 'present' else 'past'
    voice = 'pssv' if p.voice == 'passive' else 'actv'
    grammemes = {'PRTF', tense, voice, CASES[case], 'plur' if number == 'pl' else 'sing'}
    if number != 'pl':
        grammemes.add(gender)
    for form in parse.lexeme:
        if grammemes <= set(str(form.tag).replace(' ', ',').split(',')):
            return form.word
    return lemma


def gerund(p):
    """副動詞: 現在 → 不完了体 (срывая)、完了 → 完了体 (сказав)"""
    lemma = verb_lemma(Lex(p.verb.verb, 'verb', p.verb.verb_ja), 'impf' if p.tense == 'present' else 'perf') \
        if p.verb.verb else None
    parse = _parse(lemma, 'INFN') if lemma else None
    if parse is None:
        return '[%s]' % english.word(p.verb)
    want = 'pres' if p.tense == 'present' else 'past'
    forms = [f.word for f in parse.lexeme if 'GRND' in f.tag and want in f.tag and 'V-sh' not in f.tag]
    return forms[0] if forms else lemma


def participial(p, subject=None):
    """独立奪格 → когда + 節、述語的な分詞 → 副動詞 + 補語"""
    args = []
    for role, np in p.args:
        if role == 'adverb':
            args.append(adverb(np.head))
        elif role == 'prep':
            args.append(prepositional(np, p.voice == 'passive'))
        elif role == 'means' and p.voice == 'passive':
            args.append(noun_phrase(np, 'Ins'))
        else:
            args.append(noun_phrase(np, ROLE_CASES.get(role, 'Acc')))
    if p.kind == 'absolute' and p.subject is not None:
        g = _gender_of(noun_lemma(p.subject.head)[0], p.subject.gender) if not p.subject.members else 'masc'
        number = p.subject.number
        lemma = verb_lemma(Lex(p.verb.verb, 'verb', p.verb.verb_ja), 'perf' if p.tense != 'present' else 'impf',
                           transitive=p.voice == 'passive') if p.verb.verb else None
        num = 'plur' if number == 'pl' else 'sing'
        if lemma is None:
            verb = ['[%s]' % english.word(p.verb)]
        elif p.voice == 'passive':
            verb = [_inflect('быть', 'INFN', {'past', num} | ({g} if number != 'pl' else set())),
                    _short_participle(lemma, g, number)]
        else:
            verb = [_inflect(lemma, 'INFN', {'past', num} | ({g} if number != 'pl' else set()))]
        return 'когда ' + ' '.join([noun_phrase(p.subject, 'Nom')] + args + verb) + ','
    if p.voice == 'passive':
        return ', '.join([participle_form(p, 'Nom', subject.number if subject else 'sg',
                                          _gender_of(noun_lemma(subject.head)[0], subject.gender)
                                          if subject is not None and not subject.members else 'masc', False)
                          + ' ' + ' '.join(args)])
    return gerund(p) + (' ' + ' '.join(args) if args else '')


# ----------------------------------------------------------------------
# 節

def _subject_agreement(subject, clause):
    if subject is None:
        return 'masc', clause.person, clause.number
    if subject.members:
        return 'masc', 3, 'pl'
    lemma, gender = noun_lemma(subject.head)
    if subject.head.pos == 'pronoun':
        return GENDERS.get(subject.gender, 'masc'), clause.person, clause.number
    return _gender_of(lemma, gender or subject.gender), 3, subject.number


def infinitive_phrase(inner, main_subject):
    kind = inner.infinitive_kind
    subjects = inner.role('subject')
    if kind in ('saying', 'perception') and subjects:
        import dataclasses
        finite = dataclasses.replace(inner, mood='indicative', infinitive_kind='', tense='present'
                                     if inner.tense == 'present' else inner.tense)
        if subjects[0].head is not None and subjects[0].head.lemma == 'sē' and main_subject is not None:
            # 再帰代名詞は主節の主語を指す: 主語の性・数の人称代名詞に (Девочка говорит, что она …)
            ref = main_subject if not main_subject.members else subjects[0]
            gender = 'f' if _subject_agreement(ref, inner)[0] == 'femn' else 'm'
            pronoun = NP(Lex('is', 'pronoun', desc='人称代名詞'), number=ref.number, gender=gender)
            finite.args = [('subject', pronoun)] + [(r, np) for r, np in finite.args if np is not subjects[0]]
        return (', что ' if kind == 'saying' else ', как ') + realize(finite, capitalize=False)
    import dataclasses
    rest = realize(dataclasses.replace(inner, args=[(r, np) for r, np in inner.args if r != 'subject']),
                   capitalize=False)
    if kind == 'command' and subjects:
        return noun_phrase(subjects[0], 'Dat') + ' ' + rest   # велит рабу нести
    return rest


IDIOMS = {'where': 'где', 'why': 'почему', 'how': 'как', 'when': 'когда'}


def question_phrase(inner):
    """間接疑問: 読点 + 疑問詞 + 直説法の節 (спросил, почему мальчик плакал、объяснил, что он хотел …)。
    ли (num, utrum) は節の最初の語の後ろ"""
    import dataclasses
    from .frame import interrogative_np, without_interrogative
    from . import connectives
    from .frame import question_idiom
    finite = dataclasses.replace(inner, mood='indicative', question_word='')
    idiom, stripped = question_idiom(inner)
    stripped = dataclasses.replace(stripped, mood='indicative', question_word='')
    if idiom:
        return ', ' + IDIOMS[idiom] + ' ' + realize(stripped, capitalize=False)
    owner, role, wh = interrogative_np(inner)
    if wh is None:
        entry = connectives.interrogative(inner.question_word)
        word = entry[1] if entry else inner.question_word
        text = realize(finite, capitalize=False)
        if word == 'ли':
            head, _, rest = text.partition(' ')
            return ', ' + head + ' ли' + (' ' + rest if rest else '')
        return ', ' + word + ' ' + text
    pronoun = 'кто' if inner.question_word in ('quis', 'quem', 'cui', 'cūius', 'cuius') else 'что'
    case = 'Nom' if role == 'subject' else ROLE_CASES.get(role, 'Acc')
    if owner is inner and role == 'subject':
        return ', ' + realize(without_interrogative(finite, dataclasses.replace(wh, head=Lex(
            'quis' if pronoun == 'кто' else 'quid', 'pronoun'), interrogative=False)), capitalize=False)
    return ', ' + _inflect(pronoun, 'NPRO', {CASES[case]}) + ' ' + realize(without_interrogative(finite), capitalize=False)


def realize(clause, capitalize=True):
    from .frame import periphrastic, lexical_negation
    clause = lexical_negation(periphrastic(clause))   # prōgressus est → 完了の能動 (advanced / продвинулся)
    subjects = clause.role('subject')
    subject = subjects[0] if subjects else None
    gender, person, number = _subject_agreement(subject, clause)
    out = []
    possessors = [np for np in clause.role('recipient') if clause.copula and not clause.role('complement')]
    if possessors and subject is not None:
        # 所有の与格 (Liber mihi est) → у меня есть книга
        text = 'у ' + noun_phrase(possessors[0], 'Gen') + ' есть ' + noun_phrase(subject, 'Nom')
        if possessors[0].head is not None and possessors[0].head.pos == 'pronoun' and \
                PRONOUNS.get(possessors[0].head.lemma) in ('он', 'она', 'они'):
            text = text.replace('у е', 'у не', 1)
        return text[:1].upper() + text[1:] if capitalize else text
    for p in clause.adjuncts:
        if p.kind == 'absolute':
            out.append(participial(p))
    if clause.mood not in ('imperative', 'infinitive'):
        if subject is not None:
            out.append(noun_phrase(subject, 'Nom'))
            for other in subjects[1:]:
                out[-1] += ', ' + noun_phrase(other, 'Nom') + ','
        elif clause.copula or clause.tense in ('imperfect', 'perfect', 'past-perfect'):
            out.append(PERSONAL.get((person, number), 'он'))   # 過去形は人称を示さないので代名詞を補う
    for p in clause.adjuncts:
        if p.kind != 'absolute':
            out.append(', ' + participial(p, subject) + ',')
    negative_pronoun = any(np.head is not None and not np.members and
                           (PRONOUNS.get(np.head.lemma) in NEGATIVE_PRONOUNS) for _, np in clause.args)
    if clause.negated or negative_pronoun:
        out.append('не')   # 否定の代名詞は動詞の否定と一緒に (никто не вернулся。ラテン語は nēmō だけ)
    out += verb_form(clause, gender, person, number)
    for np in clause.role('complement'):
        out.append(noun_phrase(_agreeing(np, subject), 'Nom'))
    verb = verb_lemma(clause.verb) if not clause.copula else None
    for role in ('recipient', 'object'):
        for np in clause.role(role):
            case = GOVERNMENT.get(verb, ROLE_CASES[role]) if role == 'object' else ROLE_CASES[role]
            out.append(noun_phrase(np, case))
    for inner in clause.infinitives:
        out.append(infinitive_phrase(inner, subject))
    for inner in clause.questions:
        out.append(question_phrase(inner))
    for role, np in clause.args:
        if role in ('subject', 'object', 'recipient', 'complement'):
            continue
        if role == 'prep':
            out.append(prepositional(np, clause.voice == 'passive'))
        else:
            out.append(noun_phrase(np, ROLE_CASES.get(role, 'Ins')))
    out += [adverb(adv) for adv in clause.adverbs]
    text = ' '.join(w.strip() for w in out if w.strip()).replace(' ,', ',').replace(',,', ',')
    if capitalize:
        text = text[:1].upper() + text[1:]
    return text


def adverb(lex):
    """副詞: 文をつなぐ語の表 (tum → тогда) → 置き換えの表 (magnopere → очень)"""
    from . import connectives
    entry = connectives.lookup(lex.surface or lex.lemma) or connectives.lookup(lex.lemma)
    if entry:
        return entry[2]
    target = transfer.best(lex, 'ru', 'adv')
    return target.lemma if target else '[%s]' % english.word(lex)


def _agreeing(np, subject):
    """補語の形容詞を主語の性・数に (Жизнь короткая)"""
    if subject is None or np.members or np.head.pos not in ('adj', 'participle'):
        return np
    import dataclasses
    lemma, gender = noun_lemma(subject.head) if not subject.members else ('', '')
    g = _gender_of(lemma, gender or subject.gender) if lemma else 'masc'
    return dataclasses.replace(np, number=subject.number if not subject.members else 'pl',
                               gender={'masc': 'm', 'femn': 'f', 'neut': 'n'}[g])


def sentence(clauses):
    if not clauses:
        return ''
    from . import connectives
    text = connectives.join(clauses, [realize(c, capitalize=False).rstrip(',') for c in clauses], 'ru')
    return text[:1].upper() + text[1:] + '.'
