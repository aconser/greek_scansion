# -*- coding: utf-8 -*-
"""
Created on Sun Jan  7 19:01:06 2018

Trimeter Scansion
This program takes a line of iambic trimeter and returns the scansion, as far
as can be determined.  It was able to scan 70 of 73 lines from the beginning of
Sophocles' Trachiniae.  Lines where it failed involved repeated resolutions in
combination with unknown natural quantities.
Next steps:
    - The best way forward will be to identify more natural quantities, by marking
    the text with macrons, or building a function to identify common prefixes 
    with ambiguous vowel (e.g. "δια"), to cut down on the number of unknowns.
    - I haven't incorporated synezesis, but it hasn't been an issue so far, and
    may be rare enough to just ignore.  More testing needed.
    
@author: Anna Conser
"""

from greek_scansion import scan_line
import re

IAMBIC_NONFINAL = re.compile(r"""
                             ^(?:SS|L|S|X|SX|XS)  #anceps (with anapest)
                             (?:SS|L|X|SX|XS)     #long / resolved
                             (?:S|X)              #short
                             (?:SS|L|X|XS|SX)$    #long / resolved
                             """, re.VERBOSE)
IAMBIC_FINAL = re.compile(r"""
                             ^(?:SS|L|S|X|SX|XS)  #anceps (with anapest)
                             (?:SS|L|X|SX|XS)     #long / resolved
                             (?:S|X)              #short
                             (?:L|S|X)$           #final anceps
                             """, re.VERBOSE)

def is_iambic_metron (meter_string, final=False):
    """Takes a string of metrical lengths (S, L, X), and checks whether they 
    could make up a complete iambic metron.
    
    :param str meter_string: a string of metrical lengths
    :return bool:
    """
    string = meter_string
    if final:
        regex = IAMBIC_FINAL
    else:
        regex = IAMBIC_NONFINAL
    if regex.match(string):
        return True
    else:
        return False

def fill_metron (metron, final=False):
    """Replaces each unknown syllable (X) in a metron with long (L) or short (S),
    the the extent that can be determined from context.  Initial anceps cannot 
    be clarified. Metra with 4 or 6 syllables are unambiguous, while metra with
    5 syllables have 4 options, and the observed meter is used as a regex to 
    identify the matching pattern.  In ambiguous cases, the first option is
    chosen, so the list is ordered according to likelihood.
    
    :param str metron: a string containing the syllable lengths for a metron (L/S/X)
    :param bool final: indicates whether this is the final metron in a line
    :return str filled: a string with the unknown quantities filled, as possible
    """
    filled = ''
    n = len(metron)
    if n == 4:                      #four syllables can only fit this pattern
        filled = metron[0] +'LSL'
    elif n == 6:                    #six syllables can only fit this pattern
        filled = metron[0] + 'SSSSS'
    elif n == 5:
        regex = metron.replace('X', '.')  #turn the metrical data into a regex
        regex = re.compile(r'^' + regex + r'$')
        possible_metra = ['SSSSL', #first resolution
                          'SLSSS', #second resolution
                          'LSSSL', #first dactyl
                          'SSLSL', #first anapest
                          ]
        matches = [x for x in possible_metra if regex.match(x)]
        filled = matches[0]         # take the first (best) possible match
        if final and metron[-1] == 'X' and not filled.endswith('SSS'):
            filled[-1] = 'X'  #restore final anceps
    return filled
    
def scan_trimeter (line):
    """Takes the string for a line of Greek iambic trimeter and returns the 
    scansion as well as can be determined based on available information. The 
    default method is to scan from back to front, and if that doesn't work, it
    tries again from the front (by calling scan_trimeter_2()). In instances where
    a satisfactory scansion cannot be determined, the program prints a message 
    announcing the failure, without throwing an error.
    
    Scansion is returned as a string of letters indicating metrical length:
        'L' (long), 
        'S' (short), or 
        'X' (unknown)
    
    :param str line: a line of text in iambic trimeter
    :return str trimeter: a string of letters indicating metrical quantities
    """
    raw_meter = scan_line(line)
    trimeter = []
    current = ''
    is_last = True               # starting from the end
    countdown = len(raw_meter)
    for m in raw_meter[::-1]:    # iterate through meter in reverse
        current = m + current    # add each length to the front of current metron 
        if len(current) < 4:     # continue until 'current' could be a metron
            continue
        if is_iambic_metron(current, final=is_last) and ( #check for valid metron
                countdown == 1 or countdown > 4):  #last metron must use all remaining
            metron = fill_metron(current, final=is_last)
            trimeter = [metron] + trimeter  #add the metron to the trimeter list
            current = ''
            is_last = False
            countdown -= 1
    if len(trimeter) == 3:  #check for a complete line of trimeter
        return ''.join(trimeter)
    #If that fails, attempt again from the front, using scan_trimeter_2():
    trimeter = scan_trimeter_2(line)
    if len(trimeter) == 3:  #check for a complete line of trimeter
        return ''.join(trimeter)
    else:
        print('FAILED TO SCAN LINE:')
        print(line)
        print(raw_meter)
        print()

def scan_trimeter_2 (line):
    """Does the same thing as scan_trimeter(), but works from front to back.
    This is less effective overall, and is implemented as a secondary method,
    catching a few of the lines that the primary function cannot scan. Return
    is a list, rather than a joined string.
    
    :param str line: a line of text in iambic trimeter
    :return list trimeter: a list of metra, each of which is a string
    """    
    raw_meter = scan_line(line)
    trimeter = []
    current = ''
    is_last = False              # starting from the front
    countdown = len(raw_meter)
    for m in raw_meter:          # iterate through meter forwards
        current = current + m    # add each length to the end of current metron 
        if len(current) < 4:     # continue until 'current' could be a metron
            continue
        if countdown == 1:       # check whether we are at the last foot
            is_last = True
        if is_iambic_metron(current, final=is_last) and ( #check for valid metron
                countdown == 1 or countdown > 4):  #last metron must use all
            metron = fill_metron(current, final=is_last)
            trimeter.append(metron)
            current = ''
            countdown -= 1
    return trimeter

# I haven't implemented thefollowing yet, but they may prove useful in future versions.
    
POSSIBLE_METRA = ['SLSL',  #two iambs
                  'LLSL',  #anceps long
                  'SSSSL', #first resolution
                  'SLSSS', #second resolution
                  'LSSSL', #first dactyl
                  'SSLSL', #first anapest
                  'SSSSSS' #both resolutions
                 ]

TRIMETER = re.compile( """(S|L|SS)(L|SS) #foot 1 (anceps with anapest)
                          S(L|SS)        #foot 2
                          (S|L)(L|SS)    #foot 3 (anceps)
                          S(L|SS)        #foot 4
                          (S|L)(L|SS)    #foot 5 (anceps)
                          S(L|SS|S)      #foot 6
                          """, re.X)
