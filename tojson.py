import json
import argparse
import re
import ast
import random

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_file', type=str, default=None, required=True,
                       help='input file in old format')
    argparser.add_argument('--output_file', type=str, default=None, required=True,
                       help='output JSON file')
    argparser.add_argument('--prefixes', action='store_true',
                       help='output all prefixes of each sequence')
    argparser.add_argument('--slice_locations', action='store_true',
                       help="""for each package, generate k packages, where k is the number of locations,
                             that each contain only sequences ending at their respective location""")
    args = argparser.parse_args()
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

    with open(args.output_file, 'w') as fout:
        json.dump( { 'packages' : packages }, fp=fout, indent=2)
    print('\nConverted {0} packages, {1} sequences to JSON'.format(len(packages), nseqs))

def to_json_sequence(sequence, prefixes=False):
    jsequence = []
    for event in sequence.split(';')[0:-1]:
        if len(event.split('"')) == 1:
            jevent = {'branches' : int(event)}
        else:
            call = event.split('"')[1]
            s = re.split('\[|\]', event.split('"')[2])
            states = ast.literal_eval('[' + s[1] + ']')
            location = s[3]
            jevent = {'call' : call, 'states' : states, 'location' : location}
        jsequence.append(jevent)
    jsequence.append({'call' : 'TERMINAL', 'states' : states, 'location' : 'TERMINAL'})
    if prefixes:
        return [{'sequence' : jsequence[:i+1]} for i in range(len(jsequence))]
    else:
        return [{'sequence': jsequence}]

if __name__ == '__main__':
    main()
