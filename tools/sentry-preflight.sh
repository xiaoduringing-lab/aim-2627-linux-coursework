#!/bin/bash
# Provided startup preflight: check actual file existence and read access.
# Interface: bash sentry-preflight.sh MODEL_FILE CAMERA_FILE
set -eu
model=${1:?需要模型文件路径}
camera=${2:?需要设备文件路径}
printf '%s\n' 'START sentry preflight'
printf 'model=%s\ncamera=%s\n' "$model" "$camera"
if [ ! -f "$model" ]; then
    printf 'ERROR MODEL_MISSING: %s\n' "$model" >&2
    exit 10
fi
printf '%s\n' 'MODEL_READY'
if [ ! -r "$camera" ]; then
    printf 'ERROR CAMERA_DENIED: %s\n' "$camera" >&2
    exit 20
fi
printf '%s\n' 'READY'
printf '%s\n' 'NOTICE: training preflight only' >&2
