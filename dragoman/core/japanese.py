#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from . import verb_flags as Verb

# MeCab
try:
    import MeCab
    is_mecab_available = True
    tagger = MeCab.Tagger('')
    tagger.parse('')
except:
    is_mecab_available = False
    print("MeCab is not available")

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


# UniDic の活用型を IPAdic 形式に揃える
#   五段-カ行 → 五段・カ行イ音便 (行く は 五段・カ行促音便)
#   五段-ワア行 → 五段・ワ行促音便
#   上一段-マ行 / 下一段-タ行 → 一段
#   サ行変格 → サ変・スル,  カ行変格 → カ変・来ル
def normalize_conjug_type(conjug_type, surface):
    if conjug_type.startswith('文語四段-'):
        # UniDic が文語と判定する語 (摘む) も、終止形が現代語と同じなら五段として活用させる
        conjug_type = '五段-' + conjug_type[len('文語四段-'):]
    if conjug_type.startswith('五段-'):
        row = conjug_type[3:4]
        if row == 'カ':
            if surface[-2:] in ('行く', '逝く', 'いく'):
                return '五段・カ行促音便'
            return '五段・カ行イ音便'
        elif row in ('ワ', 'タ', 'ラ'):
            return '五段・%s行促音便' % row
        elif row in ('ガ',):
            return '五段・ガ行'
        else:
            return '五段・%s行' % row
    elif conjug_type[1:4] == '一段-':
        return '一段'
    elif conjug_type == 'サ行変格':
        return 'サ変・スル'
    elif conjug_type == 'カ行変格':
        return 'カ変・来ル'
    return conjug_type


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
            self.conjug_type = normalize_conjug_type(features[4], self.body)
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

    def is_stative(self):
        """状態を表す訳語 (〜である, いる, ある, 居る, 有る)。現在分詞・未完了でも「〜ている」にしない"""
        return self.stop_form.endswith(('ある', 'いる', '居る', '有る', '在る'))

    def clause_form(self, kind):
        """従属節 (分詞構文) の形: present 〜していると / passive 〜されて / active 〜して / future 〜しようとして
        (完了分詞は理由・時・付帯状況のどれにも読めるよう、て形にする)"""
        if not self.use_mecab:
            return {'present': self.stop_form + 'していると', 'passive': self.stop_form + 'されて',
                    'active': self.stop_form + 'して', 'future': self.stop_form + 'しようとして'}[kind]
        if kind == 'present':
            if self.is_stative():
                return self.stop_form + 'と'  # 不在であると
            return self.active_ing_stem() + 'ると'
        if kind == 'passive':
            return self.passive_stem() + 'て'
        if kind == 'active':
            past = self.past_form()  # 話した → 話して, 読んだ → 読んで
            return past[:-1] + ('で' if past.endswith('だ') else 'て')
        if kind == 'future':
            conj, _ = self.conjugate(MIZEN, 'う')
            return conj + 'うとして'
        raise ValueError(kind)

    def adverbial_form(self, kind):
        """主語に掛かる分詞 (述語的な分詞) の形: present 〜しながら / active 〜して / passive 〜されて / future 〜しようとして"""
        if kind != 'present':
            return self.clause_form(kind)
        if not self.use_mecab:
            return self.stop_form + 'しながら'
        conj, _ = self.conjugate(RENYOU, 'ながら')
        return conj + 'ながら'

    def attributive_form(self, kind):
        """名詞を修飾する分詞の形: present 〜している / active 〜した / passive 〜された / future 〜しようとする"""
        if not self.use_mecab:
            return {'present': self.stop_form + 'している', 'passive': self.stop_form + 'された',
                    'active': self.stop_form + 'した', 'future': self.stop_form + 'しようとする'}[kind]
        if kind == 'present':
            if self.is_stative():
                return self.stop_form  # 不在である
            return self.active_ing_stem() + 'る'
        if kind == 'passive':
            return self.passive_stem() + 'た'
        if kind == 'active':
            return self.past_form()
        if kind == 'future':
            conj, _ = self.conjugate(MIZEN, 'う')
            return conj + 'うとする'
        raise ValueError(kind)

    def negative_stem(self):
        """「ない」の前の形 (恐れ / 書か / し / 来)。ある → (な)い"""
        if not self.use_mecab:
            return self.stop_form + 'などし'
        if self.body == 'ある':
            return self.prefix
        if self.body == '愛する':
            return self.prefix + '愛さ'  # 愛しない より自然
        conj, _ = self.conjugate(MIZEN, 'ない')
        return conj

    def negative_form(self, flag):
        """否定形: 恐れない / 恐れなかった / 恐れていない / 恐れられないだろう / 恐れるな (命令)"""
        if flag & Verb.IMPERATIVE:
            if flag & Verb.PASSIVE:
                return self.passive_stem() + 'るな'
            return self.stop_form + 'な'
        if flag & Verb.PASSIVE:
            stem = self.passive_stem() + ('てい' if flag & Verb.ING else '')
        elif flag & Verb.ING and self.body != 'ある':
            stem = self.active_ing_stem()
        else:
            stem = self.negative_stem()
        if flag & Verb.FUTURE:
            return stem + ('なかっただろう' if flag & Verb.PERFECT else 'ないだろう')
        if flag & (Verb.PAST | Verb.PERFECT):
            return stem + 'なかった'
        return stem + 'ない'

    def form(self, flag, negated=False):
        if negated and not flag & Verb.PARTICIPLE:
            return self.negative_form(flag)
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
                if flag & Verb.ING and self.is_stative():
                    flag -= Verb.ING  # 状態の動詞 (ある, いる, 居る) は「〜ていた」にしない

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
        d = '%s <%s>\n' % (self.stop_form, self.conjug_type)
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


# ----------------------------------------------------------------------
# 繋辞 (sum) の述語: 補語の訳語を、形容詞・形容動詞・名詞それぞれの述語の形にする
#
#   magna est → 大きい / pulchra erat → 美しかった / laetus nōn est → うれしくない
#   beāta est → 幸福である / agricola erat → 農夫であった
#
# 時制は 'present' / 'past' / 'future'

# 連体詞は形容詞の終止形や代名詞に読み替える
RENTAISHI = {'大きな': '大きい', '小さな': '小さい', 'おかしな': 'おかしい',
             'この': 'これ', 'その': 'それ', 'あの': 'あれ'}
VERB_ENDINGS = tuple('うくぐすつぬぶむる')


def _complement_type(gloss, adjective):
    if not adjective:
        return 'noun'
    if gloss.endswith(('た', 'だ')):
        return 'ta'  # 分詞の訳 (満ちた, 憎まれた) は「〜ている」の形にする
    if gloss.endswith('い'):
        return 'i'
    if gloss.endswith('な'):
        return 'na'
    if gloss.endswith('の'):
        return 'no'
    if gloss.endswith(VERB_ENDINGS):
        return 'verb'  # 輝く
    return 'noun'


def _copula_parts(gloss, adjective):
    """(語幹, 型)。型は 'i' (形容詞), 'te' (〜ている), 'da' / 'nda' (〜である で結ぶもの)"""
    gloss = RENTAISHI.get(gloss, gloss)
    kind = _complement_type(gloss, adjective)
    if kind == 'i':
        return ('よ' if gloss == 'いい' else gloss[:-1]), 'i'  # いい → よかった
    if kind == 'ta':
        return gloss[:-1] + ('て' if gloss.endswith('た') else 'で'), 'te'
    if kind == 'na':
        return gloss[:-1], 'da'
    if kind == 'no':
        return gloss + 'もの', 'da'
    if kind == 'verb':
        return gloss + 'の', 'nda'  # 輝くのである (ほかの語とまとめて結ばない)
    return gloss, 'da'


COPULA_FORMS = {
    # (型, 否定): (現在, 過去, 未来)
    ('i', False): ('い', 'かった', 'いだろう'),
    ('i', True): ('くない', 'くなかった', 'くないだろう'),
    ('te', False): ('いる', 'いた', 'いるだろう'),
    ('te', True): ('いない', 'いなかった', 'いないだろう'),
    ('da', False): ('である', 'であった', 'であるだろう'),
    ('da', True): ('ではない', 'ではなかった', 'ではないだろう'),
}
COPULA_FORMS[('nda', False)] = COPULA_FORMS[('da', False)]
COPULA_FORMS[('nda', True)] = COPULA_FORMS[('da', True)]
TENSE_INDEX = {'present': 0, 'past': 1, 'future': 2}


def _also_form(kind, form):
    """否定の並列の「も」を入れた形: くない → くもない, ではない → でもない, いない → もいない"""
    if kind == 'i':
        return 'くも' + form[1:]
    if kind in ('da', 'nda'):
        return form.replace('では', 'でも', 1)
    return 'も' + form


def copula_predicate(glosses, adjective=True, tense='present', negated=False, also=False):
    """補語の訳語 (カンマ区切り) と sum の時制・否定から述語を作る。
    〜である で結ぶものはまとめて結ぶ (王,指導者であった / うれしかった,愉快であった)。
    also は否定の並列の最後の補語 (長くも 広くもない)"""
    parts = []
    for gloss in glosses.split(','):
        stem, kind = _copula_parts(gloss, adjective)
        if (stem, kind) not in parts:
            parts.append((stem, kind))
    result = []
    for i, (stem, kind) in enumerate(parts):
        last_of_run = i + 1 == len(parts) or kind != 'da' or parts[i + 1][1] != 'da'
        form = COPULA_FORMS[(kind, negated)][TENSE_INDEX[tense]]
        if also and negated:
            form = _also_form(kind, form)
        result.append(stem + (form if last_of_run else ''))
    return ','.join(result)


def copula_conjunctive(gloss, adjective=True, negated=False):
    """並列した補語の、最後以外の形 (長くて / 幸福で / 農夫で / 満ちていて)。
    否定なら「も」を付ける (長くも / 幸福でも / 満ちても)"""
    stem, kind = _copula_parts(gloss.split(',')[0], adjective)
    if negated:
        return stem + {'i': 'くも', 'te': 'も', 'da': 'でも', 'nda': 'でも'}[kind]
    return stem + {'i': 'くて', 'te': 'いて', 'da': 'で', 'nda': 'で'}[kind]
