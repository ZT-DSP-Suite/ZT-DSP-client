#!/usr/bin/env bash
# Repository-local self-check. Runs in the git root.
set -eu
root=$(git rev-parse --show-toplevel)
cd "$root"

PYTHONPATH=zt_dsp_py python -m pytest zt_dsp_py/tests -q
python -m py_compile fuzz/fuzz_frames.py
python -m ruff format --check zt_dsp_py
(cd zt_dsp_rs && cargo fmt --check)
echo "client self-check passed"
