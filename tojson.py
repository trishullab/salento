import json
import argparse
import re
import ast

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--input_file', type=str, default=None, required=True,
                       help='input file in old format')
    argparser.add_argument('--output_file', type=str, default=None, required=True,
                       help='output JSON file')
    args = argparser.parse_args()

    jsequences = []
    with open(args.input_file) as fin:
        for sequence in fin.readlines():
            jsequences += to_json(sequence)
    data = { 'data' : jsequences }
    packages = { 'packages' : [data] }
    with open(args.output_file, 'w') as fout:
        fout.write(json.dumps(packages, indent=2))
    print('Converted {0} sequences to JSON'.format(len(jsequences)))

def to_json(sequence):
    count = int(sequence.split()[0])
    jsequence = []
    for event in ' '.join(sequence.split()[1:]).split(';')[0:-1]:
        s = re.split('\[|\]', event)
        call = s[0].replace('"', '')
        states = ast.literal_eval('[' + s[1] + ']')
        location = s[3]
        jevent = {'call' : call, 'states' : states, 'location' : location}
        jsequence.append(jevent)
    return [{'sequence': jsequence}] * count

if __name__ == '__main__':
    main()
