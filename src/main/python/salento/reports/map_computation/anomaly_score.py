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

# Script Purpose : Driver code to write anomaly score for test data

import json
import argparse
# project imports
import metric
import data_parser


def get_result(anomaly_data):
    """
    convert anomaly data to sarif style data
    :param anomaly_data: dict containing anomaly score, events and call
    :return: dictionary containing sarif result
    """

    message = "Anomaly Score is %f, Probability Vector %s" % \
              (anomaly_data["Anomaly Score"], str(anomaly_data["Probability"]))
    sarif_results = {"codeFlows": [], "locations": [], "message": message}
    # set code flow
    codeflow_locations = {"locations": []}
    bug_locations = []
    bug_index = set(anomaly_data["Index List"])
    for i, loc in enumerate(anomaly_data["Location"]):
        loc_split = loc.split(":")
        # set the bug point
        if i in bug_index:
            error_msg = "Anomalous Usage at %s" % anomaly_data["Calls"][i]
            bug_point = dict(
                resultFile={
                    "uri": "file://" + loc_split[0],
                    "region": {
                        "startLine": int(loc_split[1])
                    }
                })
            bug_locations.append(bug_point)
        else:
            error_msg = "Call point %s at trace path seq %d" % (anomaly_data["Calls"][i],i)
        # set the trace point
        trace_point = {
            "message": error_msg,
            # steps cannot be 0
            "step": i + 1,
            "physicalLocation": {
                "uri": "file://" + loc_split[0],
                "region": {
                    "startLine": int(loc_split[1]),
                    "endLine": int(loc_split[1])
                }
            }
        }
        codeflow_locations["locations"].append(trace_point)
    sarif_results["codeFlows"].append(codeflow_locations)
    sarif_results["locations"] = bug_locations
    return sarif_results


def write_anomaly_score(metric_choice, data_file_forward, data_file_backward,
                        call, state, test_file, sarif_file, limit=100):
    """

    :param metric_choice: the metric to use
    :param data_file_forward: files with forward probabilities
    :param data_file_backward: files with reverse probabilities
    :param call: if call probability
    :param state: if state probability
    :param test_file: original test file
    :param sarif_file: sarif files name
    :param limit: limit the results
    :return:
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

    # update the state:
    if state:
        for key in process_data.aggregated_data:
            key_split = key.split('--')
            new_list = []
            for index in process_data.aggregated_data[key]["Index List"]:
                in_key = int(key_split[2]) + 1 + index
                new_list.append(in_key)
            process_data.aggregated_data[key]["Index List"] = new_list
    # convert to list
    data_list = [value for key, value in process_data.aggregated_data.items()]
    # sorted list
    data_list = sorted(
        data_list, key=lambda i: i['Anomaly Score'], reverse=True)

    sarif_data = {"runs": [], "version": "1.0.0"}
    tool_result = {"tool": {"name": "Salento"}}

    results = []
    for i, data in enumerate(data_list[0:limit]):
        converted_data = get_result(data)
        converted_data["message"] += ", seq id %d" % i
        results.append(converted_data)

    tool_result["results"] = results
    sarif_data["runs"].append(tool_result)
    if sarif_file:
        with open(sarif_file, 'w') as fwrite:
            json.dump(sarif_data, fwrite, indent=2)
    else:
        print(json.dumps(sarif_data, indent=2))


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
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help="Limit the result to top N anomaly")
    args = parser.parse_args()
    write_anomaly_score(args.metric_choice, args.data_file_forward,
                        args.data_file_backward, args.call, args.state,
                        args.test_file, args.result_file,
                        args.limit)
