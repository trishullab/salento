import os
import sys
import json
import pickle
import argparse
import itertools
import numpy as np
from time import time
from utils import weighted_pick
from collections import OrderedDict

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_file', type=str, default=None, required=True,
                       help='input JSON file')
    argparser.add_argument('--ntopics', type=int, default=None, required=True,
                       help='run LDA with n topics')
    argparser.add_argument('--output_file', type=str, default=None, required=True,
                       help='output JSON file')
    argparser.add_argument('--save_dir', type=str, default='save',
                       help='directory to store LDA model')
    argparser.add_argument('--alpha', type=float, default=0.1,
                       help='initial alpha value')
    argparser.add_argument('--num_gibbs_samples', type=int, default=100,
                       help='number of Gibbs samples for inference on given data')
    argparser.add_argument('--num_gibbs_iters', type=int, default=10,
                       help='number of Gibbs sampling iterations')
    argparser.add_argument('--gibbs_random_init', action='store_true',
                       help='randomly initialize Gibbs chain instead of from trained model')
    argparser.add_argument('--location_sensitive', action='store_true',
                       help='document is location-sensitive set of calls (default False)')
    argparser.add_argument('--top_words', type=int, default=5,
                       help='top-k words to print from each topic')
    args = argparser.parse_args()
    print('Reading data file...')
    with open(args.input_file, 'r') as fin:
        data, js = get_data(fin, args.location_sensitive)

    ok = 'r'
    while ok == 'r':
        model = LDA(args=args)
        model.train(data)
        top_words = model.top_words(args.top_words)
        for i, words in enumerate(top_words):
            print('\nTop words in Topic#{:d}'.format(i))
            for w in words:
                print('{:.2f} {:s}'.format(words[w], w))
        print('\nOK with the model (y(es)/n(o)/r(edo))? ', end='')
        ok = sys.stdin.readline().rstrip('\n')

    if ok == 'y':
        print('Saving model to {:s}'.format(os.path.join(args.save_dir, 'lda.pkl')))
        with open(os.path.join(args.save_dir, 'lda.pkl'), 'wb') as fmodel:
            pickle.dump((model.model, model.tf_vectorizer), fmodel)

        print('Running inference (Gibbs sampling) on given data...')
        dist = model.infer(data, args.num_gibbs_samples, args.num_gibbs_iters, args.gibbs_random_init)
        print('Writing to output file...')
        with open(args.output_file, 'w') as fout:
            write_data(fout, js, dist, args, top_words)

def get_data(fin, location_sensitive=False):
    js = json.loads(fin.read())
    data = []
    npackages = len(js['packages'])

    for i, package in enumerate(js['packages']):
        bow = set([(event['call'], event['location'] if location_sensitive else None)
                for trace in package['data'] for event in trace['sequence']])
        data.append(';'.join([call for (call, _) in bow if not call == 'TERMINAL']))
        print('Gathering data for LDA: {:5d}/{:d} packages'.format(i+1, npackages), end='\r')
    print()
    return data, js

def write_data(fout, js, dist, args, top_words):
    assert len(js['packages']) == len(dist)
    for (package, dist) in zip(js['packages'], dist):
        package['topic'] = list(dist)
    js['lda_args'] = vars(args)
    js['lda_top_words'] = top_words
    json.dump(js, fp=fout, indent=2)

class LDA():

    def __init__(self, args=None, from_file=None):
        """ Initialize LDA model from either arguments or a file. If both are
            provided, file will be used."""
        assert args or from_file, 'Improper initialization of LDA model'
        if from_file is not None:
            self.model, self.tf_vectorizer = pickle.load(from_file)
        else:
            self.tf_vectorizer = CountVectorizer(lowercase=False, token_pattern=u'[^;]+')
            self.model = LatentDirichletAllocation(args.ntopics, doc_topic_prior=args.alpha,
                    learning_method='batch', max_iter=100, verbose=1, evaluate_every=1, max_doc_update_iter=100,
                    mean_change_tol=1e-5)

    def top_words(self, ntop_words):
        features = self.tf_vectorizer.get_feature_names()
        top_words = [OrderedDict([(features[i], topic[i]) for i in topic.argsort()[:-ntop_words - 1:-1]])
                        for topic in self.model.components_]
        return top_words

    def train(self, data):
        tf = self.tf_vectorizer.fit_transform(data)
        self.model.fit(tf)
        # note: normalizing does not change subsequent inference, provided no further training is done
        self.model.components_ /= self.model.components_.sum(axis=1)[:, np.newaxis]

    def infer(self, data, nsamples=100, niters=10, random_init=False):
        """ Return samples from the Bayesian posterior distribution on topic
            vectors given the data, by running Gibbs sampling. Trained model
            provides topic-word distribution (components_) and, if desired,
            initial value for doc_topic_dist in the chain.
        """
        tf = self.tf_vectorizer.transform(data)
        dist = self.model.transform(tf)
        assert tf.shape[0] == dist.shape[0]
        gibbs_samples = [self.gibbs(doc, None if random_init else doc_topic_dist, nsamples, niters)
                            for doc, doc_topic_dist in zip(tf, dist)]
        return gibbs_samples

    def gibbs(self, doc, doc_topic_dist, nsamples, niters):
        """ Given a document d = w_1...w_n, we compute p(t | w_i) for each word
            w_i, where t is over topics.  From Bayes' rule:

            p(t | w_i) = p(w_i | t) p(t) / p(w_i)

            where p(w_i | t) is from the trained model, p(t) is the current
            topic distribution of d, and p(w_i) is sum_t p(w_i | t)p(t) -- a
            normalizing term. From this we sample a topic t that generated w_i.
            We do this for all w_i's and get the 'produced' vector of the count
            of words generated by each topic.
            
            Then, p(t) is updated to be a sample from dirichlet(p(t) + produced(t))
        """
        samples = [self.gibbs_one(doc, doc_topic_dist, niters) for i in range(nsamples)]
        return samples

    def gibbs_one(self, doc, doc_topic_dist, niters):
        doc = doc.toarray()[0]
        if doc_topic_dist is None:
            doc_topic_dist = np.random.dirichlet(np.random.normal(size=self.model.n_topics))
        for i in range(niters):
            t = [self.sample_topic(w, count, doc_topic_dist) for w, count in enumerate(doc)]
            topics_in_doc = list(itertools.chain(*t))
            produced = [topics_in_doc.count(j) for j in range(self.model.n_topics)]
            doc_topic_dist = np.random.dirichlet(np.add(doc_topic_dist, produced))
        return list(doc_topic_dist)

    def sample_topic(self, w, count, doc_topic_dist):
        word_topic_dist = np.array([doc_topic_dist[i] * self.model.components_[i, w]
                            for i in range(self.model.n_topics)])
        word_topic_dist /= word_topic_dist.sum()
        sampled = [weighted_pick(word_topic_dist) for i in range(count)]
        return sampled

if __name__ == '__main__':
    main()
