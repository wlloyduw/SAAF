#!/usr/bin/env python3

#
# Takes a report generated with the report_generator.py and splits it into
# a folder of CSV files. This makes importing into R significantly easier.
#
# @author Robert Cordingly
#

import sys
import os

if (len(sys.argv) > 1):

    file = sys.argv[1]
    data = ""

    filename = os.path.basename(file)
    directory = file.replace('.csv', '') + ' - spit'
    if not os.path.exists(directory):
        os.makedirs(directory)

        with open(file, 'r') as myfile:
            data = myfile.read()
    
        groups = data.split("\n\n")
    
        for chunk in groups:
            lines = chunk.split("\n")
            if len(lines) > 1:
                chunkName = lines[0].replace(':', '')
                print("Writing file " + chunkName + ".csv")

                chunkFile = open(directory + '/' + chunkName + '.csv', 'w+')
                i = 1
                while i < len(lines):
                    if ',' in lines[i]:
                        chunkFile.write(lines[i] + '\n')
                    i += 1
                chunkFile.close()

        print("File split into csv chunks!")

    else:
        print("Folder already exists!")
else:
    print("Error, please supply file to split.")

