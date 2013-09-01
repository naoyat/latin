#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gensim import corpora, models, similarities #, ldamodel
import sys
import re

import latin.ansi_color as ansi_color
import latin.textutil as textutil
import latin.latin_char as char
import latin.latindic as latindic
import latin.util as util

from latin.LatinObject import LatinObject
from latin.Word import Word
from latin.Predicate import Predicate
from latin.AndOr import AndOr, non_genitive
from latin.PrepClause import PrepClause
from latin.Sentence import Sentence


def lookup_all(surfaces_uc):
    def lookup(surface):
        items = latindic.lookup(surface)
        if items: return Word(surface, items)
        if char.isupper(surface[0]):
            surface_lower = char.tolower(surface)
            items = latindic.lookup(surface_lower)
            if items: return Word(surface, items)
        if surface[-3:] == u'que':
            items = latindic.lookup(surface[:-3])
            if items:
#                return Word(surface[:-3], items, {'enclitic':'que'})
                return Word(surface, items, {'enclitic':'que'})
        return None

    words = []

    l = len(surfaces_uc)
    i = 0
    while i < l:
        surface = surfaces_uc[i]
        if ord(surface[0]) <= 64: # 辞書引き（記号のみから成る語を除く）
            words.append(Word(surface, None))
            i += 1
            continue
        if i < l-1:
            surface2 = surface + u' ' + surfaces_uc[i+1]
            word2 = lookup(surface2)
            # print "word2:", word2.encode('utf-8'), util.render(lu2)
            if word2 is not None: # len(word2.items) > 0: #is not None: and len(lu2) > 0:
                words.append(word2)
                i += 2
                continue
        word = lookup(surface)
        if word is not None:
            words.append(word)
        else:
            words.append(Word(surface, []))
        i += 1

    # words の中での添字情報をWordインスタンスに保存
    for i, word in enumerate(words):
        word.index = i

    return words

#
# Item -> (priority, pos, base-form)
#
def base_form_of_item(item):
    # print item.pos, item.surface, item.item.get('base',None), item.item.get('pres1sg',None), repr(item.item)
    if item.pos in ('conj', 'preposition', 'adv', 'pronoun'):
        base = None
        priority = 9
    elif item.pos in ('verb', 'participle'):
        base = item.item.get('pres1sg', None)
        if base in ('sum', 'meus', 'tuus'):
            base = None
            priority = 9
        else:
            priority = 1
    elif item.pos in ('noun', 'pronoun', 'adj'):
        base = item.item.get('base', None)
        priority = 2
    else:
        base = None #item.surface
        priority = 8

    if base == '*':
        base = None
        priority = 9

    return (priority, item.pos, base)

#
# Word -> base-form
#
def base_form_of_word(word):
    if word.items:
        bases = filter(lambda x:x[2], [base_form_of_item(item) for item in word.items])
        bases.sort()
        if bases:
            return bases[0][2]
        else:
            return None
    else:
        return None

#
# ["word", ...] -> [base-form, ...]
#
def base_forms_of_words(word_surfaces):
    # unicodeに変換して
    word_surfaces_uc = [word_surface.decode('utf-8', 'strict') for word_surface in word_surfaces]
    # 辞書を引いてから
    words = lookup_all(word_surfaces_uc)

    return filter(lambda x:x, [base_form_of_word(word) for word in words])


def show_title(title):
    print
    print '  #'
    print '  #', title
    print '  #'
    print


def main():
    latindic.load(auto_macron_mode=False)


    show_title('original text')

    text = textutil.load_text_from_file('./latin.txt')
    print text[:1000], '...'
    print


    show_title('texts in base-form')

    texts_in_baseform = []
    for word_surfaces_in_a_sentence in textutil.sentence_stream(textutil.word_stream_from_text(text)):
        # print word_surfaces_in_a_sentence

        bases = base_forms_of_words(word_surfaces_in_a_sentence)
        texts_in_baseform.append(bases)

    for sentence in texts_in_baseform[:20]:
        print ' '.join([baseform.encode('utf-8') for baseform in sentence])
    print '...'
    print


    show_title('[gensim] dictionary')

    dictionary = corpora.Dictionary(texts_in_baseform)
    # dictionary.save('/tmp/latintext.dict') # store the dictionary, for future reference
    # print dictionary
    print '{',
    for token, id in dictionary.token2id.items():
        print '\"%s\": %d,' % (token.encode('utf-8'), id),
    print '}'

#    new_doc = "In Crētā īnsulā māgnum labyrinthum Daedalus aedificāvit plēnum viārum flexuōsārum."
#    new_bases = base_forms_of_words(new_doc.split())
#    # print new_bases
#    new_vec = dictionary.doc2bow(new_bases)
#    print new_vec



    show_title('[gensim] corpus')

    corpus = [dictionary.doc2bow(text) for text in texts_in_baseform]
    # corpora.MmCorpus.serialize('/tmp/latintext.mm', corpus)
    # print corpus
    for doc in corpus[:20]:
        print doc
    print '...'
    print



    show_title('tf-idf')  # term frequency * inverse document frequency

    tfidf = models.TfidfModel(corpus) # step 1 -- initialize a model
    corpus_tfidf = tfidf[corpus]
    for i, doc in enumerate(corpus_tfidf):
        print doc
        if i == 20: break
    print '...'
    print


    #
    def decode_result(item, delim):
        def translate(token):
            # print "translating \"%s\"..." % token.encode('utf-8')
            items = latindic.lookup(token)
            return items[0]['ja'] if items else '*'
        latin_tokens = re.split(delim, item)[1::2]
        jas = [translate(token) for token in latin_tokens]
        return ' / '.join(jas) # print "\t", items[0]['ja']


    NUM_TOPICS = 80
    TOPICS_TO_TAKE = 10


    show_title('LSI (Latent Semantic Indexing)')

    # initialize an LSI transformation
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=NUM_TOPICS)
    # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi
    corpus_lsi = lsi[corpus_tfidf]
    topics = lsi.print_topics(TOPICS_TO_TAKE)

    for i, item in enumerate(topics):
        print "%d) %s" % (1+i, item.encode('utf-8'))
        print "    ", decode_result(item, '"')
        print

    print



    show_title('LDA (Latent Dirichlet Allocation)')

    model = models.ldamodel.LdaModel(corpus, id2word=dictionary, num_topics=NUM_TOPICS)
    topics = model.show_topics(topics=TOPICS_TO_TAKE)
    for i, item in enumerate(topics):
        print "%d) %s" % (1+i, item.encode('utf-8'))
        print "    ", decode_result(item, ' ?[*+]')
        print

    print



#    show_title('HDP (Hierarchical Dirichlet Process)')
#
#    model = models.hdpmodel.HdpModel(corpus, id2word=dictionary)
#    topics = model.print_topics(topics=5)
#    print topics
#    for i, item in enumerate(topics):
#        print "%d) %s" % (1+i, item.encode('utf-8'))
#        print "    ", decode_result(item, ' ?[*+]')
#
#    print



if __name__ == '__main__':
    main()
