#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# 解析の結果 (格の枠) から文を作る: ラテン語に戻す (手作りの辞書だけで) と、英語にする (英語の訳語の表があれば)
#
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragoman.core import paths  # noqa: E402
from dragoman.latin import latindic, analyzer  # noqa: E402
from dragoman.generate import frame, english, latin, russian, sanskrit  # noqa: E402
from dragoman.generate.frame import Lex  # noqa: E402

_saved = None


def setUpModule():
    global _saved
    latindic.load()
    _saved = (latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER)
    latindic.LatinDic.use_wiktionary = False
    analyzer.USE_TAGGER = False


def tearDownModule():
    latindic.LatinDic.use_wiktionary, analyzer.USE_TAGGER = _saved


def clauses(text):
    analyses = list(analyzer.analyze_text(text))
    assert len(analyses) == 1, analyses
    return frame.frames(analyses[0])


class FrameTestCase(unittest.TestCase):
    def test_roles(self):
        c, = clauses('Puella rosam pulchram in hortō videt.')
        self.assertEqual((c.verb.lemma, c.tense, c.person, c.number), ('videō', 'present', 3, 'sg'))
        self.assertEqual([(r, np.head.lemma) for r, np in c.args],
                         [('subject', 'puella'), ('object', 'rosa'), ('prep', 'hortus')])
        rose = c.role('object')[0]
        self.assertEqual([m.lemma for m in rose.modifiers], ['pulcher'])
        self.assertEqual(c.role('prep')[0].prep.lemma, 'in')

    def test_infinitive_kind(self):
        c, = clauses('Mārcus puerōs in hortō lūdere dīcit.')
        inner, = c.infinitives
        self.assertEqual((inner.verb.lemma, inner.infinitive_kind), ('lūdō', 'saying'))

    def test_pronoun_lemma(self):
        c, = clauses('Haec puella illum puerum videt.')
        self.assertEqual([m.lemma for m in c.role('object')[0].modifiers], ['ille'])


class LatinRegenerationTestCase(unittest.TestCase):
    """解析 → 文の枠 → ラテン語 で元の文に戻る"""

    def again(self, text):
        return latin.sentence(clauses(text))

    def test_same_sentence(self):
        for text in ('Puella rosam pulchram in hortō videt.',
                     'Agricola nautam nōn amat.',
                     'Puerī et puellae cantant.',
                     'Rosae līliaque flōrent.',
                     'Et puer et puella cantant.',
                     'Fīlia agricolae rosās pulchrās amat.',
                     'Haec puella illum puerum videt.',
                     'Puer ā magistrō laudātur.'):
            self.assertEqual(self.again(text), text)

    def test_word_order(self):
        # 受け手 (与格) は目的語の前に置く
        self.assertEqual(self.again('Magister librōs puerīs dat.'), 'Magister puerīs librōs dat.')

    def test_accusative_subject_of_infinitive(self):
        self.assertEqual(self.again('Magister puerōs in hortō lūdere dīcit.'),
                         'Magister puerōs in hortō lūdere dīcit.')

    def test_complement_agreement(self):
        self.assertEqual(self.again('Puellae pulchrae erant.'), 'Puellae pulchrae erant.')


class EnglishMorphologyTestCase(unittest.TestCase):
    def test_verbs(self):
        self.assertEqual(english.third_singular('carry'), 'carries')
        self.assertEqual(english.third_singular('be fond of'), 'is fond of')
        self.assertEqual(english.past('see'), 'saw')
        self.assertEqual(english.past('love'), 'loved')
        self.assertEqual(english.past_participle('give'), 'given')
        self.assertEqual(english.present_participle('run'), 'running')
        self.assertEqual(english.present_participle('make'), 'making')

    def test_nouns(self):
        self.assertEqual(english.plural('rose'), 'roses')
        self.assertEqual(english.plural('city'), 'cities')
        self.assertEqual(english.plural('child'), 'children')


@unittest.skipUnless(os.path.exists(paths.data('la-en.tsv')), 'la-en.tsv が無い (tools/build_latin_english.py)')
class EnglishTestCase(unittest.TestCase):
    def english(self, text):
        return english.sentence(clauses(text))

    def test_sentences(self):
        self.assertEqual(self.english('Puella rosam pulchram in hortō videt.'),
                         'The girl sees the beautiful rose in the garden.')
        self.assertEqual(self.english('Agricola nautam nōn amat.'), 'The farmer does not love the sailor.')
        self.assertEqual(self.english('Puer ā magistrō laudātur.'), 'The boy is praised by the teacher.')
        self.assertEqual(self.english('Puellae in silvā ambulābant.'), 'The girls were walking in the forest.')

    def test_gloss_follows_japanese(self):
        # Wiktionary の最初の訳語 (traverse) ではなく、解析の日本語「歩く」に合う walk
        self.assertEqual(english.gloss(Lex('ambulō', 'verb', '歩く')), 'walk')



@unittest.skipUnless(russian.available() and english.gloss(Lex('puella', 'noun', '少女')),
                     'pymorphy3 か ru/en-index.tsv・la-en.tsv が無い')
class RussianTestCase(unittest.TestCase):
    def russian(self, text):
        return russian.sentence(clauses(text))

    def test_cases_and_agreement(self):
        self.assertEqual(self.russian('Puella rosam pulchram in hortō videt.'), 'Девочка видит красивую розу в саду.')
        self.assertEqual(self.russian('Puellae pulchrae erant.'), 'Девочки были красивые.')

    def test_aspect_and_passive(self):
        # 完了の受動 → был + 完了体の短語尾受動分詞、動作主は造格
        self.assertEqual(self.russian('Puer ā magistrō nōn laudātus est.'), 'Мальчик не был похвален учителем.')

    def test_possessive_dative(self):
        self.assertEqual(self.russian('Mihi est liber.'), 'У меня есть книга.')


@unittest.skipUnless(sanskrit.available() and english.gloss(Lex('puella', 'noun', '少女')),
                     'vidyut か sa/en-index.tsv・la-en.tsv が無い')
class SanskritTestCase(unittest.TestCase):
    def sanskrit(self, text):
        return sanskrit.sentence(clauses(text)).split('\n')[0]

    def test_cases(self):
        self.assertEqual(self.sanskrit('Puella rosam pulchram in hortō videt.'),
                         'bālikā sundarīm javām udyāne paśyati ।')
        self.assertEqual(self.sanskrit('Puer ā magistrō laudātur.'), 'bālakaḥ adhyāpakena praśasyate ।')

    def test_government(self):
        # bhī「恐れる」は奪格を取る
        self.assertEqual(self.sanskrit('Agricola nautam nōn timet.'), 'kṛṣakaḥ nāvikāt na bibheti ।')

    def test_possessive(self):
        self.assertEqual(self.sanskrit('Mihi est liber.'), 'mama pustakam asti ।')


if __name__ == '__main__':
    unittest.main()
