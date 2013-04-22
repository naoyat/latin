#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from latin.latin_noun import *
import latin.latindic


class StringTestCase(unittest.TestCase):

    def noun_decl_assertEqual(self, noun, expected):
        table = decline_noun(noun[0],
                             noun[1].decode('utf-8'),
                             noun[2].decode('utf-8') if noun[2] is not None else None,
                             noun[3],
                             noun[4])
        ss = [item['surface'].encode('utf-8') for item in table]
        tt = expected['sg'] + expected['pl'] # Nom Voc Acc Gen Dat Abl
        # for g in ss:
        #     print "[%s]" % g
        #     print "  ACTUAL  :", util.render(ss[g])
        #     print "  EXPECTED:", util.render(tt[g])
        #    self.assertEqual(ss[g], tt[g])
        self.assertEqual(ss, tt)

    def test_noun_declension_type1(self):
        self.noun_decl_assertEqual(
            ('1', 'fōrma', None, 'f', '形'), {
                'sg':['fōrma', 'fōrma', 'fōrmam', 'fōrmae', 'fōrmae', 'fōrmā'],
                'pl':['fōrmae', 'fōrmae', 'fōrmās', 'fōrmārum', 'fōrmīs', 'fōrmīs']
                })
        self.noun_decl_assertEqual(
            ('1', 'aqua', None, 'f', '水'), {
                'sg':['aqua', 'aqua', 'aquam', 'aquae', 'aquae', 'aquā'],
                'pl':['aquae', 'aquae', 'aquās', 'aquārum', 'aquīs', 'aquīs']
                })

    def test_noun_declension_type1_exception(self):
        self.noun_decl_assertEqual(
            ('1', 'dea', None, 'f', '女神'), {
                'sg':['dea', 'dea', 'deam', 'deae', 'deae', 'deā'],
                'pl':['deae', 'deae', 'deās', 'deārum', 'deābus', 'deābus'] # deābus, not deīs
                })
        self.noun_decl_assertEqual(
            ('1', 'fīlia', None, 'f', '娘'), {
                'sg':['fīlia', 'fīlia', 'fīliam', 'fīliae', 'fīliae', 'fīliā'],
                'pl':['fīliae', 'fīliae', 'fīliās', 'fīliārum', 'fīliābus', 'fīliābus'] # fīliābus, not fīliīs
                })
        


if __name__ == '__main__':
    latin.latindic.load()
    unittest.main()

