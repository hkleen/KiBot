#!/bin/bash
# if [ $KI_RELEASE == "nightly" ]; then
#      export KIAUS_USE_NIGHTLY="7.0"
# fi
# PCBnew tests
pytest-3 -v --durations=0 -m "pcbnew and (not indep)" --test_dir=output
