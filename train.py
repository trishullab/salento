from __future__ import print_function
import numpy as np
import tensorflow as tf

import argparse
import time
import os
import random
from six.moves import cPickle

from utils import TextLoader
from model import Model

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default='data/tinyshakespeare',
                       help='data directory containing input.txt')
    parser.add_argument('--save_dir', type=str, default='save',
                       help='directory to store checkpointed models')
    parser.add_argument('--rnn_size', type=int, default=128,
                       help='size of RNN hidden state')
    parser.add_argument('--num_layers', type=int, default=2,
                       help='number of layers in the RNN')
    parser.add_argument('--batch_size', type=int, default=50,
                       help='minibatch size')
    parser.add_argument('--seq_length', type=int, default=10,
                       help='RNN sequence length')
    parser.add_argument('--step', type=int, default=3,
                       help='form sequences from data every k steps')
    parser.add_argument('--num_epochs', type=int, default=30,
                       help='number of epochs')
    parser.add_argument('--grad_clip', type=float, default=5.,
                       help='clip gradients at this value')
    parser.add_argument('--learning_rate', type=float, default=0.002,
                       help='learning rate')
    parser.add_argument('--init_from', type=str, default=None,
                       help="""continue training from saved model at this path. Path must contain files saved by previous training process: 
                            'config.pkl'        : configuration;
                            'chars_vocab.pkl'   : vocabulary definitions;
                            'checkpoint'        : paths to model file(s) (created by tf).
                                                  Note: this file contains absolute paths, be careful when moving files around;
                            'model.ckpt-*'      : file(s) with model definition (created by tf)
                        """)
    args = parser.parse_args()
    train(args)

def train(args):
    data_loader = TextLoader(args.data_dir, args.batch_size, args.seq_length, args.step)
    args.vocab_size = data_loader.vocab_size
    
    model = Model(args)
    open(os.path.join(args.save_dir, 'model.json'), 'w').write(model.model.to_json())

    for e in range(args.num_epochs):
        print()
        print('-' * 50)
        print('Iteration', e)
        model.model.fit(data_loader.xdata, data_loader.ydata, batch_size=args.batch_size,
                nb_epoch=1)
        model.model.save_weights(os.path.join(args.save_dir, 'model-weights.h5'), overwrite=True)

        start_index = random.randint(0, len(data_loader.tensor) - args.seq_length - 1)
        prime = data_loader.tensor[start_index: start_index + args.seq_length]
        prime = ''.join([data_loader.chars[c] for c in prime])
        print('priming with: ' + prime)
        model.sample(data_loader.chars, data_loader.vocab, num=100, prime=prime[-args.seq_length:])


if __name__ == '__main__':
    main()
