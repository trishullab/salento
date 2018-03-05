## MAP Score

We want to use mean average precision (MAP) score to evaluate the results.
The MAP provides a single-figure measure of quality across recall levels, a good
reference can be found [here](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html).

### Metric Implemented

There are four metrics being implemented, which gives user the choice to pick the metrics.

1. [sum_raw] Sum over the raw probabilities in a sequence
2. [min_raw] Minimum of the raw probabilities in a sequence
3. [sum_llh] Sum over the log likelihood of probabilities in a sequence
4. [min_llh] Minimum over the log likelihood of probabilities in a sequence

## Metric Usage

```bash

usage: driver.py [-h] --data_file_forward DATA_FILE_FORWARD
                 [--data_file_backward DATA_FILE_BACKWARD] --metric_choice
                 {min_raw,sum_raw,sum_llh,min_llh}
                 [--test_data_file TEST_DATA_FILE] [--result_file RESULT_FILE]
                 [--direction {forward,bidirectional}]

Compute map score

optional arguments:
  -h, --help            show this help message and exit
  --data_file_forward DATA_FILE_FORWARD
                        Data file with forward raw probabilities
  --data_file_backward DATA_FILE_BACKWARD
                        Data file with backward raw probabilities
  --metric_choice {min_raw,sum_raw,sum_llh,min_llh}
                        Choose the metric to be applied
  --test_data_file TEST_DATA_FILE
                        Get anomaly keys from test_files
  --result_file RESULT_FILE
                        Write out the results in a file
  --direction {forward,bidirectional}
                        Choose type of combination
```

## Get probabilities for test data set

We want to apply different metrics on the salento test data. To achieve this we
want to have a separation of concerns, where the probability scores and the
metric applications are separated out.

There are two modes to query probabilities

1. Probabilities associated with calls
2. Probabilities associated with states

## Raw probabilities for the calls and states


A typical usage is ```python get_state_call_values.py --data_file  test.json  --model_dir train_model --result_file raw_prob.json```

The probabilities of states and calls are combined using the summation rules as given below.

```math

Pr(Call, States) = \sum_{i=0}^{i=n}{Pr(Call| States_i})*Pr(Call)}
```

where, n is maximum number of states combination available, so for a three stater binary vector, the total number of states = 6.

```bash
usage: get_state_call_values.py [-h] --data_file DATA_FILE --model_dir
                                MODEL_DIR [--result_file RESULT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --data_file DATA_FILE
                        input data file
  --model_dir MODEL_DIR
                        directory to load model from
  --result_file RESULT_FILE
                        write out result in json file


```

## Raw probabilities for the calls

A typical usage is ```python get_raw_call_values.py --data_file  test.json  --model_dir train_model --result_file raw_prob.json```

If the result file is not provided the probability scores is printed to console.

```bash

usage: get_raw_call_values.py  --data_file DATA_FILE --model_dir MODEL_DIR
                              [--result_file RESULT_FILE]

optional arguments:
  --data_file DATA_FILE
                        input test data file
  --model_dir MODEL_DIR
                        directory to load the model from
  --result_file RESULT_FILE
                        write out the result in json file

```
