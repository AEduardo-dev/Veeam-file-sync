#!/bin/bash
############################################################

set -eu

THIS=$( readlink -f "$0" )
THIS_DIR=$(dirname "${THIS}")

############################################################

rm -rf ./python-virtualenv || true

############################################################

# Create virtualenv
virtualenv="python3 -m virtualenv -p python3"
$virtualenv --always-copy python-virtualenv
source python-virtualenv/bin/activate

############################################################

# Install package into virtualenv
python3 -m pip install -r ${THIS_DIR}/requirements.txt

############################################################

# Remove unnecessary things from the venv
deactivate
find python-virtualenv -name __pycache__ -exec rm -r {} +

