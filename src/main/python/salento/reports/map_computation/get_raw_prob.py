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

from __future__ import print_function
import argparse
import json
import copy
import os
from salento.aggregators.base import Aggregator


class RawProbAggregator(Aggregator):
    """
    This is based on the simple sequence aggregator, here for each call
    the probability is retrieved. The schema of the output is below
    {
        "title" : "Schema File for representation of the probability values",
        "type" : "object",
        "properties" : {
            "type" : "object",
            "description" : "Each unit",
            "properties" : {
                "type" : "object",
                "description" : "Each Sequence",
                "properties" : {
                    "type" : "object",
                    "description" : "Each Call",
                    "properties" : {
                        "type" : "number",
                        "description" : "raw probability values"
                    }
                }
            }
        }
    }
    """

    def __init__(self,
                 data_file,
                 model_dir,
                 call_file=None,
                 state_file=None,
                 chunk=False):
        """

        :param data_file: file with test data
        :param model_dir: directory where model is saved
        :param call_file: files to store call probabilities
        :param state_file: file to store state probabilities
        :param chunk: chunk files on procedure count
        """
        Aggregator.__init__(self, data_file, model_dir)
        self.call_probs = {}
        self.state_probs = {}
        self.call_file = call_file
        self.state_file = state_file
        self.chunk = chunk

    def get_seq_call_prob(self, spec, sequence):
        """
        Compute call probability
        :param spec: latent specification
        :param sequence: a sequences of events
        :return: predicted call probabilities
        """
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            prob_value = float(
                self.distribution_next_call(
                    spec, sequence[:i+1], call=self.call(event)))
            event_data[call_key] = prob_value
        return event_data

    def get_state_prob(self, spec, sequence):
        """
        Compute state probability
        :param spec: latent specification
        :param sequence: a sequences of events
        :return: predicted states probabilities
        """
        event_data = {}
        for i, event in enumerate(sequence):
            call_key = (str(i) + '--' + event['call'])
            last_call_state = copy.deepcopy(event['states'])
            sequence[i]["states"] = []
            for s_i, st in enumerate(last_call_state):
                val = self.distribution_next_state(spec, sequence[:i + 1], st)
                st_key = call_key + '--' + str(s_i) + "#" + str(st)
                sequence[i]["states"].append(st)
                event_data[st_key] = float(val)
        return event_data

    def write_chunks(self, filename, package_number, data):
        """
        write out probabilities in chunks
        :param filename: state/call filename
        :param package_number: package number to be prepended to the file
        :param data: probabilities for every event in the package
        """
        chunk_file = os.path.join(
            os.path.dirname(filename),
            str(package_number) + '_' + os.path.basename(filename))
        with open(chunk_file, 'w') as fwrite:
            json.dump(data, fwrite)

    def write_results(self):
        """
        Write the results to files passed, if chunks then combine the chunks
        """
        if self.chunk:
            for k in range(len(self.packages())):
                # update call probs
                if self.call_file:
                    chunk_file = os.path.join(
                        os.path.dirname(self.call_file),
                        str(k) + '_' + os.path.basename(self.call_file))
                    self.call_probs[str(k)] = {}
                    with open(chunk_file, 'r') as fread:
                        self.call_probs[str(k)].update(json.load(fread))
                # update state probs
                if self.state_file:
                    chunk_file = os.path.join(
                        os.path.dirname(self.state_file),
                        str(k) + '_' + os.path.basename(self.state_file))
                    self.state_probs[str(k)] = {}
                    with open(chunk_file, 'r') as fread:
                        self.state_probs[str(k)].update(json.load(fread))
        # Write out the files
        if self.call_file:
            with open(self.call_file, 'w') as fwrite:
                json.dump(self.call_probs, fwrite)
        if self.state_file:
            with open(self.state_file, 'w') as fwrite:
                json.dump(self.state_probs, fwrite)

    def run(self):
        """
            invoke the RNN to get the probability
        """
        # iterate over units
        print("Total packages {}".format(len(self.packages())))
        for k, proc in enumerate(self.packages()):
            if 'apicalls' not in proc:
                raise AssertionError("Not a valid Evidence file")
            print(
                'Query Probability For Package Number {} '.format(k), end='\r')
            call_seq_prob = {}
            state_seq_prob = {}
            spec = self.get_latent_specification(proc)
            # iterate over sequence
            for j, sequence in enumerate(self.sequences(proc)):
                events = self.events(sequence)

                if self.call_file:
                    call_seq_prob[str(j)] = self.get_seq_call_prob(spec, events)
                if self.state_file:
                    state_seq_prob[str(j)] = self.get_state_prob(spec, events)
            # write chunks
            if self.chunk:
                if self.call_file:
                    self.write_chunks(self.call_file, k, call_seq_prob)
                if self.state_file:
                    self.write_chunks(self.state_file, k, state_seq_prob)
            else:
                if self.call_file:
                    self.call_probs[str(k)] = {}
                    self.call_probs[str(k)].update(call_seq_prob)
                if self.state_file:
                    self.state_probs[str(k)] = {}
                    self.state_probs[str(k)].update(state_seq_prob)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--data_file',
        type=str,
        required=True,
        help='input test data file with evidences')
    parser.add_argument(
        '--model_dir',
        type=str,
        required=True,
        help='directory to load the model from')
    parser.add_argument(
        '--call_prob_file',
        type=str,
        default=None,
        help='Write out the call probability in json file')
    parser.add_argument(
        '--state_prob_file',
        type=str,
        default=None,
        help='write out the state probability in json file')
    parser.add_argument(
        '--chunks',
        type=bool,
        default=False,
        help='write out results per package')
    clargs = parser.parse_args()

    if clargs.call_prob_file is None and clargs.state_prob_file is None:
        raise AssertionError("Must get call or state probability")

    with RawProbAggregator(clargs.data_file, clargs.model_dir,
                           clargs.call_prob_file, clargs.state_prob_file,
                           clargs.chunks) as aggregator:
        aggregator.run()
        aggregator.write_results()
