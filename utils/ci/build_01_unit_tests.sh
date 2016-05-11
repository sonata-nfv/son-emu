#! /bin/bash -e
set -x

# Go to the 'root' directory
SCRIPT_DIR=$(dirname $(readlink -f $0))
BASE_DIR=$(readlink -f "${SCRIPT_DIR}/../..")
cd ${BASE_DIR}

# Remove old test output
rm -rf utils/ci/junit-xml/*

# Launch the unit testing on emuvim
py.test -v --junit-xml=utils/ci/junit-xml/pytest_emuvim.xml src/emuvim/test/unittests
