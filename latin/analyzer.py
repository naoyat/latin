#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ラテン語文の解析
#   語の列 → 辞書引き → 並列句・形容詞/属格の係り先・前置詞句・述語の検出
#   → 名詞句を述語の格スロットに割り当てる
#
# 結果は SentenceAnalysis で返す。表示は latin/render.py
#
import os
from dataclasses import dataclass, field

from . import latindic
from . import ldt
from . import rftagger
from . import latin_char as char
from . import textutil
from .Word import Word
from .Predicate import Predicate
from .AndOr import AndOr, non_genitive
from .PrepClause import PrepClause


def lookup_all(surfaces_uc):
    def lookup(surface, use_wiktionary=True):
        # 手作りの辞書 (そのまま → 小文字化 → -que を外す) → Wiktionary (同じ順) の順に引く
        sources = [latindic.lookup_hand]
        if use_wiktionary:
            sources.append(latindic.lookup_wiktionary)
        for source in sources:
            items = source(surface)
            if items: return Word(surface, items)
            if char.isupper(surface[0]):
                items = source(char.tolower(surface))
                if items: return Word(surface, items)
            if surface[-3:] == 'que':
                items = source(surface[:-3])
                if items:
                    return Word(surface, items, {'enclitic':'que'})
        return None

    words = []

    l = len(surfaces_uc)
    i = 0
    while i < l:
        surface = surfaces_uc[i]
        if ord(surface[0]) <= 64: # 辞書引き（記号のみから成る語を除く）
            words.append(Word(surface, None))
            i += 1
            continue
        if i < l-1:
            surface2 = surface + ' ' + surfaces_uc[i+1]
            # 2語の形 (amātus est など) は Wiktionary からは1語目が手作りの辞書に無いときだけ引く
            # (īgnōta erant が「赦されていた」になる、のような取り違えを避ける)
            word2 = lookup(surface2, use_wiktionary=lookup(surface, use_wiktionary=False) is None)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if word2 is not None: # len(word2.items) > 0: #is not None: and len(lu2) > 0:
                words.append(word2)
                i += 2
                continue
        word = lookup(surface)
        if word is not None:
            words.append(word)
        else:
            words.append(Word(surface, []))
        i += 1

    # words の中での添字情報をWordインスタンスに保存
    for i, word in enumerate(words):
        word.index = i

    return words


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
        while j < M:
            w = words[j]
            if isinstance(w, Word):
                if w.items is None:
                    j += 1
                    continue # while-j-loop
                stop = False
                for k, item in enumerate(w.items):
                    if item.pos in ['verb', 'preposition', 'conj', 'adv']:
                        stop = True
                        break # for-k-loop
                    if item._: # subst
                        if item.pos == 'adj':
                            continue # for-k-loop
                        can_skip = False
                        yes = False
                        for case, number, gender in item._:
                            if case == 'Gen':
                                can_skip = True
                            elif case in dominates:
                                dominates = [case] # 絞り込み
                                yes = True
                                break # for-cng-loop
                            else:
                                pass
                        if not yes and not can_skip:
                            stop = True
                            break # for-k-loop
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

    detect('et')
    detect('neque')

    detect('aut')

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
                cl = AndOr('et')
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
                cl = AndOr('et')
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
            cl = AndOr('et')
            cl.add([head1])
            cl.add([head2])
            trace.extend(cl.messages)
            for j in range(first, last+1):
                visited.add(j)
            words[first] = cl
            ao_loc.add(first)
            return True

        surface = word.surface
        if surface == 'et' and i+1 < len(words):
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


def detect_verbs(words):
    verb_ix = []

    for i, word in enumerate(words):
        if isinstance(word, AndOr): continue
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


def detect_adj_correspondances(words, trace):
    M = len(words)
    nouns = {}
    adjs = []
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
            if word.surface in ('et', 'neque') or word.items[0].pos == 'preposition':
                blocks[i] = word
                continue

            first_item = word.items[0]
            if first_item.pos == 'verb':
                blocks[i] = word
                if first_item.attrib('pres1sg') != 'sum':
                    verb_blocks.add(i)
                continue
            elif first_item.pos in ('adj', 'pp'):
                if getattr(word, 'attached_to', None) is not None:
                    continue  # 並列句の中ですでに修飾語として付けたもの
                adjs.append((i, first_item._))
            elif first_item.pos == 'noun':
                nouns[i] = first_item._
            else:
                pass
        else:
            # blocks[i] = word
            pass

    if not adjs: return (words, [])

    def matches(_a, _b):
        return any([b in _a for b in _b])

    def find_target(adj_ix, a_):
        def sub(fr, to, step, transparent=()):
            for i in range(fr, to, step):
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
        if noun_ix >= 0:
            trace.append(msg + " -> NOUN#%d (%s)" % (noun_ix, words[noun_ix].surface_utf8()))
            words[noun_ix].add_modifier(words[adj_ix])
#            words[adj_ix] = None
        else:
            trace.append(msg + " -> no target noun detected")
            as_noun.add(adj_ix)

    return (words, [ix for ix in [adj_ix for adj_ix, _ in adjs] if ix not in as_noun])


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
            if word.surface in ('et', 'neque') or first_item.pos == 'preposition':
                blocks[i] = word
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

        pre = sub(gen_ix-1, -1, -1)
        if pre >= 0: return pre

        post = sub(gen_ix+1, M, 1)
        if post >= 0: return post

        return -1

    gen.sort(reverse=True)

    non_gen = set()

    for gen_ix in gen:
        msg = "// GEN#%d (%s)" % (gen_ix, words[gen_ix].surface_utf8())
        target_ix = find_target(gen_ix)
        if target_ix >= 0:
            trace.append(msg + " -> TARGET#%d (%s)" % (target_ix, words[target_ix].surface_utf8()))
            words[target_ix].add_genitive(words[gen_ix])
#            words[gen_ix] = None
        else:
            trace.append(msg + " -> no target noun detected")
            non_gen.add(gen_ix)
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
        if fr == to: continue

        well_divided_at = None
        for j in range(fr, to+1):
            if words[j].surface == ',':
                well_divided_at = j
                break
        if well_divided_at is None:
            for j in range(fr, to+1):
                if words[j].surface == 'quod':
                    well_divided_at = j-1
                    break
        if well_divided_at is None:
            for j in range(fr, to+1):
                if words[j].surface == 'et':
                    well_divided_at = j-1
                    break
        if well_divided_at is not None:
            groups[i] += list(range(fr, well_divided_at+1))
            groups[i+1] = list(range(well_divided_at+1, to+1)) + groups[i+1]
        else:
            trace.append("  NOT WELL: {%d..%d}" % (fr, to))
            # うまく分けられない。とりあえず後の方に入れる
            groups[i+1] = list(range(fr, to+1)) + groups[i+1]
    return groups


def _attach_to_predicate(words, group, verb_ix):
    """グループ内の語を述語に結びつける。結びつけられなかった語のリストを返す"""
    not_solved = []
    pred = words[verb_ix]
    for j, ix in enumerate(group):
        if ix == verb_ix: continue
        word = words[ix]
        if isinstance(word, AndOr):
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
                if word.items[1].pos == 'conj':
                    first_item = word.items[1]
                    word.items = word.items[1:]
            if first_item.pos == 'conj':
                if j < 2 and not pred.conjunction:
                    pred.conjunction = word
                else:
                    not_solved.append(word)
            elif first_item.pos == 'adv':
                if j < 2 and not pred.conjunction:
                    pred.conjunction = word
                elif word.surface in ('ō', 'Ō'):
                    # 二重になってないかチェックする or conjunction を複数取る
                    pred.conjunction = word
                else:
                    pred.add_modifier(word)
            elif first_item._:
                cases = [x[0] for x in first_item._]
                case = None
                if 'Voc' in cases and ix > 0 and words[ix-1].surface in ('ō', 'Ō'):
                    case = 'Voc'
                    # 形的にVocしかありえないケースも拾いたい
                else:
                    for x in first_item._:
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

    @property
    def text(self):
        return ' '.join(self.surfaces)


# RFTagger の品詞タグで語の解釈を絞り込むか (環境変数 LATIN_TAGGER=0 で無効。RFTagger が無ければ使わない)
USE_TAGGER = os.environ.get('LATIN_TAGGER', '1') != '0'


def _word_tags(words, tags):
    """文の語ごとのタグを、lookup_all の結果 (2語まとめた語を含む) に位置を合わせる"""
    result = []
    k = 0
    for word in words:
        n = len(word.surface.split(' '))
        result.append(tags[k] if n == 1 and k < len(tags) else None)  # 2語まとめた語 (amātus est) には付けない
        k += n
    return result


def apply_tags(words, tags):
    """タグと矛盾しない辞書の項目を先頭に、その項目の中でもタグに合う格の候補を先頭に並べ替える。
    候補は消さない (タガーの誤りで情報を失わないため。ō の後の呼格のような規則も他の候補を見られる)"""
    for word, tag in zip(words, tags):
        word.tag = tag
        if not tag or not word.items:
            continue
        features = ldt.parse(tag)
        indeclinable = features.get('pos') in ('adv', 'conj', 'preposition')
        if indeclinable:
            # 副詞・接続詞・前置詞の判定は格などの情報を持たないので、並べ替えには使わない
            # (quod の項目の並び順に依存する規則などを壊さないため)。
            # 手作りの辞書にその読みが無い場合だけ Wiktionary から補う (sōlum「〜だけ」(副詞) など)
            if any(ldt.item_matches(item.item, features) for item in word.items) or \
               any(item.attrib('source') == 'wiktionary' for item in word.items):
                continue
            extra = Word(word.surface, latindic.lookup_wiktionary(word.surface) or []).items
            matching = [item for item in extra if ldt.item_matches(item.item, features)]
        else:
            matching = [item for item in word.items
                        if ldt.item_matches(dict(item.item, _=item._), features)]
        if not matching:
            continue
        for item in matching:
            if item._ and 'case' in features:
                first = [cng for cng in item._ if ldt.item_matches({'_': [cng]}, features)]
                item._ = first + [cng for cng in item._ if cng not in first]
        word.items = matching + [item for item in word.items if item not in matching]


def tagger_enabled():
    return USE_TAGGER and rftagger.available()


def analyze_sentence(surfaces, tags=None):
    """文 (語の列) を解析する。tags は語ごとの品詞タグ (省略するとこの文だけでタガーを呼ぶ)"""
    words = lookup_all(surfaces)
    word_details = [word.detail() for word in words]
    if tagger_enabled():
        if tags is None:
            tags, = rftagger.tag_sentences([list(surfaces)])
        apply_tags(words, _word_tags(words, tags))
    trace = []

    # 並列句・形容詞/属格の係り先
    nodes, visited_ix = detect_and_or(list(words), trace)
    nodes, adj_ix = detect_adj_correspondances(nodes, trace)
    nodes, gen_ix = detect_genitive_correspondances(nodes, trace)
    for ix in visited_ix + adj_ix + gen_ix:
        nodes[ix] = None
    nodes = [node for node in nodes if node]

    nodes, _verb_ix = detect_verbs(nodes)
    nodes = detect_prep_domination(nodes)
    nodes = [node for node in nodes if node]

    # 名詞句を述語動詞に結びつける
    verbs_ix = [i for i, node in enumerate(nodes) if isinstance(node, Predicate)]
    grouping_trace = []
    groups = _group_by_verbs(nodes, verbs_ix, grouping_trace)
    clauses = []
    if verbs_ix:
        for i, group in enumerate(groups):
            not_solved = _attach_to_predicate(nodes, group, verbs_ix[i])
            clauses.append(Clause(nodes[verbs_ix[i]], not_solved))

    return SentenceAnalysis(
        surfaces=list(surfaces), words=words, word_details=word_details,
        trace=trace, nodes=nodes, verbs=[nodes[ix] for ix in verbs_ix],
        grouping_trace=grouping_trace, clauses=clauses)


def sentences(text):
    """テキストを（句点などで）文に切り分け、各文の語の列を返す"""
    return textutil.sentence_stream(textutil.word_stream_from_text(text))


def analyze_text(text):
    all_surfaces = list(sentences(text))
    # タガーはプログラムの起動が重いので、テキスト全体を1回で処理する
    all_tags = rftagger.tag_sentences(all_surfaces) if tagger_enabled() else [None] * len(all_surfaces)
    for surfaces, tags in zip(all_surfaces, all_tags):
        yield analyze_sentence(surfaces, tags)
