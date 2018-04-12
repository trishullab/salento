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

# Script Purpose : Driver code to anomaly score from a test data

from __future__ import print_function
import argparse
import subprocess
# project imports
import anomaly_score
import get_raw_prob
import metric
import reverse_sequence


def main():
    """
    main driver code to do get anomaly scores
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_file', type=str, help='input test file')
    parser.add_argument(
        '--model_forward', type=str, help='directory to load the model from')
    parser.add_argument(
        '--model_reverse', type=str, help='directory to load the model from')
    parser.add_argument(
        '--call',
        type=bool,
        help="Set True to compute anomaly score using call probability")
    parser.add_argument(
        '--state',
        type=bool,
        help="Set True to compute anomaly score using states probability")
    parser.add_argument(
        '--metric_choice',
        required=True,
        type=str,
        choices=metric.METRICOPTION.keys(),
        help="Choose the metric to be applied")
    parser.add_argument(
        '--result_file', type=str, help="File to write the anomaly score")
    parser.add_argument(
        '--path_to_evidence_extractor',
        type=str,
        required=True,
        help="Point to the path to evidence extractor")

    args = parser.parse_args()
    # check the arguments and set the necessary ones

    # set defaults
    call_prob_forward_file = None
    call_prob_reverse_file = None
    state_prob_forward_file = None
    state_prob_reverse_file = None
    prob_file_reverse = None

    forward_evidence_file = "/tmp/forward_data_file.json"
    reverse_evidence_file = "/tmp/reverse_data_file.json"
    prob_file_forward = "/tmp/prob_file_forward.json"
    if args.model_reverse:
        prob_file_reverse = "/tmp/prob_file_reverse.json"
    if args.call:
        call_prob_forward_file = prob_file_forward
        call_prob_reverse_file = prob_file_reverse
    if args.state:
        state_prob_forward_file = prob_file_forward
        state_prob_reverse_file = prob_file_reverse

    # create evidence files
    cmd = [
        "python3", args.path_to_evidence_extractor, args.test_file,
        forward_evidence_file
    ]
    subprocess.check_call(cmd)

    # generate reverse evidence file
    if args.model_reverse:

        # create reverse files
        reverse_test_file = "/tmp/reverse_test_file.json"
        reverse_sequence.reverse_seq(args.test_file, reverse_test_file)
        cmd = [
            "python3", args.path_to_evidence_extractor, reverse_test_file,
            reverse_evidence_file
        ]
        subprocess.check_call(cmd)

    # get the forward probability
    if args.model_forward:
        with get_raw_prob.RawProbAggregator(
                forward_evidence_file, args.model_forward,
                call_prob_forward_file, state_prob_forward_file) as aggregator:
            aggregator.run()
            aggregator.write_results()
    if args.model_reverse:
        with get_raw_prob.RawProbAggregator(
                reverse_evidence_file, args.model_reverse,
                call_prob_reverse_file, state_prob_reverse_file) as aggregator:
            aggregator.run()
            aggregator.write_results()
    # compute the anomaly score
    anomaly_score.write_anomaly_score(args.metric_choice,
                                      prob_file_forward,
                                      prob_file_reverse,
                                      args.call,
                                      args.state,
                                      args.test_file,
                                      args.result_file)


if __name__ == '__main__':
    main()
