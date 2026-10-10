#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 文の解析の骨組み (言語に依存しない部分)
#   辞書引き済みの語の列 → 並列句・形容詞/属格の係り先・独立奪格 (属格独立・処格独立)・分詞句・前置詞句・述語の検出
#   → 名詞句を述語の格スロットに割り当てる
#
# 言語ごとの違い (接続詞・繋辞・否定・格の助詞・独立奪格の格など) は core/language.py の設定で切り替える。
# 辞書引き・タガーなどの前処理は言語ごと (latin/analyzer.py, greek/analyzer.py, sanskrit/analyzer.py)。
# 結果は SentenceAnalysis で返す。表示は core/render.py
#
from dataclasses import dataclass, field

from . import language
from .Word import Word
from .Predicate import Predicate
from .AndOr import AndOr, non_genitive
from .PrepClause import PrepClause
from .Absolute import AblativeAbsolute
from .Participle import ParticiplePhrase, participle_kind, participle_item
from .Infinitive import InfinitiveClause, governor_kind, takes_accusative_subject
from .Question import QuestionClause, QUESTION_VERBS, is_interrogative
from .Relative import RelativeClause, is_relative


# 前置詞に支配される部分を切り出す
def detect_prep_domination(words):
    M = len(words)
    visited = [False] * M

    i = 0
    while i < M-1:
#        print " WHILE-i : %d/%d" % (i, M-1)
        word = words[i]

        # 前置詞だけ見たいので、Word以外はスキップ
        if not isinstance(word, Word):
            i += 1
            continue # while-i-loop

        # 句読点をスキップ
        if word.items is None:
            i += 1
            continue # while-i-loop

        preps = []
        for item in word.items:
            if item.pos == 'preposition':
                preps.append(item)

        if not preps:
            i += 1
            continue # while-i-loop

        # 辞書の登録順を保って重複を除く (set だと実行ごとに順序が変わる)
        dominates = list(dict.fromkeys(item.dominates for item in preps))
        # print "PREP (%s) DETECTED AT %d :" % (word.surface.encode('utf-8'), i), dominates

        j = i + 1
        noun_seen = False   # 前置詞句の名詞をもう取ったか
        numbers = set()     # その名詞の数
        while j < M:
            w = words[j]
            if isinstance(w, Word):
                if w.items and noun_seen and w.items[0].pos in ('noun', 'pronoun') and w.items[0]._ and \
                        not language.current().objects_follow_verb and not _continues_phrase(w, dominates, numbers):
                    # 名詞の後ろの名詞は、支配する格で数も合うときだけ前置詞句に入れる (同格: ad Volscōs, Rōmae hostēs、
                    # in mediō labyrinthō)。数の合わない語 (ad templum multa dōna) や、固有名詞 (単数として見る:
                    # post diēs Herculēs) は句の外
                    break # while-j-loop
                if w.items is None:
                    if w.surface in (',', ';', ':') and language.current().objects_follow_verb:
                        break # while-j-loop (句読点で前置詞句を閉じる: в Новуре, но …)
                    j += 1
                    continue # while-j-loop
                stop = False
                matched = None   # 支配する格に合う名詞の読みの格
                for k, item in enumerate(w.items):
                    if item.pos in ['verb', 'preposition', 'conj', 'adv'] or \
                            (item.pos == 'indecl' and noun_seen and not language.current().objects_follow_verb):
                        stop = True   # 名詞の後ろの格変化しない数詞も句の外 (in Thessaliā duo frātrēs)
                        break # for-k-loop
                    if item._: # subst
                        if item.pos == 'adj':
                            if noun_seen and not language.current().objects_follow_verb and \
                                    not any(case in dominates or case == 'Gen' for case, _, _ in item._):
                                stop = True   # 名詞の後ろの、格の合わない形容詞・数詞 (in Thessaliā duo frātrēs の duo)
                                break # for-k-loop
                            continue # for-k-loop
                        if noun_seen and item.pos == 'pronoun' and item.attrib('desc') in ('人称代名詞', '再帰代名詞') \
                                and not language.current().objects_follow_verb:
                            stop = True   # 名詞の後ろの人称・再帰代名詞は句の外 (in āera sē sublevāvērunt)
                            break # for-k-loop
                        can_skip = False
                        yes = False
                        for case, number, gender in item._:
                            if case in dominates:
                                matched = matched or case
                                yes = True
                                break # for-cng-loop
                            elif case == 'Gen':
                                can_skip = True  # 前置詞句の中の属格の修飾語 (属格を支配する前置詞なら上で合う)
                            else:
                                pass
                        if yes and k == 0 and language.current().objects_follow_verb:
                            # 一番の読みが支配する格なら、ほかの読み (副詞など) は見ない (ロシア語の из дома。
                            # ラテン語では別の品詞にも読める語を取り込みすぎて、UD の主語・目的語が少し下がる)
                            break # for-k-loop
                        if not yes and not can_skip:
                            stop = True
                            break # for-k-loop
                if stop and matched and not language.current().objects_follow_verb and \
                        w.items[0].pos not in ('verb', 'preposition', 'conj', 'adv'):
                    # 一番の読みが名詞で支配する格に合えば、ほかの読み (別の語の Dat/Abl など) で止めない
                    # (in hostīs: hostis の対格と、hostus の与格・奪格)
                    stop = False
                if matched:
                    dominates = [matched] # 絞り込み
                    if not noun_seen and any(item.pos in ('noun', 'pronoun') for item in w.items):
                        noun_seen = True
                        numbers = {number for item in w.items if item._ for case, number, _ in item._
                                   if case in dominates}
                if stop:
                    break # while-j-loop
            elif isinstance(w, AndOr):
                # 並列句は格が前置詞の支配格と合う場合だけ前置詞句に入れる (dē caelō ... virōs fēmināsque)
                if w.cases is not None and not any(case in dominates for case in w.cases):
                    break # while-j-loop
            elif isinstance(w, Predicate):
                break # while-j-loop
            else:
                break # while-j-loop
            j += 1

        cl = PrepClause(word, dominates[0], words[i+1:j])
        for ix in range(i, j):
            words[ix] = None
            visited[ix] = True
        words[i] = cl

#        print " [%d..%d]" % (i, j-1),
#        for w in words[i:j]:
#            try:
#                print w.surface.encode('utf-8'),
#            except:
#                pass
##        print u' '.join([w.surface for w in words[i:j]]).encode('utf-8')
#        print
        i = j

    return words


def _continues_phrase(word, dominates, numbers):
    """前置詞句の名詞の後ろの名詞が句に続くか: 支配する格の読みで、数が前の名詞と合う (固有名詞は単数だけ)"""
    item = word.items[0]
    proper = (item.attrib('base') or '')[:1].isupper()
    return any(case in dominates and number in numbers and (number == 'sg' or not proper)
               for case, number, _ in item._) or any(case == 'Gen' for case, _, _ in item._)


def detect_and_or(words, trace):
    M = len(words)

    surfaces = [word.surface for word in words]
    # カンマや活用動詞で分断しグルーピングする
    groups = []
    curr = []
    for i, surface in enumerate(surfaces):
        if surface in (',', '.', ';', '"', '!', '?'):
            groups.append(curr)
            curr = []
        elif words[i].is_verb():
            groups.append(curr)
            curr = []
        else:
            curr.append(i)
    if curr: groups.append(curr)

    # groups: [[0, 1, 2], [4, 5, 6, 7]]

    visited = set() #[False] * M
    ao_loc = set()

    # ある単語 word がグループ group 内で生起する位置（複数）を配列で返す
    #   eg. word_indices_in_group(neque, [0, 1, 2, 3, 4, 5, 6, 7]) -> [2, 4]
    def word_indices_in_group(word, group):
        return [x for x in [i if surfaces[i].lower() == word else -1 for i in group] if x>=0]

    # et-et- / neque-neque- の検出
    def detect(and_or_word):
        ao_indices = [word_indices_in_group(and_or_word, group) for group in groups]
        for i, aos in enumerate(ao_indices):
            num_of_ao = len(aos)
            if num_of_ao >= 2:
                upper = and_or_word.upper()
                # print "  %s-%s- found in #%d" % (upper, upper, i), aos
                cl = AndOr(and_or_word)
                # 区間が確定しているもの（＝最後の１つ以外）をまず追加
                for j in range(num_of_ao-1):
                    this_et_idx = aos[j]
                    next_et_idx = aos[j+1]
                    cl.add(words[this_et_idx+1:next_et_idx])
                # 最後の１つは、どこで終わるか確かめながら追加
                last_et_idx = aos[num_of_ao-1]
                end_idx = groups[i][-1] + 1
                ws = []
                idx = last_et_idx + 1  # 最後の et の後ろに語が無い場合 (ループが回らない) の範囲の終わり
                for idx in range(last_et_idx+1, end_idx):
                    word = words[idx]
                    if not isinstance(word, Word) or not word.items:
                        break  # 未知語・記号、すでにまとめた並列句 (et ... et の後の aut ... aut など)
                    first_item = word.items[0]
                    if cl.pos == 'noun':
                        # 格変化のある語に限る
                        if first_item._ is None: break
                        if non_genitive(first_item._):
                            cases = [x[0] for x in first_item._]
                            # これまでの物と格が一致する可能性がなければ排除
                            cases_x = [case for case in cl.cases if case in cases]
                            if not cases_x: break
                    ws.append(word)
                    idx += 1
                if ws:
                    cl.add(ws)
                else:
                    pass # ERROR: type mismatch

                # print "CL: [%d..%d)" % (aos[0], idx)
                # cl.dump()
                for j in range(aos[0], idx):
                    # words[j] = None
                    # visited[j] = True
                    visited.add(j)

                cl.restrict()
                trace.extend(cl.messages)

                words[aos[0]] = cl
                ao_loc.add(aos[0])
                # aos.append(aos[0])

    lang = language.current()
    for and_or_word in lang.and_words + lang.nor_words + lang.or_words:
        detect(and_or_word)

    def same(word1, word2, pos_check=True):
        if not isinstance(word1, Word) or not isinstance(word2, Word):
            return False
        if not word1.items or not word2.items:
            return False
        item1 = word1.items[0]
        item2 = word2.items[0]
        if pos_check and item1.pos != item2.pos:
            return False
        if item1.pos == 'verb':
            return False
        if not item1._ or not item2._:  # 格変化のない語 (副詞など)
            return False
        cases1 = [x[0] for x in item1._]
        cases2 = [x[0] for x in item2._]
        cases = [case for case in cases1 if case in cases2]
        if cases:
            return True
        return False


#    print
    for i, word in enumerate(words):
        if i in visited: continue
        if not word.items: continue

        # A et B
        def bind_two_if_same():
            word1 = words[i-1]
            word2 = words[i+1]
            if same(word1, word2):
                trace.append("// #%d ET #%d: %s == %s" % (i-1, i+1, word1.surface_utf8(), word2.surface_utf8()))
                cl = AndOr(language.current().and_words[0])
                cl.add([word1])
                cl.add([word2])
                trace.extend(cl.messages)
                for j in range(i-1, i+2):
                    visited.add(j)
                words[i-1] = cl
                ao_loc.add(i-1)
                return True
            else:
                return False

        # A [adj] et B [adj]
        def bind_more_if_same():
            word1 = words[i-2]
            word1a = words[i-1]
            if not word1a.items or word1a.items[0].pos != 'adj':
                return False
            if not same(word1, word1a, pos_check=False):
                return False

            word2 = words[i+1]
            with_2a = False
            if i+2 < M:
                word2a = words[i+2]
                if word2a.items and word2a.items[0].pos == 'adj':
                    if same(word2, word2a, pos_check=False):
                        with_2a = True

            if same(word1, word2):
                trace.append("// #%d #%d ET #%d (#%d): %s == %s" % (i-2, i-1, i+1, i+2, word1.surface_utf8(), word2.surface_utf8()))
                cl = AndOr(language.current().and_words[0])
                word1.add_modifier(word1a)
                cl.add([word1])
                visited.add(i-2)
                visited.add(i-1)

                if with_2a:
                    word2.add_modifier(word2a)
                    visited.add(i+2)
                cl.add([word2])
                trace.extend(cl.messages)
                visited.add(i+1)

                words[i-2] = cl
                ao_loc.add(i-2)
                return True
            else:
                return False

        # A B-que: -que の付いた語から後ろが2番目の並列要素
        #   fīlum longum mīrumque gladium → [fīlum ← longum] et [gladium ← mīrum]
        def bind_que():
            def is_pos(w, pos):
                return isinstance(w, Word) and w.items and w.items[0].pos == pos
            # 2番目の要素: -que の付いた語 (形容詞なら一致する直後の名詞まで)
            head2, mods2, last = word, [], i
            if is_pos(word, 'adj') and i+1 < M and is_pos(words[i+1], 'noun') and \
               (i+1) not in visited and same(word, words[i+1], pos_check=False):
                head2, mods2, last = words[i+1], [word], i+1
            # 1番目の要素: 直前の語 (名詞と形容詞の組まで)
            if (i-1) in visited:
                return False
            prev = words[i-1]
            head1, mods1, first = prev, [], i-1
            if i >= 2 and (i-2) not in visited:
                if is_pos(prev, 'adj') and is_pos(words[i-2], 'noun') and same(prev, words[i-2], pos_check=False):
                    head1, mods1, first = words[i-2], [prev], i-2
                elif is_pos(prev, 'noun') and is_pos(words[i-2], 'adj') and same(prev, words[i-2], pos_check=False):
                    head1, mods1, first = prev, [words[i-2]], i-2
            if not same(head1, head2, pos_check=(not mods1 and not mods2)):
                return False
            trace.append("// #%d..#%d QUE #%d..#%d: %s == %s" % (
                first, i-1, i, last, head1.surface_utf8(), head2.surface_utf8()))
            for m in mods1:
                head1.add_modifier(m)
            for m in mods2:
                head2.add_modifier(m)
            cl = AndOr(language.current().and_words[0])
            cl.add([head1])
            cl.add([head2])
            trace.extend(cl.messages)
            for j in range(first, last+1):
                visited.add(j)
            words[first] = cl
            ao_loc.add(first)
            return True

        surface = word.surface
        if surface in language.current().and_words and i+1 < len(words):
            # print "// %d ET %s" % (i, words[i+1].surface_utf8())
            if i >= 1:
                if not bind_two_if_same() and i >= 2:
                    bind_more_if_same()

        if surface[-3:] == 'que':
            if surface.lower() not in ('neque', 'itaque', 'quoque', 'atque', 'quisque', 'usque'):
                if i >= 1:
                    bind_que()

    visited_ix = [ix for ix in visited if ix not in ao_loc]#[ix for ix in visited])
    return (words, visited_ix)


def _coordinators():
    """係り先を探すときに越えない並列の接続詞 (et, neque)"""
    lang = language.current()
    return lang.and_words + lang.nor_words


ABL_PREPOSITIONS_CASE = 'Abl'
PUNCTUATION = (',', ';', ':', '.', '?', '!')


def _abl_participle_tuples(node):
    """奪格の分詞として読める語なら、その (格, 数, 性) のうち奪格のもの
    (格は言語の設定の absolute_case。ギリシア語は属格独立の属格)"""
    if not isinstance(node, Word) or not node.items:
        return []
    case = language.current().absolute_case
    return [cng for item in node.items if item.pos == 'participle'
            for cng in (item._ or []) if cng[0] == case]


def _abl_tuples(node):
    """奪格の名詞・代名詞として読める要素なら、その (格, 数, 性) のうち奪格のもの"""
    case = language.current().absolute_case
    if isinstance(node, AndOr):
        return [cng for cng in (node._ or []) if cng[0] == case] if node.pos in ('noun', 'pronoun') else []
    if not isinstance(node, Word) or not node.items:
        return []
    return [cng for item in node.items if item.pos in ('noun', 'pronoun')
            for cng in (item._ or []) if cng[0] == case]


def _agrees(a, b):
    return any(ca == cb and na == nb and (ga == gb or 'c' in (ga, gb) or None in (ga, gb))
               for ca, na, ga in a for cb, nb, gb in b)


def _is_clause_boundary(node):
    """句読点・動詞・接続詞・前置詞 (独立奪格の主語を探すときに越えない)"""
    if isinstance(node, Word):
        if node.items is None:
            return node.surface in PUNCTUATION
        return bool(node.items) and node.items[0].pos in ('verb', 'conj')
    return not isinstance(node, (AndOr, PrepClause))


def _governed_by_abl_preposition(nodes, ix):
    """直前 (同じ格の名詞が挟まっていてもよい: διὰ Ἠσαΐου τοῦ προφήτου) が、その格を支配する前置詞"""
    lang = language.current()
    j = ix - 1
    if lang.name != 'la':
        while j >= 0 and _abl_tuples(nodes[j]) and not (isinstance(nodes[j], Word) and nodes[j].items and
                                                       nodes[j].items[0].pos == 'preposition'):
            j -= 1
    prev = nodes[j] if j >= 0 else None
    return isinstance(prev, Word) and bool(prev.items) and \
        any(item.pos == 'preposition' and item.dominates == lang.absolute_case for item in prev.items)


def _governed_by_main_verb(nodes, i):
    """主節の動詞が独立奪格の格を目的語に取る (ギリシア語: ἤκουσα φωνῆς λεγούσης「声が言うのを聞いた」)"""
    lang = language.current()
    if not lang.absolute_case_verbs:
        return False
    for node in nodes[i + 1:] + nodes[:i][::-1]:
        if isinstance(node, Word) and node.items and node.items[0].pos == 'verb' and \
                node.items[0].attrib('mood') not in ('infinitive', 'participle'):
            return node.items[0].attrib('pres1sg') in lang.absolute_case_verbs
    return False


_lexicalized_cache = {}


def _comparative_forms(base):
    """形容詞としての比較級の形 (acūtus → acūtior, patēns → patentior)"""
    if base.endswith('us'):
        return [base[:-2] + 'ior']
    for nom, stem in (('ēns', 'ent'), ('āns', 'ant'), ('ens', 'ent'), ('ans', 'ant')):
        if base.endswith(nom):
            return [base[:-len(nom)] + stem + 'ior']
    return []


def _is_lexicalized_participle(word):
    """形容詞になった分詞 (acūtus「鋭い」, apertus「開けた」, patēns)。判定は言語の設定 (ラテン語は、比較級が形容詞として
    Wiktionary にあるもの)"""
    check = language.current().lexicalized_participle
    if check is None:
        return False
    base = participle_item(word).attrib('base') or ''
    key = (language.current().name, base)
    if key not in _lexicalized_cache:
        _lexicalized_cache[key] = check(base, _comparative_forms(base))
    return _lexicalized_cache[key]


def _is_gerundive(word):
    base = participle_item(word).attrib('base') or ''
    return base.endswith(('ndus', 'ndum'))


# 分詞が付いても、ふつうは様態・場所の奪格 (名詞の修飾) になる名詞: animō suspēnsō「気をもんで」,
# locīs apertīs「開けた場所で」。UD Latin-PROIEL で animus は修飾 11・独立奪格 2、locus は 25・5
MODIFIER_NOUNS = {'animus', 'locus'}


def _usually_modified(subject, complements):
    """主語の名詞が MODIFIER_NOUNS で、分詞に補語が無く、代名詞の修飾語も無い (locō ab hostibus captō は独立奪格)"""
    if complements or not isinstance(subject, Word) or not subject.items or _is_pronominal(subject):
        return False
    return subject.items[0].pos == 'noun' and subject.items[0].attrib('base') in MODIFIER_NOUNS


def _not_absolute_form(word):
    """独立奪格の分詞にならない形: 命令法の scītō「知っておけ」(書簡の決まり文句。第1活用の -ātō は
    分詞の奪格と未来命令法が同じ形なので、命令法と読めるだけでは外さない)、-ī で終わる現在分詞
    (独立奪格の現在分詞は -e: Pompēiō petente。-ī は与格か形容詞的な奪格: Pompēiō petentī)"""
    if word.surface.lower() in ('scītō', 'scito', 'scītōte', 'scitote'):
        return True
    return participle_kind(word) == 'present' and word.surface.endswith(('ī', 'i'))


def _is_pronominal(node):
    """代名詞・指示詞 (hīs rēbus の hīs のような修飾語を含む): 独立奪格の主語なら確実 (quō factō, eō absente)"""
    if isinstance(node, Word) and node.items:
        if node.items[0].pos == 'pronoun':
            return True
        return any(isinstance(m, Word) and m.items and m.items[0].pos == 'pronoun' for m in node.modifiers)
    return False


def _in_attributive_position(noun, participle):
    """冠詞と名詞の間にある分詞は名詞の修飾 (ギリシア語: τοῦ λέγοντος ἀνθρώπου「話している人の」)"""
    if not isinstance(noun, Word) or participle.index is None or noun.index is None:
        return False
    return any(isinstance(m, Word) and m.items and m.items[0].pos == 'article' and m.index is not None
               and m.index < participle.index < noun.index for m in noun.modifiers)


def detect_ablative_absolute(nodes, trace):
    """独立奪格: 奪格の分詞と、格・数・性の一致する奪格の名詞 (前3語以内、または直後)。
    名詞の直前が奪格を支配する前置詞なら前置詞句 (cum hīs rēbus cognitīs) なので対象外"""
    absolutes = []
    i = 0
    while i < len(nodes):
        participle = _abl_participle_tuples(nodes[i])
        if not participle:
            i += 1
            continue
        subject_ix = None
        for j in range(i - 1, max(-1, i - 4), -1):
            if _is_clause_boundary(nodes[j]) and not (isinstance(nodes[j], Word) and nodes[j].items and
                                                      nodes[j].items[0].pos == 'preposition'):
                break
            if _agrees(_abl_tuples(nodes[j]), participle):
                subject_ix = j
                break
        if subject_ix is not None and _governed_by_abl_preposition(nodes, subject_ix):
            subject_ix = None
        if subject_ix is None and i + 1 < len(nodes) and _agrees(_abl_tuples(nodes[i + 1]), participle) \
                and not _governed_by_abl_preposition(nodes, i):
            subject_ix = i + 1  # 分詞が先: dīmissō conciliō
        if subject_ix is None:
            i += 1
            continue
        # 動形容詞 (grātiā referendā) は独立奪格にしない。
        # 形容詞になった現在分詞 (ingeniō excellentī, aquā prōfluente) は、節の途中にあれば名詞の修飾語として残す
        # (主語が代名詞・指示詞なら独立奪格: eō absente)。完了分詞にも同じ判定をすると、UD Latin-PROIEL の
        # カエサルで本物の独立奪格 (hīs rēbus acceptīs, equō incitātō) まで外れて再現率が下がるので、しない
        at_clause_start = min(subject_ix, i) == 0 or _is_clause_boundary(nodes[min(subject_ix, i) - 1])
        latin = language.current().name == 'la'  # ラテン語の語形・語彙による規則
        if (latin and (_is_gerundive(nodes[i]) or _not_absolute_form(nodes[i]) or
                       _usually_modified(nodes[subject_ix], nodes[subject_ix + 1:i]) or
                       (participle_kind(nodes[i]) == 'present' and _is_lexicalized_participle(nodes[i])
                        and not _is_pronominal(nodes[subject_ix]) and not at_clause_start))) or \
                _in_attributive_position(nodes[subject_ix], nodes[i]) or _governed_by_main_verb(nodes, i):
            trace.append("// not ABL.ABS: %s %s" % (nodes[subject_ix].surface, nodes[i].surface))
            i += 1
            continue
        start, end = min(subject_ix, i), max(subject_ix, i)
        complements = nodes[subject_ix + 1:i] if subject_ix < i else []
        complements = [c for c in detect_prep_domination(list(complements)) if c]
        absolute = AblativeAbsolute(nodes[subject_ix], nodes[i], complements)
        trace.append("// ABL.ABS #%d..#%d (%s)" % (start, end, absolute.surface))
        nodes[start:end + 1] = [absolute]
        absolutes.append(absolute)
        i = start + 1
    return nodes, absolutes


def _participle_tuples(node):
    """分詞として読める語 (タガーの判定を優先して、最初の候補が分詞のもの) の (格, 数, 性)。
    副詞・接続詞などとしても読める語 (ita「このように」と eō の分詞 itus) は除く"""
    if not isinstance(node, Word) or not node.items or node.items[0].pos != 'participle':
        return []
    if any(item.pos in ('adv', 'conj', 'preposition', 'pronoun') for item in node.items):
        return []
    return [cng for item in node.items if item.pos == 'participle' for cng in (item._ or [])]


def _nominal_tuples(node):
    """名詞・代名詞 (並列句を含む) として読める要素の (格, 数, 性)"""
    if isinstance(node, AndOr):
        return list(node._ or []) if node.pos in ('noun', 'pronoun') else []
    if not isinstance(node, Word) or not node.items:
        return []
    return [cng for item in node.items if item.pos in ('noun', 'pronoun') for cng in (item._ or [])]


def _is_sum_word(node):
    return isinstance(node, Word) and bool(node.items) and node.items[0].pos == 'verb' and \
        language.current().is_copula(node.items[0].attrib('pres1sg'))


def _finite_verb_numbers(nodes):
    return {item.attrib('number') for node in nodes if isinstance(node, Word) and node.items
            for item in node.items[:1] if item.pos == 'verb' and item.attrib('mood') != 'infinitive'}


def _participle_complements(nodes, i, active):
    """分詞の前にある補語の始まりの位置と、一致する名詞 (掛かり先) の位置。
    対格 (能動の分詞だけ)・奪格・与格・属格の名詞、前置詞、直前の副詞を補語として前へたどる"""
    participle = _participle_tuples(nodes[i])
    start, head = i, None
    for j in range(i - 1, max(-1, i - 6), -1):
        node = nodes[j]
        if isinstance(node, Word) and node.items and node.items[0].pos == 'preposition':
            start = j
            continue
        if _is_clause_boundary(node):
            # 挿入句: Rēgīna, verbīs nūntiī commōta, lacrimāvit
            if isinstance(node, Word) and node.surface == ',' and j > 0 and \
                    _agrees(_nominal_tuples(nodes[j - 1]), participle):
                head = j - 1
            break
        nominal = _nominal_tuples(node)
        if _agrees(nominal, participle):
            head = j
            break
        cases = {case for case, _, _ in nominal}
        if nominal and ((active and 'Acc' in cases) or cases & {'Abl', 'Dat', 'Gen'}):
            start = j
            continue
        if isinstance(node, PrepClause):
            start = j
            continue
        if isinstance(node, Word) and node.items and node.items[0].pos == 'adv' and j == i - 1:
            start = j  # 分詞の直前の副詞だけ (vehementer commōtus。文頭の tum などは主節に)
            continue
        break
    return start, head


def _attach_genitives(complements):
    """補語の中で名詞の直後にある属格 (verbīs nūntiī) をその名詞に付ける"""
    result = []
    for c in complements:
        prev = result[-1] if result else None
        if isinstance(prev, Word) and prev.items and prev.items[0].pos == 'noun' and isinstance(c, Word) \
                and c.items and c.items[0].pos == 'noun' and any(case == 'Gen' for case, _, _ in c.items[0]._ or []):
            prev.add_genitive(c)
            continue
        result.append(c)
    return result


def detect_participle_phrases(nodes, trace):
    """分詞句: 分詞とその前の補語をまとめる。
    主格で主語に一致する分詞 (掛かり先が主格の名詞、または主語が省略されていて動詞と数が一致) は述語的
    (Puella flōrēs carpēns cantat → 花を摘みながら)、ほかの格の名詞に一致するものは名詞の修飾語
    (hostem fugientem → 逃げている敵を)。sum と組む完了分詞 (laudātus est) は対象外"""
    phrases = []
    verb_numbers = _finite_verb_numbers(nodes)
    i = 0
    while i < len(nodes):
        participle = _participle_tuples(nodes[i])
        if not participle or (i + 1 < len(nodes) and _is_sum_word(nodes[i + 1])) or \
                (i > 0 and _is_sum_word(nodes[i - 1])):
            i += 1
            continue
        kind = participle_kind(nodes[i])
        start, head_ix = _participle_complements(nodes, i, kind != 'passive')
        if head_ix is None and start == i and i + 1 < len(nodes) and \
                _agrees(_nominal_tuples(nodes[i + 1]), participle):
            head_ix = i + 1  # 分詞が先: fugientem hostem
        if head_ix is not None:
            head_cases = {ca for ca, na, ga in _nominal_tuples(nodes[head_ix]) if _agrees([(ca, na, ga)], participle)}
            adverbial = 'Nom' in head_cases and 'Acc' not in head_cases and bool(verb_numbers)
        else:
            numbers = {n for case, n, _ in participle if case == 'Nom'}
            if not numbers & verb_numbers:
                i += 1
                continue  # 名詞として使われた分詞 (amāns「愛する人」) などはそのまま
            adverbial = True
        head = nodes[head_ix] if head_ix is not None else None
        if not adverbial and not isinstance(head, Word):
            i += 1
            continue
        complements = _attach_genitives([c for c in detect_prep_domination(list(nodes[start:i])) if c])
        phrase = ParticiplePhrase(nodes[i], complements, head, adverbial)
        trace.append("// PARTICIPLE #%d..#%d (%s)%s" % (
            start, i, phrase.surface,
            ' -> NOUN#%d (%s)' % (head_ix, head.surface) if head is not None else ''))
        if adverbial:
            nodes[start:i + 1] = [phrase]
            i = start + 1
        else:
            head.add_modifier(phrase)
            del nodes[start:i + 1]
            i = start
        phrases.append(phrase)
    return nodes, phrases


def detect_verbs(words):
    verb_ix = []

    for i, word in enumerate(words):
        if not isinstance(word, Word): continue  # 並列句・独立奪格など
        if not word.items: continue

        verb_items = [item for item in word.items if item.pos == 'verb']
#        print "\t%d) %s" % (i, word.surface_utf8()), verb_items
        if verb_items and len(verb_items) == len(word.items):
            verb = Predicate(word)
            words[i] = verb
            verb_ix.append(i)
#            print " [%d] %s (verb %d%s)" % (i, verb.surface.encode('utf-8'), verb.person(), verb.number())
            # この動詞に関わるものを拾って繋げたい
#            verbs_at.append(i)
#            verbs[i] = verb

    return (words, verb_ix)


# 名詞に係りうる代名詞 (限定詞としても使う): hic, is, ille, iste, ipse, aliquis, quīdam など
DETERMINER_PRONOUNS = ('指示代名詞', '強意代名詞', '不定代名詞', '不定形容詞')


def detect_adj_correspondances(words, trace, consumed=()):
    """consumed: 並列句に取り込まれて、まだ列に残っている語の位置 (Bonus et fortis vir の et, fortis)。
    並列した形容詞 (et Bonus et fortis) が係り先を探すときは、自分の後ろに残っているそれらの語を飛ばす
    (et を切れ目と見ないように。名詞の並列句の中の et は切れ目のまま: Rauracīs et Tulingīs et Latobrigīs fīnitimīs)"""
    M = len(words)
    nouns = {}
    adjs = []
    determiners = []  # 名詞に係りうる代名詞 (近くに一致する名詞があるときだけ付ける)
    blocks = {}
    verb_blocks = set()  # sum 以外の動詞 (2段目の探索では越えてよい)
    boundaries = set()   # 句読点・接続詞 (2段目の探索でも越えない)

    for i in range(M):
        word = words[i]
        if isinstance(word, Predicate):
            blocks[i] = word
        elif isinstance(word, AndOr):
            if word.pos == 'adj':
                # print "ADJ.", i, word._
                adjs.append((i, word._))
        elif isinstance(word, Word):
            if not word.items:
                if word.items is None and word.surface in (',', ';', ':'):
                    boundaries.add(i)
                continue
            if word.items[0].pos == 'conj':
                boundaries.add(i)
            if word.surface in _coordinators() or word.items[0].pos == 'preposition':
                blocks[i] = word
                continue

            first_item = word.items[0]
            if first_item.pos == 'verb':
                blocks[i] = word
                if not language.current().is_copula(first_item.attrib('pres1sg')):
                    verb_blocks.add(i)
                continue
            elif first_item.pos in ('adj', 'pp'):
                if getattr(word, 'attached_to', None) is not None:
                    continue  # 並列句の中ですでに修飾語として付けたもの
                adjs.append((i, first_item._))
            elif first_item.pos == 'pronoun' and first_item.attrib('desc') in DETERMINER_PRONOUNS:
                if getattr(word, 'attached_to', None) is None and first_item._:
                    determiners.append((i, first_item._))
            elif first_item.pos == 'noun':
                nouns[i] = first_item._
            else:
                pass
        else:
            # blocks[i] = word
            pass

    if not adjs and not determiners: return (words, [])

    def matches(_a, _b):
        return any([b in _a for b in _b])

    def find_target(adj_ix, a_):
        own = set()  # 並列した形容詞が取り込んだ、後ろに残っている語
        if isinstance(words[adj_ix], AndOr):
            j = adj_ix + 1
            while j in consumed:
                own.add(j)
                j += 1

        def sub(fr, to, step, transparent=()):
            for i in range(fr, to, step):
                if i in own:
                    continue
                if i in blocks and i not in transparent:
                    return -1
                if transparent and i in boundaries:
                    return -1
                if i not in nouns:
                    continue
                n_ = nouns[i]
                if matches(n_, a_):
                    return i
            return -1

        pre = sub(adj_ix-1, -1, -1)
        if pre >= 0: return pre

        post = sub(adj_ix+1, M, 1)
        if post >= 0: return post

        # 見つからなければ sum 以外の動詞を越えて探す
        # (templum ... aedificāvit plēnum dōnōrum。sum は越えない: Rōma est māgna の māgna は補語)
        pre = sub(adj_ix-1, -1, -1, verb_blocks)
        if pre >= 0: return pre

        return sub(adj_ix+1, M, 1, verb_blocks)

    as_noun = set()

    for adj_ix, _ in adjs:
        msg = "// ADJ#%d (%s)" % (adj_ix, words[adj_ix].surface_utf8())
        noun_ix = find_target(adj_ix, _)
        predicative = language.current().predicative_adjective
        if noun_ix >= 0 and predicative and predicative(words[adj_ix], words[noun_ix]):
            # 述語的位置の形容詞 (ギリシア語: ὁ υἱὸς μείζων ἐστί「息子は大きい」) は名詞に掛けない
            trace.append(msg + " -> predicative (NOUN#%d %s)" % (noun_ix, words[noun_ix].surface_utf8()))
            as_noun.add(adj_ix)
            continue
        if noun_ix >= 0:
            trace.append(msg + " -> NOUN#%d (%s)" % (noun_ix, words[noun_ix].surface_utf8()))
            words[noun_ix].add_modifier(words[adj_ix])
#            words[adj_ix] = None
        else:
            trace.append(msg + " -> no target noun detected")
            as_noun.add(adj_ix)

    # 指示詞などの代名詞: すぐ後ろ (間に1語まで) か、すぐ前の名詞で、格・数・性が一致するものにだけ付ける
    # (hīs rēbus, eō diē, ea rēs, diē eō。eōs vīdit のように単独で使われるものは付けない)
    def is_sum(ix):
        w = words[ix] if 0 <= ix < M else None
        return isinstance(w, Word) and bool(w.items) and w.items[0].pos == 'verb' and \
            language.current().is_copula(w.items[0].attrib('pres1sg'))

    attached_determiners = []
    for det_ix, _ in determiners:
        target = -1
        for j in (det_ix + 1, det_ix + 2, det_ix - 1):
            if not (0 <= j < M) or j in blocks:
                continue
            if j == det_ix - 1 and is_sum(det_ix + 1):
                continue  # magnitūdō eadem erit: 直後が sum なら補語 (前の名詞の修飾語にしない)
            if j == det_ix + 2 and (det_ix + 1) in blocks:
                continue
            if j in nouns and matches(nouns[j], _):
                target = j
                break
        if target >= 0:
            trace.append("// DET#%d (%s) -> NOUN#%d (%s)" % (
                det_ix, words[det_ix].surface_utf8(), target, words[target].surface_utf8()))
            words[target].add_modifier(words[det_ix])
            attached_determiners.append(det_ix)

    return (words, [ix for ix in [adj_ix for adj_ix, _ in adjs] if ix not in as_noun] + attached_determiners)


def _has_other_cases(word, case):
    return any(c != case for item in (getattr(word, 'items', None) or []) for c, _, _ in (item._ or []))


def _after_genitive_preposition(words, ix):
    """属格を支配する前置詞の後ろ (間に形容詞があってもよい) の語か"""
    for j in range(ix - 1, max(-1, ix - 4), -1):
        word = words[j]
        if not isinstance(word, Word) or not word.items:
            return False
        if any(item.pos == 'preposition' and item.dominates == 'Gen' for item in word.items):
            return True
        if word.items[0].pos not in ('adj', 'participle'):
            return False
    return False


def detect_genitive_correspondances(words, trace):
    M = len(words)
    targets = {}
    gen = []
    blocks = {}

    for i in range(M):
        word = words[i]
        if isinstance(word, Predicate):
            pass #blocks[i] = word
        elif isinstance(word, AndOr):
            # targets[i] = word
            if word._ and not non_genitive(word._) and word._[0][0] == 'Gen':
                gen.append(i)
        elif isinstance(word, Word):
            if not word.items:
                blocks[i] = word
                continue

            first_item = word.items[0]
            if word.surface in _coordinators() or first_item.pos == 'preposition':
                blocks[i] = word
                continue
            if first_item.pos == 'verb' and (language.current().genitive_follows_head or language.current().genitive_precedes_head):
                blocks[i] = word  # 動詞を越えて掛けない (рефери дисквалифицировал Диксона: 対格の Диксона)
                continue
            if first_item.pos == 'adj' and first_item.attrib('base') == 'plēnus':
                targets[i] = word
                continue

            if first_item.pos != 'noun':
                continue

            targets[i] = word
            if first_item._ and not non_genitive(first_item._) and first_item._[0][0] == 'Gen':
                gen.append(i)
        else:
            # blocks[i] = word
            pass

    if not gen: return (words, [])

#    print "non-Gen:", [(ix, word.surface_utf8()) for ix,word in targets.items()]
#    print "    Gen:", gen

    def find_target(gen_ix):
        def sub(fr, to, step):
            for i in range(fr, to, step):
                if i in blocks:
                    return -1
                if i not in targets:
                    continue
                return i
            return -1

        if language.current().genitive_precedes_head:
            return sub(gen_ix+1, M, 1)  # 後ろの名詞にだけ掛ける
        pre = sub(gen_ix-1, -1, -1)
        if pre >= 0: return pre
        if language.current().genitive_follows_head:
            return -1  # 後ろの名詞には掛けない

        post = sub(gen_ix+1, M, 1)
        if post >= 0: return post

        return -1

    gen.sort(reverse=True)

    non_gen = set()

    for gen_ix in gen:
        msg = "// GEN#%d (%s)" % (gen_ix, words[gen_ix].surface_utf8())
        keep = language.current().keep_genitive
        if keep and keep(words, gen_ix):
            # 名詞に掛けずに述語の枠に残す属格 (ギリシア語の比較の属格: μείζων τοῦ πατρός「父より大きい」)
            trace.append(msg + " -> kept for the predicate")
            non_gen.add(gen_ix)
            continue
        target_ix = find_target(gen_ix)
        if target_ix >= 0:
            trace.append(msg + " -> TARGET#%d (%s)" % (target_ix, words[target_ix].surface_utf8()))
            words[target_ix].add_genitive(words[gen_ix])
#            words[gen_ix] = None
        else:
            trace.append(msg + " -> no target noun detected")
            non_gen.add(gen_ix)
            # 係り先の無い属格は、ほかの格としても読めるならそちらに (nautae: 属格・与格・主格)。
            # ギリシア語では属格としてしか読めない語は属格のまま残す (動詞の目的語: ἤκουσα τοῦ ἀνθρώπου)
            # 属格を支配する前置詞の後ろの属格 (ロシア語の от соседей「隣人から」) はそのまま
            if _after_genitive_preposition(words, gen_ix):
                continue
            if language.current().name == 'la' or _has_other_cases(words[gen_ix], 'Gen'):
                words[gen_ix].restrict_cases(('Nom','Voc','Acc','Dat','Abl','Loc'))

    return (words, [ix for ix in gen if ix not in non_gen])


def _group_by_verbs(words, verbs_ix, trace):
    """動詞が複数あるとき、語を動詞ごとのグループに分ける"""
    M = len(words)
    verb_count = len(verbs_ix)
    if verb_count <= 1:
        return [list(range(M))]

    groups = []
    groups.append(list(range(verbs_ix[0]+1)))  # [0..ix0]
    for i in range(1, verb_count-1):
        groups.append([verbs_ix[i]])
    groups.append(list(range(verbs_ix[verb_count-1], M)))
    for i in range(verb_count-1):
        fr = groups[i][-1] + 1
        to = groups[i+1][0] - 1
        if fr > to: continue
        if fr == to:
            # 動詞の間の1語: 目的語が動詞の後ろに来る言語 (ロシア語・ヘブライ語) は前の動詞に、ほかは後ろの動詞に
            # (以前はどちらにも入らず落ちていた: וַיֹּאמֶר אֱלֹהִים יְהִי אוֹר の אֱלֹהִים)
            if language.current().objects_follow_verb:
                groups[i].append(fr)
            else:
                groups[i+1] = [fr] + groups[i+1]
            continue

        well_divided_at = None
        for j in range(fr, to+1):
            if words[j].surface == ',':
                well_divided_at = j
                break
        if well_divided_at is None:
            for j in range(fr, to+1):
                if isinstance(words[j], Word) and is_relative(words[j]) and j > fr:
                    well_divided_at = j-1   # 関係代名詞は後ろの動詞の節の頭 (erant quīdam | quī īnsulam … incolēbant)
                    break
        if well_divided_at is None:
            for j in range(fr, to+1):
                if words[j].surface == 'quod':
                    well_divided_at = j-1
                    break
        if well_divided_at is None:
            for j in range(fr, to+1):
                if words[j].surface in language.current().and_words:
                    well_divided_at = j-1
                    break
        if well_divided_at is None and language.current().objects_follow_verb:
            # 接続詞の前で分ける (но, а)。無ければ前の動詞に (目的語は動詞の後ろ)
            well_divided_at = next((j - 1 for j in range(fr, to + 1) if isinstance(words[j], Word)
                                    and words[j].items and words[j].items[0].pos == 'conj'), to)
        if well_divided_at is not None:
            groups[i] += list(range(fr, well_divided_at+1))
            groups[i+1] = list(range(well_divided_at+1, to+1)) + groups[i+1]
        else:
            trace.append("  NOT WELL: {%d..%d}" % (fr, to))
            # うまく分けられない。とりあえず後の方に入れる
            groups[i+1] = list(range(fr, to+1)) + groups[i+1]
    return groups


DETERMINER_BASES = {'hic', 'is', 'ille', 'iste', 'ipse', 'īdem', 'idem', 'quīdam', 'aliquis'}


def _is_same(item):
    """īdem (同じ): sum の文では補語になりやすい"""
    return item.attrib('base') in ('īdem', 'idem') or item.ja == '同じ'


def _span(node):
    """語・並列句の位置 (最初と最後の語の index)。分からなければ (None, None)"""
    if isinstance(node, AndOr):
        indices = [w.index for words in node.words_slots for w in words
                   if isinstance(w, Word) and w.index is not None]
        return (min(indices), max(indices)) if indices else (None, None)
    index = getattr(node, 'index', None)
    return index, index


def _promote_complement(pred):
    """sum の文で補語が無く、主語の名詞に修飾語が付いているとき、その1つを補語に戻す
    (Rōma māgna est → ローマは大きい。所有形容詞・指示詞は修飾語のまま: hic puer bonus est)"""
    noms = pred.case_slot.get('Nom', []) + pred.case_slot.get('Nom/Acc', [])
    nouns = [o for o in noms if isinstance(o, Word) and o.items and o.items[0].pos in ('noun', 'pronoun')]
    if len(nouns) != 1 or len(noms) != 1:
        return  # すでに補語らしきもの (名詞以外・2つ目の名詞) がある
    subject = nouns[0]
    adjectives, sames = [], []
    for m in subject.modifiers:
        if isinstance(m, AndOr) and m.pos == 'adj':
            adjectives.append(m)  # 並列した形容詞 (via longa et lāta est)
            continue
        if not isinstance(m, Word) or not m.items:
            continue
        item = m.items[0]
        if _is_same(item):
            sames.append(m)
        elif item.pos in ('adj', 'participle') and item.attrib('desc') != '所有形容詞' \
                and item.attrib('base') not in DETERMINER_BASES:
            adjectives.append(m)
    # 主語の名詞と隣り合う形容詞は、名詞 形容詞 sum の順 (agricola laetus est「農夫はうれしい」) なら補語とみなす。
    # 形容詞 名詞 sum の順 (magnus vir est) は1つの名詞句として「偉大な男である」。主語が固有名詞なら常に補語。
    # (名詞の側が補語で主語が省略された vir māgnus erit「(彼は) 偉大な男になるだろう」は区別できず、補語は形容詞になる)
    base = subject.items[0].attrib('base') or subject.surface
    proper = base[:1].isupper()

    def separated(m):
        first, _ = _span(m)
        return first is None or subject.index is None or abs(first - subject.index) > 1

    negations = {w.index for w in pred.modifiers if isinstance(w, Word) and language.current().is_negation(w.surface)}

    def before_sum(m):
        # 名詞 形容詞 (nōn) sum の順
        first, last = _span(m)
        if first is None or subject.index is None or pred.verb.index is None:
            return False
        return first == subject.index + 1 and last < pred.verb.index \
            and set(range(last + 1, pred.verb.index)) <= negations

    candidates = [m for m in adjectives if proper or separated(m) or before_sum(m)] or sames
    if not candidates:
        return
    complement = max(candidates, key=lambda w: _span(w)[0] if _span(w)[0] is not None else -1)  # 最も後ろの語
    subject.modifiers.remove(complement)
    complement.attached_to = None
    case = 'Nom' if 'Nom' in pred.case_slot else 'Nom/Acc'
    pred.add_nominal(case, complement)


def _is_infinitive(node):
    return isinstance(node, Predicate) and node.mood() == 'infinitive'


def _only_nominative(node):
    """主格としてしか読めない名詞・代名詞 (主節の主語。不定詞句には入れない)"""
    if isinstance(node, AndOr):
        cases = {case for case, _, _ in node._ or []}
    elif isinstance(node, Word) and node.items and node.items[0].pos in ('noun', 'pronoun', 'adj'):
        cases = {case for case, _, _ in node.items[0]._ or []}
    else:
        return False
    return bool(cases) and cases <= {'Nom', 'Voc'}


def _sort_by_position(nodes):
    return sorted(nodes, key=lambda n: _span(n)[0] if _span(n)[0] is not None else 10 ** 6)


def _is_coordination(node):
    """接続詞・句読点 (不定詞とそれを支配する動詞の間には来ないもの)"""
    if isinstance(node, Word):
        if node.items is None:
            return node.surface in PUNCTUATION
        return bool(node.items) and node.items[0].pos == 'conj'
    return False


def detect_infinitive_clauses(nodes, trace):
    """不定詞と、その前の語句 (主節の動詞・句読点・接続詞・主格の語の手前まで) を不定詞句にまとめる。
    言う・思う・見る・命じるなどの動詞に支配されるものは対格不定詞 (最初の対格が不定詞の主語)。
    sum の不定詞 (esse) なら対格はすべて主語・補語の枠に入れる (Rōmam magnam esse)"""
    finite = [i for i, n in enumerate(nodes) if isinstance(n, Predicate) and not _is_infinitive(n)]
    if not finite:
        return nodes, []
    clauses = []
    i = 0
    while i < len(nodes):
        if not _is_infinitive(nodes[i]):
            i += 1
            continue
        # 支配する動詞: 接続詞・句読点を挟まない、いちばん近い定動詞 (同じ距離なら前)
        finite = [k for k, n in enumerate(nodes) if isinstance(n, Predicate) and not _is_infinitive(n)
                  and not any(_is_coordination(nodes[m]) for m in range(min(k, i) + 1, max(k, i)))]
        if not finite:
            i += 1
            continue
        governor_ix = min(finite, key=lambda k: (abs(k - i), k > i))
        governor = nodes[governor_ix]
        kind = governor_kind(governor.first_item.attrib('pres1sg'))
        if kind is None and not governor.is_sum and \
                any(item.attrib('mood') == 'imperative' for item in nodes[i].verb.items):
            i += 1
            continue  # 命令法とも読める形 (miserēre) で、支配する動詞も分からない
        start = i
        for j in range(i - 1, -1, -1):
            node = nodes[j]
            if isinstance(node, Predicate) or _only_nominative(node):
                break
            if isinstance(node, Word) and (node.items is None or (node.items and node.items[0].pos == 'conj')):
                break  # 句読点・接続詞
            start = j
        inf = nodes[i]
        inf.subordinate = True
        not_solved = _attach_to_predicate(nodes, list(range(start, i + 1)), i)
        # 句の中の主格は主格としてしか読めない語を除いてあるので、対格と読む (hostēs: Nom/Acc)
        accs = _sort_by_position(inf.case_slot.pop('Acc', []) + inf.case_slot.pop('Nom/Acc', []) +
                                 inf.case_slot.pop('Nom', []))
        two_accs = len(accs) >= 2 and not inf.is_sum
        passive = inf.first_item.attrib('voice') == 'passive'
        # 命じる動詞で対格が1つだけなら、不定詞の目的語と読む (obsidēs dare iussit)。受動の不定詞なら主語
        single_ok = kind != 'command' or passive
        if accs and ((takes_accusative_subject(kind) and (single_ok or two_accs)) or two_accs or passive and kind
                     or inf.is_sum and kind is not None):
            if inf.is_sum:
                subjects, accs = accs, []  # Rōmam magnam esse: 主語と補語
            else:
                # 再帰代名詞 sē があればそれが主語 (dīxit sē castra posuisse)
                reflexive = [a for a in accs if isinstance(a, Word) and a.surface.lower() in ('sē', 'se', 'sēsē')]
                subject = reflexive[0] if reflexive else accs[0]
                subjects, accs = [subject], [a for a in accs if a is not subject]
            inf.case_slot['Nom'] = inf.case_slot.get('Nom', []) + subjects
            if inf.is_sum:
                _promote_complement(inf)
        if accs:
            inf.case_slot['Acc'] = accs
        clause = InfinitiveClause(inf, governor, kind)
        trace.append("// INF #%d..#%d (%s) <- VERB#%d (%s) [%s]" % (
            start, i, ' '.join(n.surface for n in nodes[start:i + 1]), governor_ix, governor.surface, kind))
        nodes[start:i + 1] = not_solved + [clause]
        clauses.append(clause)
        i = start + len(not_solved) + 1
    return nodes, clauses


def _nodes_in(predicate, extra=()):
    """述語の節の中の語 (格の枠・修飾語・不定詞句の中・結びつかなかった語) をたどる"""
    stack = list(extra) + list(predicate.modifiers) + [predicate.conjunction]
    for objs in predicate.case_slot.values():
        stack.extend(objs)
    while stack:
        node = stack.pop()
        if node is None:
            continue
        yield node
        if isinstance(node, InfinitiveClause):
            stack.extend(_nodes_in(node.predicate))
        elif isinstance(node, PrepClause):
            stack.extend(node.words)
        elif isinstance(node, AndOr):
            stack.extend(w for words in node.words_slots for w in words)


def _relative_with_antecedent(word, words_by_index):
    """関係代名詞にも読める語で、すぐ前の語が性・数の一致する名詞なら先行詞のある関係代名詞"""
    relatives = [item for item in word.items if item.attrib('desc') == '関係代名詞' and item._]
    before = words_by_index.get(word.index - 1) if word.index else None
    if not relatives or before is None or not before.items:
        return False
    nouns = [item for item in before.items if item.pos in ('noun', 'pronoun') and item._]
    return any((n, g) == (n2, g2) or g2 == 'c' for r in relatives for _, n, g in r._
               for noun in nouns for _, n2, g2 in noun._)


def detect_indirect_questions(clauses, trace):
    """間接疑問: 疑問詞を含み動詞が接続法の節を、隣の節の「問う・知る・教える・言う」動詞の格の枠 'Q' に入れる。
    節が et などで始まれば前の節と並列なので、支配する動詞は後ろの節 (…, et quid fierī vellet docuit)、
    ほかは前の節を先に見る (rogāvit quid vellet)"""
    out = list(clauses)
    questions = []
    words_by_index = {}
    for c in clauses:
        for n in _nodes_in(c.predicate, c.not_solved):
            if isinstance(n, Word) and n.index is not None:
                words_by_index[n.index] = n
    for q in list(clauses):
        pred = q.predicate
        if pred.first_item.attrib('mood') != 'subjunctive':
            continue
        word = next((n for n in _nodes_in(pred, q.not_solved) if isinstance(n, Word) and is_interrogative(n)), None)
        if word is None or _relative_with_antecedent(word, words_by_index):
            continue   # 先行詞のある関係代名詞 (hominem quem ōrāculum dēmōnstrāvisset) は間接疑問ではない
        k = out.index(q)
        coordinated = pred.conjunction is not None and pred.conjunction.surface in language.current().and_words
        neighbors = [k + 1, k - 1] if coordinated else [k - 1, k + 1]
        for g in neighbors:
            if not 0 <= g < len(out):
                continue
            # 支配する動詞: 隣の節の述語か、その中の不定詞 (nē … cōgnōscere posset quō in locō …)
            candidates = [out[g].predicate] + [i.predicate for i in out[g].predicate.case_slot.get('Inf', [])]
            governor = next((c for c in candidates if c.first_item.attrib('pres1sg') in QUESTION_VERBS), None)
            if governor is None:
                continue
            question = QuestionClause(pred, governor, word)
            pred.subordinate = True
            if coordinated and g > k and governor.conjunction is None:
                governor.conjunction, pred.conjunction = pred.conjunction, None   # et は支配する動詞の節へ
            governor.add_nominal('Q', question)
            out[g].not_solved.extend(q.not_solved)
            out.remove(q)
            questions.append(question)
            trace.append('// QUESTION %s (%s) <- VERB %s' % (pred.surface, word.surface, governor.surface))
            break
    return out, questions


RELATIVE_ADVERBS = {'ubi': 'Loc', 'unde': 'Abl', 'quō': 'Acc'}   # 名詞のすぐ後ろの関係の副詞と、空所の役割


def _relative_pronoun(pred, not_solved):
    """関係節の関係代名詞と、節の中での役割 (格の枠の名前、前置詞句なら前置詞句そのもの)"""
    for case, objs in pred.case_slot.items():
        for obj in objs:
            if isinstance(obj, Word) and is_relative(obj):
                return obj, case, obj
            if isinstance(obj, PrepClause) and len(obj.words) == 1 and is_relative(obj.words[0]):
                return obj.words[0], case, obj   # in quō、cum quibus: 前置詞句ごと空所に
    for obj in not_solved:
        if isinstance(obj, Word) and is_relative(obj):
            item = next(i for i in obj.items if i.attrib('desc') == '関係代名詞')
            return obj, (item._[0][0] if item._ else 'Nom'), None
    adverb = pred.conjunction if isinstance(pred.conjunction, Word) else None
    if adverb is not None and adverb.surface.lower() == 'ubi':
        return adverb, RELATIVE_ADVERBS['ubi'], 'conjunction'   # ubi「〜するところの」(場所の空所)
    return None, None, None


def _antecedent(pronoun, words_by_index, adverb=False):
    """関係代名詞の前の、性・数の一致する名詞。句読点・前置詞の語は飛ばして6語まで。
    関係の副詞 ubi は、前の名詞 (間に動詞が1つあってもよい。句読点を挟まない: ad eum locum vēnit ubi …)"""
    if adverb:
        for index in range(pronoun.index - 1, max(-1, pronoun.index - 3), -1):
            word = words_by_index.get(index)
            if word is None:
                return None   # 句読点 (時の ubi: …, ubi …)
            if word.items and word.items[0].pos == 'noun':
                return word
            if not (word.items and word.items[0].pos == 'verb'):
                return None
        return None
    readings = {(n, g) for item in pronoun.items if item.attrib('desc') == '関係代名詞' for _, n, g in item._ or []}
    for index in range(pronoun.index - 1, max(-1, pronoun.index - 7), -1):
        word = words_by_index.get(index)
        if word is None or not word.items:
            continue
        if word.items[0].pos == 'conj':
            return None   # 間に接続詞 (et quod … supererat の quod は「〜なので」)
        nouns = [item for item in word.items if item.pos in ('noun', 'pronoun') and item._ and
                 item.attrib('desc') != '関係代名詞']
        # 固有名詞は単数の読みだけ (Herculēs の複数の読みで quō 「どこで」に合わせない)
        if any((n, g) in readings for noun in nouns for _, n, g in noun._
               if n == 'sg' or not (noun.attrib('base') or '')[:1].isupper()):
            return word
    return None


COMPARISON_WORDS = {'magis', 'plūs', 'minus', 'potius', 'prius', 'tam', 'tantō', 'aliter', 'citius', 'saepius'}


def _comparative_quam(pronoun, words_by_index):
    """比較の quam「〜より」(clārior erat quam Hector): 前の8語に比較級・magis・tam などがある"""
    if pronoun.surface.lower() != 'quam':
        return False
    for index in range(pronoun.index - 1, max(-1, pronoun.index - 9), -1):
        word = words_by_index.get(index)
        if word is not None and (word.surface.lower() in COMPARISON_WORDS or
                                 any(item.attrib('rank') == '+' for item in word.items or [])):
            return True
    return False


def _first_word_index(node):
    """語・並列句・前置詞句の最初の語の位置"""
    if isinstance(node, Word):
        return node.index
    if isinstance(node, AndOr):
        return next((w.index for words in node.words_slots for w in words if isinstance(w, Word)), None)
    if isinstance(node, PrepClause):
        return next((w.index - 1 for w in node.words if isinstance(w, Word) and w.index is not None), None)
    return None


CORRELATIVES = {'is', 'ille', 'hic', 'hīc', 'iste', 'īdem', 'ipse'}


def _agreeing_gender(pronoun, antecedent):
    """関係代名詞と先行詞の一致する性 (ea quae …: 中性複数)"""
    readings = {(n, g) for item in pronoun.items if item.attrib('desc') == '関係代名詞' for _, n, g in item._ or []}
    return next((g for item in antecedent.items if item._ for _, n, g in item._ if (n, g) in readings), None)


def _antecedent_after(pronoun, clause):
    """関係節が先行詞より前に来る形の先行詞: 後ろの節の語のうち位置の早い6語までの、性・数の一致する指示代名詞
    (is, ille, hic …: Quem puella amat, eum magister laudat の eum)"""
    readings = {(n, g) for item in pronoun.items if item.attrib('desc') == '関係代名詞' for _, n, g in item._ or []}
    words = sorted((n for n in _nodes_in(clause.predicate, clause.not_solved)
                    if isinstance(n, Word) and n.items and n.index is not None and n.index > pronoun.index),
                   key=lambda w: w.index)[:6]

    def agrees(word, demonstrative):
        for item in word.items:
            is_demonstrative = item.attrib('desc') == '指示代名詞' or \
                (item.attrib('base') or '') in CORRELATIVES
            if item.pos in ('noun', 'pronoun') and item._ and is_demonstrative == demonstrative and \
                    item.attrib('desc') != '関係代名詞' and any((n, g) in readings for _, n, g in item._):
                return True
        return False
    # 名詞は先行詞にしない (疑問の Quae īnsulae … Trōjam oppūgnāvērunt? の後ろの文の名詞を拾わないように)
    return next((w for w in words if agrees(w, True)), None)


def _gap_by_agreement(pronoun, antecedent, pred):
    """格の枠に入っていない関係代名詞の役割: 先行詞と性・数の一致する読みの格のうち、節に主語が無ければ主格、
    目的語が無ければ対格 (Puella cantat quae in hortō sedet の quae: 主格)"""
    nouns = {(n, g) for item in antecedent.items if item._ for _, n, g in item._}
    cases = [c for item in pronoun.items if item.attrib('desc') == '関係代名詞' for c, n, g in item._ or []
             if (n, g) in nouns]
    numbers = {n for item in pronoun.items if item.attrib('desc') == '関係代名詞' for c, n, g in item._ or []
               if (n, g) in nouns and c == 'Nom'}
    if pred.person() in (1, 2) or (pred.number() and numbers and pred.number() not in numbers):
        # 動詞が1・2人称、数が合わない: 関係代名詞は主語でない (Quae dīxistī「あなたが言ったこと」)
        cases = [c for c in cases if c != 'Nom']
    if not cases:
        # 解析の途中で格の候補が絞られて先行詞と合う読みが残っていない: 節に主語が無ければ主格 (いちばん多い)
        return 'Nom' if not pred.case_slot.get('Nom') else 'Acc'
    for case, slot in (('Nom', 'Nom'), ('Acc', 'Acc')):
        if case in cases and not pred.case_slot.get(slot):
            return case
    return cases[0] if cases else 'Nom'


def detect_relative_clauses(clauses, trace):
    """関係節: 関係代名詞を含む節を、前にある性・数の一致する名詞 (先行詞) の Word.relatives に付ける。
    関係代名詞は節の格の枠から外し、その役割を空所 (gap) として持つ。
    (関係節が先行詞より前に来るもの (quī …, is …)、先行詞の省かれたものは扱わない)"""
    out = list(clauses)
    relatives = []
    words_by_index = {}
    for c in clauses:
        for n in list(_nodes_in(c.predicate, c.not_solved)) + [c.predicate.verb]:
            if isinstance(n, Word) and n.index is not None:
                words_by_index.setdefault(n.index, n)
    for q in list(clauses):
        pred = q.predicate
        pronoun, gap, slot_obj = _relative_pronoun(pred, q.not_solved)
        if pronoun is None or pronoun.index is None or _comparative_quam(pronoun, words_by_index):
            continue
        antecedent = _antecedent(pronoun, words_by_index, adverb=slot_obj == 'conjunction')
        k = out.index(q)
        before = antecedent is None   # 関係節が先行詞より前 (相関の形)
        if antecedent is None and slot_obj != 'conjunction' and k + 1 < len(out) and pred.person() not in (1, 2):
            # 先行詞より前の関係節 (相関の形): 後ろの節の頭の指示代名詞 (Quī bene cantat, is laudātur)。
            # 動詞が1・2人称なら先行詞は話し手・聞き手で省かれている (quī sedēs ad dextram Patris, miserēre nōbīs)
            antecedent = _antecedent_after(pronoun, out[k + 1])
        if antecedent is None:
            continue
        if slot_obj is None:
            gap = _gap_by_agreement(pronoun, antecedent, pred)
        if any(n is antecedent for n in _nodes_in(pred, q.not_solved)):
            # 先行詞が関係節の語として付いていた: 後ろに節があればそこへ (…, et nautae, quī …, nāvem appulērunt)、
            # 無ければ前の節へ (Hīc est locus in quō …)
            finite = [t for t in (k + 1, k - 1) if 0 <= t < len(out) and
                      any(item.attrib('mood') != 'infinitive' for item in out[t].predicate.verb.items)]
            if not finite:
                continue   # 不定詞の節には入れない (poterant iī quī … relictī erant lacrimās tenēre)
            target = finite[0]
            # 先行詞と、関係代名詞より前の語 (Domine Deus, Agnus Dei, Fīlius Patris, quī tollis … の呼びかけ) を移す
            for case in list(pred.case_slot):
                moving = [o for o in pred.case_slot[case]
                          if o is not slot_obj and o is not pronoun and
                          (o is antecedent or (_first_word_index(o) is not None and
                                               _first_word_index(o) < pronoun.index))]
                if moving:
                    pred.case_slot[case] = [o for o in pred.case_slot[case] if not any(o is m for m in moving)]
                    if not pred.case_slot[case]:
                        del pred.case_slot[case]
                    for o in moving:
                        out[target].predicate.add_nominal(case, o)
            if antecedent in q.not_solved:
                q.not_solved.remove(antecedent)
        if not before and slot_obj != 'conjunction' and pred.conjunction is not None and k + 1 < len(out):
            # 関係節の節にまとめられていた接続詞は後ろの主節のもの (et arcum, quem … attulerat, intendit)。
            # 主節の conjunction に副詞 (posteā) が入っていれば修飾語へ移す (et pellem, quam …, posteā gerēbat)
            main = out[k + 1].predicate
            if main.conjunction is not None and main.conjunction.items and main.conjunction.items[0].pos == 'adv':
                main.add_modifier(main.conjunction)
                main.conjunction = None
            if main.conjunction is None:
                main.conjunction, pred.conjunction = pred.conjunction, None
        if not before and slot_obj != 'conjunction' and pred.conjunction is not None and \
                not (pred.conjunction.items and pred.conjunction.items[0].pos == 'adv'):
            # 後ろに節が無ければ先行詞のある節へ (Cyclōpēs autem pāstōrēs erant quīdam quī … incolēbant)
            owner = next((c.predicate for c in out if c is not q and
                          any(n is antecedent for n in _nodes_in(c.predicate, c.not_solved))), None)
            if owner is not None and owner.conjunction is None:
                owner.conjunction, pred.conjunction = pred.conjunction, None
        if isinstance(pronoun, Word) and slot_obj != 'conjunction':
            # 関係代名詞に係っていた語は節に戻す (quem lōtum appellābant の lōtum: 二重対格の補語)
            for attached in pronoun.modifiers + pronoun.genitives:
                cases = [c for item in getattr(attached, 'items', None) or [] if item._ for c, _, _ in item._]
                pred.add_nominal(gap if gap in cases or not cases else cases[0], attached)
            pronoun.modifiers, pronoun.genitives = [], []
        if slot_obj == 'conjunction':
            pred.conjunction = None
        elif slot_obj is not None:
            pred.case_slot[gap] = [o for o in pred.case_slot.get(gap, []) if o is not slot_obj]
            if not pred.case_slot[gap]:
                del pred.case_slot[gap]
        else:
            q.not_solved.remove(pronoun)
        if gap in ('Nom', 'Acc', 'Nom/Acc') and slot_obj is not None:
            # 主格・対格の両方に読める関係代名詞 (quae) は、解析で付いた枠より先行詞との一致と節の空きで決める
            gap = _gap_by_agreement(pronoun, antecedent, pred)
        if isinstance(gap, tuple) and slot_obj not in (None, 'conjunction'):
            gap = (gap, slot_obj)   # 前置詞句: (('prep', 'in'), PrepClause)
        pred.subordinate = True
        pred.gap = gap if not isinstance(gap, tuple) else gap[0]
        relative = RelativeClause(pred, antecedent, pronoun, gap)
        relative.gender = _agreeing_gender(pronoun, antecedent)
        antecedent.relatives.append(relative)
        out.remove(q)
        for c in out:   # 結びつかなかった語は先行詞のある節へ
            if any(n is antecedent for n in _nodes_in(c.predicate, c.not_solved)):
                c.not_solved.extend(q.not_solved)
                break
        relatives.append(relative)
        trace.append('// RELATIVE %s (%s) -> %s' % (pred.surface, pronoun.surface, antecedent.surface))
    return out, relatives


def _agreeing_with_verb(cngs, pred):
    """主格の読みのうち、3人称の動詞と数の合わないものを除く (Puellae est rosa の puellae は主格複数でなく与格単数。
    vane siṃhaḥ asti の vane は主格双数でなく処格)。合う読みが残らなければそのまま。
    単数の動詞1つに主語が並ぶ文 (nōn herba …, nōn ūvae …, nōn frūctūs erat) は見分けられない (近い主語に合わせた動詞)。
    ギリシア語の中性複数の主語は単数の動詞を取る (τὰ ζῷα τρέχει) ので除かない"""
    verb = pred.first_item
    number = verb.attrib('number')
    if number not in ('sg', 'pl', 'du') or verb.attrib('person') != 3 or verb.attrib('mood') == 'infinitive':
        return cngs

    def agrees(x):
        if x[0] not in ('Nom', 'Voc') or x[1] == number:
            return True  # 呼格も主格と同じ形なので、数の合わないものは一緒に除く (familia flēvērunt の「家族よ」)
        return language.current().name == 'grc' and x[1] == 'pl' and x[2] == 'n' and number == 'sg'
    kept = [x for x in cngs if agrees(x)]
    if pred.is_sum and all(x[0] in ('Acc', 'Voc') for x in kept):
        return cngs  # 繋辞の補語は数が合わなくてよい (flōrēs exemplum … sunt)。ほかの格の読みがあるときだけ除く
    return kept or cngs


def _attach_to_predicate(words, group, verb_ix):
    """グループ内の語を述語に結びつける。結びつけられなかった語のリストを返す"""
    not_solved = []
    pred = words[verb_ix]
    for j, ix in enumerate(group):
        if ix == verb_ix: continue
        word = words[ix]
        if isinstance(word, (AblativeAbsolute, ParticiplePhrase)):
            pred.add_subordinate(word)
        elif isinstance(word, InfinitiveClause):
            pred.add_nominal('Inf', word)
        elif isinstance(word, AndOr):
            if word.cases:
                pred.add_nominal(word.cases[0], word)
            else:
                not_solved.append(word)
        elif isinstance(word, PrepClause):
            pred.add_nominal(('prep', word.prep), word)
        elif isinstance(word, Word):
            if not word.items: continue
            first_item = word.items[0]
            if j == 0 and word.surface in ('quod', 'ut'):
                if len(word.items) > 1 and word.items[1].pos == 'conj':
                    first_item = word.items[1]
                    word.items = word.items[1:]
            if first_item.pos == 'conj':
                if j < 2 and not pred.conjunction:
                    pred.conjunction = word
                else:
                    not_solved.append(word)
            elif first_item.pos == 'adv':
                # 節の頭の副詞 (tum, deinde) は接続詞の枠に。2語の慣用句 (animō suspēnsō, quō pactō の
                # ような文頭のものを除く) は述語の修飾語として動詞の前に置く
                if j < 2 and not pred.conjunction and not language.current().is_negation(word.surface) \
                        and (' ' not in word.surface or j == 0):
                    pred.conjunction = word
                elif word.surface in language.current().vocative_particles:
                    # 二重になってないかチェックする or conjunction を複数取る
                    pred.conjunction = word
                else:
                    pred.add_modifier(word)
            elif first_item._:
                agreeing = _agreeing_with_verb(first_item._, pred)
                cases = [x[0] for x in agreeing]
                case = None
                if 'Voc' in cases and ix > 0 and words[ix-1].surface in language.current().vocative_particles:
                    case = 'Voc'
                    # 形的にVocしかありえないケースも拾いたい
                elif pred.is_sum and 'Nom' in cases and cases[0] in ('Nom', 'Acc'):
                    case = 'Nom'  # sum は対格を取らない (templum aureum est)。一番の読みが処格などの語は除く (vane「森に」)
                else:
                    cngs = agreeing
                    # 双数は、ほかの読みがあれば使わない (vane: 主格双数より処格単数)。
                    # 繋辞は対格を取らないので、ほかの読みがあれば対格は使わない (rājñaḥ putraḥ asti: 対格複数より属格単数)
                    if any(x[1] != 'du' for x in cngs):
                        cngs = [x for x in cngs if x[1] != 'du']
                    if pred.is_sum and any(x[0] != 'Acc' for x in cngs):
                        cngs = [x for x in cngs if x[0] != 'Acc']
                    if pred.is_sum:
                        # 繋辞の文では所有者の格を先に (rājñaḥ: 奪格より属格、Mārcō: 奪格より与格)
                        possessor = language.current().possessor_cases
                        cngs = sorted(cngs, key=lambda x: x[0] not in possessor)
                    for x in cngs:
                        if x[0] == 'Nom':
                            if x[2] == 'n':
                                case = 'Nom/Acc'
                            else:
                                case = x[0]
                            break
                        elif x[0] == 'Acc':
                            case = x[0]
                            break
                        else:
                            if not case:
                                case = x[0]
                pred.add_nominal(case, word)
            else:
                not_solved.append(word)
    if pred.is_sum:
        _promote_complement(pred)
    return not_solved


@dataclass
class Clause:
    """述語とそれに結びついた語。結びつけられなかった語は not_solved"""
    predicate: Predicate
    not_solved: list = field(default_factory=list)


@dataclass
class SentenceAnalysis:
    surfaces: list                  # 文の語 (表層形) の列
    words: list                     # 辞書引きの結果 (Word の列)
    word_details: list              # 辞書引き直後の各語の詳細 (構造化で絞り込まれる前)
    trace: list                     # 構造化の途中経過 (並列句・係り先の検出など)
    nodes: list                     # 構造化後の要素 (Word / AndOr / PrepClause / Predicate)
    verbs: list                     # 述語 (Predicate) の列
    grouping_trace: list            # 動詞ごとのグループ分けの途中経過
    clauses: list                   # 述語ごとの Clause。動詞がなければ空
    absolutes: list = field(default_factory=list)  # 独立奪格 (AblativeAbsolute)
    participles: list = field(default_factory=list)  # 分詞句 (ParticiplePhrase)
    infinitives: list = field(default_factory=list)  # 不定詞句 (InfinitiveClause)
    questions: list = field(default_factory=list)    # 間接疑問 (QuestionClause)
    relatives: list = field(default_factory=list)    # 関係節 (RelativeClause。先行詞の Word.relatives にも)

    @property
    def text(self):
        return ' '.join(self.surfaces)


def analyze_words(surfaces, words, word_details=None, trace=None):
    """辞書引き済みの語の列 (Word のリスト) を解析する。言語に依存しない部分 (ほかの言語の解析器からも使う)。
    すでに別の語の修飾語として付けた語 (attached_to のあるもの。ギリシア語の冠詞など) は、解析の対象から外す"""
    if word_details is None:
        word_details = [word.detail() for word in words]
    trace = [] if trace is None else trace

    # 並列句・形容詞/属格の係り先
    nodes, visited_ix = detect_and_or([w for w in words if getattr(w, 'attached_to', None) is None], trace)
    nodes, adj_ix = detect_adj_correspondances(nodes, trace, set(visited_ix))
    if language.current().absolute_case == 'Gen':
        # 属格独立 (ギリシア語) は、属格の係り先を決める前に探す (主語の属格を名詞の属格修飾にしないように)
        for ix in visited_ix + adj_ix:
            nodes[ix] = None
        nodes = [node for node in nodes if node]
        nodes, absolutes = detect_ablative_absolute(nodes, trace)
        nodes, gen_ix = detect_genitive_correspondances(nodes, trace)
        for ix in gen_ix:
            nodes[ix] = None
        nodes = [node for node in nodes if node]
    else:
        nodes, gen_ix = detect_genitive_correspondances(nodes, trace)
        for ix in visited_ix + adj_ix + gen_ix:
            nodes[ix] = None
        nodes = [node for node in nodes if node]
        nodes, absolutes = detect_ablative_absolute(nodes, trace)
    nodes, participles = detect_participle_phrases(nodes, trace)
    nodes, _verb_ix = detect_verbs(nodes)
    nodes = detect_prep_domination(nodes)
    nodes = [node for node in nodes if node]
    nodes, infinitives = detect_infinitive_clauses(nodes, trace)

    # 名詞句を述語動詞に結びつける
    verbs_ix = [i for i, node in enumerate(nodes) if isinstance(node, Predicate)]
    grouping_trace = []
    groups = _group_by_verbs(nodes, verbs_ix, grouping_trace)
    clauses = []
    if verbs_ix:
        for i, group in enumerate(groups):
            not_solved = _attach_to_predicate(nodes, group, verbs_ix[i])
            clauses.append(Clause(nodes[verbs_ix[i]], not_solved))
    clauses, questions = detect_indirect_questions(clauses, trace)
    clauses, relatives = detect_relative_clauses(clauses, trace)

    return SentenceAnalysis(
        surfaces=list(surfaces), words=words, word_details=word_details,
        trace=trace, nodes=nodes, verbs=[nodes[ix] for ix in verbs_ix],
        grouping_trace=grouping_trace, clauses=clauses, absolutes=absolutes, participles=participles,
        infinitives=infinitives, questions=questions, relatives=relatives)
