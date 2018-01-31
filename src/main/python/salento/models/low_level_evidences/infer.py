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
import tensorflow as tf
import numpy as np

import os
import json

from salento.models.low_level_evidences.model import Model
from salento.models.low_level_evidences.utils import CHILD_EDGE, SIBLING_EDGE
from salento.models.low_level_evidences.utils import read_config


class BayesianPredictor(object):

    def __init__(self, save, sess):
        self.sess = sess

        # load the saved config
        with open(os.path.join(save, 'config.json')) as f:
            config = read_config(json.load(f), chars_vocab=True)
        self.model = Model(config, True)

        # restore the saved model
        self.sess.run(tf.global_variables_initializer())
        saver = tf.train.Saver(tf.global_variables())
        ckpt = tf.train.get_checkpoint_state(save)
        saver.restore(self.sess, ckpt.model_checkpoint_path)

    def _sequence_to_graph(self, sequence, step='call'):
        seq = [('START', CHILD_EDGE)] + [(call['call'], SIBLING_EDGE) for call in sequence[:-1]]
        if len(sequence) > 0:
            if step == 'call':
                seq.append((sequence[-1]['call'], SIBLING_EDGE))
            elif step == 'state':
                seq.append((sequence[-1]['call'], CHILD_EDGE))
                for i, state in enumerate(sequence[-1]['states']):
                    seq.append(('{}#{}'.format(i, state), SIBLING_EDGE))
            else:
                raise ValueError('invalid step: {}'.format(step))

        return zip(*seq)

    # step can be 'call' or 'state', depending on if you are looking for distribution over the next call/state
    def infer_step(self, psi, sequence, step='call'):
        nodes, edges = self._sequence_to_graph(sequence, step)
        dist = self.model.infer_seq(self.sess, psi, nodes, edges)
        return self._create_distribution(dist)

    def infer_step_iter(self, psi, sequence, step='call', cache=None):
        nodes, edges = self._sequence_to_graph(sequence=sequence, step=step)
        for node, edge, dist in self.model.infer_seq_iter(self.sess, psi, nodes, edges, cache):
            yield node, self._create_distribution(dist)

    def _create_distribution(self, dist):
        return {self.model.config.decoder.chars[i]: dist[i] for i in range(len(dist))}

    def psi_random(self):
        return np.random.normal(size=[1, self.model.config.latent_size])

    def psi_from_evidence(self, js_evidences):
        return self.model.infer_psi(self.sess, js_evidences)
