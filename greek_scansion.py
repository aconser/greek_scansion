# -*- coding: utf-8 -*-
"""
This program takes a line of Greek text and returns its scansion as a list of
syllable markers: LONG ('L'), SHORT ('S'), or UNKNOWN ('X').  The module is 
appropriate for analyzing prose or poetry.

The current version incorporates the syllabify module from James Tauber's 
greek_accentuation library, but it could easily be modified to work with any 
type of syllabifier, since it analyzes consonants between vowel clusters without 
reference to their assignment to the current or subsequent syllable.

Next steps for improvement are to increase the program's ability to recognize
vowels that are long or short by nature:
    1. Create a tool to macronize known suffixes (i.e. syntactical endings).
    2. Scrape the LSJ to build a macronized dictionary of ambiguous words.

@author: Anna Conser, Columbia University, anna.conser@gmail.com
@license: MIT

"""

import re
import unicodedata
from greek_accentuation.syllabify import syllabify

# CHARACTER DEFINITIONS

VOWELS = ['α', 'ε', 'η', 'ι', 'ο', 'υ', 'ω']
vowel_re = re.compile('[' + ''.join(VOWELS) + ']')

LONG_VOWELS = ['η', 'ω']
long_vowel_re = re.compile('[' + ''.join(LONG_VOWELS) + ']')

SHORT_VOWELS = ['ε', 'ο']
short_vowel_re = re.compile('[' + ''.join(SHORT_VOWELS) + ']')

DIPHTHONGS = ['αι', 'ει', 'οι', 'υι', 'αυ', 'ευ', 'ου', 'ηυ']
diphthong_re = re.compile('(' + '|'.join(DIPHTHONGS)+ ')')

CONSONANTS = ['β', 'γ', 'δ', 'ζ', 'θ', 'κ', 'λ', 'μ', 'ν', 'ξ', 
              'π', 'ρ', 'ϲ', 'σ', 'ς', 'τ', 'φ', 'χ', 'ψ'
              ]
consonant_re = re.compile('[' + ''.join(CONSONANTS) + ']')

DOUBLE_CONS = ['ζ', 'ξ', 'ψ']
double_con_re = re.compile('[' + ''.join(DOUBLE_CONS) + ']')

LONG_MARKS = [u'\u0302',  #combining circumflex
              u'\u0304',  #macron
              u'\u02C6',  #another circumflex
              u'\u005E',  #caret
              u'\u0345',  #iota subscript
              u'\u037A'   #another iota subscript
              ]
long_mark_re = re.compile('['+ ''.join(LONG_MARKS)+']')

SHORT_MARK = u"\u0306"

MUTE_LIQUID = ['θλ', 'θρ', 'θμ', 'θν',   #voiceless stop + liquid or nasal
               'κλ', 'κρ', 'κμ', 'κν',
               'πλ', 'πρ', 'πν', 'πμ',
               'τλ', 'τρ', 'τν', 'τμ',
               'φλ', 'φρ', 'φν', 'φμ',
               'χλ', 'χρ', 'χν', 'χμ',
               'βρ', 'γρ', 'δρ'          #voiced stop + rho
               ]
# NOTE: the following stop+liquid combinations have been excluded as they almost
# universally make a syllable long by position:
# long_stop_liquids = ['γμ', 'γν', 'δμ', 'δν', 'βλ', 'γλ']

APOSTROPHE = u'\u02BC'
PUNCTUATION = ".,;·:'<>[]{}()=+"

LONG = 'L'
SHORT = 'S'
UNKNOWN = 'X'

#INTERNAL FUNCTIONS

def strip_str (string):
    """Removes diacritical markings from a string and makes lowercase.
    
    :param str string: a string of text
    :return: a string of text without diacritical markings
    :rtype: str
    """
    bare_str = ''
    for ch in string:
        bare_ch = unicodedata.normalize('NFD', ch)[0]
        bare_str += bare_ch
    bare_str = bare_str.lower()
    return bare_str

def alnum_syl (string):
    """Removes everything except alphanumeric characters from a syllable,
    including apostrophes indicating apocope. Also makes lowercase.
    """
    text = string
    text = re.sub(r'\W+', '', text)
    text = re.sub(APOSTROPHE, '', text)
    text = text.lower()
    return text

def natural_length (syl):
    """Checks the natural length of syllable, returning LONG, SHORT, or UNKNOWN.
    -- LONG is identified by long vowels, diphthongs, or long diacritics.  
    -- SHORT is identified by short vowels or a short mark.  
    -- UNKNOWN is α, ι, or υ without diacritics indicating length.  
    """
    bare_syl = strip_str(syl)  #remove diacritics from vowels
    split_chs = unicodedata.normalize('NFD', syl) #get list including diacritics
    if re.search(long_vowel_re, bare_syl): #eta and omega
        status = LONG
    elif re.search(diphthong_re, bare_syl): #diphthongs
        status = LONG
    elif re.search(long_mark_re, split_chs): #circumflex, iota subscript, marcon
        status = LONG
    elif re.search(short_vowel_re, bare_syl): #epsilon, omicron
        status = SHORT
    elif SHORT_MARK in split_chs: #short mark
        status = SHORT
    else:                  #alpha, upsilon, iota without length diacritic
        status = UNKNOWN
    return status

def positional_length (syl, next_syl):
    """Takes the two sequential syllables and returns the positional length of 
    the first. Syllables can be created using any tool that separates vowel 
    clusters.  Stop + liquid rules follow the principles that apply in tragedy
    (see notes below).
    """
    #Check for wordbreak
    if re.search(r'\s', syl[-1]+next_syl[0]):
        wordbreak = True
    else: wordbreak = False
    #Clean extraneous markings from the ends of syllables
    syl = alnum_syl(syl)
    next_syl = alnum_syl(next_syl)
    #Create a list of the consonants separating the two syls' vowel-clusters
    consonant_cluster = ''
    #Add consonants post-vowel in the first syl
    for ch in syl[::-1]:              
        if ch in CONSONANTS:
            consonant_cluster = ch + consonant_cluster
        else:
            break
    #Add consonants pre-vowel in the following syl
    for ch in next_syl:
        if ch in CONSONANTS:
            consonant_cluster +=ch
        else:
            break
    #Check for lengthening conditions:
    #Followed by a single consonant = SHORT, unless it's a double consonant
    if len(consonant_cluster) <=1:
        if re.search(double_con_re, consonant_cluster):
            status = LONG
        else:
            status = SHORT
    #Two or more consonants lengthen, except certain stop+liquid combos. If 
    #these occur after a wordbreak, first syl is short; but within a word they
    #can lengthen or not as required in context.
    else:
        if consonant_cluster in MUTE_LIQUID:
            if wordbreak == True and syl[-1] in VOWELS:
                status = SHORT
            else:
                status = UNKNOWN
        else:
            status = LONG
    #short syl can function as long at line end (final anceps)
    if next_syl == 'END' and status == SHORT:
        status = UNKNOWN
    return status
        
def scan_line (line):
    """Scans a line of Greek poetry, as best as possible without knowing 
    whether ambiguous vowels are long by nature. Returns the meter as a list of
    syllables marked LONG ('L'), SHORT ('S') or UNKNOWN ('X').
    """
    line = line.strip()
    meter = []
    syl_list = syllabify(line)
    for i, syl in enumerate(syl_list):
        current_length = natural_length(syl)
        if current_length != 'L':
            if i == len(syl_list)-1: 
                next_syl = 'END'
            else: 
                next_syl = syl_list[i+1]
            pos_len = positional_length(syl, next_syl)
            if pos_len == LONG: current_length = LONG
            elif current_length == SHORT:
                current_length = pos_len
        meter.append(current_length)
    return meter
