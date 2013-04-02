#!/usr/bin/env python
# -*- coding: utf-8 -*-

def word_stream(file):
    in_sentence = False
    with open(file, "r") as fp:
        for line in fp:
            for word in line.rstrip().split():
                if word[0] in ['"', "'"]:
                    yield word[0]
                    word = word[1:]

                last_char = word[-1]
                if not in_sentence:
                    yield "BOS"
                    in_sentence = True

                if last_char in ['"', "'"]:
                    end_quote = last_char
                    word = word[:-1]
                    last_char = word[-1]
                else:
                    end_quote = None

                if last_char in ['.', '?', '!']:
                    yield word[:-1]
                    yield last_char
                    yield "EOS"
                    in_sentence = False
                elif last_char in [',', ';', ':']:
                    yield word[:-1]
                    yield last_char
                else:
                    yield word

                if end_quote:
                    yield end_quote

def sentence_stream(ws):
    sentence = []
    for word in ws:
        if word == 'BOS':
            sentence = []
        elif word == 'EOS':
            yield sentence
            sentence = []
        else:
            sentence.append(word)

def analyse_textfile(textfile, analyzer):
    for sentence in sentence_stream(word_stream(textfile)):
        analyzer(sentence)
