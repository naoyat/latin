#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析器の評価: Universal Dependencies のラテン語ツリーバンク (CoNLL-U) を正解として使う
#
#   python3 tools/ud_eval.py [--source=caesar,cicero-off] [--limit=N] [-e N] FILE.conllu...
#
# 既定は $LATIN_DATA/ud/la_proiel-ud-*.conllu (UD Latin-PROIEL, CC BY-NC-SA 3.0。リポジトリには入れない)
# のうち、カエサル『ガリア戦記』とキケロ『義務について』『アッティクス宛書簡』の文。
# ウルガタは、品詞タガー (RFTagger) の学習データ (Latin Dependency Treebank) と重なりうるので既定では使わない。
#
# 正解にはマクロンが無いので、マクロンを推定してから解析する。測るもの:
#   coverage  何らかの解析が付いた語の割合
#   case      名詞・形容詞・代名詞などの格の正解率 (解析器が最終的に選んだ格) と、正解が候補にある割合
#   amod      形容詞・限定詞 → 名詞 の係り先 (再現率・適合率)
#   gen       属格 → 名詞 の係り先 (再現率・適合率)
#   subj/obj  動詞の主語・目的語が、解析器でもその動詞の主格・対格の枠に入っている割合 (再現率)
#
import os
import sys
import glob
import getopt
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from latin import latindic, analyzer, macronizer
from latin.Word import Word
from latin.AndOr import AndOr
from latin.PrepClause import PrepClause
from latin.Predicate import Predicate

DATA_DIR = os.environ.get('LATIN_DATA', os.path.expanduser('~/.local/share/latin-data'))
DEFAULT_FILES = sorted(glob.glob(os.path.join(DATA_DIR, 'ud', 'la_proiel-ud-*.conllu')))
UD_CASES = {'Nom': 'Nom', 'Gen': 'Gen', 'Dat': 'Dat', 'Acc': 'Acc', 'Abl': 'Abl', 'Voc': 'Voc', 'Loc': 'Loc'}
NOMINAL_UPOS = {'NOUN', 'PROPN', 'ADJ', 'DET', 'PRON', 'NUM'}


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
    meta, tokens = {}, []
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line:
            if tokens:
                yield meta, tokens
            meta, tokens = {}, []
        elif line.startswith('#'):
            key, _, value = line[2:].partition(' = ')
            meta[key] = value
        elif '-' not in line.split('\t', 1)[0] and '.' not in line.split('\t', 1)[0]:
            tokens.append(Token(line.split('\t')))
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


def word_map(analysis, owners):
    """解析器の Word → 正解の語 (2語まとめた語は先頭の語に対応させる)"""
    mapping = {}
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


def evaluate(files, sources, limit=0, show_errors=0, macronize=True):
    stats = collections.Counter()
    errors = collections.defaultdict(collections.Counter)
    sentences = []
    for path in files:
        for meta, tokens in read_conllu(path):
            if work_of(meta.get('source', '')) in sources:
                sentences.append(tokens)
    if limit:
        sentences = sentences[:limit]

    # マクロンの推定は文書単位 (時制の傾向など) なので、まとめて行う
    plain = [surfaces_of(tokens)[0] + ['.'] for tokens in sentences]
    if macronize:
        context = macronizer.Context(frequency=macronizer.default_frequency())
        flat = macronizer.macronize_words([w for s in plain for w in s], context)
        it = iter(flat)
        macronized = [[next(it).macronized for _ in s] for s in plain]
    else:
        macronized = plain
    all_tags = (analyzer.rftagger.tag_sentences(macronized) if analyzer.tagger_enabled()
                else [None] * len(macronized))

    for tokens, surfaces, tags in zip(sentences, macronized, all_tags):
        _, owners = surfaces_of(tokens)
        try:
            analysis = analyzer.analyze_sentence(surfaces, tags)
        except Exception as e:  # 解析器が落ちた文は数えて飛ばす
            stats['crashed'] += 1
            errors['crash']['%s: %s' % (type(e).__name__, ' '.join(surfaces)[:60])] += 1
            continue
        gold_of = word_map(analysis, owners)
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
            if not (gold.nominal and gold.case):
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
            if token.deprel == 'nmod' and token.case == 'Gen':
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

        # 5. 主語・目的語 (正解の動詞が解析器でも述語になっている場合)
        for clause in analysis.clauses:
            pred = clause.predicate
            gold_verb = gold_of.get(id(pred.verb))
            if gold_verb is None:
                continue
            slots = {case: {id(w) for node in objs for w in words_in(node)}
                     for case, objs in pred.case_slot.items() if isinstance(case, str)}
            for token in tokens:
                if token.head != gold_verb.id or token.deprel not in ('nsubj', 'obj'):
                    continue
                word = word_of.get(token.id)
                if word is None:
                    continue
                expected = ('Nom',) if token.deprel == 'nsubj' else ('Acc',)
                stats[token.deprel + '_gold'] += 1
                if any(id(word) in slots.get(case, ()) for case in expected + ('Nom/Acc',)):
                    stats[token.deprel + '_found'] += 1

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
    print('  主語          再現率 %s  (正解 %d)' % (pct('nsubj_found', 'nsubj_gold'), stats['nsubj_gold']))
    print('  目的語        再現率 %s  (正解 %d)' % (pct('obj_found', 'obj_gold'), stats['obj_gold']))
    if show_errors:
        for kind, counter in errors.items():
            print('  [%s の間違いの例] %s' % (kind, ', '.join(e for e, _ in counter.most_common(show_errors))))
    return stats


def main():
    opts, files = getopt.getopt(sys.argv[1:], 'e:h', ['source=', 'limit=', 'errors=', 'no-macronize',
                                                      'no-tagger', 'no-wiktionary', 'help'])
    sources = {'caesar', 'cicero-off', 'cicero-att'}
    limit = show_errors = 0
    macronize = True
    for option, arg in opts:
        if option == '--source':
            sources = set(arg.split(','))
        elif option == '--limit':
            limit = int(arg)
        elif option in ('-e', '--errors'):
            show_errors = int(arg)
        elif option == '--no-macronize':
            macronize = False
        elif option == '--no-tagger':
            analyzer.USE_TAGGER = False
        elif option == '--no-wiktionary':
            latindic.LatinDic.use_wiktionary = False
        elif option in ('-h', '--help'):
            print('Usage: python %s [--source=caesar,cicero-off,cicero-att,vulgate,other] [--limit=N] '
                  '[-e N] [--no-macronize] [--no-tagger] [--no-wiktionary] [FILE.conllu...]' % sys.argv[0])
            sys.exit()
    files = files or DEFAULT_FILES
    if not files:
        sys.exit('no CoNLL-U files (put UD Latin-PROIEL in %s/ud/)' % DATA_DIR)
    latindic.load()
    evaluate(files, sources, limit, show_errors, macronize)


if __name__ == '__main__':
    main()
