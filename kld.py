import argparse
import numpy as np
import random
import os
from six.moves import cPickle
from salento import SalentoJsonParser, type_of, to_model_alphabet
from model import Model

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--save_dir', type=str, default='save',
                       help='directory where model is stored')
    argparser.add_argument('--data_file', type=str, required=True, default=None,
                       help='Salento\'s output file in JSON')
    args = argparser.parse_args()
    kl = KLD(args)

    with open(args.data_file) as data:
        kld = kl.compute_kld(data)
        for location in kld:
            print('{:50s} : {:e}'.format(location, kld[location]))

class KLD():
    def __init__(self, args):
        with open(os.path.join(args.save_dir, 'config.pkl'), 'rb') as f:
            saved_args = cPickle.load(f)
        with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'rb') as f:
            self.chars, self.vocab = cPickle.load(f)
        with open(os.path.join(args.save_dir, 'primes.pkl'), 'rb') as f:
            self.primes = cPickle.load(f)
        self.model = Model(saved_args)
        self.model.model.load_weights(os.path.join(args.save_dir, 'weights.h5'))

    def compute_kld(self, data):

        def sequences_ending_in(location, sequences):
            ret = []
            for sequence in sequences:
                sequence = sequence['sequence']
                for i, event in enumerate(sequence):
                    if type_of(event) == 'call' and event['location'] == location:
                        ret.append(sequence[0: i+1])
            return ret

        parser = SalentoJsonParser(data)
        sequences = parser.as_sequences()
        kld_l = dict([(l, self.kld(sequences_ending_in(l, sequences)))
                for l in parser.get_call_locations()])
        return kld_l

    def kld(self, sequences):

        def norm(sequence):
            return [float(i) / sum(sequence) for i in sequence]

        def pprob(sequence, prime):
            sequence = to_model_alphabet(sequence, self.vocab)
            pr = [self.model.sample(prime + sequence[0: i+1], num=1)[1][0][event]
                  for i, event in enumerate(sequence)]
            return np.prod(pr)

        def qprob(sequence):
            pr = [1./event['branches'] for event in sequence if type_of(event) == 'branches']
            return np.prod(pr)

        prime = random.choice(self.primes)
        P = norm([pprob(sequence, prime) for sequence in sequences])
        Q = norm([qprob(sequence) for sequence in sequences])
        kld_s = list(map(lambda p, q: p * np.log(p / q), P, Q))
        return sum(kld_s)

if __name__ == '__main__':
    main()
