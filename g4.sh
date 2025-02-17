#!/bin/bash
# if [ $KI_RELEASE == "nightly" ]; then
#      export KIAUS_USE_NIGHTLY="7.0"
# fi
# Independent tests, should be the same for any KiCad version
pytest-3 -v --durations=0 -m "indep" --test_dir=output
