# *************************************************************************************
# *
# * GOVERNMENT PURPOSE RIGHTS
# *
# * Contract Number: FA8750-15-2-0270 (Prime: William Marsh Rice University)
# * Contractor Name: GrammaTech, Inc. (Right Holder - subaward R18683)
# * Contractor Address: 531 Esty Street, Ithaca, NY  14850
# * Expiration Date: 22 September 2023
# *
# * The Government's rights to use, modify, reproduce, release, perform, display, or
# * disclose this software are restricted by DFARS 252.227-7014 --Rights in
# * Noncommercial Computer Software and Noncommercial Computer Software Documentation
# * clause contained in the above identified contract.  No restrictions apply after
# * the expiration date shown above.  Any reproduction of the software or portions
# * thereof marked with this legend must also reproduce the markings and any copyright.
# *
# *************************************************************************************

# *************************************************************************************
# *
# * (c) 2014-2017 GrammaTech, Inc.  All rights reserved.
# *
# *************************************************************************************

# This script contains the mechanism to generate artificial datasets for 
# Salento training and testing

import argparse
import json
import random
import sys

# constants used in the program
class Constants:
    default_location = "a.c:1"
    default_states = [0, 0, 0]
    default_unit_name = "x"
    default_anomalous_unit_name = "anomalous"
    pair_patterns = ["(ab)*", "(ab)*-mixed", "mixed-match"]

# utility methods
class Utils:
    @staticmethod
    def create_call_obj(id, 
                        loc = Constants.default_location, 
                        states = Constants.default_states):
        """
        @id is a string representing a call id
        @loc is a string representing a location of the call
        @states is a list of integers representing the state at the call point

        @return a Salento-JSON call object
        """
        return {
            "call": id,
            "location": loc, 
            "states": states
        }

    @staticmethod
    def create_sequence_obj(lst): 
        """
        @lst is a list of call objects

        @return a Salento-JSON sequence object
        """
        return { "sequence": lst }

    @staticmethod
    def create_unit_obj(data, name = Constants.default_unit_name):
        """
        @data is list of sequence objects
        @name is a string identifying a unit

        @return a Salento-JSON unit object
        """
        return {
            "data": data, 
            "name": name
        }

    @staticmethod
    def create_salento_output(lst):
        """
        @lst is a list of unit objects

        @return a Salento-acceptable JSON object
        """
        return { "packages": lst }

    @staticmethod
    def does_obj_have_id(call_obj, id_list):
        """
        @call_obj is a Salento-JSON call obj
        @id_list is a list of strings

        @return a boolean 
        """
        for id in id_list:
            if call_obj["call"] == id:
                return True
        return False


class PatternGenerator:
    """
    Base class for various data pattern generators
    """
    def __init__(self, 
                 add_noise = False, 
                 noise_alphabets = None, 
                 noise_range = None, 
                 add_anomaly = False, 
                 num_anomalies = None):
        """
        @add_noise is True, then the generator adds noise by injecting
        random elements into the generated sequences
        
        @noise_alphabets is a list of strings, these strings are randomly
        drawn from to inject noise
        
        @add_anomaly is True, the the generator adds anomalies by deviating
        from expected patterns

        @num_anomalies is the number of anomalies we want to inject in
        the generated dataset
        """
        if add_noise:
            assert noise_alphabets is not None
            assert noise_range is not None
            assert noise_range[0] <= noise_range[1]
        if add_anomaly:
            assert num_anomalies is not None
        self.add_noise = add_noise
        self.noise_alphabets = noise_alphabets
        self.noise_range = noise_range
        self.add_anomaly = add_anomaly
        self.num_anomalies = num_anomalies
        # current_anomaly_count keeps track of how many anomalies
        # have been injected until now
        self.current_anomaly_count = 0

    def gen_sequence(self):
        """
        Generate a sequence of call objects, possibly with noise
        """
        seq = self._gen_sequence_primary()
        if self.add_noise:
            seq = self.inject_noise(seq)
        return seq

    def _gen_sequence_primary(self):
        """
        Generate a sequence of call objects, without noise
        """
        raise NotImplementedError("Missing override")

    def gen_unit(self):
        """
        Generate a unit object, potentially add an anomaly
        """
        raise NotImplementedError("Missing override")

    def salento_output(self):
        """
        Generate Salento-acceptable JSON
        """
        raise NotImplementedError("Missing override")

    def gen_anomalous_sequence(self):
        """
        Generate a sequence of call objects, but with an anomaly
        """
        raise NotImplementedError("Missing override")

    def inject_noise(self, seq):
        """
        Inject noise into an existing sequence, and return the updated sequence

        @seq is a sequence of call_objs created using @Utils.create_call_obj

        @return a modified @seq with injected noise
        """
        noise_amt = random.randrange(self.noise_range[0], 
                                     self.noise_range[1]+1)
        for i in xrange(0, noise_amt):
            point_of_insert = random.randrange(0, len(seq))
            element_to_insert = Utils.create_call_obj(
                                    random.choice(self.noise_alphabets))
            seq.insert(point_of_insert, element_to_insert)
        return seq


class ABStar(PatternGenerator):
    """
    Generates patterns of the form:
        ab ab ab ... 
    and
        cd cd cd ...
    Note that within a given sequence, the same pairs are matched
    But different sequences can use different matched pairs
    """
    def __init__(self, 
                 ab_pairs, 
                 num_pairs_range,
                 reps_in_seq_range, 
                 seq_in_unit_range,
                 num_units, 
                 add_noise = False, 
                 noise_alphabets = None, 
                 noise_range = None, 
                 add_anomaly = False, 
                 num_anomalies = None): 
        """
        @ab_pairs is a list of tuple of strings, e.g., [("a", "b"), ("c", "d")]
        these tuples are used in pairs to create the (ab)* pattern
        
        @num_pairs_range is a tuple of ints, representing (min, max) number of 
        pairs to be used within a unit

        @reps_in_seq_range is a tuple of ints, representing (min, max) number
        of repetitions of an "ab" pattern in a sequence
        
        @seq_in_unit_range is a tuple of ints, representing (min, max) number
        of sequences within a unit
        
        @num_unit is an int, representing the number of units to be generated

        @add_noise, @noise_alphabets, @noise_range, @add_anomaly, and 
        @num_anomalies are described in @PatternGenerator
        """
        PatternGenerator.__init__(self, add_noise, noise_alphabets, 
            noise_range, add_anomaly, num_anomalies)
        self.ab_pairs = ab_pairs
        assert num_pairs_range[0] <= num_pairs_range[1]
        assert reps_in_seq_range[0] <= reps_in_seq_range[1]
        assert seq_in_unit_range[0] <= seq_in_unit_range[1]
        self.num_pairs_range = num_pairs_range
        self.reps_in_seq_range = reps_in_seq_range
        self.seq_in_unit_range = seq_in_unit_range
        self.num_units = num_units
        # self.selected_pairs will be added everytime gen_unit() is called

    def _gen_sequence_primary(self):
        seq = []
        reps = random.randrange(self.reps_in_seq_range[0], 
                                self.reps_in_seq_range[1]+1)
        # pick ab ahead of time
        ab_pair = random.choice(self.selected_pairs)
        for i in xrange(0, reps):
            seq.append(Utils.create_call_obj(ab_pair[0]))
            seq.append(Utils.create_call_obj(ab_pair[1]))
        return seq

    def gen_anomalous_sequence(self):
        norm_seq = self.gen_sequence()
        self.current_anomaly_count += 1
        valid_as = map(lambda x: x[0], self.ab_pairs)
        valid_bs = map(lambda x: x[1], self.ab_pairs)
        # inject an anomaly by removing one of the paired b's
        # [TODO]: inject other forms of anomalies like:
        # (a) remove a's
        # (b) shuffle the sequence
        # (c) various anomaly combinations
        removeable_points = []
        for (i, element) in enumerate(norm_seq):
            if Utils.does_obj_have_id(element, valid_bs):
                removeable_points.append(i)
        assert len(removeable_points) > 0
        selected_remove_point = random.choice(removeable_points)
        norm_seq.pop(selected_remove_point)
        return norm_seq

    def gen_unit(self):
        num_seqs = random.randrange(self.seq_in_unit_range[0], 
                                    self.seq_in_unit_range[1]+1)
        num_pairs_to_use = random.randrange(self.num_pairs_range[0], 
                                            self.num_pairs_range[1]+1)
        # chunk up the ab_pairs into multiple buckets of max possible size
        max_chunk_size = self.num_pairs_range[1]
        num_chunks = len(self.ab_pairs) / max_chunk_size
        # select a random chunk, ignore the tail chunk
        which_chunk = random.randrange(0, num_chunks)
        selected_pairs = self.ab_pairs[(which_chunk * max_chunk_size):
            ((which_chunk + 1) * max_chunk_size)]
        assert len(selected_pairs) >= num_pairs_to_use
        self.selected_pairs = random.sample(selected_pairs, num_pairs_to_use)
        # self.selected_pairs will be used for drawing pair patterns
        sequence_data = []
        for i in xrange(0, num_seqs):
            new_seq = Utils.create_sequence_obj(self.gen_sequence())
            sequence_data.append(new_seq)
        # add anomaly if necessary
        if self.add_anomaly and \
                self.current_anomaly_count < self.num_anomalies:
            sequence_data.append(
                Utils.create_sequence_obj(self.gen_anomalous_sequence()))
            return Utils.create_unit_obj(sequence_data, 
                name = Constants.default_anomalous_unit_name)
        else: 
            return Utils.create_unit_obj(sequence_data)

    def salento_output(self):
        units = [] 
        for i in xrange(0, self.num_units):
            units.append(self.gen_unit())
        return Utils.create_salento_output(units)


class ABStarMixed(ABStar):
    """
    Generates patterns of the form:
        ab cd ab ab cd ...
    That is, each sequence can have multiple pairings, like ab and cd.
    But the pairs always appear together.
    """
    def _gen_sequence_primary(self):
        seq = []
        reps = random.randrange(self.reps_in_seq_range[0], 
                                self.reps_in_seq_range[1]+1)
        # pick ab each time in the loop
        for i in xrange(0, reps):
            ab_pair = random.choice(self.selected_pairs)
            seq.append(Utils.create_call_obj(ab_pair[0]))
            seq.append(Utils.create_call_obj(ab_pair[1]))
        return seq


class MixedMatchingPairs(ABStar):
    """
    Generates patterns of the form:
        a c d a b c b d
        |-------|
          |-|
              |-----|
                  |---|
     That is, different ab-pairs are interleaved, but the ab causality
     always holds 
    """
    def _gen_sequence_primary(self):
        reps = random.randrange(self.reps_in_seq_range[0], 
                                self.reps_in_seq_range[1]+1)
        # create an array of size reps*2
        seq = [None] * (reps * 2)
        # generate a random permutation 
        rand_list = range(0, len(seq))
        random.shuffle(rand_list)
        for i in range(0, len(seq), 2):
            (p, q) = (rand_list[i], rand_list[i+1])
            (left, right) = (min(p, q), max(p, q))
            # left and right are two order maintaining random positions
            ab_pair = random.choice(self.selected_pairs)
            seq[left] = Utils.create_call_obj(ab_pair[0])
            seq[right] = Utils.create_call_obj(ab_pair[1])
        # all pairs generated should be in order, but intermingled
        return seq

def main():
    argp = argparse.ArgumentParser(
        description='Generate artificial data for Salento')
    argp.add_argument('--input_file', type=str, required=True,
        help="Input configuration JSON file name")
    argp.add_argument('--output_file', type=str, required=True,
        help="Output file name")
    args = argp.parse_args()

    with open(args.input_file, "r") as f_read:
        config = json.load(f_read)

    try:
        data_generator = None
        if config["pattern"] in Constants.pair_patterns:
            assert "ab_pairs" in config
            assert "num_pairs_range" in config
            assert "reps_in_seq_range" in config
            assert "seq_in_unit_range" in config
            assert "num_units" in config
            assert "add_noise" in config
            assert "add_anomaly" in config
            ab_pairs = config["ab_pairs"]
            for pair in ab_pairs:
                assert len(pair) == 2
            num_pairs_range = config["num_pairs_range"]
            reps_in_seq_range = config["reps_in_seq_range"]
            seq_in_unit_range = config["seq_in_unit_range"]
            num_units = config["num_units"]
            add_noise = config["add_noise"]
            noise_alphabets = None
            noise_range = None
            if add_noise:
                assert "noise_alphabets" in config
                assert "noise_range" in config
                noise_alphabets = config["noise_alphabets"]
                noise_range = config["noise_range"]
            add_anomaly = config["add_anomaly"]
            num_anomalies = None
            if add_anomaly:
                assert "num_anomalies" in config
                num_anomalies = config["num_anomalies"]
            
            selected_class = {
                "(ab)*": ABStar, 
                "(ab)*-mixed": ABStarMixed, 
                "mixed-match": MixedMatchingPairs
            }[config["pattern"]]
            
            data_generator = selected_class(ab_pairs = ab_pairs, 
               num_pairs_range = num_pairs_range,
               reps_in_seq_range = reps_in_seq_range, 
               seq_in_unit_range = seq_in_unit_range, 
               num_units = num_units, 
               add_noise = add_noise, 
               noise_alphabets = noise_alphabets, 
               noise_range = noise_range, 
               add_anomaly = add_anomaly, 
               num_anomalies = num_anomalies)
        if data_generator is not None:
            with open(args.output_file, "w") as f_write:
                print "Generating artificial data and writing to {}".format(
                    args.output_file)
                f_write.write(json.dumps(data_generator.salento_output(), 
                                         indent=2))
    except KeyError as e:
        print "Please check input JSON for correctness: {}".format(e)
        sys.exit(-1)

    
if __name__ == '__main__':
    main()


