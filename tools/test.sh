#!/bin/bash
# 在 Ubuntu 上使用和 GitHub Actions 相同的测试入口。
set -eu
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [ "$(uname -s)" != Linux ]; then
    printf '%s\n' '请在 Ubuntu 虚拟机中运行，或推送到 GitHub Actions 自测。无需 Docker。' >&2
    exit 2
fi
mkdir -p "$root/generated"
printf 'Linux Coursework 自测（默认显示小项和失败原因）\n答题目录：%s\n报告目录：%s\n\n' \
    "$root/src/main" "$root/generated"
if sudo python3 -u "$root/tools/run_tests.py" \
    --submission "$root/src/main" --results "$root/generated" "$@"; then
    test_status=0
else
    test_status=$?
fi
printf '\n报告保存在：%s\n' "$root/generated"
printf '%s\n' '只重跑 Q3：bash tools/test.sh --question Q3' \
    '查看全部执行输出：bash tools/test.sh --verbose'
exit "$test_status"
