import json
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
    argparser.add_argument('--top_words', type=int, default=5,
                       help='top-k words to print from each topic')
    argparser.add_argument('--seed', type=int, default=None,
                       help='seed for pseudo-randomness')
    args = argparser.parse_args()
    seed = int(time()) if args.seed is None else args.seed
    with open(args.input_file, 'r') as fin, open(args.output_file, 'w') as fout:
        data, js = get_data(fin)
        lda_dist = do_lda(data, args.ntopics, args.top_words, seed)
        write_lda_dist(fout, js, lda_dist)
    print('seed: {:d}'.format(seed))

def get_data(fin):
    print('Reading data file...')
    js = json.loads(fin.read())
    lda_data = []
    npackages = len(js['packages'])

    for i, package in enumerate(js['packages']):
        bow = set([(event['call'], event['location']) for trace in package['data'] for event in trace['sequence']])
        lda_data.append(';'.join([call for (call, _) in bow if not call == 'TERMINAL']))
        print('Gathering data for LDA: {:5d}/{:d} packages'.format(i+1, npackages), end='\r')
    print()
    return lda_data, js

def do_lda(data, ntopics, top_words, seed):

    def print_top_words(model, features):
        print('\nTop %d words from ' % top_words)
        for idx, topic in enumerate(model.components_):
            print('Topic #%d:' % idx)
            print('\n'.join([features[i] for i in topic.argsort()[:-top_words - 1:-1]]))
        print()

    tf_vectorizer = CountVectorizer(lowercase=False, token_pattern=u'[^;]+;')
    tf = tf_vectorizer.fit_transform(data)
    lda = LatentDirichletAllocation(ntopics, doc_topic_prior=0.1, random_state=seed, learning_method='batch',
            max_iter=100, verbose=1, evaluate_every=1, max_doc_update_iter=100)
    print('Running LDA...')
    lda.fit(tf)

    features = tf_vectorizer.get_feature_names()
    print_top_words(lda, features)

    lda_dist = lda.transform(tf)
    return lda_dist

def write_lda_dist(fout, js, lda_dist):
    assert len(js['packages']) == len(lda_dist)
    print('Writing to output file...')
    for (package, dist) in zip(js['packages'], lda_dist):
        package['topic'] = list(dist)
    json.dump(js, fp=fout, indent=2)

if __name__ == '__main__':
    main()
