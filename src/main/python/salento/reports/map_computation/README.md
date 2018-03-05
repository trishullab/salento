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

## Usage

```python

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
