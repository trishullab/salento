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

    def run(self):
        """
            invoke the RNN to get the probability
            return combined call and state probability values
        """
        result_data = {}
        # iterate over units
        for k, package in enumerate(self.packages()):
            result_data[str(k)] = {}
            spec = self.get_latent_specification(package)
            # iterate over sequence
            for j, sequence in enumerate(self.sequences(package)):
                events = self.events(sequence)
                seq_calls = "--".join(x['call'] for x in events)
                event_key = str(j) + '--' + seq_calls
                event_data = {}
                # iterate over calls
                for i, event in enumerate(events):
                    call_key = (str(i) + '--' + event['call'])
                    call_prob = float(self.distribution_next_call(
                        spec, events[:i+1], call=self.call(event)))
                    # next state probability
                    dist = self.distribution_next_state(spec, events[:i+1], None)
                    # use the probability summation rule on conditional
                    # probability to get a unified probability value
                    # Pr(Call, States) = Pr(State0| Call)Pr(Call) +
                    #                    Pr(State1| Call)Pr(Call) +
                    #                    Pr(State2| Call)Pr(Call)
                    prob_value = 0
                    # get the individual states
                    for key, value in dist.items():
                        if '#' in key:
                            prob_value += call_prob*value
                    event_data[call_key] = prob_value
                result_data[str(k)][event_key] = event_data
        return result_data

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_file', type=str, required=True,
                        help='input data file')
    parser.add_argument('--model_dir', type=str, required=True,
                        help='directory to load model from')
    parser.add_argument('--result_file', type=str, default=None,
                        help='write out result in json file')
    clargs = parser.parse_args()

    with RawProbAggregator(clargs.data_file, clargs.model_dir) as aggregator:
        result = aggregator.run()
    if clargs.result_file:
        with open(clargs.result_file, 'w') as fwrite:
            json.dump(result, fwrite)
    else:
        print(json.dumps(result))
