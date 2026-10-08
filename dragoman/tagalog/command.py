#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# タガログ語のコマンドの設定 (core/cli.py)
#
from dragoman.core.cli import Command
from . import analyzer, dictionary, morphology

USAGE = '''
  ./dragoman.py tl -e "Binili ng lalaki ang isda."
  名詞句の標識 (ang / ng / sa) と動詞の焦点 (接辞: -um- / mag- 行為者、-in 対象、-an 場所、i- 移動物) から格を決め、
  焦点の名詞 (ang) を主題「は」にして日本語に訳す。辞書は tools/build_tagalog_dic.py
'''


def explain(word):
    item = word.items[0] if word.items else None
    if item is None:
        return []
    out = []
    if item.pos == 'verb' and item.attrib('focus') in morphology.VOICE_NAMES:
        out.append('%s・%s' % (morphology.VOICE_NAMES[item.attrib('focus')],
                              morphology.ASPECT_NAMES.get(item.attrib('aspect'), '')))
    if getattr(word, 'focus', False):
        out.append('焦点 (ang) →「は」')
    if item.attrib('relative'):
        out.append('関係節: %s (連体節にして名詞に掛ける)' % item.attrib('relative'))
    return out


def original(analysis):
    """元の文 (標識・関係節の語を含む)"""
    words = getattr(analysis, 'original', None) or analysis.surfaces
    text = ''
    for w in words:
        text += w if w in analyzer.PUNCTUATION and w not in '(“"' else (' ' if text else '') + w
    return text


MARKER_ROLES = {'ang': '標識: 焦点 (ang)', 'ng': '標識: 焦点でない参与者 (ng)', 'sa': '標識: 場所・受け手 (sa)'}
CASE_NAMES = {'Nom': '主格', 'Acc': '対格', 'Gen': '属格', 'Dat': '与格'}


def token_rows(analysis):
    """元の語ごとの (表記, 説明, 注)"""
    from dragoman.core.Item import Item
    rows = []
    for word in getattr(analysis, 'display', None) or analysis.words:
        if word.items is None:
            rows.append((word.surface, '', []))
            continue
        original = getattr(word, 'original_item', None) or word.items[0].item
        item = Item(dict(original))
        current = word.items[0]
        detail = '(%s) %s%s' % (original.get('base') or word.surface.lower(),
                                {'verb': 'v.', 'pronoun': 'pron.', 'adj': 'a.'}.get(current.pos, ''),
                                (item.ja or '').split(',')[0] if item.pos not in ('marker',) else '')
        cases = sorted({c[0] for c in (current._ or [])}, key=list(CASE_NAMES).index) if current._ else []
        if cases and len(cases) < 4:
            detail += ' [%s]' % '|'.join(CASE_NAMES.get(c, c) for c in cases)
        notes = []
        if getattr(word, 'is_linker', False):
            rows.append((word.surface, '(na)', ['繋ぎ (前の語と後ろの修飾語・関係節をつなぐ)']))
            continue
        if getattr(word, 'marker_role', None):
            notes.append(MARKER_ROLES.get(word.marker_role, '標識'))
        notes += explain(word)
        notes = [n for n in notes if not n.startswith('関係節:')]
        head = getattr(word, 'relative_of', None)
        if head is not None:
            notes.append('関係節の語 (%s に掛かる)' % head.surface)
        if current.attrib('relative'):
            notes.append('関係節「%s」が掛かる → %s' % (current.attrib('relative'), (current.ja or '').split(',')[0]))
        if getattr(word, 'is_possessor', False):
            notes.append('所有者 (前の名詞の「〜の」)')
        if getattr(word, 'linked_to', None) is not None:
            notes.append('繋ぎ (na / -ng) で %s に掛かる' % word.linked_to.surface)
        if getattr(word, 'linker', False) and current.attrib('relative'):
            notes.append('繋ぎ -ng / na (後ろの関係節を導く)')
        if current.pos == 'ay':
            notes.append('倒置の印 (前が主題、後ろが述語)')
        if getattr(word, 'predicate', False):
            notes.append('述語 (後ろの ang 名詞句が主題)')
        rows.append((word.surface, detail, notes))
    return rows


def render(analysis, options):
    from dragoman.core import render as core_render
    if options.show_word_detail:
        core_render.render_tokens(token_rows(analysis))
    core_render.render_analysis(analysis, show_word_detail=False)


# 綴りと発音のずれる語 (正書法の決まり): ng は nang [naŋ]、mga は manga [maŋa] と読む
SPOKEN = {'ng': 'nang', 'mga': 'manga'}


def speech_text(analysis, options):
    """音読に渡す文: 元の文の ng → nang、mga → manga (音声は綴りどおりに読むので)"""
    import re
    return re.sub(r"\b(ng|mga)\b", lambda m: SPOKEN[m.group(1).lower()], original(analysis), flags=re.I)


def available():
    return None if dictionary.available() else 'no Tagalog data (python3 tools/build_tagalog_dic.py)'


COMMAND = Command(lang='tl', name='タガログ語', analyzer=analyzer, dictionary=dictionary, available=available,
                  usage=USAGE, header=lambda a, o: original(a), speech_text=speech_text, explain=explain, render=render,
                  descendant_langs=('en', 'ja'), speech_lang='tl')
