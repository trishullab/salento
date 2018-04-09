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

import tensorflow as tf
import numpy as np
import re
from collections import Counter

from salento.models.low_level_evidences.utils import CONFIG_ENCODER, CONFIG_INFER


class Evidence(object):

    def init_config(self, evidence, chars_vocab):
        for attr in CONFIG_ENCODER + (CONFIG_INFER if chars_vocab else []):
            self.__setattr__(attr, evidence[attr])

    def dump_config(self):
        js = {attr: self.__getattribute__(attr) for attr in CONFIG_ENCODER + CONFIG_INFER}
        return js

    @staticmethod
    def read_config(js, chars_vocab):
        evidences = []
        for evidence in js:
            name = evidence['name']
            if name == 'apicalls':
                e = APICalls()
            else:
                raise TypeError('Invalid evidence name: {}'.format(name))
            e.init_config(evidence, chars_vocab)
            evidences.append(e)
        return evidences

    def read_data_point(self, program):
        raise NotImplementedError('read_data() has not been implemented')

    def set_chars_vocab(self, data):
        raise NotImplementedError('set_chars_vocab() has not been implemented')

    def wrangle(self, data):
        raise NotImplementedError('wrangle() has not been implemented')

    def placeholder(self, config):
        raise NotImplementedError('placeholder() has not been implemented')

    def exists(self, inputs):
        raise NotImplementedError('exists() has not been implemented')

    def init_sigma(self, config):
        raise NotImplementedError('init_sigma() has not been implemented')

    def encode(self, inputs, config):
        raise NotImplementedError('encode() has not been implemented')

    def evidence_loss(self, psi, encoding, config):
        raise NotImplementedError('evidence_loss() has not been implemented')


def _extract_evidence(program):
    sequences = program['data']
    return list(set([calls['call'] for sequence in sequences for calls in sequence['sequence']]))

def _valid_apicalls(program, max_seqs=9999, max_seq_length=9999):
    sequences = program['data']

    if max_seqs >= 0 and len(sequences) > max_seqs:
        return False

    if max_seq_length >= 0 and any([len(sequence['sequence']) > max_seq_length for sequence in sequences]):
        return False

    return True

def _get_apicalls(program, max_seqs=9999, max_seq_length=9999, KEY='apicalls', cache=True):
    if KEY in program:
        return program[KEY]
    result = _extract_evidence(program) if _valid_apicalls(program, max_seqs, max_seq_length) else []
    if cache:
        program[KEY] = result
    return result

def update_apicalls(program, max_seqs=9999, max_seqs_length=9999, KEY='apicalls'):
    if KEY in program:
        return True
    if _valid_apicalls(program, max_seq, max_seqs_length):
        program[KEY] = _extract_evidence(program)
        return True
    return False

class APICalls(Evidence):

    def read_data_point(self, program):
        return _get_apicalls(program)

    def set_chars_vocab(self, data):
        counts = Counter([c for apicalls in data for c in apicalls])
        self.chars = sorted(counts.keys(), key=lambda w: counts[w], reverse=True)
        self.vocab = dict(zip(self.chars, range(len(self.chars))))
        self.vocab_size = len(self.vocab)

    def wrangle(self, data):
        wrangled = np.zeros((len(data), 1, self.vocab_size), dtype=np.int32)
        for i, apicalls in enumerate(data):
            for c in apicalls:
                if c in self.vocab:
                    wrangled[i, 0, self.vocab[c]] = 1
        return wrangled

    def placeholder(self, config):
        return tf.placeholder(tf.float32, [config.batch_size, 1, self.vocab_size])

    def exists(self, inputs):
        i = tf.reduce_sum(inputs, axis=2)
        return tf.not_equal(tf.count_nonzero(i, axis=1), 0)

    def init_sigma(self, config):
        with tf.variable_scope('apicalls'):
            self.sigma = tf.get_variable('sigma', [])

    def encode(self, inputs, config):
        with tf.variable_scope('apicalls'):
            latent_encoding = tf.zeros([config.batch_size, config.latent_size])
            inp = tf.slice(inputs, [0, 0, 0], [config.batch_size, 1, self.vocab_size])
            inp = tf.reshape(inp, [-1, self.vocab_size])
            encoding = tf.layers.dense(inp, self.units, activation=tf.nn.tanh)
            for i in range(self.num_layers - 1):
                encoding = tf.layers.dense(encoding, self.units, activation=tf.nn.tanh)
            w = tf.get_variable('w', [self.units, config.latent_size])
            b = tf.get_variable('b', [config.latent_size])
            latent_encoding += tf.nn.xw_plus_b(encoding, w, b)
            return latent_encoding

    def evidence_loss(self, psi, encoding, config):
        sigma_sq = tf.square(self.sigma)
        loss = 0.5 * (config.latent_size * tf.log(2 * np.pi * sigma_sq + 1e-10)
                      + tf.square(encoding - psi) / sigma_sq)
        return loss
