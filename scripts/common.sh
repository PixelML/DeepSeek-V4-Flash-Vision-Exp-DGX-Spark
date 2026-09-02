#!/usr/bin/env bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-${REPO_ROOT}/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "configuration missing: ${ENV_FILE}; copy .env.example to .env" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

IMAGE_REF="ghcr.io/anemll/dspark-vllm-gx10:0.1.1@sha256:a83948492cf13df455170fb42885f5ef4db54fefe0feff0f841ecbff464ac9d8"
MODEL_REPO="deepseek-ai/DeepSeek-V4-Flash-Vision-Exp"
SERVED_MODEL_NAME="deepseek-v4-flash-vision-exp"
CONTAINER_NAME="dsv4-vision-exp-dspark"

required=(
  MODEL_DIR MODEL_REVISION HEAD_ADDR DIST_PORT NCCL_SOCKET_IFNAME NCCL_IB_HCA
  NCCL_IB_GID_INDEX API_PORT CONTEXT_LENGTH MAX_NUM_SEQS MAX_NUM_BATCHED_TOKENS
  KV_CACHE_DTYPE MTP_NUM_TOKENS
)

for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "required configuration is empty: ${name}" >&2
    exit 1
  fi
done

if [[ "${MTP_NUM_TOKENS}" != "6" ]]; then
  echo "MTP_NUM_TOKENS=${MTP_NUM_TOKENS} is not the verified value (6); the runtime" >&2
  echo "validator rejects any value below 5 or not divisible by 3 for this checkpoint." >&2
fi
