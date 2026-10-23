# 输入样例

这里的文件帮助你理解题目输入、练习命令。正式 CI 会自行生成测试数据和临时环境；这些静态样例不参与评分，不要修改或提交练习结果。

| 目录 | 对应题目 | 可以观察什么 |
|---|---|---|
| `q1/` | 目录定位与读取 | 隐藏的 `.robot-id`、交接说明和欢迎文本 |
| `q3/` | 文件整理 | 正式配置、草稿、脚本和临时缓存 |
| `q4/` | 日志分析 | 启动日志、运行日志，以及消息中出现 ERROR 的 INFO 行 |
| `q5/` | 启动故障诊断 | 三种启动场景、退出码和输出记录说明 |

例如，在仓库根目录用 Q4 样例练习已经实现的脚本：

```bash
mkdir -p generated/practice-q4
bash src/main/q4.sh "$(pwd)/samples/q4" "$(pwd)/generated/practice-q4"
cat generated/practice-q4/errors.log
```

这只执行一次脚本，不自动评分，也不等价于通过 Q4。完整自测用 `bash tools/test.sh --question Q4`，正式成绩看 GitHub Actions。

Q5 的 `launch.env` 和检查用文件、Q6 的 Debian 包、Q7 的 SSH 连接、Q8 的进程与 HTTP 服务、Bonus 的 tmux 参数由测试器准备。不要尝试仅凭这些静态文件运行全部题目。所有实际测试场景及生成规则公开在 `tests/coursework.py`。
