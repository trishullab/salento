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
    args = argparser.parse_args()
    to_json(args)

def to_json(args):
    jsequences = []
    packages = []
    name = ''
    nseqs = 0

    def add_sequences_to_package():
        random.shuffle(jsequences)
        package = { 'data' : jsequences, 'name' : name }
        if len(package['data']) > 0:
            packages.append(package)
        return len(jsequences)

    with open(args.input_file) as fin:
        for line in fin.readlines():
            if line[0] == '#':
                nseqs += add_sequences_to_package()
                jsequences = []
                name = line[4:-5]
            else:
                jsequences += to_json_sequence(line)
    nseqs += add_sequences_to_package()

    with open(args.output_file, 'w') as fout:
        fout.write(json.dumps( { 'packages' : packages }, indent=2))
    print('Converted {0} packages, {1} sequences to JSON'.format(len(packages), nseqs))

def to_json_sequence(sequence):
    count = int(sequence.split()[0])
    jsequence = []
    for event in ' '.join(sequence.split()[1:]).split(';')[0:-1]:
        if len(event.split('"')) == 1:
            jevent = {'branches' : int(event)}
        else:
            call = event.split('"')[1]
            s = re.split('\[|\]', event.split('"')[2])
            states = ast.literal_eval('[' + s[1] + ']')
            location = s[3]
            jevent = {'call' : call, 'states' : states, 'location' : location}
        jsequence.append(jevent)
    return [{'sequence': jsequence}] * count

if __name__ == '__main__':
    main()
