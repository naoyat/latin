#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 古典ギリシア語の格の読み替え (前置詞の無い属格・与格・対格を、文脈で日本語の助詞に)
#
#   動詞が支配する格   ἀκούω + 属格「〜を聞く」, πιστεύω + 与格「〜を信じる」, μάχομαι + 与格「〜と戦う」
#   比較の属格         比較級 (μείζων, -τερος) や μᾶλλον のある節の属格「〜より」
#   時の名詞           属格「〜のうちに」(νυκτός), 与格「〜に」(τῇ τρίτῃ ἡμέρᾳ), 対格「〜の間」(τρεῖς ἡμέρας)
#
# 動詞の一覧は文法書の標準的な記述による (Wiktionary にはこの情報がほとんど無い)
#

# 動詞 (見出し語) → {格: 助詞}
GOVERNMENT = {
    # 属格を取る動詞 (知覚・接触・支配・記憶・欲求・分与など)
    'ἀκούω': {'Gen': 'を'}, 'ἀκροάομαι': {'Gen': 'を'}, 'αἰσθάνομαι': {'Gen': 'を'},
    'ἅπτω': {'Gen': 'に'}, 'ἅπτομαι': {'Gen': 'に'}, 'ἄρχω': {'Gen': 'を'}, 'κρατέω': {'Gen': 'を'},
    'βασιλεύω': {'Gen': 'を'}, 'ἐπιθυμέω': {'Gen': 'を'}, 'ἐράω': {'Gen': 'を'},
    'μιμνῄσκω': {'Gen': 'を'}, 'μιμνήσκω': {'Gen': 'を'}, 'μνημονεύω': {'Gen': 'を'},
    'ἐπιλανθάνομαι': {'Gen': 'を'}, 'τυγχάνω': {'Gen': 'を'}, 'φείδομαι': {'Gen': 'を'}, 'γεύομαι': {'Gen': 'を'},
    'μετέχω': {'Gen': 'に'}, 'δέομαι': {'Gen': 'に'}, 'πειράω': {'Gen': 'を'}, 'πειράομαι': {'Gen': 'を'},
    'κατηγορέω': {'Gen': 'を'}, 'ἀμελέω': {'Gen': 'を'}, 'φροντίζω': {'Gen': 'を'}, 'ἐπιμελέομαι': {'Gen': 'の'},
    'ἀντιλαμβάνω': {'Gen': 'を'}, 'ἀπέχω': {'Gen': 'から'}, 'παύω': {'Gen': 'から'},
    # 与格を取る動詞 (信頼・服従・助力・交際・敵対・使用など)
    'πιστεύω': {'Dat': 'を'}, 'ἕπομαι': {'Dat': 'に'}, 'ἀκολουθέω': {'Dat': 'に'}, 'βοηθέω': {'Dat': 'を'},
    'χράομαι': {'Dat': 'を'}, 'πείθομαι': {'Dat': 'に'}, 'πείθω': {'Dat': 'に'}, 'ὑπακούω': {'Dat': 'に'},
    'ἀπειθέω': {'Dat': 'に'}, 'μάχομαι': {'Dat': 'と'}, 'πολεμέω': {'Dat': 'と'}, 'ὁμιλέω': {'Dat': 'と'},
    'διαλέγομαι': {'Dat': 'と'}, 'ἐντυγχάνω': {'Dat': 'に'}, 'ἀπαντάω': {'Dat': 'に'}, 'συναντάω': {'Dat': 'に'},
    'ὀργίζομαι': {'Dat': 'に'}, 'φθονέω': {'Dat': 'を'}, 'ἀρέσκω': {'Dat': 'を'}, 'εὔχομαι': {'Dat': 'に'},
    'προσκυνέω': {'Dat': 'を'}, 'δουλεύω': {'Dat': 'に'}, 'διακονέω': {'Dat': 'に'}, 'λατρεύω': {'Dat': 'に'},
    'προσέρχομαι': {'Dat': 'に'}, 'ἐπιτιμάω': {'Dat': 'を'}, 'εὐχαριστέω': {'Dat': 'に'}, 'ἐμβλέπω': {'Dat': 'を'},
}

# 比較級 (-τερος 型のほかの不規則なもの) と比較の副詞
COMPARATIVES = {'μείζων', 'κρείττων', 'κρείσσων', 'ἀμείνων', 'βελτίων', 'χείρων', 'ἥσσων', 'ἥττων',
                'ἐλάσσων', 'ἐλάττων', 'πλείων', 'πλέων', 'μᾶλλον', 'ἧσσον', 'ἧττον', 'πλέον', 'πλεῖον'}

# 時の名詞 → {格: 助詞}
TIME_NOUNS = {'ἡμέρα', 'νύξ', 'ἔτος', 'ὥρα', 'χρόνος', 'μήν', 'ἐνιαυτός', 'θέρος', 'χειμών', 'ἑσπέρα',
              'καιρός', 'αἰών', 'σάββατον', 'ἕως', 'ὄρθρος', 'μεσημβρία'}
TIME_PARTICLES = {'Gen': 'のうちに', 'Dat': 'に', 'Acc': 'の間'}


def _lemma(obj):
    items = getattr(obj, 'items', None)
    return items[0].attrib('base') if items else None


def _is_comparative(word):
    items = getattr(word, 'items', None) or []
    return any((item.attrib('base') or item.surface or '') in COMPARATIVES or
               (item.attrib('base') or '').endswith('τερος') for item in items)


def _has_comparative(pred):
    nodes = [o for objs in pred.case_slot.values() for o in objs] + list(pred.modifiers)
    words = []
    for node in nodes:
        words.append(node)
        words.extend(getattr(node, 'modifiers', []))
    return any(_is_comparative(w) for w in words)


def keep_genitive(words, ix):
    """名詞に掛けずに述語の枠に残す属格: 同じ節 (句読点まで) に比較級か μᾶλλον がある (比較の属格)"""
    def clause(rng):
        for j in rng:
            if getattr(words[j], 'items', 1) is None:  # 句読点
                return
            yield words[j]
    nearby = list(clause(range(ix - 1, -1, -1))) + list(clause(range(ix + 1, len(words))))
    nearby += [m for w in list(nearby) for m in getattr(w, 'modifiers', [])]
    return any(_is_comparative(w) for w in nearby)


# 述語的位置に置いても名詞を限定する形容詞・指示詞
DETERMINER_ADJECTIVES = {'πᾶς', 'ἅπας', 'σύμπας', 'ὅλος', 'αὐτός', 'οὗτος', 'ἐκεῖνος', 'ὅδε', 'ἕκαστος',
                         'ἑκάτερος', 'ἀμφότερος', 'μόνος', 'μέσος', 'ἄκρος', 'ἔσχατος'}


def _article(word):
    return next((m for m in getattr(word, 'modifiers', []) if getattr(m, 'items', None)
                 and m.items[0].pos == 'article'), None)


def predicative_adjective(adj, noun):
    """述語的位置の形容詞: 名詞に冠詞があり、形容詞はその冠詞と名詞の間に無く、自分の冠詞も無い
    (ὁ ἀνὴρ ἀγαθός / ἀγαθὸς ὁ ἀνήρ「その人は善い」。修飾なら ὁ ἀγαθὸς ἀνήρ, ὁ ἀνὴρ ὁ ἀγαθός)"""
    article = _article(noun)
    if article is None or _article(adj) is not None:
        return False
    if any(item.attrib('base') in DETERMINER_ADJECTIVES for item in adj.items or []):
        return False  # 述語的位置でも名詞を限定するもの (πᾶς ὁ λαός「すべての民」, οὗτος ὁ ἄνθρωπος「この人」)
    if None in (article.index, noun.index, adj.index):
        return False
    return not (article.index < adj.index < noun.index)


def particle(case, obj, pred):
    """格の枠の語 obj の助詞 (決められなければ None で、既定の助詞にする)"""
    if _lemma(obj) in TIME_NOUNS and case in TIME_PARTICLES:
        return TIME_PARTICLES[case]
    government = GOVERNMENT.get(pred.first_item.attrib('pres1sg'), {})
    if case in government:
        return government[case]
    if case == 'Gen' and _has_comparative(pred):
        return 'より'
    return None
