#!/bin/bash

if (( "$#" != 1)); then echo "You must provide path to python executable"; exit 1; fi

PYTHON_PATH=$1

sudo apt-get install ffmpeg curl youtube-dl
rc=$?; if (( $rc != 0)); then exit $rc; fi

$PYTHON_PATH -m venv env  && source ./env/bin/activate && pip install -r requirements.txt
rc=$?; if (( $rc != 0)); then exit $rc; fi

echo "Successfully installed all dependencies"
