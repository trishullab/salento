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
import collections


class SarifFileGenerator(object):
    """
        Class to do Generator Sarif file
    """

    def __init__(self, metric_choice, data_file_forward, data_file_backward,
                 call, state, test_file):
        """
        :param metric_choice: the metric to use
        :param data_file_forward: files with forward probabilities
        :param data_file_backward: files with reverse probabilities
        :param call: if call probability
        :param state: if state probability
        :param test_file: original test file
        """
        self.sarif_data = {"version": "1.0.0", "runs": []}
        # set the process
        if call:
            self.process_data = data_parser.ProcessCallData(
                data_file_forward, data_file_backward)
        elif state:
            self.process_data = data_parser.ProcessStateData(
                data_file_forward, data_file_backward)
        else:
            raise AssertionError("Either --call or --state must be set")

        self.test_file = test_file
        self.state = state
        self.metric = metric.METRICOPTION[metric_choice]

    def apply_metric(self):
        """
        Apply the metric
        :return:
        """
        self.process_data.data_parser()
        self.process_data.apply_aggregation(self.metric)

    def update_location(self):
        """
            update location
        """
        # add location information
        if self.test_file:
            location_dict = data_parser.create_location_list(
                self.test_file, self.state)
            for key, value in self.process_data.aggregated_data.items():
                self.process_data.aggregated_data[key].update(
                    location_dict.get(key, {}))

        # update the state:
        if self.state:
            for key in self.process_data.aggregated_data:
                key_split = key.split('--')
                new_list = []
                for index in self.process_data.aggregated_data[key][
                        "Index List"]:
                    in_key = int(key_split[2]) + 1 + index
                    new_list.append(in_key)
                self.process_data.aggregated_data[key]["Index List"] = new_list

    def get_all_data(self, filter_proc):
        """
            filter out traces that are not in
        """
        all_data = self.process_data.aggregated_data
        if filter_proc is False:
            return all_data

        # pick the unique keys
        temp_dict = {}
        key_dict = {}
        for key, value in all_data.items():
            key_base = key.split('--')[0]
            anomaly = value['Anomaly Score']
            if key_base not in temp_dict:
                temp_dict[key_base] = set([])
                key_dict[key_base] = []
                key_dict[key_base].append(key)
                temp_dict[key_base].add(anomaly)
            else:

                if anomaly not in temp_dict[key_base]:
                    key_dict[key_base].append(key)
                    temp_dict[key_base].add(anomaly)

        useful_key = set([])
        for key, data in key_dict.items():
            for x in data:
                useful_key.add(x)
        return {
            key: value
            for key, value in all_data.items() if key in useful_key
        }

    def create_sarif_data(self, limit):
        """
        create sarif acceptable data
        :param limit:
        :return:
        """
        all_data = self.get_all_data(True)
        data_list = [value for key, value in all_data.items()]
        # sorted list
        data_list = sorted(
            data_list, key=lambda i: i['Anomaly Score'], reverse=True)

        data_list = data_list[0:limit]
        tool_result = {"tool": {"name": "Salento"}}
        results = []
        for i, data in enumerate(data_list):
            converted_data = self.cvt_trace_to_sarif(data)
            converted_data["message"] += ", seq id %d" % i
            results.append(converted_data)

        tool_result["results"] = results
        self.sarif_data["runs"].append(tool_result)

    def cvt_trace_to_sarif(self, anomaly_data):
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
                error_msg = "Call point %s at trace path seq %d" % (
                    anomaly_data["Calls"][i], i)
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

    def write_anomaly_score(self, sarif_file, limit=100):
        """
        :param sarif_file: sarif files name
        :return:
        """
        self.apply_metric()
        self.update_location()
        self.create_sarif_data(limit)
        if sarif_file:
            with open(sarif_file, 'w') as fwrite:
                json.dump(self.sarif_data, fwrite, indent=2)
        else:
            print(json.dumps(self.sarif_data, indent=2))


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

    sarif_client = SarifFileGenerator(
        args.metric_choice, args.data_file_forward, args.data_file_backward,
        args.call, args.state, args.test_file)
    sarif_client.write_anomaly_score(args.result_file, args.limit)
