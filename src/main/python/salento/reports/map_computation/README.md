# Introduction

The scripts in this directory query a salento trained model and apply anomaly metric on them. There are two use case scenarios `anomaly score` and other is to compute `mean average precision`.

The content of the folder are

```bash
├── anomaly_score.py # anomaly score implementation script
├── compute_map.py # map computation driver
├── data_parser.py
├── driver_anomaly_score.py # main driver to get anomaly score
├── get_raw_prob.py
├── metric.py
├── README.md
└── reverse_sequence.py

```

## Metric Implemented

There are four metrics being implemented, which gives user the choice to pick the metrics.

1. [sum_raw] Sum over the raw probabilities in a sequence
2. [min_raw] Minimum of the raw probabilities in a sequence
3. [sum_llh] Sum over the log likelihood of probabilities in a sequence
4. [min_llh] Minimum over the log likelihood of probabilities in a sequence


## Anomaly Score

To get anomaly score for a given test file, the user should use the script `driver_anomaly_score.py`, the schema of the output and usage is given below.
Its worth noting that script takes in `reverse` training option which makes it bidirectional.

### Json Schema

```json
{
	"title": "Schema File for anomaly score",
	"type": "array",
	"items": {
		"type": "object",
		"properties": {
			"Anomaly Score": {
				"type": "number",
				"description": "The aggregated score"
			},
			"Locations": {
				"type": "array",
				"description": "The location of all the calls in path",
				"item": {
					"type": "string"
				}
			},
			"Index List": {
				"type": "array",
				"description": "All the indicies of the lowest prob value",
				"item": {
					"type": "integer"
				}
			},
			"Events": {
				"type": "array",
				"description": "All the call/states in path",
				"item": {
					"type": "string"
				}
			}
		}
	}
}
```

### Usage

The usage for the `driver_anomaly_score.py` is as follows

```bash

python3 salento/src/main/python/salento/reports/map_computation/driver_anomaly_score.py \
 --test_file test_data.json \
 --model_forward ~/train_model/forward_model/ \
 --model_reverse ~/train_model/reverse_model/ \
 --result_file anomaly_score_test_state.json  \
 --state True  
```

If user wants to get call probability they should set `--call True`. We can only query one of them.

```bash
usage: driver_anomaly_score.py [-h] --test_file TEST_FILE --model_forward
                               MODEL_FORWARD [--model_reverse MODEL_REVERSE]
                               [--call CALL] [--state STATE]
                               [--metric_choice {min_raw,sum_raw,sum_llh,min_llh}]
                               [--result_file RESULT_FILE]

optional arguments:
  -h, --help            show this help message and exit
  --test_file TEST_FILE
                        input test file
  --model_forward MODEL_FORWARD
                        directory to load the model from
  --model_reverse MODEL_REVERSE
                        directory to load the model from
  --call CALL           Set True to compute anomaly score using call
                        probability
  --state STATE         Set True to compute anomaly score using states
                        probability
  --metric_choice {min_raw,sum_raw,sum_llh,min_llh}
                        Choose the metric to be applied
  --result_file RESULT_FILE
                        File to write the anomaly score

```


## MAP Score

We want to use mean average precision (MAP) score to evaluate the results.
The MAP provides a single-figure measure of quality across recall levels, a good
reference can be found [here](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html).

```bash

usage: compute_map.py [-h] --data_file_forward DATA_FILE_FORWARD
                      [--data_file_backward DATA_FILE_BACKWARD]
                      --metric_choice {min_raw,sum_raw,sum_llh,min_llh}
                      [--test_data_file TEST_DATA_FILE]
                      [--result_file RESULT_FILE]
                      [--direction {forward,bidirectional}]

Compute map scores

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

## Getting the raw probabilities for test data set

The script `get_raw_prob.py` provides interface to get predicted probabilities
to get call and states information at each point along a trace path. To get calls probabilities user should pass the filename for  `--call_prob_file` and to gets states probabilities  user should pass the filename for `--state_prob_file` and if both are passed then we get probabilities associated with calls and states.



```bash
usage: get_raw_prob.py [-h] --data_file DATA_FILE --model_dir MODEL_DIR
                       [--call_prob_file CALL_PROB_FILE]
                       [--state_prob_file STATE_PROB_FILE]
  --data_file DATA_FILE
                        input test data file with evidences
  --model_dir MODEL_DIR
                        directory to load the model from
  --call_prob_file CALL_PROB_FILE
                        Write out the call probability in json file
  --state_prob_file STATE_PROB_FILE
                        write out the state probability in json file

```

#### Json Schema for the output

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
