from subprocess import Popen, PIPE
import argparse
import numpy as np


prime_prefix = 'END\n;START;"android.app.AlertDialog$Builder: android.app.AlertDialog$Builder setMessage(java.lang.CharSequence)";m1_1;m2_1;m3_1;"android.app.AlertDialog$Builder: android.app.AlertDialog$Builder setPositiveButton(java.lang.CharSequence,android.content.DialogInterface$OnClickListener)";m1_1;m2_2;m3_1;"android.app.AlertDialog$Builder: android.app.AlertDialog$Builder setNegativeButton(java.lang.CharSequence,android.content.DialogInterface$OnClickListener)";m1_1;m2_2;m3_1;"android.app.AlertDialog$Builder: android.app.AlertDialog show()";m1_3;m2_4;m3_3;END\n;START'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', type=str, default=None,
            help='input data file', required=True)
    args = parser.parse_args()
    
    with open(args.input_file) as f:
        test(f)

def test(f):
    def get_next(ls):
        return ';' + next(ls, '')

    ranks = [0] * 49
    i = 0
    for line in f.readlines():
        count = int(line.split('#')[0])
        line = line.split('#')[1]
        tokens = iter(line.split(';')[1:][:-1])
        tokens = [t # + get_next(tokens) + get_next(tokens) + get_next(tokens)
                for t in tokens]
        ranks = np.add(ranks, np.multiply(count, test_model(tokens)))
        i += 1
        print('ranks@' + str(i) + ':\n' + str(ranks) + '\n')

def test_model(sequence):
    ranks = [0] * 49
    for i in range(0, len(sequence), 4):
        prime = prime_prefix + (';' if i is not 0 else '') + ';'.join(sequence[:i])
        cmd = ['python3',  'sample.py', '--prime', prime, '-n', '1']
        stdout, stderr = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True).communicate()
        try:
            rank = stdout.split('\n').index(sequence[i])
        except ValueError:
            continue
        print(rank)
        ranks[rank] += 1
        #pred = stdout[:-2]
        #print ("prime: " + prime)
        #print (stdout[:-2] + '\n')
        #print (sequence[i] + '\n==\n' + stdout[:-2] + '\n-> ' + str(sequence[i] == stdout[:-2]))
    return ranks

if __name__ == '__main__':
    main()
