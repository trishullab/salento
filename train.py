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
    parser.add_argument('--salento', action='store_true',
                       help='data is Salento (JSON) output')
    parser.add_argument('--init_from', type=str, default=None,
                       help="""continue training from saved model at this path. Path must contain files saved by previous training process: 
                            'config.pkl'        : configuration;
                            'chars_vocab.pkl'   : vocabulary definitions;
                            'weights.h5'  : checkpointed weights
                        """)
    args = parser.parse_args()
    train(args)

def train(args):
    data_loader = TextLoader(args.data_dir, args.batch_size, args.seq_length, args.step, args.salento)
    args.vocab_size = data_loader.vocab_size
    
    # check compatibility if training is continued from previously saved model
    if args.init_from is not None:
        # check if all necessary files exist 
        assert os.path.isdir(args.init_from)," %s must be a a path" % args.init_from
        assert os.path.isfile(os.path.join(args.init_from,"config.pkl")),"config.pkl file does not exist in path %s"%args.init_from
        assert os.path.isfile(os.path.join(args.init_from,"chars_vocab.pkl")),"chars_vocab.pkl.pkl file does not exist in path %s" % args.init_from

        # open old config and check if models are compatible
        with open(os.path.join(args.init_from, 'config.pkl'), 'rb') as f:
            saved_model_args = cPickle.load(f)
        need_be_same=["rnn_size","num_layers","seq_length"]
        for checkme in need_be_same:
            assert vars(saved_model_args)[checkme]==vars(args)[checkme],"Command line argument and saved model disagree on '%s' "%checkme
        
        # open saved vocab/dict and check if vocabs/dicts are compatible
        with open(os.path.join(args.init_from, 'chars_vocab.pkl'), 'rb') as f:
            saved_chars, saved_vocab = cPickle.load(f)
        assert saved_chars==data_loader.chars, "Data and loaded model disagreee on character set!"
        assert saved_vocab==data_loader.vocab, "Data and loaded model disagreee on dictionary mappings!"
        
    with open(os.path.join(args.save_dir, 'config.pkl'), 'wb') as f:
        cPickle.dump(args, f)
    with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'wb') as f:
        cPickle.dump((data_loader.chars, data_loader.vocab), f)
    with open(os.path.join(args.save_dir, 'primes.pkl'), 'wb') as f:
        cPickle.dump(data_loader.primes, f)
        
    model = Model(args)

    if args.init_from is not None:
        model.model.load_weights(os.path.join(args.init_from, 'weights.h5'))

    delim = ';' if args.salento else ''
    for e in range(args.num_epochs):
        print()
        print('-' * 50)
        print('Iteration', e)
        model.model.fit(data_loader.xdata, data_loader.ydata, batch_size=args.batch_size,
                nb_epoch=1)
        model.model.save_weights(os.path.join(args.save_dir, 'weights.h5'), overwrite=True)

        prime = random.choice(data_loader.primes)
        print('priming with:')
        print(delim.join([data_loader.chars[c] for c in prime]))
        sample, _ = model.sample(prime)
        sample = [data_loader.chars[c] for c in sample]
        print(delim.join(sample))

if __name__ == '__main__':
    main()
