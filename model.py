import tensorflow as tf
from tensorflow.python.ops import rnn_cell
from tensorflow.python.ops import seq2seq

from cells import TopicRNNCell, TopicLSTMCell
import decoder
import numpy as np

class Model():
    def __init__(self, args, infer=False):
        self.args = args
        if infer:
            args.batch_size = 1
            args.seq_length = 1

        self.cell = TopicRNNCell(args.rnn_size)

        self.inputs = [tf.placeholder(tf.int32, [args.batch_size], name='inputs{0}'.format(i))
                for i in range(args.seq_length)]
        self.topics = [tf.placeholder(tf.float32, [args.batch_size, args.ntopics], name='topics{0}'.format(i))
                for i in range(args.seq_length)]
        self.targets = tf.placeholder(tf.int32, [args.batch_size, args.seq_length])
        self.initial_state = self.cell.zero_state(args.batch_size, tf.float32)

        projection_w = tf.get_variable("projection_w", [args.rnn_size, args.vocab_size])
        projection_b = tf.get_variable("projection_b", [args.vocab_size])

        outputs, last_state = decoder.embedding_rnn_decoder(self.inputs, self.topics, self.initial_state, self.cell, args.vocab_size, args.rnn_size, (projection_w,projection_b), feed_previous=infer)
        output = tf.reshape(tf.concat(1, outputs), [-1, args.rnn_size])
        self.logits = tf.matmul(output, projection_w) + projection_b
        self.probs = tf.nn.softmax(self.logits)
        self.cost = seq2seq.sequence_loss([self.logits],
                [tf.reshape(self.targets, [-1])],
                [tf.ones([args.batch_size * args.seq_length])])
        self.final_state = last_state
        self.train_op = tf.train.AdamOptimizer(args.learning_rate).minimize(self.cost)

        var_params = [np.prod([dim.value for dim in var.get_shape()]) for var in tf.trainable_variables()]
        if not infer:
            print('Model parameters: {}'.format(np.sum(var_params)))

    def probability(self, sess, sample, topic, vocab=None): # if vocab is None we assume it has already been applied
        prob = []
        state = self.cell.zero_state(1, tf.float32).eval()
        t = np.array(np.reshape(topic, (1, -1)), dtype=np.float)
        for char in sample:
            x = np.zeros((1,), dtype=np.int32)
            x[0] = vocab[char] if vocab is not None else char
            feed = {self.initial_state: state, self.inputs[0].name: x, self.topics[0].name: t}
            [p, state] = sess.run([self.probs, self.final_state], feed)
            prob.append(p[0])
        return prob

    def predict(self, sess, prime, topic, chars, vocab):

        def weighted_pick(weights):
            t = np.cumsum(weights)
            s = np.sum(weights)
            return(int(np.searchsorted(t, np.random.rand(1)*s)))

        state = self.cell.zero_state(1, tf.float32).eval()
        t = np.array(np.reshape(topic, (1, -1)), dtype=np.float)
        for char in prime:
            x = np.zeros((1,), dtype=np.int32)
            x[0] = vocab[char]
            feed = {self.initial_state: state, self.inputs[0].name: x, self.topics[0].name: t}
            [probs, state] = sess.run([self.probs, self.final_state], feed)

        dist = probs[0]
        prediction = chars[weighted_pick(dist)]
        return dist, prediction
