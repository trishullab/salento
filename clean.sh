#!/bin/bash
if [ $# -eq 1 -a -d "$1" ]; then
    dir=$1
    to_delete="data.npy vocab.pkl config.pkl chars_vocab.pkl primes.pkl weights.h5"
    for file in ${to_delete}
    do
        rm ${dir}/${file}
    done
fi
rm -f *.pyc
rm -f plots/*
rm -f save/*
rm -f debug.log
rm -rf __pycache__
