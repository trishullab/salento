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
import os
import logging
import json
# project imports
import anomaly_score
import get_raw_prob
import metric
import reverse_sequence


def run_cmd(cmd, log_file):
    """
        GOAL : capture the output
        :param cmd : command list
        :log_file : log file to append
    """
    with open(log_file, 'a') as fwrite:
        fwrite.write(json.dumps(cmd) + "\n")
        subprocess.check_call(cmd, stdout=fwrite, stderr=fwrite)


def main():
    """
    main driver code to do get anomaly scores
    :return:
    """
    logger = logging.getLogger("Anomaly Score Logs")
    logger.setLevel(logging.INFO)
    log_file = os.path.join("anomaly_score.log")
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

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
    forward_evidence_file = "/tmp/forward_data_file.json"
    reverse_evidence_file = "/tmp/reverse_data_file.json"
    prob_file_forward = "/tmp/prob_file_forward.json"
    prob_file_reverse = None
    # create evidence files

    cmd = [
        "python3", args.path_to_evidence_extractor, args.test_file,
        forward_evidence_file
    ]
    logger.info("Extract Evidences Forward File")
    run_cmd(cmd, log_file)

    # generate reverse evidence file
    if args.model_reverse:
        logger.info("Reverse The File")
        # create reverse files
        reverse_test_file = "/tmp/reverse_test_file.json"
        reverse_sequence.reverse_seq(args.test_file, reverse_test_file)
        cmd = [
            "python3", args.path_to_evidence_extractor, reverse_test_file,
            reverse_evidence_file
        ]
        logger.info("Extract Reverse Evidences")
        run_cmd(cmd, log_file)

    # get the forward probability
    get_raw_prob_py = os.path.join(
        os.path.dirname(__file__), 'get_raw_prob.py')
    if args.model_forward:
        cmd = [
            "python3", get_raw_prob_py, '--data_file', forward_evidence_file,
            '--model_dir', args.model_forward
        ]
        if args.call:
            cmd += ['--call_prob_file', prob_file_forward]
        elif args.state:
            cmd += ['--state_prob_file', prob_file_forward]
        logger.info("Extract Forward Probabilities")
        run_cmd(cmd, log_file)

    if args.model_reverse:
        prob_file_reverse = "/tmp/prob_file_reverse.json"
        cmd = [
            "python3", get_raw_prob_py, '--data_file', reverse_evidence_file,
            '--model_dir', args.model_reverse
        ]
        if args.call:
            cmd += ['--call_prob_file', prob_file_reverse]
        elif args.state:
            cmd += ['--state_prob_file', prob_file_reverse]
        logger.info("Extract Reverse Probabilities")
        run_cmd(cmd, log_file)
    # compute the anomaly score
    logger.info("Write out the anomaly Output")
    anomaly_score.write_anomaly_score(args.metric_choice,
                                      prob_file_forward,
                                      prob_file_reverse,
                                      args.call,
                                      args.state,
                                      args.test_file,
                                      args.result_file)


if __name__ == '__main__':
    main()
