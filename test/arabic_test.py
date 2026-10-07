#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# アラビア語: 文字 (arabic.script)、語の読み (arabic.morphology)、文の解析 (arabic.analyzer)。
# CAMeL Tools と辞書 (tools/build_arabic_dic.py) が無ければ、それを使う試験を飛ばす
#
import unittest

from arabic import script

try:
    from arabic import dictionary, morphology
    HAVE_DATA = dictionary.available() and morphology.available()
except ImportError:
    HAVE_DATA = False


class ScriptTestCase(unittest.TestCase):
    def test_bare_and_normalize(self):
        self.assertEqual(script.bare('ذَهَبَ الوَلَدُ'), 'ذهب الولد')
        self.assertEqual(script.normalize('إِلَى'), 'الى')

    def test_translit(self):
        self.assertEqual(script.translit('ذَهَبَ'), 'ḏahaba')
        self.assertEqual(script.translit('الشَّمْسُ'), 'aš-šamsu')       # 太陽文字に同化する定冠詞
        self.assertEqual(script.translit('الوَلَدُ'), 'al-waladu')
        self.assertEqual(script.translit('مَدْرَسَةٌ'), 'madrasatun')     # tāʾ marbūṭa + 格の語尾
        self.assertEqual(script.translit('مُدَرِّسَة'), 'mudarrisa')      # シャッダ、語末の tāʾ marbūṭa
        self.assertEqual(script.translit('إِلَى'), 'ilā')                # 語頭のハムザは書かない、alif maqṣūra
        self.assertEqual(script.translit('كِتابًا'), 'kitāban')
        self.assertEqual(script.translit('غَداً'), 'ġadan')              # 支えのアリフに書いた -an
        self.assertEqual(script.translit('يَكْتُبُونَ'), 'yaktubūna')
        self.assertEqual(script.translit('ذَهَبُوا'), 'ḏahabū')          # 書くだけのアリフ
        self.assertEqual(script.translit('قُرْآن'), 'qurʾān')

    def test_sun_shadda(self):
        self.assertEqual(script.sun_shadda('السُوقِ'), 'السُّوقِ')
        self.assertEqual(script.sun_shadda('الوَلَد'), 'الوَلَد')        # 月文字はそのまま
        self.assertEqual(script.sun_shadda('السوق'), 'السوق')            # 母音記号の無い語はそのまま


@unittest.skipUnless(HAVE_DATA, 'no Arabic data (CAMeL Tools / tools/build_arabic_dic.py)')
class MorphologyTestCase(unittest.TestCase):
    def test_compatible(self):
        self.assertTrue(morphology.compatible('كَتَبَ', 'كَتَبَ'))
        self.assertTrue(morphology.compatible('كتب', 'كُتُب'))           # 記号の無い入力はどれとも合う
        self.assertFalse(morphology.compatible('كُتُب', 'كَتَبَ'))

    def test_vocalized_input_narrows_readings(self):
        self.assertEqual({r.pos for r in morphology.readings('كَتَبَ')}, {'verb'})

    def test_segments_of_clitics(self):
        # وَبِالقَلَم → وَ 接続詞 + بِ 前置詞 + القَلَم 名詞 (定冠詞は本体に付けたまま)
        segments = morphology.segments(morphology.readings('وبالقلم')[0])
        self.assertEqual([item['pos'] for _, item in segments], ['conj', 'preposition', 'noun'])
        self.assertTrue(segments[2][1]['definite'])
        # كِتابُهُم → 本体 + 人称接尾辞 (属格「彼らの」)
        segments = morphology.segments(morphology.readings('كتابهم')[0])
        self.assertEqual(segments[-1][1]['ja'], '彼ら')
        self.assertTrue(segments[-1][1]['suffix'])

    def test_weak_root(self):
        self.assertEqual(morphology.weak_root('#.ل.د', 'وَلَد', 'noun'), 'و.ل.د')


@unittest.skipUnless(HAVE_DATA, 'no Arabic data (CAMeL Tools / tools/build_arabic_dic.py)')
class AnalyzerTestCase(unittest.TestCase):
    def translate(self, text):
        from arabic import analyzer
        from core import render
        return [[render.translate(c.predicate) for c in a.clauses] for a in analyzer.analyze_text(text)][0]

    def forms(self, text):
        from arabic import analyzer
        return analyzer.sentence_text(next(analyzer.analyze_text(text)).forms)

    def test_verbal_sentence(self):
        tr = self.translate('ذهب الولد إلى المدرسة.')[0]
        self.assertIn('少年', tr.split(' / ')[0])
        self.assertTrue(tr.split(' / ')[0].endswith('が'))
        self.assertIn('学校', tr)
        self.assertTrue(tr.endswith('行った'))

    def test_case_endings_in_header(self):
        # 選んだ格の語尾: 主語は主格 -u、前置詞の後ろは属格 -i、非限定の目的語は対格 -an
        self.assertEqual(self.forms('ذهب الولد إلى المدرسة.')[1], 'ḏahaba al-waladu ilā al-madrasati.')
        self.assertEqual(self.forms('كتب الطالب رسالة طويلة.')[1], 'kataba aṭ-ṭālibu risālatan ṭawīlatan.')

    def test_construct(self):
        self.assertIn('{先生の}本を', self.translate('قرأ الولد كتاب المعلم.')[0])

    def test_nominal_sentence(self):
        self.assertEqual(self.translate('الولد كبير.')[0].split(' / ')[-1], '大きい')
        self.assertEqual(self.translate('هذا كتاب.')[0], 'これは / 本である')
        self.assertIn('{この}本は', self.translate('هذا الكتاب جديد.')[0])

    def test_existential(self):
        tr = self.translate('في البيت رجل.')[0]
        self.assertTrue(tr.endswith('男が / いる'))

    def test_negation(self):
        self.assertTrue(self.translate('لم يذهب الولد إلى السوق.')[0].endswith('行かなかった'))
        self.assertTrue(self.translate('لن أذهب إلى السوق غدا.')[0].endswith('行かないだろう'))
        self.assertTrue(self.translate('ليس الولد في البيت.')[0].endswith('いない'))
        self.assertEqual(self.forms('لم يذهب الولد.')[0].split()[1], 'يَذْهَبْ')  # 要求法

    def test_inna(self):
        self.assertEqual(self.forms('إن الطالبات مجتهدات.')[1], 'inna aṭ-ṭālibāti muǧtahidātun.')  # 形は対格
        self.assertIn('学生は', self.translate('إن الطالبات مجتهدات.')[0])
        clauses = self.translate('قال إنه مريض.')
        self.assertEqual(len(clauses), 2)
        self.assertIn('彼は', clauses[1])

    def test_shared_subject_after_wa(self):
        clauses = self.translate('أكل الولد الخبز وشرب الماء.')
        self.assertIn('パンを', clauses[0])
        self.assertIn('水を', clauses[1])


if __name__ == '__main__':
    unittest.main()
