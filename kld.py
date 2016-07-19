import argparse
import numpy as np
import random
import os
import logging as log
import time
from six.moves import cPickle
from salento import SalentoJsonParser, type_of, to_model_alphabet, calls_in_sequence
from model import Model

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--save_dir', type=str, default='save',
                       help='directory where model is stored')
    argparser.add_argument('--data_file', type=str, required=True, default=None,
                       help='Salento\'s output file in JSON')
    argparser.add_argument('--plot_dir', type=str, default=None,
                       help='directory to save KLD plots in')
    argparser.add_argument('--debug', action='store_true',
                       help='enable printing debug log to debug.log')
    args = argparser.parse_args()
    if args.debug:
        log.basicConfig(level=log.DEBUG, filename='debug.log', filemode='w', format='%(message)s')
    start = time.time()
    random.seed(start)
    print('Seed: ' + str(start))
    kl = KLD(args)

    with open(args.data_file) as data:
        parser = SalentoJsonParser(data)
    
    for pack in parser.package_names():
        sequences = parser.as_sequences(pack)
        locations = parser.get_call_locations(pack)
        log.debug('### ' + pack)
        kld = kl.compute_kld(locations, sequences)
        print('### ' + pack)
        for location in locations:
            print('  {:35s} : {:.2f}'.format(location, kld[location]))
    print('Time taken: ' + str(int(time.time() - start)) + 's')

class KLD():
    def __init__(self, args):
        self.args = args
        with open(os.path.join(args.save_dir, 'config.pkl'), 'rb') as f:
            saved_args = cPickle.load(f)
        with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'rb') as f:
            self.chars, self.vocab = cPickle.load(f)
        with open(os.path.join(args.save_dir, 'primes.pkl'), 'rb') as f:
            self.primes = cPickle.load(f)
        self.model = Model(saved_args)
        self.model.model.load_weights(os.path.join(args.save_dir, 'weights.h5'))

    def compute_kld(self, locations, sequences):

        # computes the sequences ending at a location
        def sequences_ending_at(location):
            seqs = []
            for sequence in sequences:
                sequence = sequence['sequence']
                for i, event in enumerate(sequence):
                    if type_of(event) == 'call' and event['location'] == location:
                        s = calls_in_sequence(sequence[0: i+1])
                        seqs.append(s)
            return seqs

        kld_l = {}
        for l in locations:
            seqs = sequences_ending_at(l)
            kld_l[l] = self.kld(l, seqs)
        return kld_l

    def kld(self, l, seqs, nsamples=10, niters_convergence=10):

        def sample(s, n=1):
            samples = []
            for i in range(n):
                samples.append(random.choice(s))
            return samples

        def qprob(seq):
            seq = to_model_alphabet(seq, self.vocab) + [self.vocab['END']]
            prime = random.choice(self.primes)
            pr = self.model.probability(prime, seq)
            pr = [p[event] for p, event in zip(pr, seq)]
            return np.prod(pr)

        # bias is half of the negative variance of the estimate. the variance is
        # itself estimated through bootstrap resampling.
        def bias(seq, J_prime):
            values = []
            for i in range(niters_convergence):
                values.append(float(J_prime.count(seq)) / nsamples)
                J_prime = sample(seqs, nsamples)
            avg = float(sum(values)) / niters_convergence
            var = [(value - avg) ** 2 for value in values]
            var = sum(var) / (niters_convergence - 1)
            return -var / 2.

        def inner_sum(seq, J_prime):
            P = float(J_prime.count(seq)) / nsamples
            Q = qprob(seq)
            return np.log(P) - np.log(Q) - bias(seq, J_prime) if P > 0 else 0

        I_prime = [(random.choice(seqs), sample(seqs, nsamples)) for i in range(niters_convergence)]
        K = [inner_sum(seq, J_prime) for seq, J_prime in I_prime]
        return sum(K) / np.count_nonzero(K) # discard those that resulted in 0

if __name__ == '__main__':
    main()
