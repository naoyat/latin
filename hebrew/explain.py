#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 初学者向けの解説: 動詞の語根・態の型 (binyan)・時制の型、名詞の語根
#
#   וַיֹּאמֶר → 語根 א-מ-ר (ʾ-m-r)
#               態 qal (paʿal パアル): 基本の態。能動の単純な動作
#               型 wayyiqtol (連続未完了): 物語の流れ「そして〜した」
#
from . import dictionary, script

# 態の型: 聖書学での名前 → (現代ヘブライ語での名前, 読み, 解説)
BINYANIM = {
    'qal': ('paʿal', 'パアル', '基本の態。能動の単純な動作'),
    'niphal': ('nifʿal', 'ニフアル', 'qal の受動・再帰「〜される / 自ら〜する」'),
    'piel': ('piʿel', 'ピエル', '強意・反復・使役 (第2語根字を重ねる)'),
    'pual': ('puʿal', 'プアル', 'piel の受動'),
    'hiphil': ('hifʿil', 'ヒフイル', '使役「〜させる」'),
    'hophal': ('hufʿal', 'フフアル', 'hiphil の受動「〜させられる」'),
    'hithpael': ('hitpaʿel', 'ヒトパエル', '再帰・相互・ふり「自分を〜する / 互いに〜する」'),
    'qal passive': ('', '', 'qal の受動 (古い形)'),
    'polel': ('', '', 'piel にあたる形 (中の字が弱い語根)'), 'polal': ('', '', 'pual にあたる形 (中の字が弱い語根)'),
    'hithpolel': ('', '', 'hithpael にあたる形 (中の字が弱い語根)'),
    'poel': ('', '', 'piel にあたる形'), 'poal': ('', '', 'pual にあたる形'),
    'pilpel': ('', '', 'piel にあたる形 (2字を繰り返す)'), 'polpal': ('', '', 'pual にあたる形 (2字を繰り返す)'),
    'hishtaphel': ('', '', '「ひれ伏す」(ḥwh) だけの形'),
    # 聖書アラム語
    'peal': ('', 'ペアル', '基本の態 (ヘブライ語の qal にあたる)'),
    'peil': ('', 'ペイル', 'peal の受動 (古い形)「〜された」'),
    'pael': ('', 'パエル', '強意・使役 (ヘブライ語の piel にあたる。第2語根字を重ねる)'),
    'haphel': ('', 'ハフエル', '使役「〜させる」(ヘブライ語の hiphil にあたる)'),
    'aphel': ('', 'アフエル', '使役 (haphel の別形。ה が落ちた形)'),
    'shaphel': ('', 'シャフエル', '使役 (š- の付く形。外来の形)'),
    'saphel': ('', 'サフエル', '使役 (s- の付く形)'),
    'hithpeel': ('', 'ヒトペエル', 'peal の受動・再帰'),
    'ithpeel': ('', 'イトペエル', 'peal の受動・再帰 (hithpeel の別形)'),
    'hithpaal': ('', 'ヒトパアル', 'pael の受動・再帰'),
    'ithpaal': ('', 'イトパアル', 'pael の受動・再帰 (hithpaal の別形)'),
}
# 時制・法の型 (OSHB の分類) → 解説
FORMS = {
    'qatal': '完了 (qatal): 完結した行為「〜した」',
    'wayyiqtol': '連続未完了 (wayyiqtol): 物語の流れ「そして〜した」(ו と組む)',
    'yiqtol': '未完了 (yiqtol): 未完了・未来・習慣「〜する / 〜するだろう」',
    'weqatal': '連続完了 (weqatal): 未来・命令の続き「そして〜するだろう」(ו と組む)',
    'imperative': '命令形「〜せよ」',
    'jussive': '指示形: 3人称への命令・願い「〜あれ / 〜させよ」',
    'cohortative': '勧誘形: 1人称の意志「〜しよう」',
    'infinitive construct': '不定詞連語形「〜すること」(ל と「〜するために」)',
    'infinitive absolute': '不定詞独立形 (動詞の強め「必ず〜する」など)',
}


def root_text(root):
    """語根 (ברא) → ב-ר-א (b-r-ʾ)"""
    letters = script.with_final(script.consonants(root))
    if not letters:
        return root
    latin = '-'.join(script.CONSONANTS.get(c, c) for c in letters)
    return '%s (%s)' % (script.isolate('-'.join(letters)), latin)


def construct_note(item):
    """連語形 (smikhut) の解説: 組んでいる後ろの名詞・人称接尾辞"""
    own = (item.ja or '').split(',')[0]
    kind, surface, gloss = item.attrib('construct_with') or ('none', '', '')
    if kind == 'suffix':
        return '連語形 (smikhut): 人称接尾辞 -%s (%s)「%sの」が付いた形 →「%sの%s」' % (
            script.translit(surface), script.isolate(surface), gloss, gloss, own)
    if kind == 'noun':
        return '連語形 (smikhut): 後ろの %s (%s)「%s」と組んで「%sの%s」' % (
            script.translit(surface), script.isolate(surface), gloss, gloss, own)
    return '連語形 (smikhut): 後ろの名詞と組んで「〜の%s」となる形 (ここでは後ろに名詞が無い)' % own


def notes(word):
    """語の解説の行 (動詞・分詞は語根・態・型、名詞・形容詞は語根)"""
    if not word.items:
        return []
    item = word.items[0]
    lines = []
    lemma = item.attrib('lemma')
    entry = dictionary.lexicon(lemma) if lemma else None
    root = entry.get('root') if entry else None
    if item.pos in ('noun', 'adj', 'participle') and item.attrib('state') == 'construct':
        lines.append(construct_note(item))
    if item.pos in ('verb', 'participle'):
        if root:
            lines.append('語根 ' + root_text(root))
        stem = item.attrib('stem')
        if stem:
            modern, kana, desc = BINYANIM.get(stem, ('', '', ''))
            name = stem + (' (%s %s)' % (modern, kana) if modern else '')
            lines.append('態 %s: %s' % (name, desc) if desc else '態 ' + name)
            senses = (entry or {}).get('stems', {}).get(stem)
            if senses:
                lines.append('   この語根の %s (BDB): %s' % (stem, ', '.join(senses)))
        if item.pos == 'participle':
            lines.append('型 分詞 (%s)「%s」' % ('受動' if item.attrib('voice') == 'passive' else '能動',
                                            '〜された' if item.attrib('voice') == 'passive' else '〜している / 〜する者'))
        elif item.attrib('form') in FORMS:
            lines.append('型 ' + FORMS[item.attrib('form')])
    elif item.pos in ('noun', 'adj') and root and script.consonants(root) != script.consonants(item.attrib('word') or ''):
        lines.append('語根 ' + root_text(root))
    return lines
