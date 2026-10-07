#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 聖書ヘブライ語: 文字 (hebrew.script)、OSHB の語形の符号 (hebrew.morphology)、文の解析 (hebrew.analyzer)。
# 辞書 (tools/build_hebrew_dic.py) が無ければ辞書を使う試験を飛ばす
#
import unittest

from hebrew import script, morphology, dictionary

HAVE_DATA = dictionary.available()


class ScriptTestCase(unittest.TestCase):
    def test_pointed_and_consonants(self):
        self.assertEqual(script.pointed('בְּרֵאשִׁ֖ית'), 'בְּרֵאשִׁית')  # 朗唱記号を除く
        self.assertEqual(script.consonants('בְּרֵאשִׁ֖ית'), 'בראשית')

    def test_translit(self):
        self.assertEqual(script.translit('בְּרֵאשִׁית'), 'bərēʾšît')
        self.assertEqual(script.translit('הַשָּׁמַיִם'), 'haššāmayim')  # 強いダゲシュは子音を重ねる
        self.assertEqual(script.translit('רוּחַ'), 'rûaḥ')              # 盗まれたパタハ
        self.assertEqual(script.translit('יִשְׂרָאֵל'), 'yiśrāʾēl')     # ś
        self.assertEqual(script.translit('מֶלֶךְ'), 'meleḵ')           # 弱いダゲシュの無い כ
        self.assertEqual(script.translit('וַיְהִי־אוֹר'), 'wayhî-ʾôr')  # マカフ
        self.assertEqual(script.translit('מִזְבֵּחַ'), 'mizbēaḥ')        # 盗まれたパタハ
        self.assertEqual(script.translit('גָּבֹהַּ'), 'gāvōah')          # 点付きの הּ

    def test_translit_of_prefix_segments(self):
        # 1字だけの切れ目は盗まれたパタハにせず (הַ は ah でなく ha)、シェヴァは有声
        self.assertEqual(script.translit('הַ'), 'ha')
        self.assertEqual(script.translit('וְ'), 'wə')
        self.assertEqual(script.translit('וּ'), 'û')

    def test_qere_of_divine_name(self):
        # 音読では神の名を母音記号のとおりアドナイ (ヒリクの形はエロヒム) と読み替える
        self.assertEqual(script.qere('יְהוָה רֹעִי'), 'אֲדֹנָי רֹעִי')
        self.assertEqual(script.qere('אֲדֹנָי יֱהֹוִה'), 'אֲדֹנָי אֱלֹהִים')
        self.assertTrue(script.qere('וַיהוָה').endswith('אֲדֹנָי'))
        self.assertEqual(script.qere('יְהוָה רֹעִי', 'hashem'), 'הַשֵּׁם רֹעִי')
        self.assertEqual(script.qere('יְהוָה רֹעִי', 'literal'), 'יְהוָה רֹעִי')

    def test_isolate(self):
        self.assertEqual(script.isolate('אוֹר'), '⁧אוֹר⁩')
        self.assertEqual(script.isolate('abc'), 'abc')


class MorphCodeTestCase(unittest.TestCase):
    """OSHB の語形の符号 → 項目 (辞書を引かない部分)"""

    def test_verb(self):
        item = morphology.segment_item('Vqw3ms', None, 'יֹּאמֶר')
        self.assertEqual((item['pos'], item['form'], item['tense'], item['person'], item['number'], item['gender']),
                         ('verb', 'wayyiqtol', 'perfect', 3, 'sg', 'm'))

    def test_noun_and_construct(self):
        item = morphology.segment_item('Ncfsc', None, 'אִשְׁתּ')
        self.assertEqual((item['pos'], item['state']), ('noun', 'construct'))
        self.assertIn(('Nom', 'sg', 'f'), item['_'])

    def test_prefixes_and_suffix(self):
        self.assertEqual(morphology.segment_item('C', 'c', 'וְ')['pos'], 'conj')
        self.assertEqual(morphology.segment_item('Td', 'd', 'הַ')['pos'], 'article')
        self.assertEqual(morphology.segment_item('R', 'b', 'בְּ')['dominates'], 'Acc')
        suffix = morphology.segment_item('Sp3ms', None, 'וֹ')
        self.assertEqual((suffix['pos'], suffix['ja'], suffix['suffix']), ('pronoun', '彼', True))

    def test_object_marker_is_not_translated(self):
        item = morphology.segment_item('To', '853', 'אֵת')
        self.assertEqual(item['pos'], 'article')  # 冠詞と同じく名詞に付け、訳には出さない
        self.assertTrue(item['ja'].startswith(' ※目的語の標識'))


class BinyanTemplateTestCase(unittest.TestCase):
    """強い語根の型から態の型の形を作る (辞書を引かない)"""

    def generate(self, root, stem, column):
        from hebrew import binyan
        return binyan.generate(root, stem, column)

    def assertEqual(self, first, second, msg=None):
        import unicodedata
        nfc = lambda t: unicodedata.normalize('NFC', t) if isinstance(t, str) else t
        super().assertEqual(nfc(first), nfc(second), msg)

    def test_ktb(self):
        self.assertEqual(self.generate('כתב', 'qal', 'qatal'), 'כָּתַב')
        self.assertEqual(self.generate('כתב', 'qal', 'yiqtol'), 'יִכְתֹּב')       # 黙字のシェヴァの後ろの ת にダゲシュ
        self.assertEqual(self.generate('כתב', 'niphal', 'qatal'), 'נִכְתַּב')
        self.assertEqual(self.generate('כתב', 'piel', 'qatal'), 'כִּתֵּב')         # 2字目を重ねる
        self.assertEqual(self.generate('כתב', 'hiphil', 'qatal'), 'הִכְתִּיב')
        self.assertEqual(script.translit(self.generate('כתב', 'hiphil', 'qatal')), 'hiḵtîv')

    def test_sibilant_metathesis(self):
        self.assertEqual(self.generate('שמר', 'hithpael', 'qatal'), 'הִשְׁתַּמֵּר')  # hit-šammēr → hištammēr

    def test_root_input(self):
        from hebrew import binyan
        self.assertEqual(binyan.parse_root('ktb'), 'כתב')
        self.assertEqual(binyan.parse_root('כתב'), 'כתב')


@unittest.skipUnless(HAVE_DATA, 'ヘブライ語の辞書 (tools/build_hebrew_dic.py) が無い')
class BinyanAnalogyTestCase(unittest.TestCase):
    """弱い語根・喉音を含む語根の形を、同じ分類の別の語根の形から類推する"""

    def made(self, root, stem, column):
        import unicodedata
        from hebrew import binyan
        guess = binyan.analogize(root, stem, column)
        return unicodedata.normalize('NFC', guess[0]) if guess else None

    def test_weak_roots(self):
        import unicodedata
        nfc = lambda t: unicodedata.normalize('NFC', t)
        self.assertEqual(self.made('נפל', 'niphal', 'qatal'), nfc('נִפַּל'))      # I-נ: נ が次の字に同化
        self.assertEqual(self.made('בוא', 'qal', 'qatal'), nfc('בָּא'))         # II-ו + III-א (分類をゆるめて שוב から)
        self.assertEqual(self.made('עמד', 'niphal', 'yiqtol'), nfc('יֵעָמֵד'))  # 喉音は重ねず前の母音を長く

    def test_bdb_stem_senses(self):
        from hebrew import binyan
        self.assertIn('be written', dictionary.lexicon('3789')['stems']['niphal'])
        self.assertIn('raise up', dictionary.lexicon('6965b')['stems']['polel'])  # Po‛l → polel
        self.assertTrue(any('語義 (BDB): be written' in line for line in binyan.table('כתב')))

    def test_hollow_root_uses_polel(self):
        from hebrew import binyan
        self.assertEqual(binyan._stem_code('קום', 'piel'), 'o')


@unittest.skipUnless(HAVE_DATA, 'ヘブライ語の辞書 (tools/build_hebrew_dic.py) が無い')
class ExplainTestCase(unittest.TestCase):
    """初学者向けの解説: 動詞の語根・態の型・時制の型"""

    def notes(self, text, ix):
        from hebrew import analyzer, explain
        return explain.notes(analyzer.lookup_all(analyzer.tokens(text))[ix])

    def test_verb(self):
        lines = self.notes('וַיֹּאמֶר', 1)
        self.assertTrue(lines[0].startswith('語根 '), lines)
        self.assertIn('(ʾ-m-r)', lines[0])
        self.assertIn('qal (paʿal パアル)', lines[1])
        self.assertTrue(any('この語根の qal (BDB): Say' in line for line in lines), lines)
        self.assertTrue(any('wayyiqtol' in line for line in lines), lines)

    def test_construct_state(self):
        from hebrew import analyzer, explain
        words = analyzer.lookup_all(analyzer.tokens('וְר֣וּחַ אֱלֹהִ֔ים מְרַחֶ֖פֶת'))
        # רוּחַ は絶対形と連語形が同じ綴り: 後ろに名詞があるので連語形「神の霊」
        self.assertEqual(words[1].items[0].attrib('state'), 'construct')
        self.assertTrue(explain.notes(words[1])[0].startswith('連語形 (smikhut): 後ろの ʾĕlōhîm'))
        words = analyzer.lookup_all(analyzer.tokens('יְהוָ֥ה רֹ֝עִ֗י'))
        note = next(line for w in words for line in explain.notes(w) if line.startswith('連語形'))
        self.assertIn('人称接尾辞', note)

    def test_noun_root(self):
        self.assertIn('(ʾ-l-h)', self.notes('אֱלֹהִים', 0)[0])


@unittest.skipUnless(HAVE_DATA, 'ヘブライ語の辞書 (tools/build_hebrew_dic.py) が無い')
class AnalyzerTestCase(unittest.TestCase):
    def analyze(self, text):
        from hebrew import analyzer
        return list(analyzer.analyze_text(text))

    def test_genesis_1_1(self):
        # 動詞-主語-目的語。אֵת の後ろは対格、אֱלֹהִים は形が複数でも単数の動詞の主語
        pred = self.analyze('בְּרֵאשִׁ֖ית בָּרָ֣א אֱלֹהִ֑ים אֵ֥ת הַשָּׁמַ֖יִם וְאֵ֥ת הָאָֽרֶץ׃')[0].clauses[0].predicate
        tr = pred.translate()[0]
        self.assertTrue(tr.startswith('神'), tr)
        self.assertIn('を / 創造した', tr)

    def test_jussive_and_wayyiqtol(self):
        a = self.analyze('וַיֹּ֥אמֶר אֱלֹהִ֖ים יְהִ֣י א֑וֹר וַֽיְהִי־אֽוֹר׃')[0]
        trs = [c.predicate.translate()[0] for c in a.clauses]
        self.assertTrue(trs[0].startswith('そして / 神'), trs)  # 2つの動詞の間の1語 (主語) が落ちない
        self.assertEqual(trs[1], 'ひかりが / あれ')
        self.assertEqual(trs[2], 'そして / ひかりが / あった')

    def test_nominal_sentence_and_vocative(self):
        a = self.analyze('יְהוָ֥ה רֹ֝עִ֗י לֹ֣א אֶחְסָֽר׃')[0]
        self.assertTrue(a.clauses[0].predicate.translate()[0].startswith('主 (ヤハウェ)は / 私の'))
        a = self.analyze('שְׁמַ֖ע יִשְׂרָאֵ֑ל יְהוָ֥ה אֱלֹהֵ֖ינוּ יְהוָ֥ה ׀ אֶחָֽד׃')[0]
        self.assertTrue(a.clauses[0].predicate.translate()[0].startswith('イスラエルよ'))


if __name__ == '__main__':
    unittest.main()
