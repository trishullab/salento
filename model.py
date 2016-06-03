from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM, TimeDistributed
from keras.layers.embeddings import Embedding
from keras.optimizers import Adam
import numpy as np
import sys

class Model():
    def __init__(self, args):
        self.args = args
        self.model = Sequential()
        self.model.add(LSTM(args.rnn_size, input_shape=(args.seq_length, args.vocab_size), return_sequences=True))
        for i in range(1, args.num_layers):
            self.model.add(LSTM(args.rnn_size, return_sequences=False))
        self.model.add(Dense(args.vocab_size))
        self.model.add(Activation('softmax'))
        
        adam = Adam(lr=args.learning_rate, clipnorm=args.grad_clip)
        self.model.compile(loss='categorical_crossentropy', optimizer=adam)

    def sample(self, chars, vocab, num=100, prime=' ', sampling_type=1):

        def weighted_pick(weights):
            t = np.cumsum(weights)
            s = np.sum(weights)
            return(int(np.searchsorted(t, np.random.rand(1)*s)))

        ret = []
        window = prime
        for n in range(num):
            x = np.zeros((1, self.args.seq_length, self.args.vocab_size))
            for t, char in enumerate(window):
                x[0, t, vocab[char]] = 1.
            p = self.model.predict(x, verbose=0)[0]

            if sampling_type == 0:
                sample = np.argmax(p)
            elif sampling_type == 2:
                if char == ' ':
                    sample = weighted_pick(p)
                else:
                    sample = np.argmax(p)
            else: # sampling_type == 1 default:
                sample = weighted_pick(p)

            pred = chars[sample]
            window = window[1:] + pred
            sys.stdout.write(pred)
            sys.stdout.flush()
            ret += pred
        return ret


