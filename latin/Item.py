#!/usr/bin/env python
# -*- coding: utf-8 -*-
import latin.util as util # render
import latin.ansi_color as ansi_color

class Item:
    def __init__(self, item):
        self.item = item
        self.surface = item['surface']
        self.pos = item['pos']
        self.ja = item['ja']

        self._ = item.get('_', None)
        self.dominates = item.get('dominates', None)
        self.target = []
        self.modifiers = []

    def attrib(self, name, default=None):
        return self.item.get(name, default)

    def match_case(self, pos, case):
        return self.pos in pos and any([it[0] == case for it in self._])

    def can_be_genitive(self):
        return self._ and any([it[0] == 'Gen' for it in self._])

    # itemをレンダリング
    def description(self):
        name = {
            # tense
            'present':'現在', 'imperfect':'未完了', 'future':'未来', # 'past':'過去',
            'perfect':'完了', 'past-perfect': '過去完了', 'future-perfect': '未来完了',
            # mode
            'indicative':'直説法', 'subjunctive':'接続法', 'imperative':'命令法', 'infinitive':'不定法',
            #
            'participle':'分詞', 'gerundium':'動名詞',
            # 数
            'sg':'単数', 'pl':'複数',
            # (態:Genus)
            'active':'能動', 'passive':'受動',
            '-':'-'}
        # pos = item['pos']
        def short_(_):
            return '|'.join(['.'.join(s) for s in _])

        def get_base(key):
            base = self.item.get(key)
            if base is None: return ''
            return ansi_color.ANSI_FGCOLOR_YELLOW + '(' + base + ')' + ansi_color.ANSI_FGCOLOR_DEFAULT + ' '

        if self.pos == 'noun':
            return get_base('base') + '%s [%s]' % (self.ja, short_(self._)) +' // '+ util.render(self.modifiers)
        elif self.pos in ['adj', 'participle']:
            return get_base('base') + '%s.%s [%s]' % (self.pos[0], self.ja, short_(self._))
        elif self.pos == 'verb':
            return get_base('pres1sg') + 'v.%s %s%s %s.%s.%s' % (self.ja,
                                                                 self.item.get('person', 0),
                                                                 self.item.get('number', '-'),
                                                                 name[self.item.get('mood', 'indicative')],
                                                                 name[self.item.get('voice', 'active')],
                                                                 name[self.item.get('tense', 'present')],
                                                                 )
        elif self.pos == 'preposition':
            return 'prep<%s> %s' % (self.dominates, self.ja)
        else:
            if len(self.item) > 0:
                item_ = self.item.copy()
                del item_['surface'], item_['pos'], item_['ja']
                return '%s %s %s' % (self.pos, self.ja, util.render(item_))
            else:
                return '%s %s' % (self.pos, self.ja)
