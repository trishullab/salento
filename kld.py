import argparse
import tensorflow as tf
import numpy as np
import random
import os
import logging as log
import time
import pickle
from utils import sample
from data_reader import JsonParser
from model import Model
from lda import LDA

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('data_file', type=str, nargs=1,
                       help='input file in JSON')
    argparser.add_argument('--save_dir', type=str, default='save',
                       help='directory where model is stored')
    argparser.add_argument('--debug', action='store_true',
                       help='enable printing debug log to debug.log')
    argparser.add_argument('--seed', type=int, default=None,
                       help='random seed')
    argparser.add_argument('--num_samples', type=int, default=10,
                       help='number of samples used in estimators')
    argparser.add_argument('--num_iters', type=int, default=10,
                       help='number of iterations for convergence in estimators')
    argparser.add_argument('--location_sensitive', action='store_true',
                       help='document is location-sensitive set of calls (default False)')
    args = argparser.parse_args()
    if args.debug:
        log.basicConfig(level=log.DEBUG, filename='debug.log', filemode='w', format='%(message)s')
    start = int(time.time())
    random.seed(args.seed if args.seed is not None else start)

    with tf.Session() as sess:
        with open(args.data_file[0]) as data:
            parser = JsonParser(data)

        kld = KLD(args, parser, sess)
        for pack in parser.packages:
            locations = parser.locations(pack)
            print('### ' + pack['name'])
            log.debug('\n### ' + pack['name'])
            klds = [(l, kld.compute(l, pack)) for l in locations]
            for l, k in sorted(klds, key=lambda x: -x[1]):
                print('  {:35s} : {:.2f}'.format(l, k))

    print('Not in vocab: ')
    print(kld.not_in_vocab)
    print('Seed: ' + str(start))
    print('Time taken: ' + str(int(time.time() - start)) + 's')

class KLD():
    def __init__(self, args, parser, sess):
        self.args = args
        self.parser = parser
        self.sess = sess
        self.not_in_vocab = []

        with open(os.path.join(args.save_dir, 'config.pkl'), 'rb') as f:
            saved_args = pickle.load(f)
        with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'rb') as f:
            self.chars, self.vocab = pickle.load(f)

        self.model = Model(saved_args, True)
        tf.initialize_all_variables().run()
        saver = tf.train.Saver(tf.all_variables())
        ckpt = tf.train.get_checkpoint_state(args.save_dir)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(self.sess, ckpt.model_checkpoint_path)

        with open(os.path.join(args.save_dir, 'lda.pkl'), 'rb') as f:
            self.lda = LDA(from_file=f)

    def inner_sum(self, seq, seqs, topics):
        P = float(seqs.count(seq)) / len(seqs)
        Q = sum([self.reference(seq, topic) for topic in topics]) / len(topics)
        return (np.log(P) - np.log(Q)
                - self.sequence_bias(seq, seqs)
                - self.topic_bias(topics)) if P > 0 else 0

    def reference(self, seq, topic):
        """ Compute the reference probability of a sequence given a topic """
        stream = self.parser.stream(seq)
        pr = self.model.probability(self.sess, stream, topic, self.vocab)
        pr = pr[:-1] # distribution is over the next symbol, so ignore last
        stream = stream[1:] # first symbol is prime (START), so ignore it
        probs = [p[self.vocab[char]] for p, char in zip(pr, stream)]
        log.debug(topic)
        log.debug(stream)
        log.debug(probs)
        return np.prod(probs)

    def topic_bias(self, topics):
        """ TODO """
        return 0.

    def sequence_bias(self, seq, seqs):
        """ bias is half of the negative variance of the estimate. the variance
            is itself estimated through bootstrap resampling."""
        values = []
        for i in range(self.args.num_iters):
            values.append(float(seqs.count(seq)) / len(seqs))
            seqs = sample(seqs, nsamples=len(seqs))
        avg = float(sum(values)) / self.args.num_iters
        var = [(value - avg) ** 2 for value in values]
        var = sum(var) / (self.args.num_iters - 1)
        return -var / 2.

    def compute(self, l, pack):
        seqs_l = self.parser.sequences(pack, l)
        bow = set([(event['call'], event['location'] if self.args.location_sensitive else None)
                for seq in seqs_l for event in seq])
        lda_data = [';'.join([call for (call, _) in bow if not call == 'TERMINAL'])]
        not_in_vocab = [call for (call, _) in bow if call not in self.vocab]
        if not not_in_vocab == []:
            self.not_in_vocab += list(set(not_in_vocab) - set(self.not_in_vocab))
            return -1.

        log.debug('\n' + l)
        triple_sample = [(sample(seqs_l, nsamples=1),
                          sample(seqs_l, nsamples=self.args.num_samples),
                          self.lda.infer(lda_data, nsamples=self.args.num_samples)[0])
                                for i in range(self.args.num_iters)]
        K = list(map(lambda t: self.inner_sum(*t), triple_sample))
        return sum(K) / np.count_nonzero(K) # discard inner_sums that resulted in 0

if __name__ == '__main__':
    main()
