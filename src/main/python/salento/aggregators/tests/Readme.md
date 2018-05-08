# Tests

The tests in this directory would ensure that if the changes to the model or training configuration produces wild deviations its gets tracked.

## Setup

1. Environment

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/salento/src/main/python
```

### Variance Tests

The goal of the variance tests is to compute relative standard deviation for the model
across different iteration.

#### Usage

```bash
usage: test_relative_std.py  --data_file DATA_FILE --model_dir MODEL_DIR
                            [--iterations ITERATIONS]

optional arguments:
  -h, --help           
  --data_file DATA_FILE
                        input data file after evidence extraction
  --model_dir MODEL_DIR
                        directory to load model from
  --iterations ITERATIONS
                        Number of iteration to run
```

The results for the tests prints the smallest, biggest and average relative standard deviations. The ```--iterations``` controls the number of time the experiment is repeated.
