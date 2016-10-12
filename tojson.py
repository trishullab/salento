import json
import argparse
import re
import ast
import random

counts = {} # count of each call
vocab = None # vocabulary
stop_words = [] # complement of vocab

def main():
    global vocab
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_file', type=str, default=None, required=True,
                       help='input file in old format')
    argparser.add_argument('--output_file', type=str, default=None, required=True,
                       help='output JSON file')
    argparser.add_argument('--vocab_file', type=str, default=None,
                       help='file containing vocabulary (one per line)')
    argparser.add_argument('--prefixes', action='store_true',
                       help='output all prefixes of each sequence')
    argparser.add_argument('--slice_locations', action='store_true',
                       help="""for each package, generate k packages, where k is the number of locations,
                             that each contain only sequences ending at their respective location""")
    args = argparser.parse_args()
    if args.vocab_file is not None:
        with open(args.vocab_file) as f:
            args.vocab = vocab = list(set([line.split('#')[0] for line in f.readlines()]))
    to_json(args)

def to_json(args):
    jsequences = []
    packages = []
    name = ''
    nseqs = 0

    def add_sequences_to_package():
        random.shuffle(jsequences)
        if jsequences == []:
            return 0
        if not args.slice_locations:
            package = { 'data' : jsequences, 'name' : name }
            packages.append(package)
        else:
            locations = list(set([event['location'] for seq in jsequences for event in seq['sequence']]))
            seqs_l = [[seq for seq in jsequences if seq['sequence'][-1]['location'] == l] for l in locations]
            packages_l = [{ 'data' : seq_l, 'name' : name, 'slice' : l } for l, seq_l in zip(locations, seqs_l)]
            packages.extend(packages_l)

        print('{:6d} packages done'.format(len(packages)), end='\r')
        return len(jsequences)

    with open(args.input_file) as fin:
        for line in fin.readlines():
            if line[0] == '#':
                nseqs += add_sequences_to_package()
                jsequences = []
                name = line[4:-1]
            else:
                jsequences += to_json_sequence(line, args.prefixes)
    nseqs += add_sequences_to_package()

    if args.vocab_file is not None:
        args.stop_words = list(stop_words)

    with open(args.output_file, 'w') as fout:
        json.dump( { 'tojson_args' : vars(args), 'packages' : packages }, fp=fout, indent=2)

    print('Call counts (compatible with --vocab_file format):')
    for w, c in sorted(counts.items(), key=lambda x: -x[1]):
        print('{}# {}'.format(w, c))

    print('\nConverted {0} packages, {1} sequences to JSON'.format(len(packages), nseqs))

def to_json_sequence(sequence, prefixes=False):
    global stop_words
    jsequence = []
    for event in sequence.split(';')[0:-1]:
        if len(event.split('"')) == 1:
            jevent = {'branches' : int(event)}
        else:
            call = event.split('"')[1]
            if vocab is not None and call not in vocab:
                stop_words += [call] if call not in stop_words else []
                continue
            s = re.split('\[|\]', event.split('"')[2])
            states = ast.literal_eval('[' + s[1] + ']')
            location = s[3]
            jevent = {'call' : call, 'states' : states, 'location' : location}
            counts[call] = counts[call] + 1 if call in counts else 1
        jsequence.append(jevent)
    if jsequence == []:
        return []
    jsequence.append({'call' : 'TERMINAL', 'states' : states, 'location' : 'TERMINAL'})
    if prefixes:
        return [{'sequence' : jsequence[:i+1]} for i in range(len(jsequence))]
    else:
        return [{'sequence': jsequence}]

if __name__ == '__main__':
    main()
