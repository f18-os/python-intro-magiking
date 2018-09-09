#!/usr/bin/env python3

import sys
import re
import os
from collections import Counter # For easy counting

# input and output files
if len(sys.argv) is not 3:
    print("Correct usage: coolerWordCount.py <input text file> <output text file>")
    exit()

inputFname = sys.argv[1]
outputFname = sys.argv[2]

#check that input exists
if not os.path.exists(inputFname):
    print("%s does not exist. Exiting" % inputFname)
    exit()

# words "dictionary"
count = Counter()

# open input file and read. Insert words into dictionary line by line
with open(inputFname, 'r') as inputFile:
    words = re.findall('\w+', inputFile.read().lower())
    for word in words:
        count[word] += 1

# write dictionary to output file
with open(outputFname, 'w') as outputFile:
    for word in sorted(count):
        outputFile.write("%s\t%d\n" % (word, count[word]))
