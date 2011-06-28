#!/bin/sh

ROOT=`pwd`
program="${ROOT}/bin/yaturl_service.py"

export PYTHONPATH="include:$PYTHONPATH"

# clean old bytecode files
find "${ROOT}" -name '*.pyc' -delete

# start service
python $program -f
