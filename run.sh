#!/bin/bash
############################################################

set -eu

THIS=$( readlink -f "$0" )
THIS_DIR=$(dirname "${THIS}")


source python-virtualenv/bin/activate

python3 ${THIS_DIR}/file_sync.py $@