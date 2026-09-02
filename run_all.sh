#!/usr/bin/env bash
# The whole pipeline, with the gates in the right places.
# Each stage exits non-zero if its gate fails. Do not --force past a gate.
set -euo pipefail
export OPENAI_API_KEY="${OPENAI_API_KEY:-EMPTY}"

echo; echo "### smoke test (3 per arm, no gate) — checks the server talks and CoT arrives"
python -m src.generate --n 3 --no-gate || { echo "backend is not answering. Check vllm.log."; exit 2; }
echo "smoke ok. Eyeball the numbers above, then continue."

echo; echo "### stage 1: full trajectory collection"
python -m src.generate || { echo "GATE 1 FAILED. Stop. Fix src/experiment.py."; exit 2; }

echo; echo "### stage 2: probe library + blind forensic investigator"
python -m src.forensics || { echo "GATE 2 FAILED. Fix the investigator prompt."; exit 2; }

echo; echo "### stage 3: the number, controls, figures"
python -m src.analyze

echo
echo "GATE 3 has passed by definition — you now have a number."
echo "Experiments are frozen. Next: python -m src.inspect_cli --export notes.md"
