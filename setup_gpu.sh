#!/usr/bin/env bash
# Provision a RunPod box and serve the subject model.
#
# EVERYTHING PERSISTENT GOES ON /workspace. On RunPod the container disk is
# wiped when you stop the pod; the volume disk mounted at /workspace survives
# stop/start and is only lost on terminate. So the venv, the HF cache and the
# repo all live there, and stopping the pod overnight costs pennies instead of
# a 20-minute reinstall.
#
# Disk you actually need: ~40GB container, ~60GB volume.
#   model weights (Qwen3.5-9B bf16)  ~18 GB   -> /workspace/hf
#   torch + vllm + CUDA libs         ~15 GB   -> /workspace/venv
set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen3.5-9B}"
PORT="${PORT:-8000}"
MAXLEN="${MAXLEN:-32768}"
WS="${WS:-/workspace}"

export HF_HOME="${HF_HOME:-$WS/hf}"
export HF_HUB_ENABLE_HF_TRANSFER=1
mkdir -p "$HF_HOME"

echo "== disk check =="
df -h "$WS" / | sed 's/^/  /'
avail=$(df -BG --output=avail "$WS" | tail -1 | tr -dc '0-9')
if [ "${avail:-0}" -lt 40 ]; then
  echo "!! only ${avail}GB free on $WS. Qwen3.5-9B needs ~18GB plus the venv."
  echo "   Resize the volume disk or you will fail mid-download."
  exit 1
fi

echo "== venv on the persistent volume =="
if [ ! -d "$WS/venv" ]; then
  python -m venv "$WS/venv"
fi
# shellcheck disable=SC1091
source "$WS/venv/bin/activate"
pip install -q --upgrade pip uv

echo "== installing vllm (torch backend auto-selected from the host driver) =="
# --torch-backend=auto picks cu128 / cu129 / cu130 to match the driver, which is
# what makes this survive a host whose CUDA does not match the template.
uv pip install -q vllm --torch-backend=auto || pip install -q vllm
uv pip install -q -r requirements.txt || pip install -q -r requirements.txt

echo "== versions =="
python -c "import torch; print(' torch', torch.__version__, '| cuda', torch.version.cuda, '| device', torch.cuda.get_device_name(0))"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader | sed 's/^/ /'

echo "== downloading $MODEL to $HF_HOME (not counted against your 16 hours) =="
uv pip install -q "huggingface_hub[cli,hf_transfer]" || pip install -q "huggingface_hub[hf_transfer]"
hf download "$MODEL" 2>/dev/null || huggingface-cli download "$MODEL"

echo "== is it dense or MoE? =="
python - "$MODEL" <<'PY'
import json, sys, glob, os
from huggingface_hub import snapshot_download
p = snapshot_download(sys.argv[1], allow_patterns=["config.json"])
cfg = json.load(open(os.path.join(p, "config.json")))
moe = any(k in cfg for k in ("num_experts", "n_routed_experts", "num_local_experts"))
print(f"  architecture: {cfg.get('architectures')}")
print(f"  layers: {cfg.get('num_hidden_layers')}  hidden: {cfg.get('hidden_size')}")
print(f"  MoE: {moe}" + ("   <-- memory maths differs; check before stage 4" if moe else ""))
PY

echo "== serving =="
# --reasoning-parser is what puts the chain of thought in `reasoning_content`.
# Without it you get <think> inline; backend.py handles both, but the parser is cleaner.
nohup vllm serve "$MODEL" \
  --port "$PORT" \
  --max-model-len "$MAXLEN" \
  --reasoning-parser qwen3 \
  --gpu-memory-utilization 0.90 \
  > "$WS/vllm.log" 2>&1 &

echo "waiting for the server (first load takes a few minutes)..."
for i in $(seq 1 120); do
  if curl -sf "http://localhost:${PORT}/v1/models" >/dev/null; then
    echo "server up on :${PORT}"; curl -s "http://localhost:${PORT}/v1/models"; echo
    echo
    echo "NEXT:  export OPENAI_API_KEY=EMPTY"
    echo "       python -m src.generate --n 3 --no-gate"
    exit 0
  fi
  sleep 10
done
echo "server did not come up. tail $WS/vllm.log:"; tail -40 "$WS/vllm.log"; exit 1
