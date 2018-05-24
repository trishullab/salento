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
    """

    def __init__(
            self,
            data_file,
            model_dir,
            call_file=None,
            state_file=None,
            normalize=False
    ):
        """

        :param data_file: file with test data
        :param model_dir: directory where model is saved
        :param call_file: files to store call probabilities
        :param state_file: file to store state probabilities
        :param normalize: Normalize the probability
        """
        Aggregator.__init__(self, data_file, model_dir)
        self.call_probs = {}
        self.state_probs = {}
        self.call_file = call_file
        self.state_file = state_file
        self.cache = {}
        self.normalize = normalize
        self.state_chars = set()
        # set up the valid state chars
        if normalize:
            config_file = os.path.join(model_dir, 'config.json')
            with open(config_file, 'r') as fread:
                config = json.load(fread)
                for chars in config["decoder"]["chars"]:
                    # XXX assumption that state vocab will have #
                    if '#' in chars:
                        self.state_chars.add(chars)

    def get_seq_call_prob(self, spec, sequence):
        """
        Compute call probability
        :param spec: latent specification
        :param sequence: a sequences of events
        :return: predicted call probabilities
        """
        event_data = {}
        events_len = len(sequence)

        for (i, row) in enumerate(
                self.distribution_call_iter(spec, sequence, cache=self.cache)):
            if i == events_len:
                next_call = self.END_MARKER
            else:
                next_call = sequence[i]['call']
            prob = float(row.distribution.get(next_call, 0.0))
            if self.normalize:
                max_value, max_token = max(zip(row.distribution.data, row.distribution.id_to_term), key=lambda x: x[0])
                event_data[i] = {
                    "prob": prob,
                    "max_value": float(max_value),
                    "max_token": str(max_token),
                }
            else:
                event_data[i] = prob
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
            event_data[i] = {}
            last_call_state = copy.deepcopy(event['states'])
            # add the end marker
            last_call_state.append(self.END_MARKER)
            sequence[i]["states"] = []

            for state_index, state_value in enumerate(last_call_state):
                # cvt to str
                state_index = str(state_index)
                state_value_str = str(state_value)
                expected_probability = self.distribution_next_state(spec, sequence[:i + 1], state_value,
                                                   self.cache)
                st_key = state_index + "#" + state_value_str
                if self.normalize:
                    # all the possible probs to get the max value
                    # step 1 : add the current state prob
                    valid_probs = [expected_probability]
                    valid_state = [st_key]
                    # Step 2 : get the end marker prob if current state is end marker then skip
                    if state_value != self.END_MARKER:
                        valid_probs.append(self.distribution_next_state(
                            spec, sequence[:i + 1], self.END_MARKER, self.cache))
                        valid_state.append(self.END_MARKER)
                    # Step 3 : Get probability for all other possible state values at this index
                    for x in self.state_chars:
                        x_state, x_value = x.split('#')
                        # if the state is same and value is different
                        if x != st_key and x_state == state_index:
                            valid_probs.append(self.distribution_next_state(
                                spec, sequence[:i + 1], x_value, self.cache))
                            valid_state.append(x)
                    # max value
                    max_value, max_token = max(zip(valid_probs, valid_state),
                                               key=lambda x: x[0])
                    event_data[i][st_key] =  {
                        "prob": float(expected_probability),
                        "max_value": float(max_value),
                        "max_token": str(max_token)
                    }
                else:
                    event_data[i][st_key] = float(expected_probability)
                # add the last state value
                sequence[i]["states"].append(state_value)

        return event_data

    def write_results(self):
        """
        Write the results to files passed
        """
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

            self.call_probs[k] = {}
            self.state_probs[k] = {}
            spec = self.get_latent_specification(proc)

            for j, sequence in enumerate(self.sequences(proc)):
                if self.call_file:
                    self.call_probs[k][j] = self.get_seq_call_prob(
                        spec, self.events(sequence))

                if self.state_file:
                    self.state_probs[k][j] = self.get_state_prob(
                        spec, self.events(sequence))


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
        '--normalize',
        type=bool,
        default=False,
        help="Normalize the probability (using max of dist?)")
    clargs = parser.parse_args()

    if clargs.call_prob_file is None and clargs.state_prob_file is None:
        raise AssertionError("Must get call or state probability")

    with RawProbAggregator(clargs.data_file, clargs.model_dir,
                           clargs.call_prob_file,
                           clargs.state_prob_file,
                           clargs.normalize) as aggregator:
        aggregator.run()
        aggregator.write_results()
