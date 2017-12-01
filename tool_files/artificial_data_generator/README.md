## Dependencies

Tested with Python 2.7.6

## Generating a dataset

1. Create a configuration JSON file that lists the characteristics of the generated data that can be fed into Salento (either for training or testing). The schema file `config_schema.json` contains descriptions of the various configuration options. An example configuration file is given in `example_config_1.json`. The description of the various patterns can be found in the source file comments in `generate_api_traces.py`. 
2. Run `python generate_api_traces.py -h` to get information on how to generate artificial Salento data.

## Notes on current anomaly injection

Currently, the way anomalies are injected are are follows:
1. Only one sequence in a unit will have an anomaly, it is always the last sequence of the unit named "anomalous". 
2. Number of units with anomalies = value of "num_anomalies" in the input configuration. 
3. Each anomaly changes exactly one pairing so that there is one mismatched pairing: e.g., if "a" and "b" are a pair in a sequence, then "b" would be removed. 

## Example training and testing dataset generation

To generate a sample training dataset named `simple_training_1.json`, use `training_config_1.json` as follows:

```
python generate_api_traces.py --input_file training_config_1.json --output_file simple_training_1.json
```

To generate a sample testing dataset named `simple_testing_1.json`, use `testing_config_1.json` as follows:

```
python generate_api_traces.py --input_file testing_config_1.json --output_file simple_testing_1.json
```

## Contact

Email Vineeth Kashyap (vkashyap@grammatech.com) for any questions/concerns/feature requests. 