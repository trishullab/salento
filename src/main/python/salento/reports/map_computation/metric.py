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

# Purpose :   This scripts produces the different anomaly metrics

import math
import operator

class Metric(object):
    """
        given a sequence it computes a score,
        currently the seq is a list of scores
    """
    def  __init__(self):
        """ unimplemented """
        raise AssertionError("Static class should not be instantiated")

    @staticmethod
    def sum_raw(seq):
        """ compute sum """
        return None, sum(seq)

    @staticmethod
    def min_raw(seq):
        """ use min value """
        min_value = min(seq)
        min_index = [i for i, value in enumerate(seq) if value == min_value]
        return min_index, min_value

    @staticmethod
    def sum_llh(seq):
        """ use sum of the llh aggregation """
        return  None, - sum([math.log(x) for x in seq])

    @staticmethod
    def min_llh(seq):
        """ use min of the llh aggregation """
        log_val = [math.log(x) for x in seq]
        min_value = min(log_val)
        min_index = [i for i, value in enumerate(log_val) if value == min_value]
        return min_index, -min_value

METRICOPTION = {
    "sum_raw": Metric.sum_raw,
    "min_raw": Metric.min_raw,
    "sum_llh": Metric.sum_llh,
    "min_llh": Metric.min_llh}

def compute_map(data, anomalous_keys):
    """
        This function computes the map score for test data
        @data : test_Data with seq keys and anomaly scores
        @anomalous_keys : a list of the ground truth with anomalous seq key
        Assumption : Every anomalous keys is present in the data
        return map_score
    """
    # sort the data
    sorted_data = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
    # set the indices
    """
    @indices: a list of ranks of correctly retrieved items
    note that the ranks are 0-based (i.e, best rank = 0)
    """
    indices = []
    for i, keys in enumerate(sorted_data):
        if keys[0] in anomalous_keys:
            indices.append(i)
    collected_precision = []
    for i, val in enumerate(indices):
        collected_precision.append((i+1)/float(val + 1))
    map_score = sum(collected_precision)/(len(collected_precision))
    return map_score
