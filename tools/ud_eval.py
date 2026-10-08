#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析器の評価: Universal Dependencies のラテン語ツリーバンク (CoNLL-U) を正解として使う
#
#   python3 tools/ud_eval.py [--source=caesar,cicero-off] [--limit=N] [-e N] FILE.conllu...
#   python3 tools/ud_eval.py --lang=grc [--source=nt,herodotus]     古典ギリシア語
#   python3 tools/ud_eval.py --lang=sa [--source=vedic,ufal]         サンスクリット
#   python3 tools/ud_eval.py --lang=ru [--source=gsd,taiga,syntagrus] ロシア語
#   python3 tools/ud_eval.py --lang=ar                               アラビア語
#   python3 tools/ud_eval.py --lang=fa [--source=perdt,seraji]       ペルシア語
#   python3 tools/ud_eval.py --lang=hi                               ヒンディー語
#   python3 tools/ud_eval.py --lang=ur                               ウルドゥー語
#
# 古典ギリシア語 (--lang=grc) の既定は $DRAGOMAN_DATA/grc/ud/grc_*-ud-*.conllu (UD Ancient Greek-PROIEL / Perseus,
# CC BY-NC-SA) のうち、新約聖書とヘロドトス『歴史』。マクロンの推定・品詞タガーは使わない。
# 独立奪格の項目は、ギリシア語では属格独立を測る。
#
# サンスクリット (--lang=sa) の既定は $DRAGOMAN_DATA/sa/ud/sa_*-ud-test.conllu (UD Sanskrit-Vedic と
# UD Sanskrit-UFAL『パンチャタントラ』。どちらも CC BY-SA 4.0)。どちらも連声を解いて複合語を分けた語の列。
# 独立奪格の項目は処格独立を測る。
#
# ロシア語 (--lang=ru) の既定は $DRAGOMAN_DATA/ru/ud/ru_*-ud-test.conllu (UD Russian-GSD, Taiga (CC BY-SA 4.0)、
# SynTagRus (CC BY-NC-SA 4.0))。独立奪格にあたる構文は無い。
#
# アラビア語 (--lang=ar) の既定は $DRAGOMAN_DATA/ar/ud/ar_padt-ud-test.conllu (UD Arabic-PADT, CC BY-NC-SA 3.0。
# 新聞記事)。解析器には書かれたとおりの語 (接続詞・前置詞・人称接尾辞の付いた形) を渡し、解析器が分けた切れ目を
# UD の語 (複合語の行の中の語) に対応させる。
#
# ペルシア語 (--lang=fa) の既定は $DRAGOMAN_DATA/fa/ud/fa_*-ud-test.conllu (UD Persian-PerDT, Seraji。CC BY-SA 4.0)。
# 格の無い言語なので格は測らず、属格→名詞 の項目はエザーフェでつながった名詞 (nmod) を測る。
#
# ヒンディー語 (--lang=hi) の既定は $DRAGOMAN_DATA/hi/ud/hi_hdtb-ud-test.conllu (UD Hindi-HDTB, CC BY-NC-SA 4.0)。
# UD の格 (直格 Nom・斜格 Acc) と解析器の格 (後置詞の働きで読み替えた主格・対格・与格・属格) は体系が違うので格は測らず、
# 属格→名詞 は名詞に掛かる名詞 (nmod) を測る。ウルドゥー語 (--lang=ur) は UD Urdu-UDTB (CC BY-NC-SA 4.0) で同じように測る。
#
# 既定は $DRAGOMAN_DATA/ud/la_proiel-ud-*.conllu (UD Latin-PROIEL, CC BY-NC-SA 3.0。リポジトリには入れない)
# のうち、カエサル『ガリア戦記』とキケロ『義務について』『アッティクス宛書簡』の文。
# ウルガタは、品詞タガー (RFTagger) の学習データ (Latin Dependency Treebank) と重なりうるので既定では使わない。
#
# 正解にはマクロンが無いので、マクロンを推定してから解析する。測るもの:
#   coverage  何らかの解析が付いた語の割合
#   case      名詞・形容詞・代名詞などの格の正解率 (解析器が最終的に選んだ格) と、正解が候補にある割合
#   amod      形容詞・限定詞 → 名詞 の係り先 (再現率・適合率)
#   gen       属格 → 名詞 の係り先 (再現率・適合率)
#   clause    主語・目的語を持つ正解の述語のうち、解析器が述語として検出した割合
#   subj/obj  主語 (受動態の主語を含む)・目的語が、解析器でもその述語の主格・対格の枠に入っている割合 (再現率)。
#             述語が検出されなかったものも取りこぼしとして数える
#
import os
import sys
import glob
import getopt
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths
from dragoman.latin import latindic, analyzer, macronizer
from dragoman.greek import analyzer as greek_analyzer
from dragoman.sanskrit import analyzer as sanskrit_analyzer
from dragoman.russian import analyzer as russian_analyzer
from dragoman.arabic import analyzer as arabic_analyzer
from dragoman.persian import analyzer as persian_analyzer
from dragoman.hindi import analyzer as hindi_analyzer
from dragoman.urdu import analyzer as urdu_analyzer
from dragoman.core.Word import Word
from dragoman.core.AndOr import AndOr
from dragoman.core.PrepClause import PrepClause
from dragoman.core.Predicate import Predicate

DATA_DIR = paths.DATA_DIR
DEFAULT_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'ud', 'la_proiel-ud-*.conllu')))
GREEK_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'grc', 'ud', 'grc_*-ud-*.conllu')))
SANSKRIT_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'sa', 'ud', 'sa_*-ud-test.conllu')))
RUSSIAN_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'ru', 'ud', 'ru_*-ud-test.conllu')))
ARABIC_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'ar', 'ud', 'ar_*-ud-test.conllu')))
PERSIAN_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'fa', 'ud', 'fa_*-ud-test.conllu')))
HINDI_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'hi', 'ud', 'hi_*-ud-test.conllu')))
URDU_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'ur', 'ud', 'ur_*-ud-test.conllu')))
# Perseus の作品番号 (TLG) → 作品
TLG_WORKS = {'tlg0012': 'homer', 'tlg0016': 'herodotus', 'tlg0003': 'thucydides', 'tlg0011': 'sophocles',
             'tlg0085': 'aeschylus', 'tlg0006': 'euripides', 'tlg0020': 'hesiod', 'tlg0008': 'athenaeus',
             'tlg0060': 'diodorus', 'tlg0007': 'plutarch', 'tlg0013': 'homeric-hymns', 'tlg0059': 'plato',
             'tlg0032': 'xenophon', 'tlg0540': 'lysias'}
UD_CASES = {'Nom': 'Nom', 'Gen': 'Gen', 'Dat': 'Dat', 'Acc': 'Acc', 'Abl': 'Abl', 'Voc': 'Voc', 'Loc': 'Loc',
            'Ins': 'Ins', 'Par': 'Gen'}
NOMINAL_UPOS = {'NOUN', 'PROPN', 'ADJ', 'DET', 'PRON', 'NUM'}
SUBJ_RELS = ('nsubj', 'nsubj:pass')


def greek_work_of(meta):
    """ギリシア語の文の作品: PROIEL は source、Perseus は sent_id の作品番号から"""
    source = meta.get('source', '')
    if 'New Testament' in source:
        return 'nt'
    if source.startswith('Histories'):
        return 'herodotus'
    if source:
        return 'other'
    return TLG_WORKS.get(meta.get('sent_id', '').split('.')[0], 'other')


def sanskrit_work_of(meta):
    return 'ufal' if meta.get('sent_id', '').startswith('panc') else 'vedic'


def work_of(source):
    if 'belli Gallici' in source:
        return 'caesar'
    if 'Atticum' in source:
        return 'cicero-att'
    if 'De officiis' in source:
        return 'cicero-off'
    if 'Vulgate' in source:
        return 'vulgate'
    return 'other'


class Token:
    def __init__(self, fields):
        self.id = int(fields[0])
        self.form = fields[1]
        self.lemma = fields[2]
        self.upos = fields[3]
        self.feats = dict(f.split('=', 1) for f in fields[5].split('|')) if fields[5] != '_' else {}
        self.head = int(fields[6])
        self.deprel = fields[7]

    @property
    def case(self):
        return UD_CASES.get(self.feats.get('Case'))

    @property
    def nominal(self):
        return self.upos in NOMINAL_UPOS or (self.upos == 'VERB' and self.feats.get('VerbForm') == 'Part')


def read_conllu(path):
    """(メタデータ, 語の列)。複合語の行 (16-18 بموجبه) の中の語には、書かれた形 (orth) と先頭の語の番号 (orth_start) を付ける"""
    meta, tokens = {}, []
    mwt = None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line:
            if tokens:
                yield meta, tokens
            meta, tokens = {}, []
        elif line.startswith('#'):
            key, _, value = line[2:].partition(' = ')
            meta[key] = value
        elif '-' in line.split('\t', 1)[0]:
            fields = line.split('\t')
            start, end = fields[0].split('-')
            mwt = (int(start), int(end), fields[1])
        elif '.' not in line.split('\t', 1)[0]:
            token = Token(line.split('\t'))
            if mwt and mwt[0] <= int(token.id) <= mwt[1]:
                token.orth, token.orth_start = mwt[2], mwt[0]
            tokens.append(token)
    if tokens:
        yield meta, tokens


def surfaces_of(tokens):
    """解析器に渡す語の列。PROIEL は -que を別の語にしているので前の語に付け直す。
    返り値: (語の列, 語の位置 → 正解の語 (付け直した que は本体の語) の対応)"""
    words, owners = [], []
    for token in tokens:
        if token.form in ('que', '-que') and words:
            words[-1] += 'que'
            continue
        words.append(token.form)
        owners.append(token)
    return words, owners


def arabic_surfaces(tokens):
    """書かれたとおりの語の列と、語の位置 → 正解の語のリスト"""
    words, owners = [], []
    for token in tokens:
        start = getattr(token, 'orth_start', None)
        if start is not None and owners and getattr(owners[-1][0], 'orth_start', None) == start:
            owners[-1].append(token)
            continue
        words.append(getattr(token, 'orth', token.form))
        owners.append([token])
    return words, owners


CONTENT_UPOS = ('NOUN', 'PROPN', 'VERB', 'ADJ', 'NUM', 'X', 'PRON', 'DET', 'ADV', 'AUX')


def arabic_word_map(analysis, owners):
    """解析器の切れ目 → 正解の語: 数が同じなら順に、違えば本体を内容語に、接頭辞・人称接尾辞を残りに順に"""
    by_ix = {}
    for word in analysis.words:
        ix = getattr(word, 'token_ix', None)
        if ix is not None and ix < len(owners) and not word.surface.startswith('('):
            by_ix.setdefault(ix, []).append(word)
    mapping = {}
    for word in analysis.words:
        # 複数の語をまとめた動詞 (ペルシア語の خواهم رفت, کار کرد): UD の動詞 (VERB) の語に対応させる
        ixs = getattr(word, 'token_ixs', None)
        if ixs and all(i < len(owners) for i in ixs):
            golds = [g for i in ixs for g in owners[i]]
            mapping[id(word)] = next((g for g in golds if g.upos == 'VERB'), golds[-1])
            for i in ixs:
                by_ix.pop(i, None)
    for ix, words in by_ix.items():
        golds = owners[ix]
        if len(words) == len(golds):
            mapping.update((id(w), g) for w, g in zip(words, golds))
            continue
        stem = next((w for w in words if getattr(w, 'reading', None) is not None or
                     (w.items and w.items[0].attrib('main'))), words[-1])
        content = next((g for g in golds if g.upos in CONTENT_UPOS and g.upos != 'PRON'), golds[-1])
        mapping[id(stem)] = content
        rest_w = [w for w in words if w is not stem]
        rest_g = [g for g in golds if g is not content]
        before_w = [w for w in rest_w if words.index(w) < words.index(stem)]
        after_w = [w for w in rest_w if words.index(w) > words.index(stem)]
        before_g = [g for g in rest_g if int(g.id) < int(content.id)]
        after_g = [g for g in rest_g if int(g.id) > int(content.id)]
        mapping.update((id(w), g) for w, g in zip(before_w, before_g))
        mapping.update((id(w), g) for w, g in zip(after_w, after_g))
    return mapping


def word_map(analysis, owners):
    """解析器の Word → 正解の語 (2語まとめた語は先頭の語に対応させる)"""
    mapping = {}
    if any(hasattr(word, 'token_ix') for word in analysis.words):
        # サンスクリットは語を並べ替える (後置の ca) ので、元の語の位置で対応させる
        for word in analysis.words:
            ix = getattr(word, 'token_ix', None)
            if ix is not None and ix < len(owners) and ix not in {id(w) for w in mapping}:
                mapping.setdefault(id(word), owners[ix])
        return mapping
    k = 0
    for word in analysis.words:
        n = len(word.surface.split(' '))
        if k < len(owners):
            mapping[id(word)] = owners[k]
        k += n
    return mapping


def words_in(node):
    """要素に含まれる Word (並列句・前置詞句の中も)"""
    if isinstance(node, Word):
        return [node]
    if isinstance(node, AndOr):
        return [w for words in node.words_slots for w in words if isinstance(w, Word)]
    if isinstance(node, PrepClause):
        return [w for w in node.words if isinstance(w, Word)]
    return []


def evaluate(files, sources, limit=0, show_errors=0, macronize=True, lang='la'):
    greek, sanskrit, russian, arabic = lang == 'grc', lang == 'sa', lang == 'ru', lang == 'ar'
    persian = lang in ('fa', 'hi', 'ur')  # 格を測らず、nmod を属格として測る言語
    hindi = lang in ('hi', 'ur')
    urdu = lang == 'ur'
    mwt = arabic or persian  # 書かれたとおりの語を渡し、解析器の切れ目を UD の語に対応させる
    if greek or sanskrit or russian or mwt:
        macronize = False  # マクロンの推定はラテン語だけ
    absolute_case = 'Gen' if greek else 'Loc' if sanskrit else 'Abl'  # 独立奪格 / 属格独立 / 処格独立
    stats = collections.Counter()
    errors = collections.defaultdict(collections.Counter)
    sentences = []
    for path in files:
        for meta, tokens in read_conllu(path):
            work = (greek_work_of(meta) if greek else sanskrit_work_of(meta) if sanskrit
                    else os.path.basename(path).split('_')[1].split('-')[0] if russian or mwt
                    else work_of(meta.get('source', '')))
            if work in sources:
                sentences.append(tokens)
    if limit:
        sentences = sentences[:limit]

    # マクロンの推定は文書単位 (時制の傾向など) なので、まとめて行う
    plain = [(arabic_surfaces(tokens) if mwt else surfaces_of(tokens))[0] + ['.'] for tokens in sentences]
    if macronize:
        context = macronizer.Context(frequency=macronizer.default_frequency())
        flat = macronizer.macronize_words([w for s in plain for w in s], context)
        it = iter(flat)
        macronized = [[next(it).macronized for _ in s] for s in plain]
    else:
        macronized = plain
    all_tags = (analyzer.rftagger.tag_sentences(macronized) if analyzer.tagger_enabled() and lang == 'la'
                else [None] * len(macronized))

    for tokens, surfaces, tags in zip(sentences, macronized, all_tags):
        _, owners = arabic_surfaces(tokens) if mwt else surfaces_of(tokens)
        try:
            analysis = (greek_analyzer.analyze_sentence(surfaces) if greek
                        else arabic_analyzer.analyze_sentence(surfaces) if arabic
                        else urdu_analyzer.analyze_sentence(surfaces) if urdu
                        else hindi_analyzer.analyze_sentence(surfaces) if hindi
                        else persian_analyzer.analyze_sentence(surfaces) if persian
                        else sanskrit_analyzer.analyze_sentence(surfaces) if sanskrit
                        else russian_analyzer.analyze_sentence(surfaces) if russian
                        else analyzer.analyze_sentence(surfaces, tags))
        except Exception as e:  # 解析器が落ちた文は数えて飛ばす
            stats['crashed'] += 1
            errors['crash']['%s: %s' % (type(e).__name__, ' '.join(surfaces)[:60])] += 1
            continue
        gold_of = arabic_word_map(analysis, owners) if mwt else word_map(analysis, owners)
        word_of = {gold.id: word for wid, gold in gold_of.items()
                   for word in analysis.words if id(word) == wid}
        by_id = {t.id: t for t in tokens}

        # 1. 網羅率 と 2. 格
        for word in analysis.words:
            gold = gold_of.get(id(word))
            if gold is None or word.items is None:
                continue
            stats['tokens'] += 1
            stats['covered'] += bool(word.items)
            if hindi or not (gold.nominal and gold.case):
                continue
            stats['case_total'] += 1
            cases = [cng[0] for item in (word.items or []) for cng in (item._ or [])]
            if gold.case in cases:
                stats['case_oracle'] += 1
            predicted = cases[0] if cases else None
            if predicted == gold.case:
                stats['case_ok'] += 1
            else:
                errors['case'][('%s %s→%s' % (gold.form, gold.case, predicted))] += 1

        # 3. 形容詞の係り先 と 4. 属格の係り先 (正解 → 解析器)
        for token in tokens:
            head = by_id.get(token.head)
            if head is None or head.upos not in ('NOUN', 'PROPN'):
                continue
            dep_word, head_word = word_of.get(token.id), word_of.get(head.id)
            if dep_word is None or head_word is None:
                continue
            if token.deprel in ('amod', 'det') and token.upos in ('ADJ', 'DET'):
                stats['amod_gold'] += 1
                if any(m is dep_word for m in head_word.modifiers):
                    stats['amod_found'] += 1
                else:
                    errors['amod']['%s→%s' % (token.form, head.form)] += 1
            if token.deprel in ('nmod', 'nmod:poss') and (token.case == 'Gen' or persian and token.upos in ('NOUN', 'PROPN', 'PRON')):
                stats['gen_gold'] += 1
                if any(g is dep_word for g in head_word.genitives):
                    stats['gen_found'] += 1
                else:
                    errors['gen']['%s→%s' % (token.form, head.form)] += 1
        # 解析器が付けた係り (適合率)
        for word in analysis.words:
            for kind, related in (('amod', word.modifiers), ('gen', word.genitives)):
                for dep in related:
                    if not isinstance(dep, Word):
                        continue
                    gold_dep, gold_head = gold_of.get(id(dep)), gold_of.get(id(word))
                    if gold_dep is None or gold_head is None:
                        continue
                    stats[kind + '_pred'] += 1
                    stats[kind + '_pred_ok'] += gold_dep.head == gold_head.id

        # 6. 独立奪格: 正解は「奪格の分詞が advcl で、主語 (nsubj) を従える」もの
        #    (並列した2つ目以降の独立奪格は、UD では1つ目の分詞の conj になる: rēbus cognitīs ratibusque factīs)
        def is_absolute(t, depth=0):
            if t.feats.get('VerbForm') != 'Part' or t.case != absolute_case or depth > 5:
                return False
            if not any(k.head == t.id and k.deprel.startswith('nsubj') for k in tokens):
                return False
            if t.deprel == 'advcl':
                return True
            head = by_id.get(t.head)
            return t.deprel == 'conj' and head is not None and is_absolute(head, depth + 1)
        gold_abs = {t.id for t in tokens if is_absolute(t)}
        stats['abs_gold'] += len(gold_abs)
        for absolute in analysis.absolutes:
            gold_part = gold_of.get(id(absolute.verb))
            if gold_part is None:
                continue
            stats['abs_pred'] += 1
            subject_ids = {gold_of[id(w)].id for w in words_in(absolute.subject) if id(w) in gold_of}
            ok = gold_part.id in gold_abs and any(k.head == gold_part.id and k.deprel.startswith('nsubj')
                                                 and k.id in subject_ids for k in tokens)
            stats['abs_pred_ok'] += ok
            stats['abs_found'] += ok
            if not ok:
                errors['abs']['%s %s' % (' '.join(w.surface for w in words_in(absolute.subject)),
                                         absolute.verb.surface)] += 1

        # 5. 主語・目的語。UD はコピュラ構文 (Gallia est dīvīsa) で est ではなく dīvīsa を中心にし、
        #    est を cop として従えるので、中心語に cop があればその語を述語として探す
        preds = {}
        for pred in [c.predicate for c in analysis.clauses] + list(analysis.absolutes) + list(analysis.participles) + \
                [inf.predicate for inf in analysis.infinitives]:
            gold_verb = gold_of.get(id(pred.verb))  # 独立奪格・分詞句は分詞を述語として扱う
            if gold_verb is not None:
                preds[gold_verb.id] = pred
            elif isinstance(pred.verb, Word) and pred.verb.surface.startswith('('):
                # 補った繋辞 (名詞文): UD では述語の名詞・形容詞が中心語なので、枠の中で主語を従える語を述語とみなす
                for objs in pred.case_slot.values():
                    for w in (w for node in objs for w in words_in(node)):
                        gold = gold_of.get(id(w))
                        if gold is not None and any(t.head == gold.id and t.deprel in SUBJ_RELS for t in tokens):
                            preds.setdefault(gold.id, pred)
        cop_of = {t.head: t.id for t in tokens if t.deprel == 'cop'}
        heads = {t.head for t in tokens if t.deprel in SUBJ_RELS + ('obj',)}
        for head_id in heads:
            head = by_id.get(head_id)
            if head is None:
                continue
            stats['clause_gold'] += 1
            stats['clause_found'] += (head_id in preds or cop_of.get(head_id) in preds)
        for token in tokens:
            kind = 'nsubj' if token.deprel in SUBJ_RELS else 'obj' if token.deprel == 'obj' else None
            word = word_of.get(token.id)
            if kind is None or word is None:
                continue
            stats[kind + '_gold'] += 1
            pred = preds.get(token.head) or preds.get(cop_of.get(token.head))
            if pred is None:
                errors[kind]['述語が検出されない'] += 1
                continue
            slots = {case: {id(w) for node in objs for w in words_in(node)}
                     for case, objs in pred.case_slot.items() if isinstance(case, str)}
            expected = ('Nom', 'Nom/Acc') if kind == 'nsubj' else ('Acc', 'Nom/Acc')
            if any(id(word) in slots.get(case, ()) for case in expected):
                stats[kind + '_found'] += 1
            else:
                found = [case for case, ids in slots.items() if id(word) in ids]
                errors[kind]['枠: %s' % (found[0] if found else 'どの枠にも無い')] += 1

    def pct(a, b):
        return '%5.1f%%' % (100.0 * stats[a] / stats[b]) if stats[b] else '    -'

    print('文 %d / 語 %d (%s)%s' % (len(sentences), stats['tokens'], ', '.join(sorted(sources)),
                                   '  ※解析器が落ちた文 %d' % stats['crashed'] if stats['crashed'] else ''))
    print('  網羅率        %s' % pct('covered', 'tokens'))
    print('  格            %s   (正解が候補にある %s, 対象 %d 語)' % (
        pct('case_ok', 'case_total'), pct('case_oracle', 'case_total'), stats['case_total']))
    print('  形容詞→名詞   再現率 %s  適合率 %s  (正解 %d 組)' % (
        pct('amod_found', 'amod_gold'), pct('amod_pred_ok', 'amod_pred'), stats['amod_gold']))
    print('  属格→名詞     再現率 %s  適合率 %s  (正解 %d 組)' % (
        pct('gen_found', 'gen_gold'), pct('gen_pred_ok', 'gen_pred'), stats['gen_gold']))
    print('  述語の検出    %s  (主語・目的語を持つ正解の述語 %d)' % (pct('clause_found', 'clause_gold'), stats['clause_gold']))
    print('  独立奪格      再現率 %s  適合率 %s  (正解 %d)' % (
        pct('abs_found', 'abs_gold'), pct('abs_pred_ok', 'abs_pred'), stats['abs_gold']))
    print('  主語          再現率 %s  (正解 %d)' % (pct('nsubj_found', 'nsubj_gold'), stats['nsubj_gold']))
    print('  目的語        再現率 %s  (正解 %d)' % (pct('obj_found', 'obj_gold'), stats['obj_gold']))
    if show_errors:
        for kind, counter in errors.items():
            print('  [%s の間違いの例] %s' % (kind, ', '.join('%s×%d' % (e, n) for e, n in counter.most_common(show_errors))))
    return stats


def main():
    opts, files = getopt.getopt(sys.argv[1:], 'e:h', ['source=', 'limit=', 'errors=', 'no-macronize', 'lang=',
                                                      'no-tagger', 'no-wiktionary', 'help'])
    sources = None
    lang = 'la'
    limit = show_errors = 0
    macronize = True
    for option, arg in opts:
        if option == '--source':
            sources = set(arg.split(','))
        elif option == '--limit':
            limit = int(arg)
        elif option in ('-e', '--errors'):
            show_errors = int(arg)
        elif option == '--lang':
            lang = arg
        elif option == '--no-macronize':
            macronize = False
        elif option == '--no-tagger':
            analyzer.USE_TAGGER = False
        elif option == '--no-wiktionary':
            latindic.LatinDic.use_wiktionary = False
        elif option in ('-h', '--help'):
            print('Usage: python %s [--lang=la|grc|sa|ru|ar|fa|hi|ur] [--source=caesar,cicero-off,cicero-att,vulgate,other] [--limit=N] '
                  '[-e N] [--no-macronize] [--no-tagger] [--no-wiktionary] [FILE.conllu...]' % sys.argv[0])
            sys.exit()
    if sources is None:
        sources = ({'nt', 'herodotus'} if lang == 'grc' else {'vedic', 'ufal'} if lang == 'sa'
                   else {'gsd', 'taiga', 'syntagrus'} if lang == 'ru' else {'padt'} if lang == 'ar'
                   else {'perdt', 'seraji'} if lang == 'fa' else {'hdtb'} if lang == 'hi' else {'udtb'} if lang == 'ur'
                   else {'caesar', 'cicero-off', 'cicero-att'})
    files = files or {'grc': GREEK_FILES, 'sa': SANSKRIT_FILES, 'ru': RUSSIAN_FILES,
                      'ar': ARABIC_FILES, 'fa': PERSIAN_FILES, 'hi': HINDI_FILES,
                      'ur': URDU_FILES}.get(lang, DEFAULT_FILES)
    if not files:
        sys.exit('no CoNLL-U files (put UD Latin-PROIEL in %s/ud/)' % DATA_DIR)
    latindic.load()
    evaluate(files, sources, limit, show_errors, macronize, lang)


if __name__ == '__main__':
    main()
