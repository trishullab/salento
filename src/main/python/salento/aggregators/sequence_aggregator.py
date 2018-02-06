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
import numpy as np
import itertools
from operator import itemgetter

class SimpleSequenceAggregator(Aggregator):

    """
    The simple sequence aggregator computes, for each sequence, the negative
    log-likelihood of the sequence using only its calls (not states).
    """
    def __init__(self, data_file, model_dir):
        Aggregator.__init__(self, data_file, model_dir)
        self.cache = {}

    def call_dist(self, spec, events):
        for (i, row) in enumerate(self.distribution_call_iter(spec, events, cache=self.cache)):
            if i == len(events):
                next_call = self.END_MARKER
            else:
                next_call = events[i]['call']
            yield row.distribution.get(next_call, 0.0)

    def sequence_likelihood(self, spec, events):
        row = np.fromiter(self.call_dist(spec, events), dtype=np.float64)
        # Apply log to each element
        np.log(row, out=row)
        # Summate all elements
        return -np.sum(row)

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
                score = max(self.sequence_likelihood(spec, self.events(seq)) for seq in seqs_l)
                print('{:50s} : {:.4f}'.format(location, score), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True,
                        help='input data file')
    parser.add_argument('--model_dir', type=str, required=True,
                        help='directory to load model from')
    clargs = parser.parse_args()

    with SimpleSequenceAggregator(clargs.data_file, clargs.model_dir) as aggregator:
        aggregator.run()
