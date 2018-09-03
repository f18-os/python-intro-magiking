#!/usr/bin/env python

import sys
import re
import os

# input and output files
if len(sys.argv) is not 3:
    print("Correct usage: wordCount.py <input text file> <output text file>")
    exit()

inputFname = sys.argv[1]
outputFname = sys.argv[2]

#check that input exists
if not os.path.exists(inputFname):
    print("%s does not exist. Exiting" % inputFname)
    exit()

# words dictionary
score = {}

# open input file and read. Insert words into dictionary line by line
with open(inputFname, 'r') as inputFile:
    for line in inputFile:
        # remove non-word characters. (I think this is pretty elegant. Only three lines.)
        # print("As read : %s" % line)
        line = line.strip()
        # print("after line.strip(): %s" % line)
        line = re.sub('\'|-', ' ', line, flags=re.IGNORECASE)
        # print("after regex sub: %s" % line)
        words = re.split('[\W]', line) # [\W] might solve the punctuation
        for word in words:
            if word == '':
                continue
            if word.lower() in score: # try a default dict
                score[word.lower()] += 1
            else:
                score[word.lower()] = 1

# write dictionary to output file
with open(outputFname, 'w') as outputFile:
    for word in sorted(score):
        outputFile.write("%s\t%d\n" % (word, score[word]))
