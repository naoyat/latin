#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の枠 (frame.Clause) から古文 (平安の和文ふうの文語) を作る
#
#   組み立ては現代語の出口 (generate/japanese.py) と同じ (語順・関係節は連体修飾・間接疑問・不定詞句)。述語と助詞を古文に:
#   動詞: 現代語の訳語を MeCab (UniDic) の活用の型から古語の活用に直す
#         五段 → 四段 (ワア行は歴史的仮名遣いのハ行: 歌う → 歌ふ)、ある → あり (ラ変)、死ぬ → 死ぬ (ナ変)
#         上一段 → 上二段 (起きる → 起く。見る・着る・似る … は上一段のまま)
#         下一段 → 下二段 (褒める → 褒む。ア行は原則ハ行: 与える → 与ふ、見える・燃える … はヤ行、植える … はワ行)
#         来る → 来 (カ変)、する・〜する → す (サ変)、感じる → 感ず (サ変)、出る → 出づ、寝る → 寝
#   形容詞: 美しい → 美し (シク活用)、良い → 良し (ク活用)。助動詞の前はカリ活用 (美しかりけり)
#   助動詞: 過去 けり (連用形)、未完了過去 たり + けり、未来 む・打消 ず・受身 る / らる (未然形)、断定 なり (否定は にあらず)
#   助詞: 主節の主語 は、従属節・関係節の主語 の、場所 にて、起点 より
#   節: ubi・cum・quod → 已然形 + ば、sī → 未然形 + ば、quamquam → 已然形 + ども、et → 連用形 + て、関係節は連体形、
#       間接疑問は係り結び (誰か歌ひける と問ひけり)
#
import re

from dragoman.core.japanese import mecab_parse
from . import japanese
from .japanese import gloss
from .kobun_lexicon import NOUNS, VERBS, ADJECTIVES, ADVERBS

# 行 → 五十音 (あ・い・う・え・お の段)
ROWS = {'カ': 'かきくけこ', 'ガ': 'がぎぐげご', 'サ': 'さしすせそ', 'ザ': 'ざじずぜぞ', 'タ': 'たちつてと',
        'ダ': 'だぢづでど', 'ナ': 'なにぬねの', 'ハ': 'はひふへほ', 'バ': 'ばびぶべぼ', 'パ': 'ぱぴぷぺぽ',
        'マ': 'まみむめも', 'ヤ': 'や い ゆ え よ'.replace(' ', ''), 'ラ': 'らりるれろ', 'ワ': 'わゐうゑを', 'ア': 'あいうえお'}
FORMS = ('未然', '連用', '終止', '連体', '已然', '命令')
# 活用の種類 → 段 (a i u e o の位置) か語尾
ENDINGS = {'四段': ('a', 'i', 'u', 'u', 'e', 'e'),
           '上二段': ('i', 'i', 'u', 'u+る', 'u+れ', 'i+よ'),
           '下二段': ('e', 'e', 'u', 'u+る', 'u+れ', 'e+よ')}
VOWEL_INDEX = {'a': 0, 'i': 1, 'u': 2, 'e': 3, 'o': 4}
IRREGULAR = {'カ変': ('こ', 'き', 'く', 'くる', 'くれ', 'こよ'), 'サ変': ('せ', 'し', 'す', 'する', 'すれ', 'せよ'),
             'ザ変': ('ぜ', 'じ', 'ず', 'ずる', 'ずれ', 'ぜよ'), '来': ('来', '来', '来', '来る', '来れ', '来よ'),
             'ナ変': ('な', 'に', 'ぬ', 'ぬる', 'ぬれ', 'ね'), 'ラ変': ('ら', 'り', 'り', 'る', 'れ', 'れ'),
             '上一段': ('', '', 'る', 'る', 'れ', 'よ')}
KUN_ZURU = {'恥じる', '閉じる', '綴じる', '怖じる', '捩じる'}   # 和語の 〜じる (上二段ダ行)。ほか (命じる・信じる) はサ変
KAMI_ICHIDAN = {'見る', '着る', '似る', '煮る', '干る', '射る', '居る', '率る', '鋳る', '顧みる', '試みる', '用いる'}
YA_SHIMO = {'見える', '聞こえる', '燃える', '消える', '冷える', '越える', '覚える', '生える', '絶える', '栄える', '癒える',
            '肥える', '萌える', '映える', '吠える', '増える', '老いる', '報いる', '悔いる', '甘える', '仕える', '聳える'}
WA_SHIMO = {'植える', '飢える', '据える'}
SPECIAL = {'来る': ('', '来'), 'くる': ('', 'カ変'), 'する': ('', 'サ変'), 'ある': ('あ', 'ラ変'), '有る': ('有', 'ラ変'),
           'いる': ('を', 'ラ変'), '居る': ('を', 'ラ変'), '死ぬ': ('死', 'ナ変'), '去る': ('去', '四段', 'ラ'),
           '出る': ('出', '下二段', 'ダ'), '寝る': ('', '下二段', 'ナ'), '得る': ('', '下二段', 'ア'),
           '経る': ('', '下二段', 'ハ')}
# 助動詞: 活用 (未然・連用・終止・連体・已然) と、前の語に求める形
AUXILIARIES = {'けり': (('けら', '', 'けり', 'ける', 'けれ'), '連用'),
               'き': (('せ', '', 'き', 'し', 'しか'), '連用'),
               'む': (('', '', 'む', 'む', 'め'), '未然'),
               'ず': (('ざら', 'ざり', 'ず', 'ぬ', 'ね'), '未然'),
               'る': (('れ', 'れ', 'る', 'るる', 'るれ'), '未然'),
               'らる': (('られ', 'られ', 'らる', 'らるる', 'らるれ'), '未然'),
               'たり': (('たら', 'たり', 'たり', 'たる', 'たれ'), '連用')}
PRONOUNS = {('ego', 'sg'): '我', ('ego', 'pl'): '我ら', ('tū', 'sg'): '汝', ('tū', 'pl'): '汝ら',
            ('quis', 'sg'): '誰', ('quid', 'sg'): '何', ('sē', 'sg'): '己', ('sē', 'pl'): '己ら'}
DEMONSTRATIVE_NOUNS = {'hic': 'これ', 'hīc': 'これ', 'ille': 'かれ', 'is': 'それ', 'iste': 'それ'}
DEMONSTRATIVE_ADJ = {'hic': 'この', 'hīc': 'この', 'ille': 'かの', 'is': 'その', 'iste': 'その', 'īdem': '同じ'}
# 現代語の訳語 → 古語 (よく出る語だけ)
WORDS = {'彼': 'かの人', '彼女': 'かの人', '彼ら': 'かの人々', 'どこで': 'いづこにて', 'どこへ': 'いづこへ',
         'いつ': 'いつ'}
PREPOSITIONS = {('in', 'Abl'): 'にて', ('in', 'Acc'): 'へ', ('ad', 'Acc'): 'へ', ('ex', 'Abl'): 'より',
                ('ē', 'Abl'): 'より', ('ab', 'Abl'): 'より', ('ā', 'Abl'): 'より', ('cum', 'Abl'): 'と',
                ('dē', 'Abl'): 'につきて', ('sine', 'Abl'): 'なくて', ('per', 'Acc'): 'を経て',
                ('post', 'Acc'): 'の後に', ('ante', 'Acc'): 'の前に', ('sub', 'Abl'): 'の下にて', ('prō', 'Abl'): 'のために',
                ('apud', 'Acc'): 'のもとにて', ('inter', 'Acc'): 'の間にて', ('propter', 'Acc'): 'によりて',
                ('ob', 'Acc'): 'によりて', ('contrā', 'Acc'): 'に向かひて', ('trāns', 'Acc'): 'を越えて',
                ('circum', 'Acc'): 'のめぐりにて', ('prope', 'Acc'): 'の近くにて', ('super', 'Acc'): 'の上にて'}
ROLE_PARTICLES = {'object': 'を', 'recipient': 'に', 'means': 'にて', 'place': 'にて', 'possessor': 'の',
                  'source': 'より', 'complement': ''}
WH = {'quis': '誰', 'quid': '何', 'cūr': 'など', 'quārē': 'など', 'ubi': 'いづこにて', 'quō': 'いづこへ',
      'unde': 'いづこより', 'quandō': 'いつ', 'quōmodo': 'いかに', 'num': '', 'utrum': ''}


def available():
    return japanese.available()


# ----------------------------------------------------------------------
# 用言

class Verb:
    """古語の動詞: 語幹 (漢字・かな) と活用の種類・行"""

    def __init__(self, stem, kind, row=''):
        self.stem, self.kind, self.row = stem, kind, row

    def form(self, name):
        i = FORMS.index(name)
        if self.kind in IRREGULAR:
            return self.stem + IRREGULAR[self.kind][i]
        vowel, _, tail = ENDINGS[self.kind][i].partition('+')
        kana = ROWS[self.row][VOWEL_INDEX[vowel]]
        return self.stem + kana + tail

    def __repr__(self):
        return '%s(%s%s)' % (self.form('終止'), self.kind, self.row)


def classical_verb(modern):
    """現代語の動詞の辞書形 → 古語の動詞 (Verb)。意味を置き換える語は kobun_lexicon.VERBS から"""
    replaced = VERBS.get(modern)
    if isinstance(replaced, tuple):
        return Verb(*replaced)
    if replaced:
        modern = replaced
    if modern in SPECIAL:
        return Verb(*SPECIAL[modern])
    if modern.endswith('する') and len(modern) > 2:
        return Verb(modern[:-2], 'サ変')   # 愛する → 愛す
    if modern.endswith(('来る', 'くる')) and len(modern) > 2:
        return Verb(modern[:-2], '来') if modern.endswith('来る') else Verb(modern[:-2], 'カ変')
    try:
        body, features = mecab_parse(modern)[-1]
    except Exception:
        return None
    prefix = modern[:len(modern) - len(body)]
    ctype, reading = features[4], features[6] if len(features) > 6 else ''
    if ctype.startswith('五段-') or ctype.startswith('文語四段-'):
        row = ctype.split('-')[1][0]
        row = 'ハ' if row == 'ワ' else row   # 歌う → 歌ふ
        if body in ('ある', '有る', '在る'):
            return Verb(prefix + body[:-1], 'ラ変')
        return Verb(prefix + body[:-1], '四段', row)
    if ctype.startswith('サ行変格') or ctype.startswith('サ変'):
        return Verb(prefix + body[:-2], 'サ変')
    if ctype.startswith('カ行変格') or ctype.startswith('カ変'):
        return Verb(prefix + body[:-2], 'カ変')
    if ctype.startswith('上一段-'):
        row = ctype.split('-')[1][0]
        if body in KAMI_ICHIDAN:
            return Verb(prefix + body[:-1], '上一段')
        if row == 'ザ' and body not in KUN_ZURU:
            return Verb(prefix + body[:-2], 'ザ変')   # 感じる → 感ず、命じる → 命ず
        stem = prefix + body[:-2]
        if row == 'ア':
            row = 'ヤ' if body in YA_SHIMO else 'ハ'   # 老いる → 老ゆ、強いる → 強ふ
        elif row == 'ザ':
            row = 'ダ'   # 恥じる → 恥づ
        return Verb(stem, '上二段', row)
    if ctype.startswith('下一段-'):
        row = ctype.split('-')[1][0]
        stem = prefix + body[:-2]
        if row == 'ア':
            row = 'ヤ' if body in YA_SHIMO else 'ワ' if body in WA_SHIMO else 'ハ'   # 与える → 与ふ、見える → 見ゆ
        return Verb(stem, '下二段', row)
    return None


def adjective_forms(modern):
    """現代語の形容詞 (美しい・良い) → (語幹, シク / ク)。形容動詞 (静かな) は None"""
    if modern.endswith('しい'):
        return modern[:-2], 'シク'
    if modern.endswith('い') and len(modern) >= 2:
        return modern[:-1], 'ク'
    return None


def adjective(modern, name):
    """形容詞の活用形 (ク・シク活用。助動詞の前の未然・連用はカリ活用)。古語は kobun_lexicon.ADJECTIVES から"""
    entry = ADJECTIVES.get(modern)
    if isinstance(entry, str):   # 名詞に係る語 (よろづの・疲れたる)。述語なら 〜なり
        if name == '連体':
            return entry
        modern = entry[:-1] if entry.endswith('の') else entry
        entry = None
    if isinstance(entry, tuple):
        stem, kind = entry
        if kind == 'ナリ':
            modern, found = stem, None
        else:
            found = (stem, kind)
    else:
        found = adjective_forms(modern)
    if found is None:   # 形容動詞・名詞: なり
        base = modern[:-1] if modern.endswith('な') else modern
        return base + {'未然': 'なら', '連用': 'に', '終止': 'なり', '連体': 'なる', '已然': 'なれ',
                       '連用+aux': 'なり', '未然+aux': 'なら'}[name]
    stem, kind = found
    s = 'し' if kind == 'シク' else ''
    table = {'未然': stem + s + 'く', '連用': stem + s + 'く', '終止': stem + 'し', '連体': stem + s + 'き',
             '已然': stem + s + 'けれ', '連用+aux': stem + s + 'かり', '未然+aux': stem + s + 'から'}
    return table[name]


def attach(word_form, aux, name):
    """前の形 + 助動詞の name 形"""
    forms, _ = AUXILIARIES[aux]
    i = FORMS.index(name) if name != '命令' else 4
    return word_form + forms[min(i, 4)]


def chain(verb, clause, name):
    """動詞 + 助動詞 (受身 → 打消 → 時) の name 形 (終止・連体・已然・連用・未然)"""
    steps = []
    if clause.voice == 'passive':
        steps.append('る' if verb.kind in ('四段', 'ナ変', 'ラ変') else 'らる')
    if clause.negated:
        steps.append('ず')
    tense = clause.tense
    if tense == 'imperfect' and not clause.negated and verb.kind != 'ラ変' and not clause.question_word:
        steps += ['たり', 'けり']   # 未完了過去は存続の たり + けり (住みたりけり「住んでいた」)。間接疑問 (時制の一致) は除く
    elif tense in ('perfect', 'imperfect', 'past-perfect'):
        steps.append('けり')
    elif tense in ('future', 'future-perfect') and not clause.negated:
        steps.append('む')
    if not steps:
        return verb.form(name)
    text = verb.form(AUXILIARIES[steps[0]][1])
    for k, aux in enumerate(steps):
        last = k == len(steps) - 1
        if last:
            text = attach(text, aux, name)
        else:
            nxt = steps[k + 1]
            need = AUXILIARIES[nxt][1]
            if aux == 'ず' and nxt == 'けり':
                text += 'ざり'   # 〜ざりけり
            else:
                text = attach(text, aux, need)
    return text


def predicate(clause, name='終止'):
    """述語の name 形"""
    if clause.copula or clause.verb.lemma == 'sum':   # 日本語の入口の いる・ある (sum) も
        complements = clause.role('complement')
        if not complements:   # 存在: 人・動物は をり、ほかは あり
            animate = any(np.animate for np in clause.role('subject'))
            return chain(Verb('を' if animate else 'あ', 'ラ変'), clause, name)
        np = complements[0]
        is_adj = not np.members and np.head is not None and np.head.pos in ('adj', 'participle')
        if is_adj:
            word = WORDS.get(gloss(np.head), gloss(np.head))
            return _adjective_predicate(word, clause, name)
        text = noun_phrase(np)
        if clause.negated:   # 〜にあらず
            return text + 'に' + chain(Verb('あ', 'ラ変'), _replace(clause, negated=True), name)
        past = clause.tense in ('perfect', 'imperfect', 'past-perfect')
        if past:
            return text + 'なり' + attach('', 'けり', name)
        return text + adjective('な', name)[0:0] + {'終止': 'なり', '連体': 'なる', '已然': 'なれ', '連用': 'にて',
                                                    '未然': 'なら'}[name]
    modern = japanese.collocation(clause, gloss(clause.verb))   # 雨の降る (落ちる でなく)
    modern = WORDS.get(modern, modern)
    if not re.search('[うくぐすつぬぶむる]$', modern):
        modern += 'する'
    verb = classical_verb(modern)
    if verb is None:
        return modern
    return chain(verb, clause, name)


def _adjective_predicate(word, clause, name):
    past = clause.tense in ('perfect', 'imperfect', 'past-perfect')
    if clause.negated:
        text = adjective(word, '未然+aux') + 'ず'
        if past:
            return adjective(word, '未然+aux') + 'ざり' + attach('', 'けり', name)
        return text if name == '終止' else adjective(word, '未然+aux') + {'連体': 'ぬ', '已然': 'ね', '連用': 'ず',
                                                                         '未然': 'ず'}.get(name, 'ず')
    if past:
        return adjective(word, '連用+aux') + attach('', 'けり', name)
    return adjective(word, name)


def _replace(clause, **kw):
    import dataclasses
    return dataclasses.replace(clause, **kw)


# ----------------------------------------------------------------------
# 名詞句・節

def word_of(lex):
    w = gloss(lex)
    if lex.pos == 'adv':
        return ADVERBS.get(w) or WORDS.get(w, w)
    return NOUNS.get(w) or WORDS.get(w) or ADVERBS.get(w, w)


def noun_phrase(np):
    if np.members:
        return 'と'.join(noun_phrase(m) for m in np.members)
    head = np.head
    if head.pos == 'pronoun' and head.lemma == 'quis' and np.gender == 'n':
        word = '何'
    elif head.pos == 'pronoun' and (head.lemma, np.number) in PRONOUNS:
        word = PRONOUNS[(head.lemma, np.number)]
    elif head.pos == 'pronoun' and head.lemma == 'is' and not np.modifiers and not np.relatives:
        word = 'かの人々' if np.number == 'pl' else 'かの人'
    elif head.pos == 'pronoun' and np.relatives and head.lemma in DEMONSTRATIVE_NOUNS:
        word = 'もの' if np.gender == 'n' else '人'
    elif head.pos == 'pronoun' and head.lemma in DEMONSTRATIVE_NOUNS:
        word = DEMONSTRATIVE_NOUNS[head.lemma]
    else:
        word = word_of(head)
        if np.number == 'pl' and np.animate and not word.endswith(('ども', 'たち', 'ら')):
            word += 'ども'
    before = []
    for gen in np.genitives:
        before.append(noun_phrase(gen) + 'の')
    for r in np.relatives:
        before.append(clause_text(r, name='連体', attributive=True))
    for m in np.modifiers:
        if hasattr(m, 'members'):
            before.append('、'.join(_attributive_adj(x.head) for x in m.members))
        elif m.pos == 'pronoun' and m.lemma in DEMONSTRATIVE_ADJ:
            before.insert(len(np.genitives) + len(np.relatives), DEMONSTRATIVE_ADJ[m.lemma])
        else:
            before.append(_attributive_adj(m))
    return ''.join(before) + word


def _attributive_adj(lex):
    w = gloss(lex)
    if w in ADJECTIVES:
        return adjective(w, '連体')
    if w.endswith('の') or w in NOUNS:
        return NOUNS.get(w, w)
    if w.endswith(('た', 'だ')):
        past = _past_attributive(w)
        if past:
            return past
    return adjective(w, '連体')


VERB_TAILS = ('る', 'う', 'く', 'ぐ', 'す', 'つ', 'む', 'ぶ', 'ぬ')


def _past_attributive(modern):
    """連体の 〜た → 連用形 + たる (疲れた → 疲れたる、燃えた → 燃えたる)。
    受身 (祝福された・捕えられた・書かれた) は 未然形 + る / らる の連用形 + たる (捕へられたる)"""
    verb = None
    passive = re.match(r'^(.+?)(され|られ|れ)た$', modern)
    if passive:
        base, kind = passive.groups()
        if kind == 'され':
            verb = classical_verb(base + 'する')
        elif kind == 'られ':
            verb = classical_verb(base + 'る')
        else:   # 五段の受身: 書かれた → 書く、歌われた → 歌ふ
            old_base = base[:-1] + 'は' if base.endswith('わ') else base
            for tail in VERB_TAILS:
                candidate = classical_verb(base[:-1] + tail) if len(base) > 1 else None
                if candidate is not None and candidate.kind == '四段' and candidate.form('未然') == old_base:
                    verb = candidate
                    break
        if verb is not None:
            aux = 'る' if verb.kind in ('四段', 'ナ変', 'ラ変') else 'らる'
            return attach(verb.form('未然'), aux, '連用') + 'たる'
        # 受身として作れない 〜れた (疲れた・隠れた) は能動の 〜た
    from dragoman.core.japanese import JaVerb
    stem = re.sub('(った|んだ|いだ|いた|した|た|だ)$', '', modern)
    for ending in ('る', 'う', 'つ', 'く', 'ぐ', 'む', 'ぶ', 'ぬ', 'す'):
        candidate = stem + ending
        try:
            if JaVerb(candidate).past_form() == modern:
                verb = classical_verb(candidate)
                break
        except Exception:
            continue
    return verb.form('連用') + 'たる' if verb else None


def clause_text(clause, name='終止', attributive=False, topic=None):
    """節 → 古文 (述語の name 形まで)"""
    from .frame import lexical_negation, periphrastic
    clause = lexical_negation(periphrastic(clause))   # nesciō → 知らず
    parts = [_participial(p) for p in clause.adjuncts if p.kind == 'absolute']
    subjects = clause.role('subject')
    if topic is None:
        topic = name == '終止' and not attributive and not clause.subordinator
    for np in subjects:
        if attributive and clause.gap == 'subject':
            continue
        parts.append(noun_phrase(np) + ('は' if topic else 'の'))
    for p in clause.adjuncts:
        if p.kind != 'absolute':
            parts.append(_participial(p))
    for role in ('recipient', 'object'):
        for np in clause.role(role):
            if attributive and clause.gap == role:
                continue
            parts.append(noun_phrase(np) + ROLE_PARTICLES[role])
    for role, np in clause.args:
        if role in ('subject', 'object', 'recipient', 'complement'):
            continue
        if role == 'prep' and np.prep is not None:
            if clause.voice == 'passive' and np.prep.lemma in ('ā', 'ab'):
                parts.append(noun_phrase(np) + 'に')
            else:
                particle = PREPOSITIONS.get((np.prep.lemma, np.case), 'にて')
                if particle == 'にて' and _existence(clause):
                    particle = 'に'   # 家にをり・都に住む (存在・居住の動詞の場所)
                parts.append(noun_phrase(np) + particle)
        elif attributive and clause.gap == role:
            continue
        else:
            particle = 'に' if role == 'means' and np.animate else ROLE_PARTICLES.get(role, 'にて')   # 与格と奪格の同形
            parts.append(noun_phrase(np) + particle)
    for inner in clause.infinitives:
        parts.append(infinitive(inner, clause))
    for inner in clause.questions:
        parts.append(question(inner))
    for adv in clause.adverbs:
        word = word_of(adv)
        if word in CLAUSE_INITIAL:
            parts.insert(0, word)   # もし雨降らば (節の頭に)
        else:
            parts.append(word)
    parts.append(predicate(clause, name))
    return ''.join(parts)


CLAUSE_INITIAL = {'もし', 'もしも', 'たとひ', 'たとえ', 'かりに', 'さて', 'されど', 'されば', 'しかるに'}
_existence = japanese._existence   # 存在・居住の動詞 (場所は に)


def infinitive(inner, governor):
    kind = inner.infinitive_kind
    finite = _replace(inner, mood='indicative')
    if kind == 'saying':
        return clause_text(finite, name='終止', topic=False) + 'と'
    return clause_text(finite, name='連体', topic=False) + 'を'   # 歌ふを聞く・行くを望む


def question(inner):
    """間接疑問: 疑問詞 + か …連体形 (係り結び) + と"""
    finite = _replace(inner, mood='indicative')
    has_np = any(np.interrogative for _, np in inner.args)
    if has_np:
        # 疑問の名詞句の助詞を か に (誰か歌ひける)
        text = clause_text(finite, name='連体', topic=False)
        for wh in ('誰の', '何を', '何の', '誰を', '誰に'):
            if wh in text:
                text = text.replace(wh, wh[0] + 'か', 1)
                break
        return text + 'と'
    if inner.question_word in ('num', 'utrum'):
        return clause_text(finite, name='終止', topic=False) + 'やと'
    return WH.get(inner.question_word, '') + 'か' + clause_text(finite, name='連体', topic=False) + 'と'


def _participial(p):
    """分詞句・独立奪格: 連用形 + て (王の死にて、…)"""
    from .frame import Lex
    ja = p.verb.verb_ja or _latin_verb_ja(p.verb)
    modern = gloss(Lex(p.verb.verb, 'verb', ja, lang=p.verb.lang)) if ja else gloss(p.verb)
    modern = WORDS.get(modern, modern)
    if not re.search('[うくぐすつぬぶむる]$', modern):
        modern += 'する'
    verb = classical_verb(modern)
    if verb is None:
        form = modern
    elif p.voice == 'passive':
        aux = 'る' if verb.kind in ('四段', 'ナ変', 'ラ変') else 'らる'
        form = attach(verb.form('未然'), aux, '連用') + 'て'
    elif p.tense == 'present' and p.kind == 'absolute':
        form = verb.form('連体') + 'に'   # 現在分詞の独立句: 乙女の歌ふに
    else:
        form = verb.form('連用') + 'て'
    args = ''.join(noun_phrase(np) + ROLE_PARTICLES.get(role, 'にて') for role, np in p.args if role != 'adverb')
    subject = noun_phrase(p.subject) + 'の' if p.subject is not None else ''
    return subject + args + form + ('、' if p.kind == 'absolute' else '')


def _latin_verb_ja(participle):
    """ラテン語の分詞のもとの動詞の日本語の訳語 (captus → 捕える)"""
    if participle.lang not in ('', 'la') or not participle.verb:
        return ''
    from . import latin
    return next((item['ja'] for _, item in latin._forms(participle.verb, 'verb')[:5] if item.get('ja')), '')


# 従属の接続詞 → (述語の形, 後ろに付ける語)
SUBORDINATORS = {'ubi': ('已然', 'ば'), 'cum': ('已然', 'ば'), 'quod': ('已然', 'ば'), 'quia': ('已然', 'ば'),
                 'quoniam': ('已然', 'ば'), 'postquam': ('連用', 'て後'), 'sī': ('未然', 'ば'),
                 'nisi': ('未然', 'ずは'), 'dum': ('連体', '間に'), 'quamquam': ('已然', 'ども'), 'etsī': ('已然', 'ども'),
                 'ut': ('連体', 'ために'), 'nē': ('未然', 'じとて'), 'antequam': ('未然', 'ぬ先に'),
                 'simul': ('連体', 'やいなや')}


def sentence(clauses):
    if not clauses:
        return ''
    out = ''
    for i, clause in enumerate(clauses):
        last = i == len(clauses) - 1
        if clause.subordinator in SUBORDINATORS:
            name, suffix = SUBORDINATORS[clause.subordinator]
            if clause.subordinator in ('sī',) and clause.tense in ('perfect', 'imperfect'):
                clause = _replace(clause, tense='present')
            if clause.subordinator == 'postquam':
                clause = _replace(clause, tense='present')
            out += clause_text(clause, name=name) + suffix + '、'
            continue
        if not last and 'et' in clauses[i + 1].connectives:
            out += clause_text(_replace(clause, tense='present'), name='連用', topic=True) + 'て、'
            continue
        if not last and 'sed' in clauses[i + 1].connectives:
            out += clause_text(clause, name='已然', topic=True) + 'ど、'
            continue
        out += clause_text(clause, name='終止') + ('。' if last else '、')
    return out
