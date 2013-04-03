#!/usr/bin/env python
# -*- coding: utf-8 -*-

import strutil
import unittest

import latindic
import latin_adj
import util

def partial_surfaces(table, start, end):
    t = {'m':[], 'f':[], 'n':[]}
    for item in table:
        g = item['gender']
        t[g].append( item['surface'].encode('utf-8') )
    for g in t:
        t[g] = t[g][start:end]
    return t


def transpose(expected):
    # wiktionary style -> my format
    t = {'m':[], 'f':[], 'n':[]}

    for case in ['Nom','Voc','Acc','Gen','Dat','Abl']:
        surfaces = expected[case]
        if len(surfaces) == 4:
            t['m'].append(surfaces[0])
            t['f'].append(surfaces[0])
            t['n'].append(surfaces[1])
        else:
            t['m'].append(surfaces[0])
            t['f'].append(surfaces[1])
            t['n'].append(surfaces[2])

    for case in ['Nom','Voc','Acc','Gen','Dat','Abl']:
        surfaces = expected[case]
        if len(surfaces) == 4:
            t['m'].append(surfaces[2])
            t['f'].append(surfaces[2])
            t['n'].append(surfaces[3])
        else:
            t['m'].append(surfaces[3])
            t['f'].append(surfaces[4])
            t['n'].append(surfaces[5])

    return t


class StringTestCase(unittest.TestCase):

    def adj_decl_assertEqual(self, adj, expected):
        table = latin_adj.decline_adj(*adj)
        ss = partial_surfaces(table, 0, 12)
        tt = transpose(expected)
        # for g in ss:
        #     print "[%s]" % g
        #     print "  ACTUAL  :", util.render(ss[g])
        #     print "  EXPECTED:", util.render(tt[g])
        #    self.assertEqual(ss[g], tt[g])
        self.assertEqual(ss, tt)

    def test_adj_declension(self):
        self.adj_decl_assertEqual(
            ('1', 'bonus', 'bona', 'bonum', '良い'), {
                'Nom':['bonus', 'bona', 'bonum', 'bonī', 'bonae', 'bona'],
                'Gen':['bonī', 'bonae', 'bonī',    'bonōrum', 'bonārum', 'bonōrum'],
                'Dat':['bonō', 'bonae', 'bonō',   'bonīs', 'bonīs', 'bonīs'],
                'Acc':['bonum', 'bonam', 'bonum', 'bonōs', 'bonās', 'bona'],
                'Abl':['bonō', 'bonā', 'bonō',    'bonīs', 'bonīs', 'bonīs'],
                'Voc':['bone', 'bona', 'bonum',   'bonī', 'bonae', 'bona']
                })

        self.adj_decl_assertEqual(
            ('1', 'līber', 'lībera', 'līberum', '自由な'), {
                'Nom':['līber', 'lībera', 'līberum', 'līberī', 'līberae', 'lībera'],
                'Gen':['līberī', 'līberae', 'līberī', 'līberōrum', 'līberārum', 'līberōrum'],
                'Dat':['līberō', 'līberae', 'līberō', 'līberīs', 'līberīs', 'līberīs'],
                'Acc':['līberum', 'līberam', 'līberum', 'līberōs', 'līberās', 'lībera'],
                'Abl':['līberō', 'līberā', 'līberō', 'līberīs', 'līberīs', 'līberīs'],
                'Voc':['līber', 'lībera', 'līberum', 'līberī', 'līberae', 'lībera']
                })

        self.adj_decl_assertEqual(
            ('1', 'pulcher', 'pulchra', 'pulchrum', '美しい'), {
                'Nom':['pulcher', 'pulchra', 'pulchrum', 'pulchrī', 'pulchrae', 'pulchra'],
                'Gen':['pulchrī', 'pulchrae', 'pulchrī', 'pulchrōrum', 'pulchrārum', 'pulchrōrum'],
                'Dat':['pulchrō', 'pulchrae', 'pulchrō', 'pulchrīs', 'pulchrīs', 'pulchrīs'],
                'Acc':['pulchrum', 'pulchram', 'pulchrum', 'pulchrōs', 'pulchrās', 'pulchra'],
                'Abl':['pulchrō', 'pulchrā', 'pulchrō', 'pulchrīs', 'pulchrīs', 'pulchrīs'],
                'Voc':['pulcher', 'pulchra', 'pulchrum', 'pulchrī', 'pulchrae', 'pulchra']
                })

        self.adj_decl_assertEqual(
            ('2', 'fortis', 'fortis', 'forte', '勇敢な'), {
                'Nom':['fortis', 'forte', 'fortēs', 'fortia'],
                'Gen':['fortis', 'fortis', 'fortium', 'fortium'],
                'Dat':['fortī', 'fortī', 'fortibus', 'fortibus'],
                'Acc':['fortem', 'forte', 'fortēs', 'fortia'],
                'Abl':['fortī', 'fortī', 'fortibus', 'fortibus'],
                'Voc':['fortis', 'forte', 'fortēs', 'fortia']
                })

        self.adj_decl_assertEqual(
            ('2', 'ācer', 'ācris', 'ācre', '鋭い'), {
                'Nom':['ācer',  'ācris', 'ācre',  'ācrēs',   'ācrēs',   'ācria'],
                'Gen':['ācris', 'ācris', 'ācris', 'ācrium',  'ācrium',  'ācrium'],
                'Dat':['ācrī',  'ācrī',   'ācrī',   'ācribus', 'ācribus', 'ācribus'],
                'Acc':['ācrem', 'ācrem', 'ācre',  'ācrēs',   'ācrēs',   'ācria'],
                'Abl':['ācrī',  'ācrī',   'ācrī',   'ācribus', 'ācribus', 'ācribus'],
                'Voc':['ācer',  'ācris', 'ācre',  'ācrēs',   'ācrēs',   'ācria']
                })

        self.adj_decl_assertEqual(
            ('2', 'audāx', 'audācis', '-', '大胆な'), {
                'Nom':['audāx', 'audāx', 'audācēs', 'audācia'],
                'Gen':['audācis', 'audācis', 'audācium', 'audācium'],
                'Dat':['audācī', 'audācī', 'audācibus', 'audācibus'],
                'Acc':['audācem', 'audāx', 'audācēs', 'audācia'],
                'Abl':['audācī', 'audācī', 'audācibus', 'audācibus'],
                'Voc':['audāx', 'audāx', 'audācēs', 'audācia']
                })

        self.adj_decl_assertEqual(
            ('2', 'prūdēns', 'prūdentis', '-', '思慮ある'), {
                'Nom':['prūdēns', 'prūdēns', 'prūdentēs', 'prūdentia'],
                'Gen':['prūdentis', 'prūdentis', 'prūdentium', 'prūdentium'],
                'Dat':['prūdentī', 'prūdentī', 'prūdentibus', 'prūdentibus'],
                'Acc':['prūdentem', 'prūdēns', 'prūdentēs', 'prūdentia'],
                'Abl':['prūdentī', 'prūdentī', 'prūdentibus', 'prūdentibus'],
                'Voc':['prūdēns', 'prūdēns', 'prūdentēs', 'prūdentia']
                })

        self.adj_decl_assertEqual(
            ('2', 'vetus', 'veteris', '-', '古い,老いた'), {
                'Nom':['vetus', 'vetus', 'veterēs', 'vetera'],
                'Gen':['veteris', 'veteris', 'veterum', 'veterum'],
                'Dat':['veterī', 'veterī', 'veteribus', 'veteribus'],
                'Acc':['veterem', 'vetus', 'veterēs', 'vetera'],
                'Abl':['vetere', 'vetere', 'veteribus', 'veteribus'],
                'Voc':['vetus', 'vetus', 'veterēs', 'vetera']
                })

if __name__ == '__main__':
    latindic.load()
    unittest.main()
