#!/bin/bash
# 接口：bash start-service.sh CONFIG STATE_DIRECTORY
# 只负责启动，等待就绪、请求和停止由学生完成。
set -eu
config=${1:?需要配置文件}
state=${2:?需要服务状态目录}
mkdir -p "$state"
tool_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 "$tool_dir/service.py" "$config" > "$state/service.log" 2>&1 < /dev/null &
printf '%s\n' "$!" > "$state/pid"
