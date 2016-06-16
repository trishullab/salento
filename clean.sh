#!/bin/bash
for dir in $(ls data); do
    rm -f data/${dir}/vocab.pkl
    rm -f data/${dir}/data.npy
done
rm -f *.pyc
rm -f plots/*
rm -f save/*
rm -f debug.log
rm -rf __pycache__
