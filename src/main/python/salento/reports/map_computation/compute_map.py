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

# Script Purpose : Driver code to compute maps score for test data

from __future__ import print_function
import json
import argparse
import operator
# project imports
import metric
import data_parser


def get_anamolous_list(test_data_file):
    """
    helper script to read a ground truth file with anomalous entries.
    This is used to compute the ranking for MAP score
    @test_data_file : Salento acceptable Test Data File with anomalous entry
    returns a list of anomalous keys
    """
    with open(test_data_file, 'r') as fread:
        json_data = json.load(fread)

    anamolous_keys = set()
    for k, data in enumerate(json_data['packages']):
        for j, seq in enumerate(data['data']):
            if data['name'] == 'anomalous' and j == len(data['data']) - 1:
                call_key = ''.join([seqs['call'] for seqs in seq['sequence']])
                seq_key = '%d_%d_%s' % (k, j, call_key)
                anamolous_keys.add(seq_key)
    return anamolous_keys


def compute_map(data, anomalous_keys):
    """
        This function computes the map score for test data
        @data : test_Data with seq keys and anomaly scores
        @anomalous_keys : a list of the ground truth with anomalous seq key
        Assumption : Every anomalous keys is present in the data
        return map_score
    """
    # sort the data
    sorted_data = sorted(
        data.items(), key=operator.itemgetter(1), reverse=True)
    # set the indices
    # @indices: a list of ranks of correctly retrieved items
    # note that the ranks are 0-based (i.e, best rank = 0)
    indices = []
    for i, keys in enumerate(sorted_data):
        if keys[0] in anomalous_keys:
            indices.append(i)
    collected_precision = []
    for i, val in enumerate(indices):
        collected_precision.append((i + 1) / float(val + 1))
    map_score = sum(collected_precision) / (len(collected_precision))
    return map_score


def get_map_score():
    """
    computes the map score
    """
    parser = argparse.ArgumentParser(description="Compute map scores")
    parser.add_argument(
        '--data_file_forward',
        required=True,
        type=str,
        help="Data file with forward raw probabilities")
    parser.add_argument(
        '--data_file_backward',
        type=str,
        help="Data file with backward raw probabilities")
    parser.add_argument(
        '--metric_choice',
        required=True,
        type=str,
        choices=metric.METRICOPTION.keys(),
        help="Choose the metric to be applied")
    parser.add_argument(
        '--test_data_file', type=str, help="Get anomaly keys from test_files")
    parser.add_argument(
        '--result_file',
        default=None,
        type=str,
        help="Write out the results in a file")
    parser.add_argument(
        '--direction',
        default='forward',
        type=str,
        choices=['forward', 'bidirectional'],
        help="Choose type of combination")
    args = parser.parse_args()
    # anomalous key
    anomalous_keys = get_anamolous_list(args.test_data_file)
    process_data = data_parser.ProcessCallData(args.data_file_forward,
                                               args.data_file_backward)
    # apply metric
    process_data.apply_aggregation(metric.METRICOPTION[args.metric_choice])
    # get map score
    map_scores = compute_map(process_data.aggregated_data, anomalous_keys)
    if args.result_file:
        with open(args.result_file, 'w') as f_write:
            json.dump(map_scores, f_write)
    else:
        print(json.dumps(map_scores, indent=2))


if __name__ == "__main__":
    get_map_score()
