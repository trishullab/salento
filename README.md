# char-rnn-keras
Multi-layer LSTMs for character-level language models using Keras.

Inspired from [char-rnn-tensorflow](https://github.com/sherjilozair/char-rnn-tensorflow)

# Requirements
- [Keras](http://keras.io)
- h5py for Python, to save models

# Basic Usage
To train with default parameters on the tinyshakespeare corpus, run `python train.py`.

To sample from a checkpointed model, `python sample.py`.
