# Salento
Salento is a statistical bug-detection framework based on the machine learning model used by [Bayou](https://github.com/capergroup/bayou).
For technical details about Salento refer to the paper
*Bayesian Specification Learning for Finding API Usage Errors*, FSE'17 ([link](https://dl.acm.org/citation.cfm?id=3106284))

## Requirements
- Python3 (Tested with 3.5.1)
- [Tensorflow](http://www.tensorflow.org) (Tested with 1.4)

## Training
To train a Salento model on a data file, say `DATA.json`:

1. Setup environment:
```
export PYTHONPATH=$PYTHONPATH:/path/to/salento/src/main/python
```

2. Ensure that the data is in the right JSON format using the schema file `doc/json_schemas/salento_input_schema.json`.

3. **(Optional.)** Extract evidences from the data:
```
python3 src/main/python/scripts/evidence_extractor.py DATA.json DATA-training.json
```
This will create a `DATA-training.json` after extracting evidences from each package in `DATA.json`. Run with `--help` for more options that you can use to filter the sequences selected for training.

4. Go to the model folder and start training with a model configuration:
```
cd src/main/python/salento/models/low_level_evidences
python3 train.py /path/to/DATA-training.json --config config.json
```
Run with `--help` to see a description of the model configuration options. Edit `config.json` as needed.

## Inference
To test a trained model on some test data:

1-3. Follow steps 1-3 above to produce a file `DATA-testing.json` with evidences.

4. Go to the aggregators folder and run one of the aggregators on the test data:
```
cd src/main/python/salento/aggregators
python3 sequence_aggregator.py --data_file /path/to/DATA-testing.json --model_dir /path/to/model/directory
```
The model directory should contain the trained model's files, such as `checkpoint`, `config.json`, etc.
