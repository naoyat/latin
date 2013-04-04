#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from latin.latin_verb_reg import *
import latin.util

def decode_utf8(s):
    if isinstance(s, str):
        return s.decode('utf-8')
#    print s, s.__class__
#    if s is None:
    return None
#    else:

AMO = ('amō', 'amāvī', 'amātum', 'amāre')
MONEO = ('moneō', 'monuī', 'monitum', 'monēre')
REGO = ('regō', 'rēxī', 'rēctum', 'regere')
CAPIO = ('capiō', 'cēpī', 'captum', 'capere')
AUDIO = ('audiō', 'audīvī', 'audītum', 'audīre')

class LatinVerbTestCase(unittest.TestCase):
    def assert_conjugation_with_voice(self, actual, expected, sine_qua_non):
        actual_forms = {'active':[], 'passive':[]}
        for item in actual:
            for name, value in sine_qua_non.items():
                if not item.has_key(name) or item[name] != value:
                    self.fail("{'%s':'%s'} not exist" % (name, value))
            voice = item['voice']
            surface = item['surface']
            actual_forms[voice].append(surface)

        expected_forms = {'active':[], 'passive':[]}
        for voice, forms in expected.items():
            for form in forms:
                if isinstance(form, tuple):
                    expected_forms[voice] += map(decode_utf8, form)
                elif isinstance(form, str):
                    expected_forms[voice].append(form.decode('utf-8'))
                else:
                    pass

        if actual_forms != expected_forms:
            print "ACTUAL:", latin.util.render(actual_forms)
            print "EXPECTED:", latin.util.render(expected_forms)

        self.assertEqual(actual_forms, expected_forms)

    def assert_conjugation_with_gender(self, actual, expected, sine_qua_non):
        actual_forms = {'m':[], 'f':[], 'n':[]}
        for item in actual:
            for name, value in sine_qua_non.items():
                if not item.has_key(name) or item[name] != value:
                    self.fail("{'%s':'%s'} not exist" % (name, value))
            gender = item['gender']
            surface = item['surface']
            actual_forms[gender].append(surface)

        expected_forms = {'m':[], 'f':[], 'n':[]}
        for gender, forms in expected.items():
            for form in forms:
                if isinstance(form, tuple):
                    expected_forms[gender] += map(decode_utf8, form)
                elif isinstance(form, str):
                    expected_forms[gender].append(form.decode('utf-8'))
                else:
                    pass

        if actual_forms != expected_forms:
            print "ACTUAL:", latin.util.render(actual_forms)
            print "EXPECTED:", latin.util.render(expected_forms)

        self.assertEqual(actual_forms, expected_forms)


class PresentTestCase(LatinVerbTestCase):
    def assert_present_conjugation(self, type, params, expected):
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_present(type, pres1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'present'})

    def test_present_type1(self):
        self.assert_present_conjugation(CONJ_1, AMO, {
                'active':['amō', 'amās', 'amat', 'amāmus', 'amātis', 'amant'],
                'passive':['amor', ('amāris', 'amāre'), 'amātur', 'amāmur', 'amāminī', 'amantur']
                })

    def test_present_type2(self):
        self.assert_present_conjugation(CONJ_2, MONEO, {
                'active':['moneō', 'monēs', 'monet', 'monēmus', 'monētis', 'monent'],
                'passive':['moneor', ('monēris', 'monēre'), 'monētur', 'monēmur', 'monēminī', 'monentur']
                })

    def test_present_type3a(self):
        self.assert_present_conjugation(CONJ_3A, REGO, {
                'active':['regō', 'regis', 'regit', 'regimus', 'regitis', 'regunt'],
                'passive':['regor', ('regeris', 'regere'), 'regitur', 'regimur', 'regiminī', 'reguntur']
                })

    def test_present_type3b(self):
        self.assert_present_conjugation(CONJ_3B, CAPIO, {
                'active':['capiō', 'capis', 'capit', 'capimus', 'capitis', 'capiunt'],
                'passive':['capior', ('caperis', 'capere'), 'capitur', 'capimur', 'capiminī', 'capiuntur']
                })

    def test_present_type4(self):
        self.assert_present_conjugation(CONJ_4, AUDIO, {
                'active':['audiō', 'audīs', 'audit', 'audīmus', 'audītis', 'audiunt'],
                'passive':['audior', ('audīris', 'audīre'), 'audītur', 'audīmur', 'audīminī', 'audiuntur']
                })


class ImperativeTestCase(LatinVerbTestCase):
    def assert_imperative_conjugation(self, type, params, expected):
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_imperative(type, pres1sg)
        self.assert_conjugation_with_voice(actual, expected, {'mood':'imperative'})

    def test_imperative_type1(self):
        self.assert_imperative_conjugation(CONJ_1, AMO, {
                               'active':[None, 'amā', None, None, 'amāte', None,
                                         None, 'amātō', 'amātō', None, 'amātōte', 'amantō'],
                               'passive':[None, 'amāre', None, None, 'amāminī', None,
                                          None, 'amātor', 'amātor', None, None, 'amantor']
                               })

    def test_imperative_type2(self):
        self.assert_imperative_conjugation(CONJ_2, MONEO, {
                               'active':[None, 'monē', None, None, 'monēte', None,
                                         None, 'monētō', 'monētō', None, 'monētōte', 'monentō'],
                               'passive':[None, 'monēre', None, None, 'monēminī', None,
                                          None, 'monētor', 'monētor', None, None, 'monentor']
                               })

    def test_imperative_type3a(self):
        self.assert_imperative_conjugation(CONJ_3A, REGO, {
                               'active':[None, 'rege', None, None, 'regite', None,
                                         None, 'regitō', 'regitō', None, 'regitōte', 'reguntō'],
                               'passive':[None, 'regere', None, None, 'regiminī', None,
                                          None, 'regitor', 'regitor', None, None, 'reguntor']
                               })

    def test_imperative_type3b(self):
        self.assert_imperative_conjugation(CONJ_3B, CAPIO, {
                               'active':[None, 'cape', None, None, 'capite', None,
                                         None, 'capitō', 'capitō', None, 'capitōte', 'capiuntō'],
                               'passive':[None, 'capere', None, None, 'capiminī', None,
                                          None, 'capitor', 'capitor', None, None, 'capiuntor']
                               })

    def test_imperative_type4(self):
        self.assert_imperative_conjugation(CONJ_4, AUDIO, {
                               'active':[None, 'audī', None, None, 'audīte', None,
                                         None, 'audītō', 'audītō', None, 'audītōte', 'audiuntō'],
                               'passive':[None, 'audīre', None, None, 'audīminī', None,
                                          None, 'audītor', 'audītor', None, None, 'audiuntor']
                               })


class ImperfectTestCase(LatinVerbTestCase):
    def assert_imperfect_conjugation(self, type, params, expected):
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_imperfect(type, pres1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'imperfect'})

    def test_imperfect_type1(self):
        self.assert_imperfect_conjugation(CONJ_1, AMO, {
                'active':['amābam', 'amābās', 'amābat', 'amābāmus', 'amābātis', 'amābant'],
                'passive':['amābar', ('amābāris', 'amābāre'), 'amābātur', 'amābāmur', 'amābāminī', 'amābantur']
                })

    def test_imperfect_type2(self):
        self.assert_imperfect_conjugation(CONJ_2, MONEO, {
                'active':['monēbam', 'monēbās', 'monēbat', 'monēbāmus', 'monēbātis', 'monēbant'],
                'passive':['monēbar', ('monēbāris', 'monēbāre'), 'monēbātur', 'monēbāmur', 'monēbāminī', 'monēbantur']
                })

    def test_imperfect_type3A(self):
        self.assert_imperfect_conjugation(CONJ_3A, REGO, {
                'active':['regēbam', 'regēbās', 'regēbat', 'regēbāmus', 'regēbātis', 'regēbant'],
                'passive':['regēbar', ('regēbāris', 'regēbāre'), 'regēbātur', 'regēbāmur', 'regēbāminī', 'regēbantur']
                })

    def test_imperfect_type3B(self):
        self.assert_imperfect_conjugation(CONJ_3B, CAPIO, {
                'active':['capiēbam', 'capiēbās', 'capiēbat', 'capiēbāmus', 'capiēbātis', 'capiēbant'],
                'passive':['capiēbar', ('capiēbāris', 'capiēbāre'), 'capiēbātur', 'capiēbāmur', 'capiēbāminī', 'capiēbantur']
                })

    def test_imperfect_type4(self):
        self.assert_imperfect_conjugation(CONJ_4, AUDIO, {
                'active':['audiēbam', 'audiēbās', 'audiēbat', 'audiēbāmus', 'audiēbātis', 'audiēbant'],
                'passive':['audiēbar', ('audiēbāris', 'audiēbāre'), 'audiēbātur', 'audiēbāmur', 'audiēbāminī', 'audiēbantur']
                })


class FutureTestCase(LatinVerbTestCase):
    def assert_future_conjugation(self, type, params, expected):
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_future(type, pres1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'future'})

    def test_future_type1(self):
        self.assert_future_conjugation(CONJ_1, AMO, {
                'active':['amābō', 'amābis', 'amābit', 'amābimus', 'amābitis', 'amābunt'],
                'passive':['amābor', ('amāberis', 'amābere'), 'amābitur', 'amābimur', 'amābiminī', 'amābuntur']
                })

    def test_future_type2(self):
        self.assert_future_conjugation(CONJ_2, MONEO, {
                'active':['monēbō', 'monēbis', 'monēbit', 'monēbimus', 'monēbitis', 'monēbunt'],
                'passive':['monēbor', ('monēberis', 'monēbere'), 'monēbitur', 'monēbimur', 'monēbiminī', 'monēbuntur']
                })

    def test_future_type3A(self):
        self.assert_future_conjugation(CONJ_3A, REGO, {
                'active':['regam', 'regēs', 'reget', 'regēmus', 'regētis', 'regent'],
                'passive':['regar', ('regēris', 'regēre'), 'regētur', 'regēmur', 'regēminī', 'regentur']
                })

    def test_future_type3B(self):
        self.assert_future_conjugation(CONJ_3B, CAPIO, {
                'active':['capiam', 'capiēs', 'capiet', 'capiēmus', 'capiētis', 'capient'],
                'passive':['capiar', ('capiēris', 'capiēre'), 'capiētur', 'capiēmur', 'capiēminī', 'capientur']
                })

    def test_future_type4(self):
        self.assert_future_conjugation(CONJ_4, AUDIO, {
                'active':['audiam', 'audiēs', 'audiet', 'audiēmus', 'audiētis', 'audient'],
                'passive':['audiar', ('audiēris', 'audiēre'), 'audiētur', 'audiēmur', 'audiēminī', 'audientur']
                })


class PerfectTestCase(LatinVerbTestCase):
    def assert_perfect_conjugation(self, type, params, expected):
        _pres1sg, perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_perfect(perf1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'perfect'})

    def test_perfect_type1(self):
        self.assert_perfect_conjugation(CONJ_1, AMO, {
                'active':['amāvī', 'amāvistī', 'amāvit', 'amāvimus', 'amāvistis', ('amāvērunt', 'amāvēre')],
                })

    def test_perfect_type2(self):
        self.assert_perfect_conjugation(CONJ_2, MONEO, {
                'active':['monuī', 'monuistī', 'monuit', 'monuimus', 'monuistis', ('monuērunt', 'monuēre')]
                })

    def test_perfect_type3A(self):
        self.assert_perfect_conjugation(CONJ_3A, REGO, {
                'active':['rēxī', 'rēxistī', 'rēxit', 'rēximus', 'rēxistis', ('rēxērunt', 'rēxēre')]
                })

    def test_perfect_type3B(self):
        self.assert_perfect_conjugation(CONJ_3B, CAPIO, {
                'active':['cēpī', 'cēpistī', 'cēpit', 'cēpimus', 'cēpistis', ('cēpērunt', 'cēpēre')]
                })

    def test_perfect_type4(self):
        self.assert_perfect_conjugation(CONJ_4, AUDIO, {
                'active':['audīvī', 'audīvistī', 'audīvit', 'audīvimus', 'audīvistis', ('audīvērunt', 'audīvēre')]
                })

#    def test_perfect_sum(self):
#        self.assert_perfect_conjugation(None, 'sum', {
#                'active':['fuī', 'fuistī', 'fuit', 'fuimus', 'fuistis', ('fuērunt', 'fuēre')]
#                })

class PastPerfectTestCase(LatinVerbTestCase):
    def assert_past_perfect_conjugation(self, type, params, expected):
        _pres1sg, perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_past_perfect(perf1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'past-perfect'})

    def test_past_perfect_type2(self):
        self.assert_past_perfect_conjugation(CONJ_2, MONEO, {
                'active':['monueram', 'monuerās', 'monuerat', 'monuerāmus', 'monuerātis', 'monuerānt']
                })


class FuturePerfectTestCase(LatinVerbTestCase):
    def assert_future_perfect_conjugation(self, type, params, expected):
        _pres1sg, perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_future_perfect(perf1sg)
        self.assert_conjugation_with_voice(actual, expected, {'tense':'future-perfect'})

    def test_future_perfect_type3A(self):
        self.assert_future_perfect_conjugation(CONJ_3A, REGO, {
                'active':['rēxerō', 'rēxeris', 'rēxerit', 'rēxerimus', 'rēxeritis', 'rēxerint']
                })


class PassivePerfectTestCase(LatinVerbTestCase):
    def assert_passive_perfect_conjugation(self, type, params, expected):
        _pres1sg, _perf1sg, supinum, _inf = map(decode_utf8, params)
        actual = conjugate_passive_perfect(supinum)
        self.assert_conjugation_with_gender(actual, expected, {'voice':'passive', 'tense':'perfect'})

    def test_passive_perfect_type1(self):
        self.assert_passive_perfect_conjugation(CONJ_1, AMO, {
                'm':['amātus sum', 'amātus es', 'amātus est', 'amātī sumus', 'amātī estis', 'amātī sunt'],
                'f':['amāta sum', 'amāta es', 'amāta est', 'amātae sumus', 'amātae estis', 'amātae sunt'],
                'n':['amātum sum', 'amātum es', 'amātum est', 'amāta sumus', 'amāta estis', 'amāta sunt']
                })


class PassivePastPerfectTestCase(LatinVerbTestCase):
    def assert_passive_past_perfect_conjugation(self, type, params, expected):
        _pres1sg, _perf1sg, supinum, _inf = map(decode_utf8, params)
        actual = conjugate_passive_past_perfect(supinum)
        self.assert_conjugation_with_gender(actual, expected, {'voice':'passive', 'tense':'past-perfect'})

    def test_passive_past_perfect_type1(self):
        self.assert_passive_past_perfect_conjugation(CONJ_1, AMO, {
                'm':['amātus eram', 'amātus erās', 'amātus erat', 'amātī erāmus', 'amātī erātis', 'amātī erant'],
                'f':['amāta eram', 'amāta erās', 'amāta erat', 'amātae erāmus', 'amātae erātis', 'amātae erant'],
                'n':['amātum eram', 'amātum erās', 'amātum erat', 'amāta erāmus', 'amāta erātis', 'amāta erant'],
                })


class PassiveFuturePerfectTestCase(LatinVerbTestCase):
    def assert_passive_future_perfect_conjugation(self, type, params, expected):
        _pres1sg, _perf1sg, supinum, _inf = map(decode_utf8, params)
        actual = conjugate_passive_future_perfect(supinum)
        self.assert_conjugation_with_gender(actual, expected, {'voice':'passive', 'tense':'future-perfect'})

    def test_passive_future_perfect_type1(self):
        self.assert_passive_future_perfect_conjugation(CONJ_1, AMO, {
                'm':['amātus erō', 'amātus eris', 'amātus erit', 'amātī erimus', 'amātī eritis', 'amātī erunt'],
                'f':['amāta erō', 'amāta eris', 'amāta erit', 'amātae erimus', 'amātae eritis', 'amātae erunt'],
                'n':['amātum erō', 'amātum eris', 'amātum erit', 'amāta erimus', 'amāta eritis', 'amāta erunt'],
                })


class SubjunctivePresentTestCase(LatinVerbTestCase):
    def assert_subjunctive_present_conjugation(self, type, params, expected):
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_subjunctive_active_present(type, pres1sg) \
            + conjugate_subjunctive_passive_present(type, pres1sg)
        self.assert_conjugation_with_voice(actual, expected, {'mood':'subjunctive', 'tense':'present'})

    def test_subjunctive_present_type1(self):
        self.assert_subjunctive_present_conjugation(CONJ_1, AMO, {
                'active':['amem', 'amēs', 'amet', 'amēmus', 'amētis', 'ament'],
                'passive':['amer', ('amēris', 'amēre'), 'amētur', 'amēmur', 'amēminī', 'amentur']
                })

    def test_subjunctive_present_type2(self):
        self.assert_subjunctive_present_conjugation(CONJ_2, MONEO, {
                'active':['moneam', 'moneās', 'moneat', 'moneāmus', 'moneātis', 'moneant'],
                'passive':['monear', ('moneāris', 'moneāre'), 'moneātur', 'moneāmur', 'moneāminī', 'moneantur']
                })

    def test_subjunctive_present_type3A(self):
        self.assert_subjunctive_present_conjugation(CONJ_3A, REGO, {
                'active':['regam', 'regās', 'regat', 'regāmus', 'regātis', 'regant'],
                'passive':['regar', ('regāris', 'regāre'), 'regātur', 'regāmur', 'regāminī', 'regantur']
                })

    def test_subjunctive_present_type3B(self):
        self.assert_subjunctive_present_conjugation(CONJ_3B, CAPIO, {
                'active':['capiam', 'capiās', 'capiat', 'capiāmus', 'capiātis', 'capiant'],
                'passive':['capiar', ('capiāris', 'capiāre'), 'capiātur', 'capiāmur', 'capiāminī', 'capiantur']
                })

    def test_subjunctive_present_type4(self):
        self.assert_subjunctive_present_conjugation(CONJ_4, AUDIO, {
                'active':['audiam', 'audiās', 'audiat', 'audiāmus', 'audiātis', 'audiant'],
                'passive':['audiar', ('audiāris', 'audiāre'), 'audiātur', 'audiāmur', 'audiāminī', 'audiantur']
                })


class SubjunctiveImperfectTestCase(LatinVerbTestCase):
    def assert_subjunctive_imperfect_conjugation(self, type, params, expected):
        _pres1sg, _perf1sg, _supinum, inf = map(decode_utf8, params)
        actual = conjugate_subjunctive_active_imperfect(inf) \
            + conjugate_subjunctive_passive_imperfect(inf)
        self.assert_conjugation_with_voice(actual, expected, {'mood':'subjunctive', 'tense':'imperfect'})

    def test_subjunctive_imperfect_type1(self):
        self.assert_subjunctive_imperfect_conjugation(CONJ_1, AMO, {
                'active':['amārem', 'amārēs', 'amāret', 'amārēmus', 'amārētis', 'amārent'],
                'passive':['amārer', ('amārēris', 'amārēre'), 'amārētur', 'amārēmur', 'amārēminī', 'amārentur']
                })

    def test_subjunctive_imperfect_type2(self):
        self.assert_subjunctive_imperfect_conjugation(CONJ_2, MONEO, {
                'active':['monērem', 'monērēs', 'monēret', 'monērēmus', 'monērētis', 'monērent'],
                'passive':['monērer', ('monērēris', 'monērēre'), 'monērētur', 'monērēmur', 'monērēminī', 'monērentur']
                })

    def test_subjunctive_imperfect_type3A(self):
        self.assert_subjunctive_imperfect_conjugation(CONJ_3A, REGO, {
                'active':['regerem', 'regerēs', 'regeret', 'regerēmus', 'regerētis', 'regerent'],
                'passive':['regerer', ('regerēris', 'regerēre'), 'regerētur', 'regerēmur', 'regerēminī', 'regerentur']
                })

    def test_subjunctive_imperfect_type3B(self):
        self.assert_subjunctive_imperfect_conjugation(CONJ_3B, CAPIO, {
                'active':['caperem', 'caperēs', 'caperet', 'caperēmus', 'caperētis', 'caperent'],
                'passive':['caperer', ('caperēris', 'caperēre'), 'caperētur', 'caperēmur', 'caperēminī', 'caperentur']
                })

    def test_subjunctive_imperfect_type4(self):
        self.assert_subjunctive_imperfect_conjugation(CONJ_4, AUDIO, {
                'active':['audīrem', 'audīrēs', 'audīret', 'audīrēmus', 'audīrētis', 'audīrent'],
                'passive':['audīrer', ('audīrēris', 'audīrēre'), 'audīrētur', 'audīrēmur', 'audīrēminī', 'audīrentur']
                })


class SubjunctivePerfectTestCase(LatinVerbTestCase):
    def assert_subjunctive_perfect_conjugation(self, type, params, expected):
        _pres1sg, perf1sg, supinum, _inf = map(decode_utf8, params)
        actual = conjugate_subjunctive_active_perfect(perf1sg)
        self.assert_conjugation_with_voice(actual,
                                           {'active':expected['active'], 'passive':[]},
                                           {'mood':'subjunctive', 'voice':'active', 'tense':'perfect'})
        actual = conjugate_subjunctive_passive_perfect(supinum)
        self.assert_conjugation_with_gender(actual,
                                            expected['passive'],
                                            {'mood':'subjunctive', 'voice':'passive', 'tense':'perfect'})

    def test_subjunctive_perfect_type1(self):
        self.assert_subjunctive_perfect_conjugation(CONJ_1, AMO, {
                'active':['amāverim', 'amāveris', 'amāverit', 'amāverimus', 'amāveritis', 'amāverint'],
                'passive':{'m':['amātus sim', 'amātus sīs', 'amātus sit', 'amātī sīmus', 'amātī sītis', 'amātī sint'],
                           'f':['amāta sim', 'amāta sīs', 'amāta sit', 'amātae sīmus', 'amātae sītis', 'amātae sint'],
                           'n':['amātum sim', 'amātum sīs', 'amātum sit', 'amāta sīmus', 'amāta sītis', 'amāta sint']}
                })


class SubjunctivePastPerfectTestCase(LatinVerbTestCase):
    def assert_subjunctive_past_perfect_conjugation(self, type, params, expected):
        _pres1sg, perf1sg, supinum, _inf = map(decode_utf8, params)
        actual = conjugate_subjunctive_active_past_perfect(perf1sg)
        self.assert_conjugation_with_voice(actual,
                                           {'active':expected['active'], 'passive':[]},
                                           {'mood':'subjunctive', 'voice':'active', 'tense':'past-perfect'})
        actual = conjugate_subjunctive_passive_past_perfect(supinum)
        self.assert_conjugation_with_gender(actual,
                                            expected['passive'],
                                            {'mood':'subjunctive', 'voice':'passive', 'tense':'past-perfect'})

    def test_subjunctive_past_perfect_type1(self):
        self.assert_subjunctive_past_perfect_conjugation(CONJ_1, AMO, {
                'active':['amāvissem', 'amāvissēs', 'amāvisset', 'amāvissēmus', 'amāvissētis', 'amāvissent'],
                'passive':{'m':['amātus essem', 'amātus essēs', 'amātus esset', 'amātī essēmus', 'amātī essētis', 'amātī essent'],
                           'f':['amāta essem', 'amāta essēs', 'amāta esset', 'amātae essēmus', 'amātae essētis', 'amātae essent'],
                           'n':['amātum essem', 'amātum essēs', 'amātum esset', 'amāta essēmus', 'amāta essētis', 'amāta essent']}
                })

class GerundiveTestCase(LatinVerbTestCase):
    def assert_gerundive_conjugation(self, type, params, expected):
        def forms(actual):
            return [item['surface'] for item in actual]
        pres1sg, _perf1sg, _supinum, _inf = map(decode_utf8, params)
        actual = conjugate_gerundive(type, pres1sg)
        self.assertEqual(forms(actual), map(decode_utf8, expected['gerundive']))
        actual = conjugate_gerund(type, pres1sg)
        self.assertEqual(forms(actual), map(decode_utf8, expected['gerund']))

    def test_gerundive_type1(self):
        self.assert_gerundive_conjugation(CONJ_1, AMO, {
                'gerundive':['amandus', 'amanda', 'amandum'],
                'gerund':['amandum', 'amandī']
                })

class InfinitiveTestCase(LatinVerbTestCase):
    def assert_infinitive_conjugation(self, type, params, expected):
        pres1sg, perf1sg, supinum, inf = map(decode_utf8, params)
        actual = conjugate_infinitive(type, inf, perf1sg, supinum)
        self.assert_conjugation_with_voice(actual, expected, {'mood':'infinitive'})

    def test_infinitive_type1(self):
        self.assert_infinitive_conjugation(CONJ_1, AMO, {
                'active':['amāre', 'amāvisse', ('amātūrus esse', 'amātūra esse', 'amātūrum esse')],
                'passive':['amārī', ('amātus esse', 'amāta esse', 'amātum esse'), 'amātum īrī']
                })

    def test_infinitive_type3a(self):
        self.assert_infinitive_conjugation(CONJ_3A, REGO, {
                'active':['regere', 'rēxisse', ('rēctūrus esse', 'rēctūra esse', 'rēctūrum esse')],
                'passive':['regī', ('rēctus esse', 'rēcta esse', 'rēctum esse'), 'rēctum īrī']
                })


class ParticipleTestCase(LatinVerbTestCase):
    def assert_participle_conjugation(self, type, params, expected):
        pres1sg, perf1sg, supinum, inf = map(decode_utf8, params)
        actual = conjugate_participle(type, inf, perf1sg, supinum)
        self.assert_conjugation_with_voice(actual, expected, {'pos':'participle'})





if __name__ == '__main__':
    unittest.main()
