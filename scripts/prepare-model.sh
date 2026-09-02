#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

echo "staging ${MODEL_REPO}@${MODEL_REVISION} into ${MODEL_DIR}"

mkdir -p "${MODEL_DIR}"

huggingface-cli download "${MODEL_REPO}" \
  --revision "${MODEL_REVISION}" \
  --local-dir "${MODEL_DIR}" \
  --local-dir-use-symlinks False

"${SCRIPT_DIR}/verify-model.py" "${MODEL_DIR}"
