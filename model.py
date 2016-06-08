from keras.models import Sequential
from keras.layers import Dense, Activation, LSTM, TimeDistributedDense, Dropout
from keras.layers.embeddings import Embedding
from keras.optimizers import Adam
import numpy as np
import sys

class Model():
    def __init__(self, args):
        self.args = args
        self.model = Sequential()
        self.model.add(LSTM(args.rnn_size, input_shape=(args.seq_length, args.vocab_size), return_sequences=True))
        self.model.add(Dropout(0.2))
        for i in range(1, args.num_layers):
            self.model.add(LSTM(args.rnn_size, return_sequences=True))
            self.model.add(Dropout(0.2))
        self.model.add(TimeDistributedDense(args.vocab_size))
        self.model.add(Activation('softmax'))
        
        adam = Adam(lr=args.learning_rate, clipnorm=args.grad_clip)
        print('Compiling model...')
        self.model.compile(loss='categorical_crossentropy', optimizer=adam)

    def sample(self, prime, num=100):

        def weighted_pick(weights):
            t = np.cumsum(weights)
            s = np.sum(weights)
            return(int(np.searchsorted(t, np.random.rand(1)*s)))

        sample = []
        prob = []
        window = prime[-self.args.seq_length:]
        for n in range(num):
            x = np.zeros((1, self.args.seq_length, self.args.vocab_size))
            for t, c in enumerate(window):
                x[0, t, c] = 1.
            p = self.model.predict(x, verbose=0)[0][self.args.seq_length-1]
            s = weighted_pick(p)
            window = window[1:] + [s]
            sample += [s]
            prob.append(p)
        return sample, prob


