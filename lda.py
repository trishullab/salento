import os
import sys
import json
import pickle
import argparse
from time import time

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
    argparser.add_argument('--top_words', type=int, default=5,
                       help='top-k words to print from each topic')
    args = argparser.parse_args()
    with open(args.input_file, 'r') as fin:
        data, js = get_data(fin)

    model = LDA(args)
    model.train(data)
    model.print_top_words(args.top_words)
    print('\nOK with the model (y/n)? ', end='')
    ok = sys.stdin.readline()

    if ok[0] == 'y':
        with open(os.path.join(args.save_dir, 'lda.pkl'), 'wb') as fmodel:
            pickle.dump((model.model, model.tf_vectorizer), fmodel)

        dist = model.infer(data)
        with open(args.output_file, 'w') as fout:
            write_dist(fout, js, dist)

def get_data(fin):
    print('Reading data file...')
    js = json.loads(fin.read())
    data = []
    npackages = len(js['packages'])

    for i, package in enumerate(js['packages']):
        bow = set([(event['call'], event['location']) for trace in package['data'] for event in trace['sequence']])
        data.append(';'.join([call for (call, _) in bow if not call == 'TERMINAL']))
        print('Gathering data for LDA: {:5d}/{:d} packages'.format(i+1, npackages), end='\r')
    print()
    return data, js

def write_dist(fout, js, dist):
    assert len(js['packages']) == len(dist)
    print('Writing to output file...')
    for (package, dist) in zip(js['packages'], dist):
        package['topic'] = list(dist)
    json.dump(js, fp=fout, indent=2)

class LDA():

    def __init__(self, args, from_file=None):
        if from_file is not None:
            self.model, self.tf_vectorizer = pickle.load(from_file)
        else:
            self.tf_vectorizer = CountVectorizer(lowercase=False, token_pattern=u'[^;]+;')
            self.model = LatentDirichletAllocation(args.ntopics, doc_topic_prior=args.alpha,
                    learning_method='batch', max_iter=100, verbose=1, evaluate_every=1, max_doc_update_iter=100)

    def print_top_words(self, top_words):
        features = self.tf_vectorizer.get_feature_names()
        print('\nTop %d words from ' % top_words)
        for idx, topic in enumerate(self.model.components_):
            print('Topic #%d:' % idx)
            print('\n'.join([features[i] for i in topic.argsort()[:-top_words - 1:-1]]))
        print()

    def train(self, data):
        tf = self.tf_vectorizer.fit_transform(data)
        self.model.fit(tf)

    def infer(self, data):
        tf = self.tf_vectorizer.transform(data)
        dist = self.model.transform(tf)
        return dist

if __name__ == '__main__':
    main()
