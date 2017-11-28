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
import json
import numpy as np
import random
from collections import Counter
from itertools import chain

from salento.models.low_level_evidences.utils import CHILD_EDGE, SIBLING_EDGE


class Reader():
    def __init__(self, clargs, config):
        self.config = config

        # read the raw evidences and targets
        print('Reading data file...')
        raw_evidences, raw_targets = self.read_data(clargs.input_file[0])
        raw_evidences = [[raw_evidence[i] for raw_evidence in raw_evidences] for i, ev in
                         enumerate(config.evidence)]

        # align with number of batches
        config.num_batches = int(len(raw_targets) / config.batch_size)
        assert config.num_batches > 0, 'Not enough data'
        sz = config.num_batches * config.batch_size
        for i in range(len(raw_evidences)):
            raw_evidences[i] = raw_evidences[i][:sz]
        raw_targets = raw_targets[:sz]

        # setup input and target chars/vocab
        if clargs.continue_from is None:
            for ev, data in zip(config.evidence, raw_evidences):
                ev.set_chars_vocab(data)
            counts = Counter([n for path in raw_targets for (n, _) in path])
            config.decoder.chars = sorted(counts.keys(), key=lambda w: counts[w], reverse=True)
            config.decoder.vocab = dict(zip(config.decoder.chars, range(len(config.decoder.chars))))
            config.decoder.vocab_size = len(config.decoder.vocab)

        # wrangle the evidences and targets into numpy arrays
        self.inputs = [ev.wrangle(data) for ev, data in zip(config.evidence, raw_evidences)]
        self.nodes = np.zeros((sz, config.decoder.max_seq_length), dtype=np.int32)
        self.edges = np.zeros((sz, config.decoder.max_seq_length), dtype=np.bool)
        self.targets = np.zeros((sz, config.decoder.max_seq_length), dtype=np.int32)
        for i, path in enumerate(raw_targets):
            self.nodes[i, :len(path)] = list(map(config.decoder.vocab.get, [p[0] for p in path]))
            self.edges[i, :len(path)] = [p[1] == CHILD_EDGE for p in path]
            self.targets[i, :len(path)-1] = self.nodes[i, 1:len(path)]  # shifted left by one

        # split into batches
        self.inputs = [np.split(ev_data, config.num_batches, axis=0) for ev_data in self.inputs]
        self.nodes = np.split(self.nodes, config.num_batches, axis=0)
        self.edges = np.split(self.edges, config.num_batches, axis=0)
        self.targets = np.split(self.targets, config.num_batches, axis=0)

        # reset batches
        self.reset_batches()

    def get_seq_paths(self, js, idx=0):
        if idx == len(js):
            return [[('STOP', SIBLING_EDGE)]]

        call = js[idx]['call']
        pv = [[(call, CHILD_EDGE)] +
              [('{}#{}'.format(i, state), SIBLING_EDGE) for i, state in enumerate(js[idx]['states'])] +
              [('STOP', SIBLING_EDGE)]]
        ph = [[(call, SIBLING_EDGE)] + path for path in self.get_seq_paths(js, idx + 1)]
        return pv + ph

    def read_data(self, filename):
        with open(filename) as f:
            js = json.load(f)
        data_points = []
        ignored, done = 0, 0

        for program in js['packages']:
            if 'data' not in program:
                continue
            try:
                evidence = [ev.read_data_point(program) for ev in self.config.evidence]
                sequences = list(chain.from_iterable([self.get_seq_paths(seq['sequence']) for seq in program['data']]))
                for sequence in sequences:
                    sequence.insert(0, ('START', CHILD_EDGE))
                    assert len(sequence) <= self.config.decoder.max_seq_length
                    data_points.append((evidence, sequence))
            except AssertionError:
                ignored += 1
            done += 1
        print('{:8d} programs in training data'.format(done))
        print('{:8d} programs ignored by given config'.format(ignored))

        # randomly shuffle to avoid bias towards initial data points during training
        random.shuffle(data_points)
        evidences, targets = zip(*data_points)

        return evidences, targets

    def next_batch(self):
        batch = next(self.batches)
        n, e, y = batch[:3]
        ev_data = batch[3:]

        # reshape the batch into required format
        rn = np.transpose(n)
        re = np.transpose(e)

        return ev_data, rn, re, y

    def reset_batches(self):
        self.batches = iter(zip(self.nodes, self.edges, self.targets, *self.inputs))
