import json

def type_of(event):
    if 'call' in event:
        return 'call'
    raise KeyError('Malformed event', event)

def calls_in_sequence(sequence):
    return [event for event in sequence if type_of(event) == 'call']

def calls_as_tokens(sequence):
    s = []
    call_events = calls_in_sequence(sequence)
    for event in call_events:
        s += [event['call']] + [str(i) + '_' + str(state) for i, state in enumerate(event['states'])]
    return s

def to_model_alphabet(sequence, vocab):
    return [vocab[token] for token in calls_as_tokens(sequence)]

START, END = 'START', 'END'
class JsonParser():
    def __init__(self, f):
        self.json_data = json.loads(f.read())

    def as_tokens(self, start_end=False):
        ret = []
        topics = []
        npackages = len(self.json_data['packages'])
        nsequences = 0
        for i, package in enumerate(self.json_data['packages']):
            print('Reading traces from {:4d}/{:d} packages...'.format(i+1, npackages), end='\r')
            for topic in package['topic']:
                seq = []
                for data_point in package['data']:
                    nsequences += 1
                    seq += [START] if start_end else []
                    seq += calls_as_tokens(data_point['sequence'])
                    seq += [END] if start_end else []
                ret += seq
                for i in range(len(seq)):
                    topics.append(topic)
        print()
        print('Read {:d} traces from {:d} packages'.format(nsequences, npackages))
        return ret, topics

    def package_names(self):
        return [package['name'] for package in self.json_data['packages']]

    def get_call_locations(self, package_name=None):
        locations = []
        for package in self.json_data['packages']:
            if package_name and not package['name'] == package_name:
                continue
            for data_point in package['data']:
                for event in data_point['sequence']:
                    if type_of(event) == 'call':
                        locations.append(event['location'])
        return set(locations)

    def as_sequences(self, package_name=None):
        seqs = []
        for package in self.json_data['packages']:
            if package and not package['name'] == package_name:
                continue
            for data_point in package['data']:
                seqs.append(data_point)
        return seqs
