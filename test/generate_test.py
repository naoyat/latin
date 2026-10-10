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


class PeriphrasticTestCase(unittest.TestCase):
    def test_deponent_perfect(self):
        # 繋辞 + 形式受動態動詞の完了分詞 (prōgressus est) → 完了の能動、ふつうの動詞の分詞 → 受動
        from dragoman.generate.frame import Clause, NP
        participle = NP(Lex('prōgressus', 'participle', '', verb='prōgredior', ptense='past'))
        clause = Clause(Lex('sum', 'verb'), copula=True, args=[('complement', participle)])
        again = frame.periphrastic(clause)
        self.assertEqual((again.verb.lemma, again.tense, again.voice, again.copula, again.args),
                         ('prōgredior', 'perfect', 'active', False, []))
        participle = NP(Lex('occīsus', 'participle', '', verb='occīdō', ptense='past'))
        clause = Clause(Lex('sum', 'verb'), tense='imperfect', copula=True, args=[('complement', participle)])
        self.assertEqual((frame.periphrastic(clause).tense, frame.periphrastic(clause).voice),
                         ('past-perfect', 'passive'))


class QuestionTestCase(unittest.TestCase):
    """間接疑問: 解析で支配する動詞の格の枠 'Q' に入れ、文の枠では questions に"""

    def test_analysis_and_frame(self):
        analysis, = analyzer.analyze_text('Magister rogāvit quis cantāret.')
        self.assertEqual(len(analysis.clauses), 1)
        question, = analysis.clauses[0].predicate.case_slot['Q']
        self.assertEqual((question.word.surface, question.predicate.surface), ('quis', 'cantāret'))
        self.assertEqual(question.translate()[0][-3:], '}かを')
        main, = frame.frames(analysis)
        self.assertEqual([q.question_word for q in main.questions], ['quis'])
        self.assertEqual(latin.sentence([main]), 'Magister quis cantāret rogāvit.')

    def test_relative_is_not_a_question(self):
        # 先行詞 (性・数の一致する名詞) のすぐ後ろの quem は関係代名詞
        analysis, = analyzer.analyze_text('Puer magistrum quem puella amet videt.')
        self.assertFalse(any('Q' in c.predicate.case_slot for c in analysis.clauses))

    def test_not_a_question(self):
        # 支配する動詞が問う・知る類でなければ入れない (ubi + 接続法の時の節)
        analysis, = analyzer.analyze_text('Puer cantat ubi puella dormiat.')
        self.assertFalse(any('Q' in c.predicate.case_slot for c in analysis.clauses))


class RelativeTestCase(unittest.TestCase):
    """関係節: 先行詞の名詞に付き、関係代名詞の格を空所の役割として持つ"""

    def test_analysis(self):
        analysis, = analyzer.analyze_text('Puella puerum videt quem magister laudat.')
        self.assertEqual(len(analysis.clauses), 1)
        relative, = analysis.relatives
        self.assertEqual((relative.antecedent.surface, relative.pronoun.surface, relative.gap),
                         ('puerum', 'quem', 'Acc'))
        self.assertIn('{教師,先生が 称賛する,ほめる}少年を', analysis.clauses[0].predicate.translate()[0])

    def test_subject_gap(self):
        # 主格・対格のどちらにも読める quae は、先行詞との一致と節の空きで主格 (主語を補わない)
        analysis, = analyzer.analyze_text('Puella cantat quae in hortō sedet.')
        self.assertEqual(analysis.relatives[0].gap, 'Nom')
        self.assertTrue(analysis.clauses[0].predicate.translate()[0].startswith('{{庭}'))

    def test_relative_before_antecedent(self):
        # 先行詞より前の関係節 (相関の形): 後ろの節の指示代名詞が先行詞。日本語は「{…する}人」
        analysis, = analyzer.analyze_text('Quem puella amat, eum magister laudat.')
        relative, = analysis.relatives
        self.assertEqual((relative.antecedent.surface, relative.gap), ('eum', 'Acc'))
        self.assertIn('{少女が 愛する}人を', analysis.clauses[0].predicate.translate()[0])

    def test_connecting_relative(self):
        # 文頭の関係代名詞 + 従属の接続詞 (Quod cum …「それを … したとき」) は前の文を指す。関係節にしない
        analysis, = analyzer.analyze_text('Quod cum puella vīdisset, eum magister laudāvit.')
        self.assertEqual(analysis.relatives, [])

    def test_comparative_quam(self):
        analysis, = analyzer.analyze_text('Nēmō clārior erat quam Hector.')
        self.assertEqual(analysis.relatives, [])

    def test_latin(self):
        # 関係節は先行詞のすぐ後ろに戻す (関係節が主節の動詞の前に入った文の解析はまだできない)
        self.assertEqual(latin.sentence(clauses('Puella puerum videt quem magister laudat.')),
                         'Puella puerum quem magister laudat videt.')
        self.assertEqual(latin.sentence(clauses('Puella cantat quae in hortō sedet.')),
                         'Puella quae in hortō sedet cantat.')


class ConnectiveTestCase(unittest.TestCase):
    """文をつなぐ語・従属節の接続詞"""

    def test_frame(self):
        main, = clauses('Puella autem cantat.')
        self.assertEqual(main.connectives, ['autem'])
        sub, main = clauses('Ubi puella cantat, puer dormit.')
        self.assertEqual((sub.subordinator, sub.after_main, main.subordinator), ('ubi', False, ''))
        main, = clauses('Puer ad hortum venit ubi puella cantat.')
        garden = main.role('prep')[0]   # 名詞のすぐ後ろの ubi は関係節「〜するところの」
        self.assertEqual([(r.gap, r.relative.surface) for r in garden.relatives], [('place', 'ubi')])

    def test_latin(self):
        # 後置の語 (autem, igitur) は節の2語目に
        for text in ('Puella autem cantat.', 'Agricola igitur nautam amat.', 'Ubi puella cantat, puer dormit.'):
            self.assertEqual(latin.sentence(clauses(text)), text)

    def test_sanskrit_correlative(self):
        from dragoman.generate import connectives
        sub, main = clauses('Ubi puella cantat, puer dormit.')
        self.assertEqual(connectives.join([sub, main], ['A', 'B'], 'sa'), 'yadA A tadA B')   # yadā … tadā …
        self.assertEqual(connectives.join([sub, main], ['A', 'B'], 'en'), 'when A, B')


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

    def test_connectives(self):
        self.assertEqual(self.english('Ubi puella cantat, puer dormit.'), 'When the girl sings, the boy sleeps.')
        self.assertEqual(self.english('Puer ad hortum venit ubi puella cantat.'),
                         'The boy comes to the garden where the girl sings.')
        self.assertEqual(self.english('Puella puerum videt quem magister laudat.'),
                         'The girl sees the boy whom the teacher praises.')
        self.assertEqual(self.english('Quem puella amat, eum magister laudat.'),
                         'The teacher praises him whom the girl loves.')

    def test_indirect_question(self):
        self.assertEqual(self.english('Magister rogāvit quis cantāret.'), 'The teacher asked who was singing.')
        self.assertEqual(self.english('Rēx rogat quid puer videat.'), 'The king asks what the boy sees.')
        self.assertEqual(self.english('Puella nescit quis cantet.'), 'The girl does not know who sings.')

    def test_homographs(self):
        # 同綴の語は解析の日本語の訳語で (volō「飛ぶ」/「望む」)、決まらなければ語形と基本形で (appellō)
        self.assertEqual(english.gloss(Lex('volō', 'verb', '飛ぶ')), 'fly')
        self.assertEqual(english.gloss(Lex('volō', 'verb', '願う,欲しい')), 'wish')
        self.assertEqual(english.gloss(Lex('appellō', 'verb', '?', surface='appellābātur')), 'address as')
        self.assertEqual(english.gloss(Lex('appellō', 'participle', '?', surface='appulsa')),
                         'drive or move to')

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
        # 優先表の語だけの文 (英梵辞典の表の有無で変わらない)。形容詞は名詞の性に一致 (sundaram pustakam)
        self.assertEqual(self.sanskrit('Puella librum pulchrum in hortō videt.'),
                         'bālikā sundaram pustakam udyāne paśyati ।')
        self.assertEqual(self.sanskrit('Puer ā magistrō laudātur.'), 'bālakaḥ adhyāpakena praśasyate ।')

    def test_government(self):
        # bhī「恐れる」は奪格を取る
        self.assertEqual(self.sanskrit('Agricola nautam nōn timet.'), 'kṛṣakaḥ nāvikāt na bibheti ।')

    def test_possessive(self):
        self.assertEqual(self.sanskrit('Mihi est liber.'), 'mama pustakam asti ।')

    def test_participles(self):
        # 分詞はもとの動詞の語根から: 現在 → śānac / śatṛ、完了 → kta、形式受動態 → ktavatu、動形容詞 → tavya
        def form(lemma, verb, ptense, linga='m', case='Nom'):
            return sanskrit.participle_from_lex(Lex(lemma, 'participle', '', verb=verb, ptense=ptense),
                                                linga, case, 'sg')
        self.assertEqual(form('fugiēns', 'fugiō', 'present', case='Acc'), 'palAyamAnam')
        self.assertEqual(form('laudāta', 'laudō', 'past', 'f'), 'praSastA')
        self.assertEqual(form('locūtus', 'loquor', 'past'), 'uditavAn')
        self.assertEqual(form('cantandus', 'cantō', 'future', 'n'), 'gAtavyam')



from dragoman.generate import from_japanese  # noqa: E402


@unittest.skipUnless(from_japanese.available(), 'MeCab が無い')
class JapaneseInputTestCase(unittest.TestCase):
    """日本語の文 → 文の枠 → ラテン語"""

    def latin(self, text):
        return latin.sentence(from_japanese.parse(text))

    def test_simple(self):
        self.assertEqual(self.latin('少女が庭で美しい薔薇を見た。'), 'Puella rosam pulchram in hortō vīdit.')
        self.assertEqual(self.latin('農夫は水夫を愛さない。'), 'Agricola nautam nōn amat.')

    def test_passive_agent(self):
        self.assertEqual(self.latin('少年は先生に褒められた。'), 'Puer ā magistrō laudātus est.')

    def test_relative_clause(self):
        # 連体修飾節: 空所は節の中で欠けている格 (褒める は他動詞で が があるので目的語)
        self.assertEqual(self.latin('先生が褒める少年は本を読んでいた。'), 'Puer quem magister laudat librum legēbat.')

    def test_complement_clauses(self):
        self.assertEqual(self.latin('私は少女が歌うのを見た。'), 'Puellam cantāre vīdī.')
        self.assertEqual(self.latin('少年は少女が来ると言った。'), 'Puer puellam venīre dīxit.')
        self.assertEqual(self.latin('あなたは誰が来たか知らない。'), 'Quis vēnerit nōn scīs.')

    def test_subordinate_clauses(self):
        self.assertEqual(self.latin('少年が庭で寝ているとき、少女は歌った。'),
                         'Ubi puer in hortō dormiēbat, puella cantāvit.')


    def test_round_trip(self):
        # 日本語 → 文の枠 → 日本語 (語はラテン語の見出しの訳語に置き換わる: 先生 → 教師)
        from dragoman.generate import japanese
        for text in ('私は少女が歌うのを見た。', '少年は少女が来ると言った。', 'あなたは誰が来たか知らない。'):
            self.assertEqual(japanese.sentence(from_japanese.parse(text)), text)
        self.assertEqual(japanese.sentence(from_japanese.parse('少年は先生に褒められた。')), '少年は教師に称賛された。')


class JapaneseOutputTestCase(unittest.TestCase):
    """ラテン語 → 文の枠 → 日本語"""

    def japanese(self, text):
        from dragoman.generate import japanese
        return japanese.sentence(clauses(text))

    def test_relative_and_passive(self):
        self.assertEqual(self.japanese('Puella puerum videt quem magister laudat.'),
                         '少女は教師が称賛する少年を見る。')
        self.assertEqual(self.japanese('Puer ā magistrō laudātur.'), '少年は教師に称賛される。')


if __name__ == '__main__':
    unittest.main()
