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
import time
# project imports
import anomaly_score
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--test_file',
        required=True,
        type=str,
        help='input test file')
    parser.add_argument(
        '--model_forward',
        required=True,
        type=str,
        help='directory to load the model from')
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
        default='min_llh',
        type=str,
        choices=metric.METRICOPTION.keys(),
        help="Choose the metric to be applied")
    parser.add_argument(
        '--result_file', type=str, help="File to write the anomaly score")
    parser.add_argument(
        '--normalize',
        type=bool,
        default=False,
        help="Normalize the probability (using max of dist?)")

    args = parser.parse_args()
    # check the arguments and set the necessary ones
    if not args.call and not args.state:
        raise AssertionError("Either call or state should be set!")

    if args.call and args.state:
        raise AssertionError("You can only set call or state both not both")
    # set logger
    logger = logging.getLogger("Anomaly Score Logs")
    logger.setLevel(logging.INFO)
    time_str = time.strftime("%Y%m%d-%H%M%S")
    log_file = time_str + "_anomaly_score.log"
    fh = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # set defaults
    forward_evidence_file = "/tmp/forward_data_file.json"
    reverse_evidence_file = "/tmp/reverse_data_file.json"
    prob_file_forward = "/tmp/prob_file_forward.json"
    prob_file_reverse = None
    reverse_test_file = None

    # create evidence files
    evidence_extractor_py = os.path.join(
        os.path.dirname(__file__),
        "../../../scripts/evidence_extractor.py"
    )
    cmd = [
        "python3", evidence_extractor_py, args.test_file,
        forward_evidence_file
    ]
    logger.info("Extract Evidences Forward File")
    run_cmd(cmd, log_file)

    # get the forward probability
    get_raw_prob_py = os.path.join(
        os.path.dirname(__file__), 'get_raw_prob.py')
    if args.model_forward:
        cmd = [
            "python3", get_raw_prob_py, '--data_file', forward_evidence_file,
            '--model_dir', args.model_forward,
            '--normalize', args.normalize
        ]
        if args.call:
            cmd += ['--call_prob_file', prob_file_forward]
        elif args.state:
            cmd += ['--state_prob_file', prob_file_forward]

        logger.info("Extract Forward Probabilities")
        run_cmd(cmd, log_file)
    # get reverse probability
    if args.model_reverse:
        logger.info("Reverse The File")
        # create reverse files
        reverse_test_file = "/tmp/reverse_test_file.json"
        reverse_sequence.reverse_seq(args.test_file, reverse_test_file)
        # generate reverse evidence file
        cmd = [
            "python3", evidence_extractor_py, reverse_test_file,
            reverse_evidence_file
        ]
        logger.info("Extract Reverse Evidences")
        run_cmd(cmd, log_file)
        prob_file_reverse = "/tmp/prob_file_reverse.json"
        cmd = [
            "python3", get_raw_prob_py, '--data_file', reverse_evidence_file,
            '--model_dir', args.model_reverse,
            '--normalize', args.normalize
        ]
        if args.call:
            cmd += ['--call_prob_file', prob_file_reverse]
        elif args.state:
            cmd += ['--state_prob_file', prob_file_reverse]
        logger.info("Extract Reverse Probabilities")
        run_cmd(cmd, log_file)
    # compute the anomaly score
    logger.info("Write out the anomaly Output")
    sarif_client = anomaly_score.SarifFileGenerator(
        args.metric_choice,
        prob_file_forward,
        prob_file_reverse,
        args.call,
        args.state,
        args.test_file)
    sarif_client.write_anomaly_score(args.result_file)

    # clean up the tmp files
    os.remove(forward_evidence_file)
    os.remove(reverse_evidence_file)
    os.remove(prob_file_forward)
    if args.model_reverse:
        os.remove(prob_file_reverse)
        os.remove(reverse_test_file)


if __name__ == '__main__':
    main()
