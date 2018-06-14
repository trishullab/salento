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

# Script process the pattern and gets the difference between the good and bad pattern anomaly

import json
import os
import subprocess

from salento.reports.map_computation import data_parser, metric


class PatternLoss(object):
    """
    class to compute external loss
    """

    def __init__(self, model_dir, good_pattern_file, bad_pattern_file):
        """

        :param model_dir:  model directory to pick last epoch model
        :param good_pattern_file:
        :param bad_pattern_file:
        """
        self.model_dir = model_dir

        self.good_pattern_evidence_file = '/tmp/good_evidence.json'
        self.bad_pattern_evidence_file = '/tmp/bad_evidence.json'
        self.call = False
        self.state = False

        self.extract_evidence(good_pattern_file,
                              self.good_pattern_evidence_file)
        self.extract_evidence(bad_pattern_file,
                              self.bad_pattern_evidence_file)

    def extract_evidence(self, pattern_file, evidence_file):
        """

        :param pattern_file: pattern file
        :param evidence_file: the extracted evidence file
        :return:
        """

        with open(pattern_file, 'r') as fread:
            data = json.load(fread)


        # cvt to evidence file
        evidence_extractor_py = os.path.join(
            os.path.dirname(__file__),
            "../../../scripts/evidence_extractor.py")
        cmd = ["python3", evidence_extractor_py, pattern_file, evidence_file]
        subprocess.check_call(cmd)

    def get_anomaly_score(self, evidence_file):
        """
            file to compute an anomaly vector
            :param evidence_file: good or bad trace pattern evidence file
            :return: list of anomaly scores for the pattern file
        """
        get_raw_prob_py = os.path.join(
            os.path.dirname(__file__), '..', 'map_computation',
            'get_raw_prob.py')
        # get probability
        prob_file = '/tmp/prob_file.json'
        cmd = [
            'python3', get_raw_prob_py, '--data_file', evidence_file,
            '--model_dir', self.model_dir, '--normalize', 'True'
        ]
        if self.call:
            cmd.append('--call_prob_file')
            cmd.append(prob_file)
        if self.state:
            cmd.append('--state_prob_file')
            cmd.append(prob_file)

        subprocess.check_call(cmd)
        # apply metric
        if self.call:
            parser = data_parser.ProcessCallData(prob_file, None)
        if self.state:
            parser = data_parser.ProcessStateData(prob_file, None)
        parser.data_parser()
        parser.apply_aggregation(metric.Metric.min_llh)
        # compute anomaly
        anomaly = [
            parser.aggregated_data[key]["Anomaly Score"]
            for key in parser.aggregated_data
        ]
        return anomaly

    def loss_func(self):
        """
        External loss function
        :return: loss
        """
        # get the anomaly scores
        good_anomaly = self.get_anomaly_score(self.good_pattern_evidence_file)
        bad_anomaly = self.get_anomaly_score(self.bad_pattern_evidence_file)

        try :
            loss = 1 - sum([abs(x - y) for x in bad_anomaly for y in good_anomaly]) / (
                len(bad_anomaly) * len(good_anomaly))
        except ZeroDivisionError:
            loss = float('inf')

        return loss
