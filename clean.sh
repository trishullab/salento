#!/bin/bash
if [ $# -eq 1 -a -d "$1" ]; then
    dir=$1
    to_delete="config.pkl chars_vocab.pkl lda.pkl checkpoint model.ckpt*"
    for file in ${to_delete}
    do
        rm ${dir}/${file}
    done
fi
rm -f *.pyc
rm -f save/*
rm -f debug.log
rm -rf __pycache__
