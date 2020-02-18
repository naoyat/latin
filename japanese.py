#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import Verb

# MeCab
try:
    import MeCab
    is_mecab_available = True
    tagger = MeCab.Tagger('')
    tagger.parse('')
except:
    is_mecab_available = False

def mecab_parse(text_utf8):
    # print('MECAB_PARSE', text_utf8)
    if not is_mecab_available: return None

    result = []
    node = tagger.parseToNode(text_utf8)
    while node:
        # print(21, node.surface)
        if node.surface != '':
            result.append((node.surface, node.feature.split(',')))
        node = node.next #() #__next__
    return result


MIZEN   = 1
RENYOU  = 2
SHUUSHI = 3
RENTAI  = 4
KATEI   = 5
MEIREI  = 6

kana = {
    'ア': "あいうえお",
    'カ': "かきくけこ", 'ガ': "がぎぐげご",
    'サ': "さしすせそ", 'ザ': "ざじずぜそ",
    'タ': "たちつてと", 'ダ': "だぢづでど",
    'ナ': "なにぬねの",
    'ハ': "はひふへほ", 'バ': "ばびぶべぼ", 'パ': "ぱぴぷぺぽ",
    'マ': "まみむめも",
    'ヤ': "やいゆえよ",
    'ラ': "らりるれろ",
    'ワ': "わいうえお"
    }



def conj_form(suffix_uc, conjug_type, conj_form, after=None):
    conjug_group = conjug_type[:2]

    if conjug_group == '五段':
        row = conjug_type[3:4]
        if conj_form == MIZEN:
            if after[0] == 'う':
                return (kana[row][4], False) # ォ
            else:
                return (kana[row][0], False) # ァ
        elif conj_form == RENYOU:
            if after[0] in ('た', 'て'):
                if row == 'カ':
                    if conjug_type == '五段・カ行促音便': # 行く→「行って」
                        return ('っ', False) # 促音便
                    else:
                        # 書く→「書いて」
                        return ('い', False) # イ音便
                elif row == 'ガ':
                    return ('い', True) # イ音便
                elif row in ('ナ', 'マ', 'バ'):
                    return ('ん', True) # 撥音便
                elif row in ('タ', 'ラ', 'ワ'):
                    return ('っ', False) # 促音便
            return (kana[row][1], False) # ィ
        elif conj_form in [SHUUSHI, RENTAI]:
            return (kana[row][2], False) # ゥ
        elif conj_form in [KATEI, MEIREI]:
            return (kana[row][3], False) # ェ

    elif conjug_group == '一段':
        if conj_form == MIZEN:
            if after[0] == 'う':
                return ('よ', False)
            else:
                return ('', False)
        elif conj_form in [SHUUSHI, RENTAI]:
            return ('る', False)
        elif conj_form == MEIREI:
            return ('ろ', False)
        else:
            return ('', False)

    elif conjug_group == 'サ変':
        if conj_form == MIZEN:
            if after[0] == 'う':
                return ('しよ', False)
            elif after[0] == 'れ':
                return ('さ', False)
            else:
                return ('し', False)
        elif conj_form in [SHUUSHI, RENTAI]:
            return ('する', False)
        elif conj_form == MEIREI:
            return ('しろ', False)
        else:
            if after[0] == 'れ':
                return ('さ', False)
            else:
                return ('し', False)

    elif conjug_group == 'カ変':
        if conj_form == MIZEN:
            if after[0] == 'う':
                return ('よ', False)
            else:
                return ('', False)
        elif conj_form in [SHUUSHI, RENTAI]:
            return ('る', False)
        elif conj_form == MEIREI:
            return ('い', False)
        else:
            return ('', False)

    else:
        return ('{' + suffix_uc + '}', False)


class JaVerb:
    def __init__(self, stop_form, use_mecab=True):
        if is_mecab_available and use_mecab:
            morphemes = mecab_parse(stop_form)
            # print(131, stop_form, morphemes)
            prefix = [m[0] for m in morphemes[:-1]]
            self.prefix = ''.join(prefix)
            self.body, features = morphemes[-1]
            self.conjug_type = features[4]
            self.use_mecab = True

            if self.conjug_type[:2] == 'サ変':
                suffix_length = 2
            else:
                suffix_length = 1

            uc = self.body
            self.body_stem = uc[:-suffix_length]
            self.body_suffix_uc = uc[-suffix_length:]
        else:
            self.prefix = ''
            self.body = stop_form
            self.conjug_type = '〜などする'
            self.use_mecab = False

        self.stop_form = self.prefix + self.body

    def conjugate(self, conjug_form, after=None):
        if conjug_form == SHUUSHI:
            conj = self.stop_form
            vocalize = False
        else:
            form_uc, vocalize = conj_form(self.body_suffix_uc, self.conjug_type, conjug_form, after)
            conj = self.prefix + self.body_stem + form_uc
        return (conj, vocalize)


    def passive_stem(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(MIZEN, 'れる')
            if self.conjug_type[:2] in ('五段', 'サ変'):
                return conj + 'れ'
            else:
                return conj + 'られ'
        else:
            return self.stop_form + "などされ"

    def active_ing_stem(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(RENYOU, 'てい')
            if vocalize:
                return conj + 'でい'
            else:
                return conj + 'てい'
        else:
            return self.stop_form + "などしてい"

    def past_form(self):
        if self.use_mecab:
            conj, vocalize = self.conjugate(RENYOU, 'た')
            if vocalize:
                return conj + 'だ'
            else:
                return conj + 'た'
        else:
            return self.stop_form + "などした"

    def form(self, flag):
        if flag & Verb.PARTICIPLE:
            if flag & Verb.FUTURE:
                # return "<p+しようとしている>"
                conj, vocalize = self.conjugate(MIZEN, 'う')
                return conj + 'うとしている'
            elif flag & Verb.PERFECT:
                stem = self.passive_stem()
                return stem + 'た'
            else:
                conj, vocalize = self.conjugate(RENYOU, 'つつ')
                return conj + 'つつある'
            # return "<p+しつつある>"
        elif flag & Verb.INDICATIVE:
            # 直説法
            if flag & Verb.PASSIVE:
                # 受動態
                stem = self.passive_stem()
#                if flag & Verb.ING or not flag & Verb.PERFECT:
                if flag & Verb.ING:
                    stem += 'てい' # ing-stem

                if flag & Verb.PAST: # or flag & PERFECT:
                    # 過去
                    if flag & Verb.PERFECT:
                        return stem + 'た'
                    else:
                        return stem + 'た'
                elif flag & Verb.FUTURE:
                    # 未来
                    if flag & Verb.PERFECT:
                        return stem + 'ただろう'
                    else:
                        return stem + 'るだろう'
                else:
                    # 現在
                    if flag & Verb.PERFECT:
                        return stem + 'た'
                    else:
                        return stem + 'る'
            else:
                # 能動態
                # stem = self.present_active_form()
                if flag & Verb.ING and self.body in ('ある'):
                    flag -= Verb.ING

                if flag & Verb.ING:
                    ing_stem = self.active_ing_stem()

                # past-form
                past = self.past_form()

                if flag & Verb.PAST: # or flag & PERFECT:
                    # 過去
                    if flag & Verb.PERFECT:
                        return past
                    elif flag & Verb.ING:
                        return ing_stem + 'た'
                    else:
                        return past
                elif flag & Verb.FUTURE:
                    # 未来
                    if flag & Verb.PERFECT:
                        return past + 'だろう'
                    elif flag & Verb.ING:
                        return ing_stem + 'るだろう'
                    else:
                        return self.stop_form + 'だろう'
                else:
                    # 現在
                    if flag & Verb.PERFECT:
                        return past
                    elif flag & Verb.ING:
                        return ing_stem + 'る'
                    else:
                        return self.stop_form

        elif flag & Verb.IMPERATIVE:
            # 命令法
            if flag & Verb.PASSIVE:
                # 受動態
                stem = self.passive_stem()
                return stem + 'ろ'
            else:
                # 能動態
                if self.use_mecab:
                    conj, _vocalize = self.conjugate(MEIREI)
                    return conj
                else:
                    return self.stop_form + "などしろ"
        else:
            pass
        return '?'

    #
    def description(self):
        d = '%s <%s>\n' % (self.stop_form, self.conjug_type.encode('utf-8'))
        d += ' - '+ ' '.join([
            self.form( Verb.INDICATIVE_ACTIVE_PRESENT ), self.form( Verb.INDICATIVE_ACTIVE_PRESENT | Verb.ING ),
            self.form( Verb.INDICATIVE_ACTIVE_IMPERFECT ),
            self.form( Verb.INDICATIVE_ACTIVE_FUTURE ), self.form( Verb.INDICATIVE_ACTIVE_FUTURE | Verb.ING ),
            self.form( Verb.INDICATIVE_ACTIVE_PERFECT ),
            self.form( Verb.INDICATIVE_ACTIVE_PAST_PERFECT ),
            self.form( Verb.INDICATIVE_ACTIVE_FUTURE_PERFECT ),
            ]) + '\n'
        d += ' - '+ ' '.join([
            self.form( Verb.INDICATIVE_PASSIVE_PRESENT ), self.form( Verb.INDICATIVE_PASSIVE_PRESENT | Verb.ING ),
            self.form( Verb.INDICATIVE_PASSIVE_IMPERFECT ),
            self.form( Verb.INDICATIVE_PASSIVE_FUTURE ), self.form( Verb.INDICATIVE_PASSIVE_FUTURE | Verb.ING ),
            self.form( Verb.INDICATIVE_PASSIVE_PERFECT ),
            self.form( Verb.INDICATIVE_PASSIVE_PAST_PERFECT ),
            self.form( Verb.INDICATIVE_PASSIVE_FUTURE_PERFECT ),
            ]) + '\n'
        d += ' - '+ ' '.join([
            self.form( Verb.IMPERATIVE_ACTIVE_PRESENT ),
            # self.form( Verb.IMPERATIVE_ACTIVE_FUTURE ),
            self.form( Verb.IMPERATIVE_PASSIVE_PRESENT ),
            # self.form( Verb.IMPERATIVE_PASSIVE_FUTURE )
            ]) + '\n'
        return d
#            self.present_active_form(), self.present_active_form_ing(),
#            self.perfect_active_form(), self.imperfect_active_form(),
#            self.future_active_form(), self.future_active_form_ing(),
#            self.present_passive_form(), self.present_passive_form_ing(),
#            self.perfect_passive_form(), self.imperfect_passive_form(),
#            self.future_passive_form(), self.future_passive_form_ing(),


if __name__ == '__main__':
    for s in ('建てる', '住む', '飲み込む', '〜である', '与える', '入る', '貫く',
              '結びつける', '繋ぐ', '救う', '保つ', '観察する', '注意を払う',
              '殺す', '滅ぼす', '逃げる', '来る',
              '別れる', '棄てる', '見捨てる', '戻る', '帰る', '書く', '行く',
              '叫ぶ'):
        v_with_mecab = JaVerb(s, use_mecab=True)
        v_without_mecab = JaVerb(s, use_mecab=False)
        print(v_with_mecab.description())
#        print v_without_mecab.description()
#        print
