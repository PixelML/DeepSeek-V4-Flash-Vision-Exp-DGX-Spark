#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! "$1" =~ ^[01]$ ]]; then
  echo "usage: $0 <node-rank: 0|1>" >&2
  exit 2
fi

NODE_RANK="$1"
HEADLESS="${NODE_RANK}"  # rank 1 (worker) runs headless; rank 0 (head) does not
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

[[ -f "${MODEL_DIR}/model.safetensors.index.json" ]] || {
  echo "model checkpoint missing: ${MODEL_DIR}" >&2
  exit 1
}

docker image inspect "${IMAGE_REF}" >/dev/null

if docker ps -a --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
  docker rm --force "${CONTAINER_NAME}" >/dev/null
fi

mkdir -p "${REPO_ROOT}/cache/huggingface"

docker run --detach \
  --name "${CONTAINER_NAME}" \
  --restart unless-stopped \
  --network host \
  --ipc host \
  --gpus all \
  --shm-size 32g \
  --ulimit memlock=-1:-1 \
  --cap-add IPC_LOCK \
  --device /dev/infiniband \
  --log-opt max-size=100m \
  --log-opt max-file=5 \
  --env NODE_RANK="${NODE_RANK}" \
  --env HEADLESS="${HEADLESS}" \
  --env DIST_INIT_ADDR="${HEAD_ADDR}:${DIST_PORT}" \
  --env API_PORT="${API_PORT}" \
  --env CONTEXT_LENGTH="${CONTEXT_LENGTH}" \
  --env MAX_NUM_SEQS="${MAX_NUM_SEQS}" \
  --env MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS}" \
  --env KV_CACHE_DTYPE="${KV_CACHE_DTYPE}" \
  --env MTP_NUM_TOKENS="${MTP_NUM_TOKENS}" \
  --env VLLM_USE_BREAKABLE_CUDAGRAPH="${VLLM_USE_BREAKABLE_CUDAGRAPH}" \
  --env GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION}" \
  --env HF_HUB_OFFLINE=1 \
  --env TRANSFORMERS_OFFLINE=1 \
  --env NCCL_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME}" \
  --env GLOO_SOCKET_IFNAME="${NCCL_SOCKET_IFNAME}" \
  --env NCCL_NET=IB \
  --env NCCL_IB_DISABLE=0 \
  --env NCCL_IB_HCA="${NCCL_IB_HCA}" \
  --env NCCL_IB_GID_INDEX="${NCCL_IB_GID_INDEX}" \
  --env DSPARK_ENABLE_ISSUE141_SPARSE_MLA_CHUNK=1 \
  --env DSPARK_ENABLE_ISSUE138_RESPONSES_HISTORY_COMPAT=1 \
  --env ENABLE_VLLM_GB10_PATCH=1 \
  --mount type=bind,src="${MODEL_DIR}",dst=/models/dsv4-vision-exp,readonly \
  --mount type=bind,src="${REPO_ROOT}/cache/huggingface",dst=/root/.cache/huggingface \
  "${IMAGE_REF}" \
  --model-path /models/dsv4-vision-exp \
  --served-model-name "${SERVED_MODEL_NAME}" \
  --tp 2 \
  --nnodes 2 \
  --node-rank "${NODE_RANK}" \
  --dist-init-addr "${DIST_INIT_ADDR}" \
  --kv-cache-dtype "${KV_CACHE_DTYPE}" \
  --speculative-algorithm DSPARK \
  --mtp-num-tokens "${MTP_NUM_TOKENS}" \
  --max-num-seqs "${MAX_NUM_SEQS}" \
  --max-num-batched-tokens "${MAX_NUM_BATCHED_TOKENS}" \
  --context-length "${CONTEXT_LENGTH}" \
  --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
  --host 0.0.0.0 \
  --port "${API_PORT}"

echo "started ${CONTAINER_NAME} rank=${NODE_RANK} headless=${HEADLESS}"
