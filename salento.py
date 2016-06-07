import json

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
                    ret += [event['call']]
                    for i, state in enumerate(event['states']):
                        ret += [str(i) + '_' + str(state)]
                ret += ['END'] if start_end else []
        return ret
