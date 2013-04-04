#!/usr/bin/env python
# -*- coding: utf-8 -*-

import verb
import unittest

class VerbTestCase(unittest.TestCase):
    def test_pres1sg_to_presstem(self):
        f = verb.pres1sg_to_presstem
        self.assertEqual(f("amO"), "amA") # 1
        self.assertEqual(f("moneO"), "monE") # 2
        self.assertEqual(f("regO"), "rege") # 3A
        self.assertEqual(f("capiO"), "cape") # 3B
        self.assertEqual(f("audiO"), "audI") # 4

    def test_pres1sg_to_inf(self):
        f = verb.pres1sg_to_inf
        self.assertEqual(f("amO"), "amAre") # 1
        self.assertEqual(f("moneO"), "monEre") # 2
        self.assertEqual(f("regO"), "regere") # 3A
        self.assertEqual(f("capiO"), "capere") # 3B
        self.assertEqual(f("audiO"), "audIre") # 4

    def test_inf_to_pres1sg(self):
        f = verb.inf_to_pres1sg
        self.assertEqual(f("amAre"), "amO") # 1
        self.assertEqual(f("monEre"), "moneO") # 2
        self.assertEqual(f("regere"), "regO") # 3A
        self.assertEqual(f("capere"), "capiO") # 3B
        self.assertEqual(f("audIre"), "audiO") # 4

    def test_conj_present(self):
        f = verb.conj_present
        self.assertEqual(f("amO"), ['amO', 'amAs', 'amat', 'amAmus', 'amAtis', 'amant'])
        self.assertEqual(f("moneO"), ['moneO', 'monEs', 'monet', 'monEmus', 'monEtis', 'monent'])
        self.assertEqual(f("regO"), ['regO', 'regis', 'regit', 'regimus', 'regitis', 'regunt'])
        self.assertEqual(f("capiO"), ['capiO', 'capis', 'capit', 'capimus', 'capitis', 'capiunt'])
        self.assertEqual(f("audiO"), ['audiO', 'audIs', 'audIt', 'audImus', 'audItis', 'audiunt'])

    def test_conj_present_passive(self):
        f = verb.conj_present_passive
        self.assertEqual(f("amO"), ['amor', 'amAris', 'amAtur', 'amAmur', 'amAminI', 'amantur'])
        self.assertEqual(f("moneO"), ['moneor', 'monEris', 'monEtur', 'monEmur', 'monEminI', 'monentur'])
        self.assertEqual(f("regO"), ['regor', 'regeris', 'regitur', 'regimur', 'regiminI', 'reguntur'])
        self.assertEqual(f("capiO"), ['capior', 'caperis', 'capitur', 'capimur', 'capiminI', 'capiuntur'])
        self.assertEqual(f("audiO"), ['audior', 'audIris', 'audItur', 'audImur', 'audIminI', 'audiuntur'])

if __name__ == '__main__':
    unittest.main()
