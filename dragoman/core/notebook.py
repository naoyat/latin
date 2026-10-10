#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析結果をノート (HTML) に清書する: --html=FILE (PDF は --pdf=FILE。HTML を Chrome のヘッドレス印刷で)
#
#   文ごとに
#     訳           節ごとの逐語訳 (原文の直下に)
#     行間逐語訳   語ごとに 原文 / (転写) / 見出し語 / 文法 / 日本語の訳語 を縦に揃える
#     図A 弧の図    語を原文の順に並べ、述語から格の枠の語へ、名詞から修飾語へ … 弧を張る (ブラウザで文字幅を測って SVG に)
#     図B 入れ子    述語 → 格の枠 → 語 (端末の字下げの表示と同じ構造) を箱の入れ子で
#     語の詳細      辞書引きの結果と、解説・子孫語 (-D)・語源 (-E)
#
#   ページの上のチェックボックスで、表示する部分を選べる (印刷にも効く)
#
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from .Word import Word
from .Predicate import Predicate
from .AndOr import AndOr
from .PrepClause import PrepClause
from .Absolute import AblativeAbsolute
from .Participle import ParticiplePhrase
from .Infinitive import InfinitiveClause
from .Question import QuestionClause

CASE_NAMES = {'Nom': '主格', 'Acc': '対格', 'Gen': '属格', 'Dat': '与格', 'Abl': '奪格', 'Loc': '処格',
              'Ins': '具格', 'Voc': '呼格', 'Inf': '不定詞', 'Q': '間接疑問', 'Nom/Acc': '主格/対格'}
TENSES = {'present': '現在', 'imperfect': '未完了', 'future': '未来', 'perfect': '完了', 'past-perfect': '過去完了',
          'future-perfect': '未来完了', 'aorist': 'アオリスト'}
MOODS = {'indicative': '直説法', 'subjunctive': '接続法', 'imperative': '命令法', 'infinitive': '不定法',
         'optative': '希求法', 'participle': '分詞'}
VOICES = {'active': '能動', 'passive': '受動', 'middle': '中動', 'middle-passive': '中受動'}
ANSI = re.compile(r'\x1b\[[0-9;]*m')
NOTE_KINDS = {'32': 'explain', '36': 'descendants', '35': 'etymology'}   # 端末の色 → 種類 (緑・シアン・マゼンタ)
RTL = re.compile('[֐-ࣿיִ-﷿ﹰ-﻿]')


def plain(text):
    return ANSI.sub('', text or '')


def note_kind(line):
    m = re.match(r'\x1b\[(\d+)m', line or '')
    return NOTE_KINDS.get(m.group(1), 'note') if m else 'note'


# ----------------------------------------------------------------------
# 語

def lemma_of(item):
    return item.attrib('base') or item.attrib('pres1sg') or item.attrib('lemma') or item.surface


def grammar_of(item):
    """文法の短い表示 (Acc.sg.f、3sg 現在 直説法 能動)"""
    if item.pos in ('verb', 'participle') and (item.attrib('person') or item.attrib('mood')):
        parts = []
        if item.attrib('person'):
            parts.append('%s%s' % (item.attrib('person'), item.attrib('number') or ''))
        parts += [TENSES.get(item.attrib('tense') or 'present', item.attrib('tense')),
                  MOODS.get(item.attrib('mood') or 'indicative', item.attrib('mood')),
                  VOICES.get(item.attrib('voice') or 'active', item.attrib('voice'))]
        if item._:
            parts.append('|'.join('.'.join(x or '-' for x in t) for t in item._[:2]))
        return ' '.join(p for p in parts if p)
    if item._:
        return '|'.join('.'.join(x or '-' for x in t) for t in item._[:3])
    return {'preposition': '前置詞', 'conj': '接続詞', 'adv': '副詞', 'article': '冠詞'}.get(item.pos, item.pos)


POS_NAMES = {'noun': '名', 'adj': '形', 'verb': '動', 'participle': '分', 'adv': '副', 'pronoun': '代', 'conj': '接',
             'preposition': '前', 'article': '冠', 'num': '数', 'interj': '間', 'particle': '小辞'}


def readings(word):
    """語の読み (辞書引きの候補) を1行ずつ: 見出し語 品詞 文法 訳語 (辞書の内部の値は出さない)"""
    out = []
    for item in word.items:
        ja = item.ja if not isinstance(item.ja, (list, tuple)) else ','.join(item.ja)
        line = '%s 〔%s〕 %s — %s' % (lemma_of(item), POS_NAMES.get(item.pos, item.pos),
                                    grammar_of(item) if item.pos not in POS_NAMES or item._ or item.attrib('mood') else '',
                                    plain(ja or ''))
        if line not in out:
            out.append(re.sub(' +', ' ', line))
    return out


def first_gloss(item):
    ja = item.ja or ''
    if isinstance(ja, (list, tuple)):
        ja = ','.join(ja)
    return ja.split(',')[0].strip()


def case_class(word):
    """語の色の種類 (端末と同じ配色: 主格 青、対格 黒、属格 緑、奪格 黄、与格 赤紫)"""
    if not isinstance(word, Word) or not word.items:
        return ''
    if word.items[0].pos == 'verb':
        return 'verb'
    for case in ('Nom', 'Acc', 'Gen', 'Abl', 'Dat', 'Loc', 'Ins'):
        if word.has_subst_case(case):
            return 'c-' + case
    return ''


# ----------------------------------------------------------------------
# 図A: 弧 (述語 → 格の枠の語、名詞 → 修飾語 …)

class Arcs:
    def __init__(self, words):
        self.words = words
        self.arcs = []
        self.seen = set()

    def add(self, head, dep, label, kind=''):
        if head is None or dep is None or head == dep or (head, dep) in self.seen:
            return
        self.seen.add((head, dep))
        self.arcs.append({'from': head, 'to': dep, 'label': label, 'kind': kind})

    def prep_index(self, prep):
        """前置詞句の前置詞の語の位置 (句の最初の語の前を後ろへ探す)"""
        first = next((w.index for w in prep.words if isinstance(w, Word) and w.index is not None), None)
        if first is None:
            return None
        for i in range(first - 1, max(-1, first - 4), -1):
            if self.words[i].surface.lower() == prep.prep.lower():
                return i
        return first - 1 if first > 0 else None

    def heads(self, node):
        """節点の頭の語の位置の列 (並列句は要素ごと)"""
        if isinstance(node, Word):
            return [node.index] if node.index is not None else []
        if isinstance(node, AndOr):
            return [i for words in node.words_slots for w in words[:1] for i in self.heads(w)]
        if isinstance(node, PrepClause):
            i = self.prep_index(node)
            return [i] if i is not None else []
        if isinstance(node, (InfinitiveClause, QuestionClause)):
            return self.heads(node.predicate.verb)
        if isinstance(node, (AblativeAbsolute, ParticiplePhrase)):
            return self.heads(node.verb)
        if isinstance(node, Predicate):
            return self.heads(node.verb)
        return []

    def walk(self, node):
        if isinstance(node, Predicate):
            self.predicate(node)
        elif isinstance(node, Word):
            self.word(node)
        elif isinstance(node, AndOr):
            conj = node.words_slots
            for words in conj:
                for w in words[:1]:
                    self.walk(w)
        elif isinstance(node, PrepClause):
            p = self.prep_index(node)
            for w in node.words:
                for h in self.heads(w):
                    self.add(p, h, node.dominated_case and CASE_NAMES.get(node.dominated_case, node.dominated_case),
                             'prep')
                self.walk(w)
        elif isinstance(node, (InfinitiveClause, QuestionClause)):
            self.predicate(node.predicate)
        elif isinstance(node, AblativeAbsolute):
            v = self.heads(node.verb)
            for h in self.heads(node.subject):
                self.add(v[0] if v else None, h, '主語', 'subject')
            self.walk(node.subject)
            for c in node.complements:
                for h in self.heads(c):
                    self.add(v[0] if v else None, h, self.case_label(c), '')
                self.walk(c)
        elif isinstance(node, ParticiplePhrase):
            v = self.heads(node.verb)
            for c in node.complements:
                for h in self.heads(c):
                    self.add(v[0] if v else None, h, self.case_label(c), '')
                self.walk(c)

    def case_label(self, node):
        cases = getattr(node, 'cases', None)
        if isinstance(node, Word) and node.items and node.items[0]._:
            cases = [node.items[0]._[0][0]]
        if isinstance(node, PrepClause):
            return '前置詞'
        return CASE_NAMES.get(cases[0], cases[0]) if cases else ''

    def predicate(self, pred):
        v = self.heads(pred.verb)
        v = v[0] if v else None
        for case, objs in pred.case_slot.items():
            if isinstance(case, tuple):
                label, kind = '前置詞', 'prep'
            else:
                label, kind = CASE_NAMES.get(case, case), {'Nom': 'subject', 'Acc': 'object'}.get(case, '')
                if case == 'Inf':
                    kind = 'clause'
                elif case == 'Q':
                    kind = 'clause'
            for obj in objs:
                for h in self.heads(obj):
                    self.add(v, h, label, kind)
                self.walk(obj)
        for mod in pred.modifiers:
            for h in self.heads(mod):
                self.add(v, h, '副詞', 'adv')
        if isinstance(pred.conjunction, Word):
            for h in self.heads(pred.conjunction):
                self.add(v, h, 'つなぎ', 'adv')
        for sub in pred.subordinates:
            label = '独立' if isinstance(sub, AblativeAbsolute) else '分詞'
            for h in self.heads(sub):
                self.add(v, h, label, 'clause')
            self.walk(sub)

    def word(self, word):
        for mod in word.modifiers:
            article = isinstance(mod, Word) and mod.items and mod.items[0].pos == 'article'
            for h in self.heads(mod):
                self.add(word.index, h, '冠詞' if article else '修飾', 'mod')
            self.walk(mod)
        for gen in word.genitives:
            for h in self.heads(gen):
                self.add(word.index, h, '属格', 'mod')
            self.walk(gen)
        for r in word.relatives:
            v = self.heads(r.predicate.verb)
            if v:
                self.add(word.index, v[0], '関係節', 'clause')
                gap = r.gap[0][1] if isinstance(r.gap, tuple) and isinstance(r.gap[0], tuple) else r.gap
                self.add(v[0], r.pronoun.index, '空所 ' + CASE_NAMES.get(gap, str(gap)), 'gap')
            self.predicate(r.predicate)


def arcs_of(analysis):
    a = Arcs(analysis.words)
    for clause in analysis.clauses:
        a.predicate(clause.predicate)
        for n in clause.not_solved:
            a.walk(n)
    if not analysis.clauses:
        for node in analysis.nodes:
            a.walk(node)
    return a.arcs


# ----------------------------------------------------------------------
# 図B: 入れ子の箱

def esc(text):
    return html.escape(plain(str(text)))


def tree(node):
    if isinstance(node, Predicate):
        rows = []
        if isinstance(node.conjunction, Word) and node.conjunction.items:
            rows.append(slot('つなぎ', [node.conjunction]))
        if node.modifiers:
            rows.append(slot('副詞', node.modifiers))
        for sub in node.subordinates:
            rows.append(slot('独立' if isinstance(sub, AblativeAbsolute) else '分詞', [sub]))
        for case, objs in node.case_slot.items():
            label = '前置詞' if isinstance(case, tuple) else CASE_NAMES.get(case, case)
            rows.append(slot(label, objs))
        info = '%s %s%s' % (MOODS.get(node.mood(), node.mood()), node.person() or '', node.number() or '')
        return ('<div class="box pred"><div class="head"><span class="w verb">%s</span> <span class="info">%s</span>'
                '</div>%s</div>' % (esc(node.surface), esc(info), ''.join(rows)))
    if isinstance(node, AndOr):
        members = ''.join(tree(words[0]) for words in node.words_slots if words)
        return '<div class="box andor"><div class="head">[%s]</div>%s</div>' % (esc(node.and_or_word), members)
    if isinstance(node, PrepClause):
        inner = ''.join(tree(w) for w in node.words)
        return ('<div class="box prep"><div class="head">%s <span class="info">+%s</span></div>%s</div>'
                % (esc(node.prep), esc(CASE_NAMES.get(node.dominated_case, node.dominated_case)), inner))
    if isinstance(node, InfinitiveClause):
        return '<div class="box clause"><div class="head">不定詞句</div>%s</div>' % tree(node.predicate)
    if isinstance(node, QuestionClause):
        return ('<div class="box clause"><div class="head">間接疑問 (%s)</div>%s</div>'
                % (esc(node.word.surface), tree(node.predicate)))
    if isinstance(node, AblativeAbsolute):
        inner = tree(node.subject) + ''.join(tree(c) for c in node.complements)
        return ('<div class="box clause"><div class="head">独立 <span class="w verb">%s</span></div>%s</div>'
                % (esc(node.verb.surface), inner))
    if isinstance(node, ParticiplePhrase):
        inner = ''.join(tree(c) for c in node.complements)
        return ('<div class="box clause"><div class="head">分詞 <span class="w verb">%s</span></div>%s</div>'
                % (esc(node.verb.surface), inner))
    if isinstance(node, Word):
        if not node.items:
            return ''
        children = ''.join(tree(g) for g in node.genitives) + ''.join(tree(m) for m in node.modifiers)
        for r in node.relatives:
            gap = r.gap[0][1] if isinstance(r.gap, tuple) and isinstance(r.gap[0], tuple) else r.gap
            children += ('<div class="box clause"><div class="head">関係節 %s <span class="info">空所: %s</span></div>%s'
                         '</div>' % (esc(r.pronoun.surface), esc(CASE_NAMES.get(gap, gap)), tree(r.predicate)))
        gloss = first_gloss(node.items[0])
        return ('<div class="box word"><div class="head"><span class="w %s">%s</span> <span class="gloss">%s</span>'
                '</div>%s</div>' % (case_class(node), esc(node.surface), esc(gloss), children))
    return ''


def slot(label, objs):
    return '<div class="slot"><div class="label">%s</div><div class="items">%s</div></div>' % (
        esc(label), ''.join(tree(o) for o in objs))


# ----------------------------------------------------------------------
# ノート

class Notebook:
    def __init__(self, title='dragoman'):
        self.title = title
        self.sentences = []

    def add(self, analysis, header=None, word_notes=None, romanize=None, show_word_detail=True,
            show_translation=True, rendered=None):
        """解析結果を1文足す。rendered があれば (独自の表示の言語: 古文など) その文字列をそのまま載せる"""
        from . import render
        if rendered is not None:   # 独自の表示の言語: 見出しと表示だけ
            text = header or ' '.join(getattr(analysis, 'surfaces', []) or [getattr(analysis, 'text', '')])
            self.sentences.append({'text': plain(text), 'words': [], 'arcs': [], 'tree': '', 'translations': [],
                                   'detail': False, 'rendered': plain(rendered), 'rtl': bool(RTL.search(text))})
            return
        words = []
        for word in analysis.words:
            if not word.items:
                if word.items is None:   # 句読点
                    words.append({'surface': word.surface, 'punct': True})
                else:
                    words.append({'surface': word.surface, 'unknown': True})
                continue
            item = word.items[0]
            notes = [{'kind': note_kind(line), 'text': plain(line)} for line in (word_notes(word) if word_notes else [])]
            words.append({'surface': word.surface, 'roman': romanize(word.surface) if romanize else '',
                          'lemma': lemma_of(item), 'grammar': grammar_of(item), 'gloss': first_gloss(item),
                          'cls': case_class(word), 'pos': item.pos,
                          'detail': readings(word), 'notes': notes})
        translations = []
        if show_translation and rendered is None:
            for clause in analysis.clauses:
                try:
                    translations.append(plain(render.translate(clause.predicate)))
                except Exception as e:   # 訳せない節があってもノートは作る
                    translations.append('(訳せない: %s)' % e)
        trees = ''
        if rendered is None:
            trees = ''.join(tree(c.predicate) for c in analysis.clauses) or \
                ''.join(tree(n) for n in analysis.nodes)
        text = header or ' '.join(analysis.surfaces)
        self.sentences.append({'text': plain(text), 'words': words, 'arcs': arcs_of(analysis) if rendered is None else [],
                               'tree': trees, 'translations': translations, 'detail': show_word_detail,
                               'rendered': plain(rendered) if rendered else '',
                               'rtl': bool(RTL.search(' '.join(analysis.surfaces)))})

    def html(self):
        body = []
        for n, s in enumerate(self.sentences, 1):
            body.append(sentence_html(n, s))
        data = json.dumps([{'words': s['words'], 'arcs': s['arcs'], 'rtl': s['rtl']} for s in self.sentences],
                          ensure_ascii=False)
        return TEMPLATE.replace('%TITLE%', html.escape(self.title)).replace('%BODY%', '\n'.join(body)) \
            .replace('%DATA%', data.replace('</', '<\\/'))

    def write(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.html())
        if path.endswith('.pdf'):
            raise ValueError('use write_pdf')

    def write_pdf(self, path):
        """Chrome (Chromium) のヘッドレス印刷で PDF に"""
        chrome = find_chrome()
        if chrome is None:
            sys.exit('PDF には Google Chrome か Chromium が要る (--html で HTML を書き出してブラウザで印刷もできる)')
        with tempfile.TemporaryDirectory() as tmp:
            page = os.path.join(tmp, 'note.html')
            self.write(page)
            subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                            '--virtual-time-budget=10000', '--print-to-pdf=' + os.path.abspath(path),
                            'file://' + page], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def find_chrome():
    for path in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                 '/Applications/Chromium.app/Contents/MacOS/Chromium'):
        if os.path.exists(path):
            return path
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome'):
        found = shutil.which(name)
        if found:
            return found
    return None


def heading(text):
    """見出しの文。右から左の文字の文に転写の括弧が付いていれば (בָּרָא … (bārā …)) 向きを分けて"""
    m = re.match(r'^(.*?)\s*\(([^()]*)\)\s*$', text)
    if m and RTL.search(m.group(1)) and not RTL.search(m.group(2)):
        return ('<bdi class="text" dir="rtl">%s</bdi><br><span class="rm" dir="ltr">%s</span>'
                % (esc(m.group(1)), esc(m.group(2))))
    return '<bdi class="text" dir="auto">%s</bdi>' % esc(text)


def sentence_html(n, s):
    out = ['<section class="sentence" data-n="%d">' % (n - 1)]
    out.append('<h2><span class="num">%d</span> %s</h2>' % (n, heading(s['text'])))
    if s['rendered']:
        out.append('<pre class="rendered">%s</pre></section>' % esc(s['rendered']))
        return '\n'.join(out)
    if s['translations']:
        out.append('<div class="part translation"><div class="ttl">訳</div><ul>%s</ul></div>'
                   % ''.join('<li>%s</li>' % esc(t) for t in s['translations']))
    cols = []
    for w in s['words']:
        if w.get('punct'):
            cols.append('<div class="col punct"><div class="sf">%s</div></div>' % esc(w['surface']))
            continue
        if w.get('unknown'):
            cols.append('<div class="col"><div class="sf">%s</div><div class="gl">?</div></div>' % esc(w['surface']))
            continue
        cols.append('<div class="col"><div class="sf w %s">%s</div>%s<div class="lm" dir="auto">%s</div>'
                    '<div class="gr" dir="ltr">%s</div><div class="gl" dir="ltr">%s</div></div>'
                    % (w['cls'], esc(w['surface']),
                       '<div class="rm" dir="ltr">%s</div>' % esc(w['roman']) if w['roman'] else '',
                       esc(w['lemma']), esc(w['grammar']), esc(w['gloss'])))
    out.append('<div class="part interlinear"><div class="ttl">行間逐語訳</div><div class="cols"%s>%s</div></div>'
               % (' dir="rtl"' if s['rtl'] else '', ''.join(cols)))
    out.append('<div class="part arcs"><div class="ttl">図A 弧</div><svg class="arcsvg"></svg></div>')
    out.append('<div class="part tree"><div class="ttl">図B 入れ子</div><div class="trees">%s</div></div>' % s['tree'])
    if s['detail']:
        rows = []
        for i, w in enumerate(s['words']):
            if w.get('punct'):
                continue
            notes = ''.join('<div class="note %s">%s</div>' % (x['kind'], esc(x['text'])) for x in w.get('notes', []))
            detail = ''.join('<div class="rd">%s</div>' % esc(r) for r in w.get('detail') or ['?'])
            rows.append('<tr><td class="i">%d</td><td class="w %s">%s</td><td>%s%s</td></tr>'
                        % (i, w.get('cls', ''), esc(w['surface']), detail, notes))
        out.append('<div class="part detail"><div class="ttl">語の詳細</div><table>%s</table></div>' % ''.join(rows))
    out.append('</section>')
    return '\n'.join(out)


TEMPLATE = r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%TITLE%</title>
<style>
:root { --ink: #222; --sub: #666; --line: #ccc; --bg: #fff; --box: #f6f6f4;
        --nom: #1f5fbf; --acc: #222; --gen: #2e7d32; --abl: #a07000; --dat: #a0309a; --verb: #c62828; }
body { font-family: "Gentium Plus", "Noto Serif", "Times New Roman", "Noto Serif Hebrew", "Noto Naskh Arabic",
       "Noto Serif Devanagari", "Hiragino Mincho ProN", "Noto Serif CJK JP", serif;
       color: var(--ink); background: var(--bg); margin: 0 auto; max-width: 60rem; padding: 1rem; line-height: 1.5; }
.controls { font-family: sans-serif; font-size: .8rem; color: var(--sub); border-bottom: 1px solid var(--line);
            padding-bottom: .5rem; margin-bottom: 1rem; display: flex; flex-wrap: wrap; gap: .25rem 1rem; }
.sentence { border-bottom: 1px solid var(--line); padding: .5rem 0 1.25rem; break-inside: avoid-page; }
h2 { font-size: 1.25rem; font-weight: normal; margin: .5rem 0; }
h2 .rm { font-size: .9rem; color: var(--sub); font-style: italic; }
h2 .num { font-family: sans-serif; font-size: .8rem; color: var(--sub); vertical-align: middle; }
.part { margin: .75rem 0; }
.part > .ttl { font-family: sans-serif; font-size: .7rem; color: var(--sub); margin-bottom: .25rem; }
.cols { display: flex; flex-wrap: wrap; gap: .5rem .9rem; }
.trees { display: flex; flex-wrap: wrap; gap: .5rem; align-items: flex-start; }
.col { display: flex; flex-direction: column; }
.col .sf { font-size: 1.1rem; } .col .rm { font-size: .8rem; color: var(--sub); font-style: italic; }
.col .lm { font-size: .8rem; } .col .gr { font-family: sans-serif; font-size: .65rem; color: var(--sub); }
.col .gl { font-size: .85rem; max-width: 9em; }
.cols[dir="rtl"] .col > div { text-align: right; }
.col.punct { justify-content: flex-start; }
.w.c-Nom { color: var(--nom); font-weight: bold; } .w.c-Acc { color: var(--acc); font-weight: bold; }
.w.c-Gen { color: var(--gen); font-weight: bold; } .w.c-Abl, .w.c-Loc, .w.c-Ins { color: var(--abl); font-weight: bold; }
.w.c-Dat { color: var(--dat); font-weight: bold; } .w.verb { color: var(--verb); font-weight: bold; }
.arcsvg { display: block; max-width: 100%; height: auto; }
.arcsvg text { font-family: inherit; } .arcsvg .lbl { font-family: sans-serif; font-size: 10px; fill: var(--sub); }
.arcsvg .gl { font-size: 11px; fill: var(--sub); }
.arcsvg path { fill: none; stroke: #888; stroke-width: 1.1; }
.arcsvg path.subject { stroke: var(--nom); } .arcsvg path.object { stroke: #444; }
.arcsvg path.clause { stroke: var(--verb); stroke-dasharray: 4 2; } .arcsvg path.gap { stroke: #bbb; stroke-dasharray: 2 2; }
.arcsvg path.mod { stroke: #999; }
.box { border: 1px solid var(--line); border-radius: 4px; padding: .2rem .4rem; margin: .15rem 0; background: var(--box); }
.box .box { background: var(--bg); }
.box .head { white-space: nowrap; } .box .info, .box .gloss { font-size: .75rem; color: var(--sub); }
.box.pred > .head { border-bottom: 1px dotted var(--line); margin-bottom: .2rem; }
.box.clause { border-color: #e0a0a0; } .box.andor, .box.prep { border-style: dashed; }
.slot { display: flex; gap: .4rem; align-items: flex-start; }
.slot .label { font-family: sans-serif; font-size: .7rem; color: var(--sub); min-width: 3.5em; padding-top: .35rem; }
.slot .items { display: flex; flex-wrap: wrap; gap: .3rem; }
.translation ul { margin: 0; padding-left: 1.2rem; }
.detail table { border-collapse: collapse; font-size: .85rem; }
.detail td { border-top: 1px solid #eee; padding: .15rem .4rem; vertical-align: top; }
.detail td.i { color: var(--sub); font-family: sans-serif; font-size: .7rem; }
.rd + .rd { color: var(--sub); font-size: .8rem; }
.note { font-size: .8rem; } .note.explain { color: var(--gen); } .note.descendants { color: #00838f; }
.note.etymology { color: var(--dat); }
pre.rendered { white-space: pre-wrap; font-size: .85rem; }
body.no-interlinear .interlinear, body.no-arcs .arcs, body.no-tree .tree, body.no-translation .translation,
body.no-detail .detail { display: none; }
@media print { .controls { display: none; } body { max-width: none; padding: 0; } @page { size: A4; margin: 15mm; } }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { --ink: #ddd; --sub: #999; --line: #444; --bg: #1b1b1b; --box: #242424;
         --nom: #6ea8ff; --acc: #eee; --gen: #7cc47f; --abl: #e0b84a; --dat: #e07ad8; --verb: #ff6b6b; }
}
@media print { :root { --ink: #222; --sub: #666; --line: #ccc; --bg: #fff; --box: #f6f6f4;
        --nom: #1f5fbf; --acc: #222; --gen: #2e7d32; --abl: #a07000; --dat: #a0309a; --verb: #c62828; } }
</style>
</head>
<body>
<div class="controls">
  <label><input type="checkbox" data-part="translation" checked> 訳</label>
  <label><input type="checkbox" data-part="interlinear" checked> 行間逐語訳</label>
  <label><input type="checkbox" data-part="arcs" checked> 図A 弧</label>
  <label><input type="checkbox" data-part="tree" checked> 図B 入れ子</label>
  <label><input type="checkbox" data-part="detail" checked> 語の詳細</label>
</div>
%BODY%
<script>
const DATA = %DATA%;
for (const box of document.querySelectorAll('.controls input')) {
  const key = 'dragoman-part-' + box.dataset.part;
  try { if (localStorage.getItem(key) === '0') box.checked = false; } catch (e) {}
  const apply = () => document.body.classList.toggle('no-' + box.dataset.part, !box.checked);
  box.addEventListener('change', () => { apply(); try { localStorage.setItem(key, box.checked ? '1' : '0'); } catch (e) {} });
  apply();
}
const NS = 'http://www.w3.org/2000/svg';
function el(name, attrs, parent) {
  const e = document.createElementNS(NS, name);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
const short = s => (s || '').length > 10 ? s.slice(0, 9) + '…' : (s || '');
const COLORS = {'c-Nom': 'var(--nom)', 'c-Acc': 'var(--acc)', 'c-Gen': 'var(--gen)', 'c-Abl': 'var(--abl)',
                'c-Loc': 'var(--abl)', 'c-Ins': 'var(--abl)', 'c-Dat': 'var(--dat)', 'verb': 'var(--verb)'};
function drawArcs(svg, data) {
  const words = data.words, GAP = 14, LEVEL = 18;
  // 語の幅を測る
  const xs = [], ws = [];
  let x = 4;
  const probe = el('g', {}, svg);
  for (const w of words) {
    const t = el('text', {'font-size': 15}, probe); t.textContent = w.surface;
    const g = el('text', {'font-size': 11, 'class': 'gl'}, probe); g.textContent = short(w.gloss);
    const width = Math.max(t.getBBox().width, g.getBBox().width, 8);
    xs.push(x); ws.push(width); x += width + GAP;
  }
  svg.removeChild(probe);
  const total = x;
  const center = i => data.rtl ? total - (xs[i] + ws[i] / 2) : xs[i] + ws[i] / 2;
  // 弧の高さ: 内側の弧より1段上
  const arcs = data.arcs.filter(a => a.from < words.length && a.to < words.length)
    .map(a => ({...a, lo: Math.min(a.from, a.to), hi: Math.max(a.from, a.to)}))
    .sort((a, b) => (a.hi - a.lo) - (b.hi - b.lo));
  for (const a of arcs) {
    a.level = 1;
    for (const b of arcs) {
      if (b === a || b.level === undefined) continue;
      if (b.lo >= a.lo && b.hi <= a.hi && (b.hi - b.lo) < (a.hi - a.lo)) a.level = Math.max(a.level, b.level + 1);
      else if (b.lo < a.hi && b.hi > a.lo && (b.hi - b.lo) === (a.hi - a.lo) && b.level >= a.level) a.level = b.level + 1;
    }
  }
  const maxLevel = Math.max(0, ...arcs.map(a => a.level));
  const base = maxLevel * LEVEL + 22;
  svg.setAttribute('viewBox', `0 0 ${total} ${base + 40}`);   // 紙の幅より広ければ縮める
  svg.setAttribute('width', total);
  svg.setAttribute('height', base + 40);
  for (const a of arcs) {
    const x1 = center(a.from), x2 = center(a.to), top = base - 6 - a.level * LEVEL;
    const off = (x2 > x1 ? 1 : -1) * 3;
    const r = Math.min(8, Math.abs(x2 - x1) / 2);
    const d = `M ${x1 + off} ${base - 6} L ${x1 + off} ${top + r} Q ${x1 + off} ${top} ${x1 + off + Math.sign(x2 - x1) * r} ${top}` +
              ` L ${x2 - off - Math.sign(x2 - x1) * r} ${top} Q ${x2 - off} ${top} ${x2 - off} ${top + r} L ${x2 - off} ${base - 6}`;
    el('path', {d, 'class': a.kind || ''}, svg);
    el('path', {d: `M ${x2 - off - 3} ${base - 11} L ${x2 - off} ${base - 6} L ${x2 - off + 3} ${base - 11}`,
                'class': a.kind || ''}, svg);
    const lbl = el('text', {x: (x1 + x2) / 2, y: top - 2, 'text-anchor': 'middle', 'class': 'lbl'}, svg);
    lbl.textContent = a.label;
  }
  words.forEach((w, i) => {
    const t = el('text', {x: center(i), y: base + 10, 'text-anchor': 'middle', 'font-size': 15,
                          'font-weight': COLORS[w.cls] ? 'bold' : 'normal', fill: COLORS[w.cls] || 'var(--ink)'}, svg);
    t.textContent = w.surface;
    const g = el('text', {x: center(i), y: base + 27, 'text-anchor': 'middle', 'class': 'gl'}, svg);
    g.textContent = short(w.gloss);
  });
}
document.querySelectorAll('section.sentence').forEach(sec => {
  const svg = sec.querySelector('.arcsvg');
  if (svg) drawArcs(svg, DATA[+sec.dataset.n]);
});
</script>
</body>
</html>
'''
