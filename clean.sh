#!/bin/bash
to_delete="data.npy vocab.pkl config.pkl chars_vocab.pkl primes.pkl weights.h5"
for file in ${to_delete}
do
    find . -iname ${file} | xargs rm -f
done
rm -f *.pyc
rm -f plots/*
rm -f save/*
rm -f debug.log
rm -rf __pycache__
