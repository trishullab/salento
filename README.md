# Salento
Salento is a statistical bug-detection framework for Android/Java applications.
For technical details refer to the paper

Bayesian Specification Learning for Finding API Usage Errors, FSE'17 ([link](https://dl.acm.org/citation.cfm?id=3106284))

Salento consists of the following parts:

1. A data extraction tool based on soot, called the driver, for extracting API sequences from Java bytecode and Android.

2. Latent Dirichlet Allocation (LDA) over a training dataset of traces generated from driver.

3. Recurrent neural networks (RNN) for symbol-level language model* using Tensorflow

4. Kullback-Leibler (KL) Divergence computation for a set of program locations.

## Requirements
- Python 3 (Tested with 3.5.1)
- [scikit-learn](http://scikit-learn.org/stable) module for Python 3
- [Tensorflow](http://www.tensorflow.org) (Tested with 0.12)
- JDK 1.8



## Setup and Usage
#### Driver
The soot version distributed (2.5.0) has been compiled with JDK "1.7.0_80" and is compatible with JRE (build 1.7.0_80-b15).

1. Setup two environment variables as follows

    ```
    export SALENTO_ANDROID_HOME=/path/to/salento-driver-android
    export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk1.7.0_80.jdk/Contents/Home
    ```

    Note: there should be a "jre" folder within `$JAVA_HOME`

2. Compile the driver by running
    ```
    cd $SALENTO_ANDROID_HOME
    ant
    ```

3. (Optional) Add `$SALENTO_ANDROID_HOME` to `$PATH` for the "driver" script

4. Run the driver by executing:
    
    `driver <app>.apk <optional soot args>`
    
#### Statistical Model

To run LDA and produce topic distributions for each package in a dataset DATA.json, run `python3 lda.py --input_file DATA.json` and follow instructions.

To train with default parameters on a training data file DATA-training.json, run `python3 train.py DATA-training.json`.

To predict the next symbol using a saved model, `python3 predict.py`.

To compute KL-Divergence values for a testing data set DATA-testing.json, `python3 kld.py DATA-testing.json`
    


*Inspired from [char-rnn-tensorflow](https://github.com/sherjilozair/char-rnn-tensorflow)
