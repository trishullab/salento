# salento
Statistical bug-finding framework for Java/Android applications

Latent Dirichlet Allocation (LDA) over a training dataset of traces generated from [driver](https://bitbucket.org/vijayaraghavan-murali/salento-driver-android).

Recurrent neural networks (RNN) for symbol-level language model using Tensorflow.
(inspired from [char-rnn-tensorflow](https://github.com/sherjilozair/char-rnn-tensorflow))

Kullback-Leibler (KL) Divergence computation for a set of program locations.

# Requirements
- Python3 (Tested with 3.5.1)
- [sklearn](http://scikit-learn.org/stable) for LDA
- [Tensorflow](http://www.tensorflow.org)

# Basic Usage
To run LDA and produce topic distributions for each package in a dataset DATA.json, run `python3 lda.py --input_file DATA.json` and follow instructions.

To train with default parameters on a training data file DATA-training.json, run `python3 train.py DATA-training.json`.

To predict the next symbol using a saved model, `python3 predict.py`.

To compute KL-Divergence values for a testing data set DATA-testing.json, `python3 kld.py DATA-testing.json`
