#!/bin/bash
# Q8：repair 时识别并停止采集器、修复 HTTP 服务；cleanup 时停止修复后的服务。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
set -eu
input=${1:?需要输入目录}
output=${2:?需要输出目录}

action=${3:-repair}

source "$input/process.env"
mkdir -p "$output"
url="http://127.0.0.1:$TARGET_PORT/status"

if [ "$action" = cleanup ]; then
    pid=$(cat "$output/service/pid")
    kill -TERM "$pid"
    for i in {1..30}; do
        if ! curl -s --connect-timeout 1 --max-time 1 "$url" > /dev/null; then
            exit 0
        fi
        sleep 0.1
    done
    exit 1
fi

if [ "$action" != repair ]; then
    exit 1
fi

user=$(ps -p "$TARGET_PID" -o user= | awk '{print $1}')
state=$(ps -p "$TARGET_PID" -o stat= | awk '{print $1}')
command=$(ps -ww -p "$TARGET_PID" -o args=)
printf 'pid=%s\nuser=%s\nstate=%s\ncommand=%s\n' "$TARGET_PID" "$user" "$state" "$command" > "$output/process.txt"
cat "$WORKER_LOG" > "$output/collector-sample.log"

kill -TERM "$TARGET_PID"
for i in {1..20}; do
    if ! kill -0 "$TARGET_PID" 2>/dev/null; then
        break
    fi
    sleep 0.1
done

kill -TERM "$SERVICE_PID"
for i in {1..20}; do
    if ! kill -0 "$SERVICE_PID" 2>/dev/null; then
        break
    fi
    sleep 0.1
done

printf 'bind=127.0.0.1\nport=%s\nroute=/status\n' "$TARGET_PORT" > "$output/server.conf"
bash "$START_TOOL" "$output/server.conf" "$output/service"

ready=0
for i in {1..30}; do
    if curl -s --connect-timeout 1 --max-time 1 -o "$output/http-body.txt" -w '%{http_code}\n' "$url" > "$output/http-status.txt"; then
        if [ "$(cat "$output/http-status.txt")" = 200 ]; then
            ready=1
            break
        fi
    fi
    sleep 0.1
done
test "$ready" -eq 1
test "$(cat "$output/http-body.txt")" = 'SENTRY READY'
