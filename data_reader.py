import json
import itertools

START, END = 'START', 'END'

class JsonParser():
    def __init__(self, f):
        self.json_data = json.loads(f.read())
        self.packages = self.json_data['packages']

    def read(self):
        """ Read the entire dataset of sequences with topics into lists
            !!! MEMORY INTENSIVE METHOD !!!"""
        ret = []
        topics = []
        npackages = len(self.packages)
        nsequences = 0
        for i, package in enumerate(self.packages):
            print('Reading traces from {:4d}/{:d} packages...'.format(i+1, npackages), end='\r')
            for topic in package['topic']:
                seq = []
                for data_point in package['data']:
                    nsequences += 1
                    seq += self.stream(data_point['sequence'])
                ret += seq
                for i in range(len(seq)):
                    topics.append(topic)
        print()
        print('Read {:d} traces from {:d} packages'.format(nsequences, npackages))
        return ret, topics

    def stream(self, sequence):
        s = [[event['call']] + [str(i) + '_' + str(state) for i, state in enumerate(event['states'])]
                for event in sequence]
        return [START] + list(itertools.chain(*s)) + [END]

    def locations(self, package):
        locations = [event['location'] for data_point in package['data']
                        for event in data_point['sequence']]
        return list(set(locations))

    def sequences(self, package, location=None):
        """ Get all sequences in package. If location is given, then get all
            sequences in package that end at location."""
        seqs = []
        for data_point in package['data']:
            seq = data_point['sequence']
            if location is None or seq[-1]['location'] == location:
                seqs.append(seq)
        return seqs
