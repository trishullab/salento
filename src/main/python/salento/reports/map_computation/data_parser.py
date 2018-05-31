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

# Script Purpose : Implement code to parse raw prob data and apply aggregation
from __future__ import print_function
import json

END_MARKER = "STOP"

class ProcessData(object):
    """ Takes in detailed probability call computes the metrics """

    def __init__(self, forward_prob_file=None, reverse_prob_file=None):
        """
        :param forward_prob_file: file with forward probability
        :param reverse_prob_file: file with reverse probability
        """
        self.forward_prob_data = None
        self.reverse_prob_data = None
        # read the probability data
        if forward_prob_file:
            with open(forward_prob_file, 'r') as fread:
                self.forward_prob_data = json.load(fread)
        if reverse_prob_file:
            with open(reverse_prob_file, 'r') as fread:
                self.reverse_prob_data = json.load(fread)
        # stores the sequence vector for reverse data
        self.reverse_obj = {}
        # stores the sequence vector for forward  data
        self.forward_obj = {}
        # aggregated results  after applying metric
        self.aggregated_data = {}
        # call or state events list for the sequence
        self.event_list = {}
        self.call = None

    def data_parser(self):
        """
        Implement custom data parser that sets the
        a unique sequence key and prob vector associated with it
        """
        raise NotImplementedError("Override it!")

    def apply_aggregation(self, operator_type):
        """
        reads the sequence and applies the aggregation function
        it then store the result in the self.aggregated_data
        :param operator_type: one of the operators from Metric Option
        it updates the anomaly for the sequence
        """
        for seq_key in self.forward_obj:
            # get the forward prob
            forward_probs = self.forward_obj[seq_key]
            # get the reverse prob
            if self.reverse_prob_data:
                reverse_probs = self.reverse_obj[seq_key]
                combined_probability_vector = list(
                    map(lambda t: t[0] * t[1], zip(forward_probs,
                                                   reverse_probs)))
            else:
                combined_probability_vector = forward_probs
            # ignore the first prob value
            if self.call:
                index_list, score = operator_type(combined_probability_vector[1:])
                # add +1 to index to account for not using first prob
                index_list = [x + 1 for x in index_list]
            else:
                try:
                    index_list, score = operator_type(combined_probability_vector)
                except:
                    index_list = []
                    score = float('-inf')

            self.aggregated_data[seq_key] = {
                "Anomaly Score": score,
                "Index List": index_list,
                "Events": self.event_list[seq_key],
                "Probability": combined_probability_vector
            }


class ProcessCallData(ProcessData):
    """  Process Data using our notation """

    def __init__(self, forward_prob_file, reverse_prob_file=None):
        """
        :param forward_prob_file: file with forward probability
        :param reverse_prob_file: file with reverse probability
        """
        ProcessData.__init__(self, forward_prob_file, reverse_prob_file)
        self.call = True

    def data_parser(self):
        """
            custom data parser, returns
            a. unique seq_key
            b. seq_prob
        """
        for unit_key in self.forward_prob_data:
            for seq_key in self.forward_prob_data[unit_key].keys():
                new_seq_key = "%s--%s" % (unit_key, seq_key)
                self.event_list[new_seq_key] = []
                prob_vector = []
                data_vector = self.forward_prob_data[unit_key][seq_key]
                for i in range(len(data_vector)):
                    prob_vector.append(data_vector[str(i)])

                self.forward_obj[new_seq_key] = prob_vector
        # set the reverse
        if self.reverse_prob_data:
            for unit_key in self.reverse_prob_data:
                for seq_key in self.reverse_prob_data[unit_key]:
                    prob_vector = []
                    new_seq_key = "%s--%s" % (unit_key, seq_key)
                    data_vector = self.reverse_prob_data[unit_key][seq_key]
                    for i in range(
                            len(data_vector)-1, -1, -1):
                        prob_vector.append(data_vector[str(i)])
                    # ignore the first prob value
                    self.reverse_obj[new_seq_key] = prob_vector
            assert set(self.forward_obj.keys()) == set(
                self.reverse_obj.keys()), "Incompatible datasets"


class ProcessStateData(ProcessData):
    """  Process Data using our notation """

    def __init__(self, forward_prob_file, reverse_prob_file=None):
        """
         :param forward_prob_file: file with forward probability
         :param reverse_prob_file: file with reverse probability
         """
        ProcessData.__init__(self, forward_prob_file, reverse_prob_file)

    def data_parser(self):
        """
        Convert the state probabilities into vector for aggregation
        the reverse converts the index to reverse direction
        ex,
        forward ["0--a--0" : 1, "1--b--0" : 2]
        reverse will be [ "0--b--0" : 2, "1--a--0" : 1]
        The code endures that reverse is computed.
        """
        for unit_key in self.forward_prob_data:
            for seq_key in self.forward_prob_data[unit_key]:
                seq_data = self.forward_prob_data[unit_key][seq_key]
                for i in range(len(seq_data)):
                    new_seq_key = "%s--%s--%s" % (unit_key, seq_key, i)
                    state_data = self.forward_prob_data[unit_key][seq_key][str(i)]
                    self.forward_obj[new_seq_key] = [0] * len(state_data)
                    self.event_list[new_seq_key] = [0] * len(state_data)
                    for key, value in state_data.items():
                        prob_val = value["prob"]
                        max_val =  value["max_value"]
                        norm_val =  float(prob_val)/ float(max_val)
                        self.forward_obj[new_seq_key][int(key[0])] = norm_val
                        self.event_list[new_seq_key][int(key[0])] = key

        # set the reverse
        if self.reverse_prob_data:
            for unit_key in self.reverse_prob_data:
                for seq_key in self.reverse_prob_data[unit_key]:
                    seq_data = self.reverse_prob_data[unit_key][seq_key]
                    seq_len = len(seq_data)
                    for i in range(seq_len-1, -1, -1):
                        new_seq_key = "%s--%s--%s" % (unit_key, seq_key, seq_len-1-i)
                        state_data = seq_data[str(i)]
                        state_len = len(state_data)
                        self.reverse_obj[new_seq_key] = [0] * state_len
                        for key, value in state_data.items():
                            prob_val = value["prob"]
                            max_val =  value["max_value"]
                            norm_val =  float(prob_val)/ float(max_val)
                            self.reverse_obj[new_seq_key][int(key[0])] = norm_val
            # reverse the states vector
            for key in self.reverse_obj:
                self.reverse_obj[key].reverse()
            # check if the keys match
            assert set(self.forward_obj.keys()) == set(
                self.reverse_obj.keys()), "Incompatible datasets" + str(set(self.forward_obj.keys()) - set(
                self.reverse_obj.keys())) + str(set(self.reverse_obj.keys()) - set(
                self.forward_obj.keys()))


def create_location_list(test_file, state=False, key_list=None):
    """
    create a mapping for the location
    :param state: set true if the data has state information
    :param test_file: salento acceptable json file
    :param key_list : create a dictionary put of filtered traces only
    :return: dict with location information
    """
    location_dict = {}
    with open(test_file, 'r') as fread:
        salento_data = json.load(fread)

    for k, proc in enumerate(salento_data["packages"]):
        for j, sequence in enumerate(proc["data"]):
            if state:
                for i, event in enumerate(sequence["sequence"]):
                    new_seq_key = "%s--%s--%s" % (str(k), str(j), str(i))
                    if key_list and new_seq_key not in key_list:
                        continue
                    location_list = [
                        event["location"] for event in sequence["sequence"]
                    ]
                    call_list = [
                        event["call"] for event in sequence["sequence"]
                    ]
                    call = call_list[i]
                    location = location_list[i]
                    # state vector with end marker
                    state_vector = event['states'] + [END_MARKER]
                    for l, st in enumerate(state_vector):
                        if l == len(state_vector) - 1:
                            state_id = "End Marker %s" % st
                        else:
                            state_id = "%s with State index %d with value %d" % (
                                call, l, st)
                        location_list.insert(i + l + 1, location)
                        call_list.insert(i + l + 1, state_id)

                    location_dict[new_seq_key] = {
                        "Location": location_list,
                        "Calls": call_list
                    }
            else:
                key = str(k) + "--" + str(j)
                if key_list and key not in key_list:
                    continue
                location_list = [
                    event["location"] for event in sequence["sequence"]
                ]
                call_list = [event["call"] for event in sequence["sequence"]]
                # add end marker
                call_list.append(END_MARKER)
                # add last location
                location_list.append(location_list[-1])

                location_dict[key] = {
                    "Location": location_list,
                    "Calls": call_list
                }
    return location_dict
