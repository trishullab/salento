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


def write_anomaly_score(metric_choice, data_file_forward, data_file_backward,
                        call, state, test_file, result_file):
    """

    :param metric_choice:
    :param data_file_forward:
    :param data_file_backward:
    :param call:
    :param state:
    :param test_file:
    :param result_file:
    :return:
    {
        "title": "Schema File for anomaly score",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "Anomaly Score": {
                    "type": "number",
                    "description": "The aggregated score"
                },
                "Locations": {
                    "type": "array",
                    "description": "The location of all the calls in path",
                    "item": {
                        "type": "string"
                    }
                },
                "Index List": {
                    "type": "array",
                    "description": "All the indicies of the lowest prob value",
                    "item": {
                        "type": "integer"
                    }
                },
                "Events": {
                    "type": "array",
                    "description": "All the call/states in path",
                    "item": {
                        "type": "string"
                    }
                }
            }
        }
    }

    """

    if call:
        process_data = data_parser.ProcessCallData(data_file_forward,
                                                   data_file_backward)
    elif state:
        process_data = data_parser.ProcessStateData(data_file_forward,
                                                    data_file_backward)
    else:
        raise AssertionError("Either --call or --state must be set")
    process_data.data_parser()
    process_data.apply_aggregation(metric.METRICOPTION[metric_choice])

    # add location information
    if test_file:
        location_dict = data_parser.create_location_list(test_file, state)
        for key, value in process_data.aggregated_data.items():
            process_data.aggregated_data[key].update(
                location_dict.get(key, {}))
    # convert to list
    data_list = [value for key, value in process_data.aggregated_data.items()]
    # sorted list
    data_list = sorted(
        data_list, key=lambda i: i['Anomaly Score'], reverse=True)

    if result_file:
        with open(result_file, 'w') as fwrite:
            json.dump(data_list, fwrite, indent=2)
    else:
        print(json.dumps(data_list, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute Anomaly scores")
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
        '--result_file', type=str, help="File to write the anomaly score")
    parser.add_argument('--test_file', type=str, help="test_file_used")
    parser.add_argument('--call', type=bool, help="Set True for call file")
    parser.add_argument(
        '--state', type=bool, help="Set True for state anomaly")

    args = parser.parse_args()
    write_anomaly_score(args.metric_choice, args.data_file_forward,
                        args.data_file_backward, args.call, args.state,
                        args.test_file, args.result_file)
