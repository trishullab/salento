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
import numpy as np
import tensorflow as tf

import argparse
import time
import os
import sys
import json
import textwrap

import ray
import ray.tune as tune

from salento.models.low_level_evidences.data_reader import Reader, smart_open
from salento.models.low_level_evidences.model import Model
from salento.models.low_level_evidences.utils import read_config, dump_config
from salento.reports.validation_exp import ExternalLoss

HELP = """\
Config options should be given as a JSON file (see config.json for example):
{                                         |
    "model": "lle"                        | The implementation id of this model (do not change)
    "latent_size": 32,                    | Latent dimensionality
    "batch_size": 50,                     | Minibatch size
    "num_epochs": 100,                    | Number of training epochs
    "learning_rate": 0.02,                | Learning rate
    "print_step": 1,                      | Print training output every given steps
    "alpha": 1e-05,                       | Hyper-param associated with KL-divergence loss
    "beta": 1e-05,                        | Hyper-param associated with evidence loss
    "evidence": [                         | Provide each evidence type in this list
        {                                 |
            "name": "apicalls",           | Name of evidence ("apicalls")
            "units": 64,                  | Size of the encoder hidden state
            "num_layers": 3               | Number of densely connected layers
            "tile": 1                     | Repeat the encoding n times (to boost its signal)
        }                                 |
    ],                                    |
    "decoder": {                          | Provide parameters for the decoder here
        "units": 256,                     | Size of the decoder hidden state
        "num_layers": 3,                  | Number of layers in the decoder
        "max_seq_length": 32              | Maximum length of the sequence
    }                                     |
}                                         |
"""

def trainer(cnfg, reporter):
   """
   :param cnfg: a dictionary of configuration
   :param reporter: ray reporter for logging value, passed by the tuner decorator, user has to do nothing
   """

    dict_ext = str(hash(frozenset(cnfg)))
    # update the name
    clargs.save += dict_ext
    pattern_loss.model_dir = clargs.save
    # create model dir
    os.mkdir(clargs.save)
    # update config
    config = read_config(cnfg, chars_vocab=clargs.continue_from)
    reader = Reader(clargs, config)
    # write the config
    with open(os.path.join(clargs.save, 'config.json'), 'w') as f:
        json.dump(dump_config(config), fp=f, indent=2)
    # set the model
    model = Model(config)

    with tf.Session() as sess:
        tf.global_variables_initializer().run()
        saver = tf.train.Saver(tf.global_variables(), max_to_keep=None)
        tf.train.write_graph(sess.graph_def, clargs.save, 'model.pbtxt')
        tf.train.write_graph(sess.graph_def, clargs.save, 'model.pb', as_text=False)

        # restore model
        if clargs.continue_from is not None:
            ckpt = tf.train.get_checkpoint_state(clargs.continue_from)
            saver.restore(sess, ckpt.model_checkpoint_path)

        # training
        for i in range(config.num_epochs):
            reader.reset_batches()
            avg_loss = avg_evidence = avg_latent = avg_generation = 0
            for b in range(config.num_batches):
                start = time.time()

                # setup the feed dict
                ev_data, n, e, y = reader.next_batch()
                feed = {model.targets: y}
                for j, ev in enumerate(config.evidence):
                    feed[model.encoder.inputs[j].name] = ev_data[j]
                for j in range(config.decoder.max_seq_length):
                    feed[model.decoder.nodes[j].name] = n[j]
                    feed[model.decoder.edges[j].name] = e[j]

                # run the optimizer
                loss, evidence, latent, generation, mean, covariance, _ \
                    = sess.run([model.loss,
                                model.evidence_loss,
                                model.latent_loss,
                                model.gen_loss,
                                model.encoder.psi_mean,
                                model.encoder.psi_covariance,
                                model.train_op], feed)
                end = time.time()
                avg_loss += np.mean(loss)
                avg_evidence += np.mean(evidence)
                avg_latent += np.mean(latent)
                avg_generation += generation
                step = i * config.num_batches + b
                if step % config.print_step == 0:
                    print('{}/{} (epoch {}), evidence: {:.3f}, latent: {:.3f}, generation: {:.3f}, '
                          'loss: {:.3f}, mean: {:.3f}, covariance: {:.3f}, time: {:.3f}'.format
                          (step, config.num_epochs * config.num_batches, i,
                           np.mean(evidence),
                           np.mean(latent),
                           generation,
                           np.mean(loss),
                           np.mean(mean),
                           np.mean(covariance),
                           end - start))
            checkpoint_dir = os.path.join(clargs.save, 'model{}.ckpt'.format(i))
            saver.save(sess, checkpoint_dir)

            ext_loss = pattern_loss.loss_func()
            print(ext_loss)

            print('Model checkpointed: {}. Average for epoch evidence: {:.3f}, latent: {:.3f}, '
                  'generation: {:.3f}, loss: {:.3f}, ext_loss: {:.3f}'.format
                  (checkpoint_dir,
                   avg_evidence / config.num_batches,
                   avg_latent / config.num_batches,
                   avg_generation / config.num_batches,
                   avg_loss / config.num_batches,
                   ext_loss))
            reporter(timesteps_total=i, mean_validation_accuracy=ext_loss)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(HELP))
    parser.add_argument('input_file', type=str, nargs=1,
                        help='input data file')
    parser.add_argument('--python_recursion_limit', type=int, default=10000,
                        help='set recursion limit for the Python interpreter')
    parser.add_argument('--save', type=str, default='save',
                        help='checkpoint model during training here')
    parser.add_argument('--config', type=str, default=None,
                        help='config file (see description above for help)')
    parser.add_argument('--continue_from', type=str, default=None,
                        help='ignore config options and continue training model checkpointed here')
    parser.add_argument('--good_pattern_file', type=str,
            help='good pattern file with schema pattern_file_schema.json')
    parser.add_argument('--bad_pattern_file', type=str,
            help='bad patterns file with schema pattern_file_schema.json')
    parser.add_argument('--state', type=bool,
            help='set true for state')
    parser.add_argument('--call', type=bool,
            help='set true for call')
    clargs = parser.parse_args()
    sys.setrecursionlimit(clargs.python_recursion_limit)
    if clargs.config and clargs.continue_from:
        parser.error('Do not provide --config if you are continuing from checkpointed model')
    if not clargs.config and not clargs.continue_from:
        parser.error('Provide at least one option: --config or --continue_from')

    # TODO this should be passed as command line option. Refactor this in next iteration
    basic_config = {
    "model": "lle",
    "learning_rate": tune.grid_search([0.0001, 0.001, 0.01]),
    "latent_size": 32,
    "batch_size":  tune.grid_search([25, 50, 100]),
    "num_epochs": 5,
    "print_step": 100,
    "alpha": 0,
    "beta": 0,
    "evidence": [
        {
            "name": "apicalls",
            "units": tune.grid_search([16, 32]),
            "num_layers": tune.grid_search([1, 2, 3]),
            "tile": 1
        }
    ],
    "decoder": {
        "units": tune.grid_search([16, 32]),
        "num_layers": tune.grid_search([1, 2, 3]),
        "max_seq_length": tune.grid_search([16, 32])
    }
    }

    pattern_loss = ExternalLoss.PatternLoss(clargs.save, clargs.good_pattern_file, clargs.bad_pattern_file)
    if clargs.call:
        pattern_loss.call = True
    if clargs.state:
        pattern_loss.state = True

    ray.init(num_cpus=1, num_gpus=0)
    tune.register_trainable("train_func", trainer)

    tune.run_experiments({
        "my_experiment": {
        "run": "train_func",
        "repeat" : 1,
        "stop": {"mean_validation_accuracy": 0.00., 'timesteps_total':4},
        "config": basic_config,
        "local_dir": "ray_results",
        }
    }, )
