"""
# ****************************************************************************
#
# GOVERNMENT PURPOSE RIGHTS
#
# Contract Number: FA8750-15-2-0270 (Prime: William Marsh Rice University)
# Contractor Name: GrammaTech, Inc. (Right Holder - subaward R18683)
# Contractor Address: 531 Esty Street, Ithaca, NY  14850
# Expiration Date: 22 September 2023
#
# The Government's rights to use, modify, reproduce, release, perform,
# display, or disclose this software are restricted by DFARS 252.227-7014
# Rights in Noncommercial Computer Software and Noncommercial Computer Software
# Documentation clause contained in the above identified contract.
# No restrictions apply after the expiration date shown above.
# Any reproduction of the software or portions thereof marked with this legend
# must also reproduce the markings and any copyright.
#
# ****************************************************************************
# ****************************************************************************
#
# (c) 2014-2018 GrammaTech, Inc.  All rights reserved.
#
# ****************************************************************************

"""

from __future__ import print_function
import argparse
import json
import copy
import os
from salento.aggregators.base import Aggregator


class RawProbAggregator(Aggregator):
    """
    This is based on the simple sequence aggregator, here for each call
    the probability is retrieved. The schema of the output is below
    {
        "title" : "Schema File for representation of the probability values",
        "type" : "object",
        "properties" : {
            "type" : "object",
            "description" : "Each unit",
            "properties" : {
                "type" : "object",
                "description" : "Each Sequence",
                "properties" : {
                    "type" : "object",
                    "description" : "Each Call",
                    "properties" : {
                        "type" : "number",
                        "description" : "raw probability values"
                    }
                }
            }
        }
    }
    """

    def __init__(self,
                 data_file,
                 model_dir,
                 good_seq,
                 bad_seq):
        """

        :param data_file: file with test data
        :param model_dir: directory where model is saved
        """
        Aggregator.__init__(self, data_file, model_dir)
        self.good_seq = good_seq
        self.bad_seq = bad_seq
        self.good_seq_prob = {}
        self.bad_seq_prob = {}

    def get_call_prob(self, spec, sequence):
        """
        Compute call probability
        :param spec: latent specification
        :param sequence: a sequences of events
        :return: predicted call probabilities
        """
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            prob_value = float(
                self.distribution_next_call(
                    spec, sequence, call=self.call(event)))
            event_data[call_key] = prob_value
        return event_data

    def get_state_prob(self, spec, sequence):
        """
        Compute state probability
        :param spec: latent specification
        :param sequence: a sequences of events
        :return: predicted states probabilities
        """
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            last_call_state = copy.deepcopy(event['states'])
            sequence[i]["states"] = []
            for s_i, st in enumerate(last_call_state):
                val = self.distribution_next_state(spec, sequence[:i + 1], st)
                st_key = call_key + '--' + str(s_i) + "#" + str(st)
                sequence[i]["states"].append(st)
                event_data[st_key] = float(val)
        return event_data

    def is_valid_bad_seq(self, events):
        """
        check if the sequence is a valid bad sequence
        :param events: object of sequences
        :return: if call list is same as seq list
        """
        bad_call_list = [event['call'] for event in events if event['call'] in self.bad_seq]
        return bad_call_list == self.bad_seq

    def is_valid_good_seq(self, events):
        """
         check if the sequence is a valid good sequence
        :param events: object of sequences
        :return:
        """
        good_call_list = [event['call'] for event in events if event['call'] in self.good_seq]
        return good_call_list == self.good_seq

    def run(self, call=True, state=False):
        """
        :param call: get call probability
        :param state: set to get state probability
        """
        """
            invoke the RNN to get the probability
        """
        print("Total packages {}".format(len(self.packages())))
        for k, package in enumerate(self.packages()):
            print(
                'Query Probability For Package Number {} '.format(k), end='\r')
            spec = self.get_latent_specification(package)
            # iterate over sequence
            for j, sequence in enumerate(self.sequences(package)):
                events = self.events(sequence)

                if self.is_valid_bad_seq(events):
                    if k not in self.bad_seq_prob:
                        self.bad_seq_prob[k] = {}
                    if call:
                        self.bad_seq_prob[k][j] = self.get_call_prob(spec, events)
                    if state:
                        self.bad_seq_prob[k][j] = self.get_state_prob(spec, events)
                if self.is_valid_good_seq(events):
                    if k not in self.good_seq_prob:
                        self.good_seq_prob[k] = {}
                    if call:
                        self.good_seq_prob[k][j] = self.get_call_prob(spec, events)
                    elif state:
                        self.good_seq_prob[k][j] = self.get_state_prob(spec, events)

    def write_files(self, good_seq_prob_file=None, bad_seq_prog_file=None):
        """
        write out the file
        :param good_seq_prob_file: string containing the file to write out the good patterns probability
        :param bad_seq_prog_file: string containing the file to write out the wrong patterns probability

        """
        if good_seq_prob_file:
            with open(good_seq_prob_file, 'w') as fwrite:
                json.dump(self.good_seq_prob, fwrite)
        if bad_seq_prog_file:
            with open(bad_seq_prog_file, 'w') as fwrite:
                json.dump(self.bad_seq_prob, fwrite)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data_file',
        type=str,
        required=True,
        help='input test data file with evidences')
    parser.add_argument(
        '--model_dir',
        type=str,
        required=True,
        help='directory to load the model from')
    parser.add_argument(
        '--good_seq_prob_file',
        type=str,
        default=None,
        help='Write out the good probability in json file')
    parser.add_argument(
        '--bad_seq_prog_file',
        type=str,
        default=None,
        help='write out the bad probability in json file')
    parser.add_argument(
        '--good_pattern',
        type=str,
        nargs='+',
        help='good patterns list')
    parser.add_argument(
        '--bad_pattern',
        type=str,
        nargs='+',
        help='bad pattern list')
    parser.add_argument(
        '--call',
        type=bool,
        help="Set True to compute anomaly score using call probability")
    parser.add_argument(
        '--state',
        type=bool,
        help="Set True to compute anomaly score using states probability")

    clargs = parser.parse_args()

    with RawProbAggregator(clargs.data_file, clargs.model_dir, clargs.good_pattern, clargs.bad_pattern) as aggregator:
        aggregator.run(clargs.call, clargs.state)
        aggregator.write_files(clargs.good_seq_prob_file, clargs.bad_seq_prog_file)
