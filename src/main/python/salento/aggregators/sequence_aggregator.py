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


class SimpleSequenceAggregator(Aggregator):

    """
    The simple sequence aggregator computes, for each sequence, the negative
    log-likelihood of the sequence using only its calls (not states).
    """
    def __init__(self, data_file, model_dir):
        Aggregator.__init__(self, data_file, model_dir)

    def run(self):
        for k, package in enumerate(self.packages()):
            print('Package {}----'.format(k))
            spec = self.get_latent_specification(package)
            for j, sequence in enumerate(self.sequences(package)):
                events = self.events(sequence)
                llh = 0.
                for i, event in enumerate(events):
                    llh += math.log(self.distribution_next_call(spec, events[:i], call=self.call(event)))
                llh += math.log(self.distribution_next_call(spec, events, call=self.END_MARKER))
                print('{:4d} : {:.4f}'.format(j, -llh), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True,
                        help='input data file')
    parser.add_argument('--model_dir', type=str, required=True,
                        help='directory to load model from')
    clargs = parser.parse_args()

    with SimpleSequenceAggregator(clargs.data_file, clargs.model_dir) as aggregator:
        aggregator.run()
