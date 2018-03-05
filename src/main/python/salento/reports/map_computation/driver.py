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

import json
import argparse
# project imports
import metric
import data_parser


def get_map_score(data_file_forward, data_file_backward, metric_choice,
                  anomalous_keys, direction='forward'):
    """
       computes the map score
       @data_file_forward (type:string) : file with forward probabilities
       @data_file_backward (type:string) : file with reverse probabilities
       @metric_choice (type:string) : key of metric to apply
       @anomalous_keys (type:list) : list of procedures that are anomalous,
       identified by the unique keys
       @direction (type:string) : option for forward or bi-directional
       returns Mean Average Precision Score
    """
    if direction == 'forward':
        #set forward data
        process_data = data_parser.ProcessDataImpl(data_file_forward)
        process_data.data_parser()
    else:
        # set bidirectional
        process_data = data_parser.ProcessBiDataImpl(data_file_forward, data_file_backward)
    # apply metric
    process_data.apply_aggregation(metric.METRICOPTION[metric_choice])
    # get map score
    map_score = metric.compute_map(process_data.aggregated_data, anomalous_keys)
    return map_score

if __name__ == "__main__":
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
        '--test_data_file',
        type=str,
        help="Get anomaly keys from test_files")
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
    anomalous_keys = data_parser.get_anamolous_list(args.test_data_file)

    map_scores = get_map_score(
        args.data_file_forward,
        args.data_file_backward,
        args.metric_choice,
        anomalous_keys,
        args.direction)
    if args.result_file:
        with open(args.result_file, 'w') as fwrite:
            json.dump(map_scores, fwrite)
    else:
        print(json.dumps(map_scores, indent=2))
