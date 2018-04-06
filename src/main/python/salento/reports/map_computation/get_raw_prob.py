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

    def __init__(self, data_file, model_dir):
        Aggregator.__init__(self, data_file, model_dir)
        self.call_probs = {}
        self.state_probs = {}
        self.call_use = False
        self.state_use = False

    def get_call_prob(self, spec, sequence):
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            prob_value = float(
                self.distribution_next_call(
                    spec, sequence, call=self.call(event)))
            event_data[call_key] = prob_value
        return event_data

    def get_state_prob(self, spec, sequence):
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            last_call_state = copy.deepcopy(event['states'])
            sequence[i]["states"] = []
            for s_i, st in enumerate(last_call_state):
                val = self.distribution_next_state(spec, sequence[:i+1], st)
                st_key = call_key + '--' + str(s_i) + "#" + str(st)
                sequence[i]["states"].append(st)
                event_data[st_key] = float(val)
        return event_data

    def run(self):
        """
            invoke the RNN to get the probability
        """
        # iterate over units
        for k, package in enumerate(self.packages()):
            if self.call_use:
                self.call_probs[str(k)] = {}
            if self.state_use:
                self.state_probs[str(k)] = {}
            spec = self.get_latent_specification(package)
            # iterate over sequence
            for j, sequence in enumerate(self.sequences(package)):
                events = self.events(sequence)
                if self.call_use:
                    self.call_probs[str(k)][str(j)] = self.get_call_prob(
                        spec, events)
                if self.state_use:
                    self.state_probs[str(k)][str(j)] = self.get_state_prob(
                        spec, events)


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
        '--call_prob_file',
        type=str,
        default=None,
        help='Write out the call probability in json file')
    parser.add_argument(
        '--state_prob_file',
        type=str,
        default=None,
        help='write out the state probability in json file')
    clargs = parser.parse_args()

    if clargs.call_prob_file is None and clargs.state_prob_file is None:
        raise AssertionError("Must get call or state probability")

    with RawProbAggregator(clargs.data_file, clargs.model_dir) as aggregator:
        if clargs.call_prob_file:
            aggregator.call_use = True
        if clargs.state_prob_file:
            aggregator.state_use = True
        aggregator.run()

        if clargs.call_prob_file:
            with open(clargs.call_prob_file, 'w') as fwrite:
                json.dump(aggregator.call_probs, fwrite)
        if clargs.state_prob_file:
            with open(clargs.state_prob_file, 'w') as fwrite:
                json.dump(aggregator.state_probs, fwrite)
