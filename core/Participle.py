#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 分詞句: 分詞とその補語 (目的語・前置詞句など) のまとまり
#
#   述語的な分詞 (主語に一致する主格の分詞。副詞的に訳す)
#     Puella flōrēs carpēns cantat.     少女は 花を摘みながら 歌う
#     Haec locūtus discessit.            これを話して 立ち去った
#   名詞を修飾する分詞 (ほかの格の名詞に一致する分詞。連体修飾で訳す)
#     Mīlitēs hostem fugientem cēpērunt. 兵士は {逃げている}敵を 捕えた
#
# 分詞の種類 (kind): present (現在分詞) / active (形式受動態動詞の完了分詞。能動の意味) /
#                   passive (完了分詞。受動) / future (未来分詞)
#
from .LatinObject import LatinObject
from .Word import Word
from .AndOr import AndOr
from . import language

KIND_LABELS = {'present': '現在分詞', 'passive': '完了分詞・受動', 'active': '完了分詞', 'future': '未来分詞'}


def participle_item(word):
    return next((item for item in word.items if item.pos == 'participle'), word.items[0])


def participle_kind(word):
    item = participle_item(word)
    tense = item.attrib('tense')
    if tense == 'present':
        return 'present'
    if tense == 'future':
        return 'future'
    voice = item.attrib('voice')
    if voice:
        # ギリシア語のアオリスト・完了分詞は態で (γενόμενος アオリスト中動「〜して」, λυθείς アオリスト受動「〜されて」)
        return 'passive' if voice == 'passive' or (voice == 'middle-passive' and tense == 'perfect') else 'active'
    pres1sg = item.attrib('pres1sg') or ''
    return 'active' if pres1sg.endswith('r') else 'passive'  # 形式受動態動詞 (loquor) の完了分詞は能動


def kind_label(word):
    kind = participle_kind(word)
    if participle_item(word).attrib('tense') == 'aorist':
        return 'アオリスト分詞' + ('・受動' if kind == 'passive' else '')
    return KIND_LABELS[kind]


def verb_gloss(word, lang=None):
    """分詞のもとの動詞の訳語 (日本語なら活用させるため)。(訳語, 言語)。lang は言語の設定 (辞書の引き先)"""
    item = participle_item(word)
    pres1sg = item.attrib('pres1sg')
    lookup = (lang or language.current()).lookup
    if pres1sg and lookup:
        for entry in lookup(pres1sg) or []:
            if entry.get('pos') == 'verb' and entry.get('ja'):
                return entry['ja'].split(',')[0], entry.get('gloss_lang', 'ja')
    return item.ja.split(',')[0], item.attrib('gloss_lang', 'ja')


def participle_translation(word, style, language_=None):
    """分詞の訳。style は 'absolute' (独立奪格) / 'adverbial' / 'attributive'"""
    from .japanese import JaVerb
    gloss, lang = verb_gloss(word, language_)
    kind = participle_kind(word)
    if lang != 'ja':
        return '%s[%s]' % (gloss, kind_label(word))
    try:
        verb = JaVerb(gloss)
        if style == 'adverbial':
            return verb.adverbial_form(kind)
        if style == 'attributive':
            return verb.attributive_form(kind)
        return verb.clause_form(kind)
    except Exception:
        return gloss + '[分詞]'


def _objects(complements):
    return [c for c in complements if isinstance(c, Word) and c.items and c.items[0]._ and
            any(case == 'Acc' for case, _, _ in c.items[0]._)]


class ParticiplePhrase(LatinObject):
    def __init__(self, participle, complements=(), head=None, adverbial=True):
        self.language = language.current()  # 訳すときにもこの言語の設定 (辞書の引き先) を使う
        self.verb = participle                  # 分詞 (Word)
        self.complements = list(complements)    # 分詞の補語 (目的語・前置詞句・奪格など)
        self.head = head                        # 一致する名詞 (主語が省略されていれば None)
        self.adverbial = adverbial              # True: 述語的 (〜しながら) / False: 連体修飾 (〜している)
        self.surface = ' '.join(n.surface for n in self.complements + [participle])
        self.surface_len = len(self.surface)
        # 評価 (tools/ud_eval.py) で述語と同じように扱えるよう、目的語の枠を持たせる
        self.case_slot = {}
        if head is not None and adverbial:
            self.case_slot['Nom'] = [head]
        objects = _objects(self.complements) if participle_kind(participle) != 'passive' else []
        if objects:
            self.case_slot['Acc'] = objects

    def kind(self):
        return participle_kind(self.verb)

    def _particle(self, node):
        """補語の格の助詞 (前置詞句・副詞には付けない)"""
        if node in self.case_slot.get('Acc', []):
            return 'を'
        if isinstance(node, AndOr) and node.pos in ('noun', 'pronoun'):
            cases = {case for case, _, _ in node._ or []}
        elif isinstance(node, Word) and node.items and node.items[0].pos in ('noun', 'pronoun'):
            cases = {case for case, _, _ in node.items[0]._ or []}
        else:
            return ''
        for case, particle in (('Abl', 'で'), ('Dat', 'に'), ('Gen', 'の')):
            if case in cases:
                return particle
        return ''

    def translate(self):
        complements = [c.translate()[0] + self._particle(c) for c in self.complements]
        verb = participle_translation(self.verb, 'adverbial' if self.adverbial else 'attributive', self.language)
        text = ''.join(c + ' ' for c in complements) + verb
        return ('{' + text + '}' if self.adverbial else text, False)
