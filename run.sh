#!/bin/env bash

SECRET=`cat ./.SECRET`

source .venv/bin/activate
python3 ./main.py ${SECRET}
