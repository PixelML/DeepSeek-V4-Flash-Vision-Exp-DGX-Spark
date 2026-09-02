#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "${SCRIPT_DIR}/common.sh"

for host in "${HEAD_HOST}" "${WORKER_HOST}"; do
  ssh "${host}" "test -f '${REMOTE_INSTALL_DIR}/.env'"
  ssh "${host}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/verify-model.py '${MODEL_DIR}'"
  ssh "${host}" "docker image inspect '${IMAGE_REF}' >/dev/null"
done

ssh "${HEAD_HOST}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/stop-node.sh"
ssh "${WORKER_HOST}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/stop-node.sh"

# The worker must be waiting before the head initializes distributed setup.
# Starting the head first leaves it with nothing to bind to.
ssh "${WORKER_HOST}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/start-node.sh 1"
ssh "${HEAD_HOST}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/start-node.sh 0"

echo "waiting for the DeepSeek-V4-Flash-Vision-Exp API"
for attempt in $(seq 1 120); do
  if ssh "${HEAD_HOST}" "cd '${REMOTE_INSTALL_DIR}' && ./scripts/probe-api.py" \
    | grep -q "${SERVED_MODEL_NAME}"; then
    echo "API ready after attempt ${attempt}"
    exit 0
  fi

  for host in "${HEAD_HOST}" "${WORKER_HOST}"; do
    if ! ssh "${host}" "docker ps --format '{{.Names}}'" \
      | grep -qx "${CONTAINER_NAME}"; then
      echo "${host} exited before readiness" >&2
      ssh "${host}" "docker logs --tail 200 '${CONTAINER_NAME}'" || true
      exit 1
    fi
  done
  sleep 15
done

echo "timed out waiting for the DeepSeek-V4-Flash-Vision-Exp API" >&2
exit 1
