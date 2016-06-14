import argparse
import numpy as np
import random
import os
from six.moves import cPickle
from matplotlib import pyplot as plt
from scipy.interpolate import spline
from salento import SalentoJsonParser, type_of, to_model_alphabet
from model import Model

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--save_dir', type=str, default='save',
                       help='directory where model is stored')
    argparser.add_argument('--data_file', type=str, required=True, default=None,
                       help='Salento\'s output file in JSON')
    argparser.add_argument('--plot_dir', type=str, default=None,
                       help='directory to save KLD plots in')
    args = argparser.parse_args()
    kl = KLD(args)

    with open(args.data_file) as data:
        kld = kl.compute_kld(data)
        for location in kld:
            print('{:35s} : {:e}'.format(location, kld[location]))

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
        kld_l = dict([(l, self.kld(l, sequences_ending_in(l, sequences)))
                for l in parser.get_call_locations()])
        return kld_l

    def kld(self, location, sequences):

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
        K = list(map(lambda p, q: p * np.log(p / q), P, Q))
        if self.args.plot_dir is not None:
            self.save_plot(location, P, Q, K)
        return sum(K)

    def save_plot(self, location, P, Q, K):
        data = sorted(zip(P, Q, K), key=lambda x: x[1])
        x = np.array(range(0, len(data)))
        x_smooth = np.linspace(x.min(), x.max(), 300)
        P_smooth = spline(x, np.array([d[0] for d in data]), x_smooth)
        Q_smooth = spline(x, np.array([d[1] for d in data]), x_smooth)
        K_smooth = spline(x, np.array([d[2] for d in data]), x_smooth)
        line1, = plt.plot(x_smooth, P_smooth, label='True dist.', c='b', linewidth=2)
        line2, = plt.plot(x_smooth, Q_smooth, label='Observed dist.', c='g', linewidth=2)
        line3, = plt.plot(x_smooth, K_smooth, label='KLD', c='r', linewidth=2)
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
