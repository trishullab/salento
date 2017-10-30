# Copyright 2017 Rice University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
import math
import argparse
import itertools

from data_reader import JsonParser
from datetime import datetime

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('data_file', type=str, nargs=1,
                       help='input file in JSON')
    argparser.add_argument('--corpus', type=str, required=True,
                       help='corpus file in JSON')
    args = argparser.parse_args()
    print(args)
    start = datetime.now()
    print('Started at {}'.format(start))
    with open(args.corpus) as f:
        corpus_seqs = get_corpus_seqs(f)
    with open(args.data_file[0]) as f:
        compute_1nn(f, corpus_seqs)
    print('Time taken: {}'.format(datetime.now() - start))

def compute_1nn(f, corpus_seqs):
    """ Do a quick 1nn calculation just to see if the distance (KLD) is
        infinity or not. The KLD is infinity if there's a sequence in the test
        package (p > 0) that is not there in the corpus (q = 0)."""
    parser = JsonParser(f)
    for pack in parser.packages:
        locations = parser.locations(pack)
        print('### ' + pack['name'])
        seqs = map(strip_locations, [parser.sequences(pack, l) for l in locations])
        klds = [(l, check_infinite_kld(seqs_l, corpus_seqs)) for l, seqs_l in zip(locations, seqs)]
        for l, k in sorted(klds, key=lambda x: -x[1]):
            print('  {:35s} : {:.2f}'.format(l, k))

def check_infinite_kld(seqs, corpus_seqs):
    for seq in seqs:
        if seq not in corpus_seqs:
            return math.inf
    return -1. # to denote "not infinity"

def get_corpus_seqs(f):
    parser = JsonParser(f)
    seqs = map(strip_locations, [parser.sequences(pack) for pack in parser.packages])
    chain = list(itertools.chain(*seqs))
    chain.sort(key=lambda x: len(x))
    return [key for key, _ in itertools.groupby(chain)]

def strip_locations(seqs):
    for seq in seqs:
        for event in seq:
            del event['location']
    return seqs

if __name__ == '__main__':
    main()
