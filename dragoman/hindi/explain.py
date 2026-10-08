#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 初学者向けの解説: 動詞の形 (分詞・助動詞の組み合わせ)、能格 ने、後置詞と斜格、属格 का/की/के の一致
#
from . import dictionary, script

FORMS = {
    'habitual': '未完了分詞 (-tā / -tī / -te): 習慣・現在。助動詞 hai / thā と組む',
    'perfective': '完了分詞 (-ā / -ī / -e): 完了「〜した」。他動詞なら主語に ne が付き、動詞は目的語に一致',
    'future': '未来 (-ūgā / -egā …)「〜するだろう」',
    'subjunctive': '接続法「〜しよう / 〜するかもしれない」',
    'imperative': '命令形',
    'stem': '語幹 (rahā・saktā などと組む)',
    'infinitive': '不定詞 (-nā)「〜すること」',
    'conjunctive': '接続分詞 (-kar)「〜して」',
    'present': '現在 (honā「〜である」)',
    'past': '過去 (honā「〜であった」)',
}


def notes(word):
    if not word.items:
        return []
    item = word.items[0]
    lines = []
    if item.pos == 'verb':
        form = item.attrib('form')
        lines.append('形 ' + FORMS.get(form, form or ''))
        if item.attrib('voice') == 'passive':
            lines.append('受動: 完了分詞 + jānā「〜される」')
        gender = {'m': '男性', 'f': '女性'}.get(item.attrib('gender'))
        if gender and item.attrib('tense') in ('perfect', 'pluperfect', 'present', 'imperfect', 'progressive'):
            lines.append('一致: %s%s (分詞は主語、ne の文では目的語の性・数に一致)' % (
                gender, {'sg': '単数', 'pl': '複数'}.get(item.attrib('number'), '')))
    if getattr(word, 'ergative', False):
        lines.append('能格: ne の付いた主語 (完了形の他動詞の文)')
    if item._ and any(c[0] == 'Obl' for c in item._):
        lines.append('斜格: 後置詞の前の形 (laṛkā → laṛke mẽ、laṛkõ ko)')
    return lines
