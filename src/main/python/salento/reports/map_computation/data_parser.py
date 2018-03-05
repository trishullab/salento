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
import sys
# substitute inf with low value
LOW_PROB = 10e-50

class ProcessData(object):
    """ Takes in detailed probability call computes the metrics """
    def __init__(self, data_file):
        """ read the data file """
        with open(data_file, 'r') as fread:
            self.prob_data = json.load(fread)

    def data_parser(self):
        """ implement custom data parser that returns
        a unique sequence key and prob vector associated with it"""
        raise NotImplementedError("Override it!")

    def apply_aggregation(self, operator_type):
        """
            reads the sequence and applies the aggregation function
            store the result in the self.aggregated_data
            @operator_type : one of the operators from Metric Option
            side effect : it creates unique key for each sequence
        """
        raise NotImplementedError("Override it!")

class ProcessDataImpl(ProcessData):
    """  Process Data using our notation """
    def __init__(self, data_file):
        """ read the data file """
        ProcessData.__init__(self, data_file)
        self.forward_obj = {}
        self.aggregated_data = {}

    def data_parser(self):
        """
            custom data parser, returns
            a. unique seq_key
            b. seq_prob
        """
        for unit_key in self.prob_data:
            for seq_key in self.prob_data[unit_key]:
                prob_vector = self.prob_data[unit_key][seq_key].values()
                new_seq_key = "%s--%s" % (str(unit_key), seq_key)
                self.forward_obj[new_seq_key] = prob_vector

    def apply_aggregation(self, operator_type):
        """
            reads the sequence and applies the aggregation function
            it then store the result in the self.aggregated_data
            @operator_type : one of the operators from Metric Option
            side effect : it creates unique key for each sequence
        """
        for seq_key in self.forward_obj:
            self.aggregated_data[seq_key] = operator_type(self.forward_obj[seq_key])

class ProcessStates(ProcessData):
    """  Process Data using our notation """
    def __init__(self, data_file):
        """ read the data file """
        ProcessData.__init__(self, data_file)
        self.forward_obj = {}
        self.aggregated_data = {}

    def data_parser(self):
        """
        Parse the probability data using data parser
        it update the forward object dictionary with
        unique seq_key and probability vector associated with sequences
        """
        for unit_key in self.prob_data:
            for seq_key in self.prob_data[unit_key]:
                prob_vector = []
                for call_key in self.prob_data[unit_key][seq_key]:
                    prob_value = min(item.values()[0] for item in \
                        self.prob_data[unit_key][seq_key][call_key])
                    if prob_value == float('-inf'):
                        print('Infinite : %s--%s' % (seq_key, call_key), file=sys.stderr)
                        # set a low value
                        prob_value = LOW_PROB
                    prob_vector.append(prob_value)
                new_seq_key = "%s_%s" % (str(unit_key), seq_key)
                self.forward_obj[new_seq_key] = prob_vector

    def apply_aggregation(self, operator_type):
        """
            reads the sequence and applies the aggregation function
            store the result in the self.aggregated_data
            @operator_type : one of the operators from Metric Option
            side effect : it creates unique key for each sequence
        """
        for seq_key in self.forward_obj:
            self.aggregated_data[seq_key] = operator_type(self.forward_obj[seq_key])

class ProcessBiDataImpl(object):
    def __init__(self, data_file_forward, data_file_backward):
        """
        read the data file
        @data_file_forward : file name string for forward probability
        @data_file_backward : file name string for reverse probability
        """
        with open(data_file_forward, 'r') as fread_forward:
            self.prob_data_forward = json.load(fread_forward)
        with open(data_file_backward, 'r') as fread_backward:
            self.prob_data_backward = json.load(fread_backward)
        self.aggregated_data = {}

    def data_parser(self):
        """
        Parse the probability data using data parser
        it update the forward and backward object dictionary with
        unique seq_key and probability vector associated with sequences
        It also ensures the key mapping is correct for the reverse sequence
        """
        forward_obj = {}
        backward_obj = {}

        for unit_key in self.prob_data_forward:
            for seq_key in self.prob_data_forward[unit_key]:
                prob_vector = self.prob_data_forward[unit_key][seq_key].values()
                new_seq_key = "%s--%s" % (str(unit_key), seq_key)
                forward_obj[new_seq_key] = prob_vector


        for unit_key in self.prob_data_backward:
            for seq_key in self.prob_data_backward[unit_key]:
                prob_vector = list(self.prob_data_backward[unit_key][seq_key].values())
                (seq_num, seq_string) = seq_key.split("--", 1)
                # s[::-1] reverses s
                rev_seq = "--".join(list(reversed(seq_string.split("--"))))
                new_seq_key = "%s--%s--%s" % (str(unit_key), seq_num, rev_seq)
                backward_obj[new_seq_key] = prob_vector[::-1]
        assert len(set(forward_obj.keys()) & set(backward_obj.keys())) == \
                 len(forward_obj), "Incompatible datasets"

        return (forward_obj, backward_obj)

    def apply_aggregation(self, operator_type):
        """
            reads the sequence and applies the aggregation function
            store the result in the self.aggregated_data
            @operator_type : one of the operators from Metric Option
            side effect : it creates unique key for each sequence
        """
        (forward_obj, backward_obj) = self.data_parser()

        for k, forward_probs in forward_obj.iteritems():
            backward_probs = backward_obj[k]
            assert len(forward_probs) == len(backward_probs)
            # multiple reverse and forward
            combined_probability_vector = map(
                lambda t: min(t[0], t[1]), zip(forward_probs, backward_probs))
            self.aggregated_data[k] = operator_type(
                combined_probability_vector)

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

