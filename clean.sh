#!/bin/bash
for dir in $(ls data); do
    rm -f data/${dir}/vocab.pkl
    rm -f data/${dir}/data.npy
    rm -f save/*
    rm -rf __pycache__
done
