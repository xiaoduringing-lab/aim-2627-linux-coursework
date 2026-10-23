#!/bin/bash
# Q5：运行 launch.env 给定的启动前检查，保存 stdout/stderr、真实退出码和诊断报告。
# 完整接口与验收规格见 Problem.pdf。只修改本文件，不修改测试或工具。
set -eu
input=${1:?需要输入目录}
output=${2:?需要输出目录}

source "$input/launch.env"
mkdir -p "$output"

if bash "$LAUNCH_TOOL" "$MODEL_PATH" "$CAMERA_PATH" > "$output/stdout.log" 2> "$output/stderr.log"; then
    code=0
else
    code=$?
fi

echo "$code" > "$output/exit-code.txt"
case "$code" in
    0)
        result=SUCCESS
        reason=NONE
        ;;
    10)
        result=FAILED
        reason=MODEL_MISSING
        ;;
    20)
        result=FAILED
        reason=CAMERA_DENIED
        ;;
    *)
        exit "$code"
        ;;
esac

printf 'result=%s\nexit_code=%s\nreason=%s\n' "$result" "$code" "$reason" > "$output/report.txt"
