"""
This script takes in salento acceptable sequence and reverse the sequence. 
The ordering of unit remains the same
"""

import sys
import json


def reverse_seq(inputfile, outfile):
    """
    reverse the data file
    :param inputfile: input data file
    :param outfile: output data file
    :return:
    """

    with open(inputfile, 'r') as fread:
        json_data = json.load(fread)

    # iterate and reverse in memory
    for pack in json_data['packages']:
        for seq in pack["data"]:
            seq['sequence'].reverse()
            # reverse state
            for events in seq['sequence']:
                events['states'].reverse()
    # write out the file
    with open(outfile, 'w') as fwrite:
        json.dump(json_data, fwrite)


if __name__ == "__main__":
    reverse_seq(sys.argv[1], sys.argv[2])
