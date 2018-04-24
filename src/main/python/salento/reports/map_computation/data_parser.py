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
            index_list, score = operator_type(combined_probability_vector)
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

    def data_parser(self):
        """
            custom data parser, returns
            a. unique seq_key
            b. seq_prob
        """
        for unit_key in self.forward_prob_data:
            for seq_key in self.forward_prob_data[unit_key]:
                prob_vector = self.forward_prob_data[unit_key][
                    seq_key].values()
                event_vector = self.forward_prob_data[unit_key][seq_key].keys()
                new_seq_key = "%s--%s" % (str(unit_key), seq_key)
                self.forward_obj[new_seq_key] = prob_vector
                self.event_list[new_seq_key] = sorted(
                    event_vector, key=lambda x: int(x.split('--')[0]))
        # set the reverse
        if self.reverse_prob_data:
            for unit_key in self.reverse_prob_data:
                for seq_key in self.reverse_prob_data[unit_key]:
                    # reverse the
                    new_seq_key = "%s--%s" % (str(unit_key), seq_key)
                    prob_vector = reversed(
                        list(self.reverse_prob_data[unit_key][seq_key]
                             .values()))
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
                key_list = self.forward_prob_data[unit_key][seq_key].keys()
                key_list = sorted(
                    key_list,
                    key=lambda x: (int(x.split('--')[0]), x.split('--')[2]))
                for key in key_list:
                    value = self.forward_prob_data[unit_key][seq_key][key]
                    key_split = key.split('--')
                    key_id = key_split[0]

                    new_seq_key = "%s--%s--%s" % (str(unit_key), seq_key,
                                                  key_id)
                    if new_seq_key not in self.forward_obj:
                        self.forward_obj[new_seq_key] = []
                        self.event_list[new_seq_key] = []
                    self.forward_obj[new_seq_key].append(value)
                    self.event_list[new_seq_key].append(key)
        # set the reverse
        if self.reverse_prob_data:
            for unit_key in self.reverse_prob_data:
                for seq_key in self.reverse_prob_data[unit_key]:
                    key_list = sorted(
                        self.reverse_prob_data[unit_key][seq_key].keys(),
                        key=lambda x: (int(x.split('--')[0]), x.split('--')[2])
                    )
                    # get the length sequence
                    total_states = len(
                        set([key.split('--')[0] for key in key_list]))
                    for key in key_list:
                        value = self.reverse_prob_data[unit_key][seq_key][key]
                        key_split = key.split('--')
                        # reverse the key index
                        key_id = total_states - int(key_split[0]) - 1

                        new_seq_key = "%s--%s--%s" % (str(unit_key), seq_key,
                                                      str(key_id))
                        if new_seq_key not in self.reverse_obj:
                            self.reverse_obj[new_seq_key] = []
                        self.reverse_obj[new_seq_key].append(value)
            # reverse the states vector
            for key in self.reverse_obj:
                self.reverse_obj[key].reverse()
            # check if the keys match
            assert set(self.forward_obj.keys()) == set(
                self.reverse_obj.keys()), "Incompatible datasets"


def create_location_list(test_file, state=False):
    """
    create a mapping for the location
    :param state: set true if the data has state information
    :param test_file: salento acceptable json file
    :return: dict with location information
    """
    location_dict = {}
    with open(test_file, 'r') as fread:
        salento_data = json.load(fread)

    for k, proc in enumerate(salento_data["packages"]):
        for j, sequence in enumerate(proc["data"]):
            if state:
                for i, event in enumerate(sequence["sequence"]):
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

                    new_seq_key = "%s--%s--%s" % (str(k), str(j), str(i))

                    location_dict[new_seq_key] = {
                        "Location": location_list,
                        "Calls": call_list
                    }
            else:
                location_list = [
                    event["location"] for event in sequence["sequence"]
                ]
                call_list = [event["call"] for event in sequence["sequence"]]
                # add end marker
                call_list.append(END_MARKER)
                # add last location
                location_list.append(location_list[-1])
                key = str(k) + "--" + str(j)
                location_dict[key] = {
                    "Location": location_list,
                    "Calls": call_list
                }
    return location_dict
