from __future__ import print_function
import numpy as np

import argparse
import time
import os
import random
from six.moves import cPickle

from utils import TextLoader
from model import Model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_dir', type=str, default='save',
                       help='model directory to store checkpointed models')
    parser.add_argument('-n', type=int, default=100,
                       help='number of characters to sample')

    args = parser.parse_args()
    sample(args)

def sample(args):
    with open(os.path.join(args.save_dir, 'config.pkl'), 'rb') as f:
        saved_args = cPickle.load(f)
    with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'rb') as f:
        chars, _ = cPickle.load(f)
    with open(os.path.join(args.save_dir, 'primes.pkl'), 'rb') as f:
        primes = cPickle.load(f)
    model = Model(saved_args)
    model.model.load_weights(os.path.join(args.save_dir, 'weights.h5'))
    prime = random.choice(primes)
    sample, _ = model.sample(prime, args.n)
    sample = [chars[c] for c in sample]
    print((';' if saved_args.salento else '').join(sample))

if __name__ == '__main__':
    main()
