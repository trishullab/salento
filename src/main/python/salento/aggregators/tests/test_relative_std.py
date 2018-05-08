# *************************************************************************************
# *
# * GOVERNMENT PURPOSE RIGHTS
# *
# * Contract Number: FA8750-15-2-0270 (Prime: William Marsh Rice University)
# * Contractor Name: GrammaTech, Inc. (Right Holder - subaward R18683)
# * Contractor Address: 531 Esty Street, Ithaca, NY  14850
# * Expiration Date: 22 September 2023
# *
# * The Government's rights to use, modify, reproduce, release, perform, display, or
# * disclose this software are restricted by DFARS 252.227-7014 --Rights in
# * Noncommercial Computer Software and Noncommercial Computer Software Documentation
# * clause contained in the above identified contract.  No restrictions apply after
# * the expiration date shown above.  Any reproduction of the software or portions
# * thereof marked with this legend must also reproduce the markings and any copyright.
# *
# *************************************************************************************
# *************************************************************************************
# *
# * (c) 2014-2017 GrammaTech, Inc.  All rights reserved.
# *
# *************************************************************************************

# This script computes the relative standard deviations using the raw probabilities

from __future__ import print_function
import argparse
import numpy as np
from salento.aggregators.base import Aggregator

class RawProbAggregator(Aggregator):
    """
    This is based on the simple sequence aggregator, here for each call
    the probablitiy is retrieved. The schema of the output is below
    {
        "title" : "Schema File for representation of the probablity values",
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
                        "description" : "raw probablitiy values"
                    }
                }
            }
        }
    }
    """
    def __init__(self, data_file, model_dir):
        Aggregator.__init__(self, data_file, model_dir)

    def run(self):
        result_data = {}
        for k, package in enumerate(self.packages()):
            result_data[str(k)] = {}
            spec = self.get_latent_specification(package)
            for j, sequence in enumerate(self.sequences(package)):
                events = self.events(sequence)
                event_data = {}
                for i, event in enumerate(events):
                    call_key = (str(i) + '_' + event['call'])
                    prob_value = float(self.distribution_next_call(
                        spec, events[:i], call=self.call(event)))
                    event_data[call_key] = prob_value
                event_key = str(j) + '_' + "".join(x['call'] for x in events)
                result_data[str(k)][event_key] = event_data
        return result_data

def compute_rel_std(all_json_objs):
    """
        return the relative std for each call across compute across every iteration
        @all_json_objects : it is the list of dict with prob values from each iteration
    """
    all_rel_stds = []
    for units in all_json_objs:
        for unit_k, unit_v in units.items():
            for seq_k, seq_v in unit_v.items():
                for call_k, _ in seq_v.items():
                    # compute variation across all iteration
                    collection = [o[unit_k][seq_k][call_k] for o in all_json_objs]
                    rel_std = 100 * np.std(collection)/np.mean(collection)
                    all_rel_stds.append(rel_std)
    return all_rel_stds

def driver(data_file, model_dir, iteration):
    """
        main driver function
        @data_file : test file with evidences
        @model_dir : directory where the model is saved
        @iteration : number of iterations
    """
    all_results = []
    with RawProbAggregator(data_file, model_dir) as aggregator:
        for _ in range(0, iteration):
            result = aggregator.run()
            all_results.append(result)
    # compute relative std error
    all_rel_stds = compute_rel_std(all_results)

    # print the results
    print("Smallest relative standard deviation: {}".format(min(all_rel_stds)))
    print("Biggest relative standard deviation: {}".format(max(all_rel_stds)))
    print("Average relative standard deviation: {}".format(np.mean(all_rel_stds)))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data_file',
        type=str,
        required=True,
        help='input data file')
    parser.add_argument(
        '--model_dir',
        type=str,
        required=True,
        help='directory to load model from')
    parser.add_argument(
        '--iterations',
        type=int, default=10,
        help='Number of iteration to run the results')
    args = parser.parse_args()

    driver(args.data_file, args.model_dir, args.iterations)
