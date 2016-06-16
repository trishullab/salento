import json

def type_of(event):
    if 'call' in event:
        return 'call'
    if 'branches' in event:
        return 'branches'
    raise KeyError('Malformed event', event)

def calls_in_sequence(sequence):
    return [event for event in sequence if type_of(event) == 'call']

def to_model_alphabet(sequence, vocab):
    s = []
    call_events = [event for event in sequence if type_of(event) == 'call']
    for event in call_events:
        s += [event['call']] + ['m' + str(i+1) + '_' + state for i, state in enumerate(event['states'])]
    return list(map(vocab.get, s))

class SalentoJsonParser():
    def __init__(self, f):
        self.json_data = json.loads(f.read())
        self._packages = len(self.json_data['packages'])
        self._sequences = sum([len(p['data']) for p in self.json_data['packages']])
        print('Read {0} packages, {1} sequences'.format(self._packages, self._sequences))

    def as_tokens(self, start_end=False):
        ret = []
        for package in self.json_data['packages']:
            for data_point in package['data']:
                ret += ['START'] if start_end else []
                for event in data_point['sequence']:
                    if type_of(event) == 'call':
                        ret += [event['call']]
                        for i, state in enumerate(event['states']):
                            ret += [str(i) + '_' + str(state)]
                ret += ['END'] if start_end else []
        return ret

    def get_call_locations(self):
        locations = []
        for package in self.json_data['packages']:
            for data_point in package['data']:
                for event in data_point['sequence']:
                    if type_of(event) == 'call':
                        locations.append(event['location'])
        return set(locations)

    def as_sequences(self):
        seqs = []
        for package in self.json_data['packages']:
            for data_point in package['data']:
                seqs.append(data_point)
        return seqs
