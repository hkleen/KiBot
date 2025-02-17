#!/bin/bash
# if [ $KI_RELEASE == "nightly" ]; then
#      export KIAUS_USE_NIGHTLY="7.0"
# fi
set -e
# Eeschema tests
pytest-3 -v --durations=0 -m "eeschema and (not indep)" --test_dir=output
# KiCad2Step tests and others
pytest-3 -v --durations=0 -m "slow and (not (pcbnew or eeschema or indep))" --log-cli-level debug --test_dir=output
