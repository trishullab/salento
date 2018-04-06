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

The script `get_raw_prob.py` provides interface to get predicted probabilities
to get call and states information for each point. To get calls probabilities user should
pass the filename for  `--call_prob_file` and to gets states probabilities  user should
pass the filename for `--state_prob_file` and if both are passed then we get probabilities associated with calls and states. 


```bash
usage: get_raw_prob.py [-h] --data_file DATA_FILE --model_dir MODEL_DIR
                       [--call_prob_file CALL_PROB_FILE]
                       [--state_prob_file STATE_PROB_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --data_file DATA_FILE
                        input test data file with evidences
  --model_dir MODEL_DIR
                        directory to load the model from
  --call_prob_file CALL_PROB_FILE
                        Write out the call probability in json file
  --state_prob_file STATE_PROB_FILE
                        write out the state probability in json file

```

#### Json Schema for th output

```json
{
	"title": "Schema File for representation of the probability values",
	"type": "object",
	"properties": {
		"type": "object",
		"description": "Each Procedure/Project",
		"properties": {
			"type": "object",
			"description": "Each Sequence in the procedure",
			"properties": {
				"type": "object",
				"description": "Each Call/State",
				"properties": {
					"type": "number",
					"description": "raw probability values"
				}
			}
		}
	}
}
```
