#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ペルシア語: 文字 (persian.script)、語形の解析 (persian.morphology)、文の解析 (persian.analyzer)。
# 辞書 (tools/build_persian_dic.py) が無ければ辞書を使う試験を飛ばす
#
import unittest

from persian import script, dictionary

HAVE_DATA = dictionary.available()


class ScriptTestCase(unittest.TestCase):
    def test_normalize_and_key(self):
        self.assertEqual(script.normalize('كتاب'), 'کتاب')               # アラビア文字の ك → ک
        self.assertEqual(script.normalize('علي'), 'علی')                 # ي → ی
        self.assertEqual(script.key('می‌روم'), 'میروم')                  # ZWNJ を除く

    def test_rough_translit(self):
        self.assertEqual(script.rough_translit('آی'), 'ây')


@unittest.skipUnless(HAVE_DATA, 'no Persian data (tools/build_persian_dic.py)')
class MorphologyTestCase(unittest.TestCase):
    def best(self, word):
        from persian import morphology
        return morphology.analyses(word)[0]

    def test_verbs(self):
        cases = {
            'می‌روم': ('miravam', 1, 'sg', 'present', False),       # mi- + 現在語幹 rav + -am
            'نرفتند': ('naraftand', 3, 'pl', 'perfect', True),      # 否定 + 過去語幹 + -and
            'می‌آید': ('miâyad', 3, 'sg', 'present', False),        # 母音で終わる語幹 + y
            'نمی‌دانم': ('nemidânam', 1, 'sg', 'present', True),
            'رفته‌ام': ('rafte-am', 1, 'sg', 'perfect', False),     # 現在完了
            'نوشت': ('nevešt', 3, 'sg', 'perfect', False),          # na- + وشت ではない
        }
        for word, (roman, person, number, tense, negative) in cases.items():
            item = self.best(word).main
            self.assertEqual((item['roman'], item['person'], item['number'], item['tense'], bool(item.get('negative'))),
                             (roman, person, number, tense, negative), word)

    def test_imperative(self):
        item = self.best('بیا').main
        self.assertEqual((item['roman'], item['mood']), ('biyâ', 'imperative'))

    def test_nominal_suffixes(self):
        a = self.best('کتاب‌هایم')                      # 本 + 複数 + 「私の」
        self.assertEqual(a.segments[0][1]['roman'], 'ketâbhâ')
        self.assertEqual(a.segments[1][1]['ja'], '私')
        a = self.best('خسته‌ام')                        # 形容詞 + 繋辞の接語「私は疲れている」
        self.assertEqual(a.segments[1][1]['pos'], 'verb')
        self.assertEqual(self.best('نامه‌ای').main['roman'], "nâme'i")  # 不定の -i (ZWNJ の前が本体)

    def test_relational_adjective(self):
        from persian import morphology
        self.assertEqual(morphology.relational_adjective('جهانی').main['pos'], 'adj')


@unittest.skipUnless(HAVE_DATA, 'no Persian data (tools/build_persian_dic.py)')
class AnalyzerTestCase(unittest.TestCase):
    def run_text(self, text):
        from persian import analyzer
        from core import render
        a = next(analyzer.analyze_text(text))
        return [render.translate(c.predicate) for c in a.clauses], analyzer.sentence_text(a.forms)[1]

    def test_present_with_dropped_subject(self):
        tr, roman = self.run_text('من به مدرسه می‌روم.')
        self.assertEqual(roman, 'man be madrese miravam.')
        self.assertTrue(tr[0].endswith('行く'))

    def test_ra_object(self):
        tr, _ = self.run_text('دانشجویان فارسی را می‌خوانند.')
        self.assertIn('ペルシア語を', tr[0])

    def test_ezafe(self):
        tr, roman = self.run_text('دختر کوچک گل‌های زیبا را دید.')
        self.assertEqual(roman, 'doxtar-e kučak golhâ-ye zibâ râ did.')   # 書かれないエザーフェを補う
        self.assertIn('{美しい}花を', tr[0])
        tr, roman = self.run_text('کتاب علی روی میز است.')
        self.assertTrue(roman.startswith('ketâb-e ali'))
        self.assertIn('{Aliの}本が', tr[0])

    def test_copula(self):
        self.assertEqual(self.run_text('این کتاب خوب است.')[0][0], '{この}本は / 良い')
        self.assertEqual(self.run_text('من خسته‌ام.')[0][0], '私は / 疲れている')

    def test_multiword_verbs(self):
        self.assertTrue(self.run_text('ما فردا به تهران خواهیم رفت.')[0][0].endswith('行くだろう'))
        self.assertTrue(self.run_text('این نامه دیروز نوشته شد.')[0][0].endswith('書かれた'))
        self.assertTrue(self.run_text('پدرم در خانه کار می‌کند.')[0][0].endswith('はたらく'))

    def test_negation(self):
        self.assertTrue(self.run_text('او به مدرسه نرفت.')[0][0].endswith('行かなかった'))


if __name__ == '__main__':
    unittest.main()
