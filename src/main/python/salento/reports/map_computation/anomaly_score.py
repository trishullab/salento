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
import gc
import heapq
# project imports
import metric
import data_parser


class FilterTraces(object):
    """ Implement different filtering options"""

    @staticmethod
    def filter_using_location(data):
        """
        :param data: input data list of dict, with the following keys
                ['Index List', // subset of the location at which the anomaly is lowest
                 'Location',   // list of all locations for each events
                 'Calls',      // list  of all events [not used in this function]
                 'key',        // unique key to identify this trace path or event sequence
                 'Probability', // prob vector associated with the events of interest( calls or states) [not used in this function]
                 'Anomaly Score' // Anomaly Score
                 ]
        :return: filtered list of data points
        """

        unit_dict = {}
        for value in data:
            # group by base key
            key = value["key"]
            unit_key = key.split('--')[0]
            if unit_key not in unit_dict:
                unit_dict[unit_key] = {}

            anomaly = value["Anomaly Score"]
            for index in value["Index List"]:
                location = value["Location"][index]
                if location not in unit_dict[unit_key]:
                    unit_dict[unit_key][location] = set([])
                # add the anomaly to the location
                unit_dict[unit_key][location].add((anomaly, key))

        valid_keys = set()
        # filter to get max anomaly at a location
        for unit_key, value in unit_dict.items():
            for location in value:
                # tuple of anomaly score and key, where max is done on first element(anomaly)
                max_anomaly = max(value[location])
                # add the valid key
                valid_keys.add(max_anomaly[1])
        return [entry for entry in data if entry["key"] in valid_keys]


class SarifFileGenerator(object):
    """
        Class to do Generator Sarif file
    """

    def __init__(self, metric_choice, data_file_forward, data_file_backward,
                 call, state, test_file, filter_proc):
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
        self.call = call
        self.state = state
        self.metric = metric.METRICOPTION[metric_choice]
        self.filter_proc = filter_proc
        self.data_list = []

    def apply_metric(self):
        """
        Apply the metric
        :return:
        """
        self.process_data.data_parser()
        self.process_data.apply_aggregation(self.metric)
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

    def update_location(self, valid_key=None):
        """
            update location
            @:param valid_key: list of keys to filter the data, useful get for once we need
        """
        # add location information
        location_dict = {}
        if self.test_file:
            location_dict = data_parser.create_location_list(
                self.test_file, self.state, valid_key)
        return location_dict

    def generate_anomaly_data(self, limit):
        """
        Reduce the data, apply metric, limit, update location, filter out

        :param limit: limit the result (usually 100 times the sarif file limit)
        """
        # apply metric
        self.apply_metric()
        h = []
        # reduce out to keep only the limited data

        for key, value in self.process_data.aggregated_data.items():
            value["key"] = key
            anomaly = value['Anomaly Score']
            # add to heap below limit
            if len(h) < limit:
                heapq.heappush(h, (anomaly, value))
            # remove after the limit
            else:
                heapq.heappushpop(h, (anomaly, value))

        # remove
        del self.process_data
        gc.collect()
        # keep the sorted list
        data_list = list(
            reversed([heapq.heappop(h)[1] for _ in range(len(h))]))
        # add the location
        loc_key = [val["key"] for val in data_list]
        location_dict = self.update_location(loc_key)
        new_data = []
        for entry in data_list:
            loc_entry = location_dict.get(entry["key"], None)
            if loc_entry:
                entry.update(loc_entry)
                new_data.append(entry)
        data_list = new_data

        # filtering
        if self.filter_proc:
            self.data_list = FilterTraces.filter_using_location(data_list)
        else:
            self.data_list = data_list

    def cvt_trace_to_sarif(self, anomaly_data):
        """
        convert anomaly data to sarif style data
        :param anomaly_data: dict containing anomaly score, events and call
        :return: dictionary containing sarif result
        """

        bug_index = set(anomaly_data["Index List"])
        if len(bug_index) == 1:
            index = str(anomaly_data["Index List"][0] + 1)
        else:
            index = ",".join([index_val + 1 for index_val in bug_index])
        message = "Anomaly Score is %f, Lowest prob. event in trace below: %s" % \
                  (anomaly_data["Anomaly Score"], index)
        sarif_results = {"codeFlows": [], "locations": [], "message": message}
        # set code flow
        codeflow_locations = {"locations": []}
        bug_locations = []

        for i, loc in enumerate(anomaly_data["Location"]):
            loc_split = loc.split(":")
            event = anomaly_data["Calls"][i]
            # set the bug point
            if i in bug_index:
                bug_point = dict(
                    resultFile={
                        "uri": "file://" + loc_split[0],
                        "region": {
                            "startLine": int(loc_split[1])
                        }
                    })
                bug_locations.append(bug_point)
            # update the index to get the correct probability
            if self.state:
                if "#" in event:
                    state_index, value = event.split("#")
                    prob = str(anomaly_data["Probability"][int(state_index)])
                    event = value
                else:
                    prob = str("NA")
            else:
                prob = str(anomaly_data["Probability"][i])
            # new message is set here
            error_msg = "event: %s, prob: %s" % (event, prob)
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

        self.generate_anomaly_data(limit * 100)
        # apply
        tool_result = {"tool": {"name": "Salento"}}
        results = []
        count = 0
        for i, data in enumerate(self.data_list):
            try:
                converted_data = self.cvt_trace_to_sarif(data)
                results.append(converted_data)
            except:
                count += 1
        print("Error in %d out of %d" % (count, len(self.data_list)))
        tool_result["results"] = results
        self.sarif_data["runs"].append(tool_result)
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
    parser.add_argument(
        '--filter_proc',
        type=bool,
        default=False,
        help="Set True to filter use unique anomaly per procedure")
    args = parser.parse_args()

    sarif_client = SarifFileGenerator(
        args.metric_choice, args.data_file_forward, args.data_file_backward,
        args.call, args.state, args.test_file, args.filter_proc)
    sarif_client.write_anomaly_score(args.result_file, args.limit)
