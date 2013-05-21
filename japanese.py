#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

# MeCab
try:
    import MeCab
    is_mecab_available = True
    tagger = MeCab.Tagger('')
except:
    is_mecab_available = False

def mecab_parse(text_utf8):
    if not is_mecab_available: return None

    result = []
    node = tagger.parseToNode(text_utf8)
    while node:
        if node.surface != '':
            result.append((node.surface, node.feature.split(',')))
        node = node.next
    return result


MIZEN   = 1
RENYOU  = 2
SHUUSHI = 3
RENTAI  = 4
KATEI   = 5
MEIREI  = 6

kana = {
    u'ア': u"あいうえお",
    u'カ': u"かきくけこ", u'ガ': u"がぎぐげご",
    u'サ': u"さしすせそ", u'ザ': u"ざじずぜそ",
    u'タ': u"たちつてと", u'ダ': u"だぢづでど",
    u'ナ': u"なにぬねの",
    u'ハ': u"はひふへほ", u'バ': u"ばびぶべぼ", u'パ': u"ぱぴぷぺぽ",
    u'マ': u"まみむめも",
    u'ヤ': u"やいゆえよ",
    u'ラ': u"らりるれろ",
    u'ワ': u"わいうえお"
    }

def conj_form(suffix_uc, conjug_type, conj_form, after=None):
    conjug_group = conjug_type[:2]

    if conjug_group == u'五段':
        row = conjug_type[3:4]
        if conj_form == MIZEN:
            return (kana[row][0], False) # ァ
        elif conj_form == RENYOU:
            if after[0] in (u'た', u'て'):
                if row == u'カ':
                    if conjug_type == u'五段・カ行促音便': # 行く→「行って」
                        return (u'っ', False) # 促音便
                    else:
                        # 書く→「書いて」
                        return (u'い', False) # イ音便
                elif row == u'ガ':
                    return (u'い', True) # イ音便
                elif row in (u'ナ', u'マ', u'バ'):
                    return (u'ん', True) # 撥音便
                elif row in (u'タ', u'ラ', u'ワ'):
                    return (u'っ', False) # 促音便
            return (kana[row][1], False) # ィ
        elif conj_form in [SHUUSHI, RENTAI]:
            return (kana[row][2], False) # ゥ
        elif conj_form in [KATEI, MEIREI]:
            return (kana[row][3], False) # ェ

    elif conjug_group == u'一段':
        if conj_form in [SHUUSHI, RENTAI]:
            return (u'る', False)
        else:
            return (u'', False)

    elif conjug_group == u'サ変':
        if conj_form in [SHUUSHI, RENTAI]:
            return (u'する', False)
        else:
            if after == u'れる':
                return (u'さ', False)
            else:
                return (u'し', False)

    elif conjug_group == u'カ変':
        if conj_form in [SHUUSHI, RENTAI]:
            return (u'る', False)
        else:
            return (u'', False)

    else:
        return (u'{' + suffix_uc + u'}', False)


class JaVerb:
    def __init__(self, stop_form, use_mecab=True):
        if is_mecab_available and use_mecab:
            morphemes = mecab_parse(stop_form)
            prefix = map(lambda m:m[0], morphemes[:-1])
            self.prefix = ''.join(prefix)
            self.body, features = morphemes[-1]
            self.conjug_type = features[4].decode('utf-8')
            self.use_mecab = True

            if self.conjug_type[:2] == u'サ変':
                suffix_length = 2
            else:
                suffix_length = 1

            uc = self.body.decode('utf-8')
            self.body_stem = uc[:-suffix_length].encode('utf-8')
            self.body_suffix_uc = uc[-suffix_length:]
        else:
            self.prefix = ''
            self.body = stop_form
            self.conjug_type = u'〜などする'
            self.use_mecab = False

        self.stop_form = self.prefix + self.body

    def conjugate(self, conjug_form, after=None):
        if conjug_form == SHUUSHI:
            conj = self.stop_form
            vocalize = False
        else:
            form_uc, vocalize = conj_form(self.body_suffix_uc, self.conjug_type, conjug_form, after)
            conj = self.prefix + self.body_stem + form_uc.encode('utf-8')
        return (conj, vocalize)

    def passive_stem(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(MIZEN, u'れる')
            if self.conjug_type[:2] in (u'五段', u'サ変'):
                return conj + 'れ'
            else:
                return conj + 'られ'
        else:
            return self.stop_form + "などされ"

    # 能動
    def present_active_form(self):
        conj, _vocalize = self.conjugate(SHUUSHI)
        return conj

    def active_ing_stem(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(RENYOU, u'てい')
            if vocalize:
                return conj + 'でい'
            else:
                return conj + 'てい'
        else:
            return self.stop_form + "などしてい"

    def present_active_form_ing(self):
        if self.body in ('ある'):
            return self.present_active_form()
        else:
            return self.active_ing_stem() + 'る'

    def perfect_active_form(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(RENYOU, u'た')
            if vocalize:
                return conj + 'だ'
            else:
                return conj + 'た'
        else:
            return self.stop_form + "などした"

    def imperfect_active_form(self):
        if self.body in ('ある'):
            return self.perfect_active_form()
        else:
            return self.active_ing_stem() + 'た'

    def future_active_form(self):
        if self.use_mecab:
            conj, _vocalize = self.conjugate(SHUUSHI)
            return conj + 'だろう'
        else:
            return self.stop_form + "だろう"

    def future_active_form_ing(self):
        if self.body in ('ある'):
            return self.future_active_form()
        else:
            return self.active_ing_stem() + 'るだろう'

    def imperative_active_form(self):
        if self.use_mecab:
            conj, _vocalize = self.conjugate(SHUUSHI)
            return conj + 'だろう'
        else:
            return self.stop_form + "などしろ"

    # 受動
    def present_passive_form(self):
        return self.passive_stem() + 'る'

    def passive_ing_stem(self):
        return self.passive_stem() + 'てい'

    def present_passive_form_ing(self):
        return self.passive_ing_stem() + 'る'

    def perfect_passive_form(self):
        return self.passive_stem() + 'た'

    def imperfect_passive_form(self):
        return self.passive_ing_stem() + 'た'

    def future_passive_form(self):
        return self.passive_stem() + 'るだろう'

    def future_passive_form_ing(self):
        return self.passive_ing_stem() + 'るだろう'

    def imperative_passive_form(self):
        return self.passive_stem() + 'ろ'

    #
    def description(self):
        return "%s <%s>\n - %s %s %s %s %s %s\n - %s %s %s %s %s %s" % (
            self.stop_form, self.conjug_type.encode('utf-8'),
            self.present_active_form(), self.present_active_form_ing(),
            self.perfect_active_form(), self.imperfect_active_form(),
            self.future_active_form(), self.future_active_form_ing(),
            self.present_passive_form(), self.present_passive_form_ing(),
            self.perfect_passive_form(), self.imperfect_passive_form(),
            self.future_passive_form(), self.future_passive_form_ing(),
            )


if __name__ == '__main__':
    for s in ('建てる', '住む', '飲み込む', '〜である', '与える', '入る', '貫く',
              '結びつける', '繋ぐ', '救う', '保つ', '観察する', '注意を払う',
              '殺す', '滅ぼす', '逃げる', '来る',
              '別れる', '棄てる', '見捨てる', '戻る', '帰る', '書く', '行く',
              '叫ぶ'):
        v_with_mecab = JaVerb(s, use_mecab=True)
        v_without_mecab = JaVerb(s, use_mecab=False)
        print v_with_mecab.description()
#        print v_without_mecab.description()
#        print
