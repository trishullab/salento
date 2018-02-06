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

from __future__ import print_function
import math
import argparse
from salento.aggregators.base import Aggregator
import itertools
from operator import itemgetter

class KLDAggregator(Aggregator):

    """
    KL-divergence based aggregator computes the anomaly score of each location l as follows:
        1. Gather the set of sequences that end at l
        2. Compute the probability of each sequence from the set of sequences as p
        3. Compute the probability of the same sequence from the model as q
        4. KL-divergence from the sequence = p * (log p - log q).
        5. Repeat 2-4 for every sequence that ends at l, adding to the quantity at 4. This is final score for l.
        6. Repeat 1-5 for each location in the package.
    """

    def __init__(self, data_file, model_dir):
        Aggregator.__init__(self, data_file, model_dir)
        self.cache = {}

    def log_likelihood(self, spec, sequence):
        llh = 0.
        events = self.events(sequence)
        calls = list(s['call'] for s in events)
        calls.append(self.END_MARKER)
        
        for (row, next_call) in zip(self.distribution_state_iter(spec, events, cache=self.cache), calls):
            llh += math.log(row.distribution[next_call])
            for prob in row.states:
                llh += math.log(prob)

            if next_call != self.END_MARKER:
                dist = row.next_state()
                llh += math.log(dist[self.END_MARKER])

        return llh

    def compute_kld(self, spec, sequences):
        counted = []
        kld = 0.
        for sequence in sequences:
            if sequence in counted:
                continue
            counted.append(sequence)
            p = sequences.count(sequence) / len(sequences)
            log_p = math.log(p)
            log_q = self.log_likelihood(spec, sequence)
            kld += p * (log_p - log_q)
        return kld

    def sequences_ending_at(self, sequences):
        elems_by_loc = ((self.location(self.events(seq)[-1]), seq)
            for seq in sequences if len(self.events(seq)) > 0)
        elems = itertools.groupby(sorted(elems_by_loc, key=itemgetter(0)), itemgetter(0))
        for location, row in elems:
            yield location, map(itemgetter(1), row)

    def run(self):
        for k, package in enumerate(self.packages()):
            print('Package {}----'.format(k))
            spec = self.get_latent_specification(package)
            sequences = self.sequences(package)
            for location, seqs_l in self.sequences_ending_at(sequences):
                kld_score = self.compute_kld(spec, list(seqs_l))
                print('{:50s} : {:.4f}'.format(location, kld_score), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True,
                        help='input data file')
    parser.add_argument('--model_dir', type=str, required=True,
                        help='directory to load model from')
    clargs = parser.parse_args()

    with KLDAggregator(clargs.data_file, clargs.model_dir) as aggregator:
        aggregator.run()
