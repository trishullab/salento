import argparse
import numpy as np
import random
import os
import logging as log
import time
from six.moves import cPickle
from matplotlib import pyplot as plt
from scipy.interpolate import spline
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
    kl = KLD(args)

    with open(args.data_file) as data:
        parser = SalentoJsonParser(data)
    
    for pack in parser.package_names():
        sequences = parser.as_sequences(pack)
        locations = parser.get_call_locations(pack)
        log.debug('### ' + pack)
        kld = kl.compute_kld(locations, sequences)
        print('### ' + pack)
        for location in kld:
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

        # computes paths that terminate at location, and also
        # the call sequences that terminate at location (domain)
        def paths_ending_at(location):
            paths = []
            domain = []
            for sequence in sequences:
                sequence = sequence['sequence']
                for i, event in enumerate(sequence):
                    if type_of(event) == 'call' and event['location'] == location:
                        s = sequence[0: i+1] # also includes branches
                        os = calls_in_sequence(s)
                        if not s in paths:
                            paths.append(s)
                        if not os in domain:
                            domain.append(os)
            return paths, domain

        kld_l = {}
        for l in locations:
            paths, domain = paths_ending_at(l)
            kld_l[l] = self.kld(l, paths, domain)
        return kld_l

    def kld(self, l, paths, domain):

        def norm(arr):
            return [float(i) / sum(arr) for i in arr]

        def qprob(sequence):
            sequence = to_model_alphabet(sequence, self.vocab) + [self.vocab['END']]
            prime = random.choice(self.primes)
            pr = self.model.probability(prime, sequence)
            pr = [p[event] for p, event in zip(pr, sequence)]
            log.debug([self.chars[e] for e in sequence])
            log.debug(pr)
            return np.prod(pr)

        def pprob(sequence):
            def pprob_path(path):
                pr = [1./event['branches'] for event in path if type_of(event) == 'branches']
                return np.prod(pr)
            pr = [pprob_path(path) for path in paths if calls_in_sequence(path) == sequence]
            return np.sum(pr)

        log.debug('')
        log.debug(l)
        P = norm([pprob(sequence) for sequence in domain])
        Q = [qprob(sequence) for sequence in domain]
        K = list(map(lambda p, q: p * np.log(p / q), P, Q))
        log.debug('P: ' + ' '.join('{:.2f}'.format(e) for e in P))
        log.debug('Q: ' + ' '.join('{:.2e}'.format(e) for e in Q))
        log.debug('K: ' + ' '.join('{:.2f}'.format(e) for e in K))
        log.debug('')
        if self.args.plot_dir is not None:
            self.save_plot(l, P, Q, K)
        return sum(K)

    def save_plot(self, location, P, Q, K):
        data = sorted(zip(P, Q, K), key=lambda x: x[1])
        x = np.array(range(0, len(data)))
        line1, = plt.plot(x, P, label='P', c='b', linewidth=2)
        line2, = plt.plot(x, Q, label='Q', c='g', linewidth=2)
        line3, = plt.plot(x, K, label='KLD', c='r', linewidth=2)
        plt.ylabel('Probability')
        plt.xlabel('Sequence')
        plt.grid(alpha=0.8)
        xmin, xmax, ymin, ymax = plt.axis()
        plt.axis((xmin, xmax, ymin, 1.0))
        plt.legend(handles=[line1, line2, line3])
        plt.title(location)
        plt.savefig(os.path.join(self.args.plot_dir, location + '.pdf'))
        plt.clf()

if __name__ == '__main__':
    main()
