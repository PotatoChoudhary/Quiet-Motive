#!/usr/bin/env bash
# Provision a fresh single-A100 box and serve the subject model.
# Runpod / Vast: pick a PyTorch 2.x CUDA 12.x image, 80GB A100, >=200GB disk.
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen3.5-9B}"     # 4B / 9B / 27B all fit an 80GB A100 in bf16
PORT="${PORT:-8000}"
MAXLEN="${MAXLEN:-32768}"

echo "== installing =="
pip install -q --upgrade pip
pip install -q vllm
pip install -q -r requirements.txt

echo "== downloading $MODEL (not counted against your 16 hours) =="
pip install -q "huggingface_hub[cli]"
hf download "$MODEL" || huggingface-cli download "$MODEL"

echo "== serving =="
# --reasoning-parser is what puts the chain of thought in `reasoning_content`.
# Without it you get <think> inline; backend.py handles both, but the parser is cleaner.
nohup vllm serve "$MODEL" \
  --port "$PORT" \
  --max-model-len "$MAXLEN" \
  --reasoning-parser qwen3 \
  --gpu-memory-utilization 0.90 \
  > vllm.log 2>&1 &

echo "waiting for the server (first load takes a few minutes)..."
for i in $(seq 1 120); do
  if curl -sf "http://localhost:${PORT}/v1/models" >/dev/null; then
    echo "server up on :${PORT}"; curl -s "http://localhost:${PORT}/v1/models"; echo
    exit 0
  fi
  sleep 10
done
echo "server did not come up. tail vllm.log:"; tail -40 vllm.log; exit 1
