# Q5：启动故障诊断

正式测试器准备 `launch.env`、模型路径和设备路径，再运行教师的 `tools/sentry-preflight.sh`。该程序实际检查文件是否存在及是否可读，不需要 ROS 或真实相机。

| 场景 | 真实退出码 | 诊断 |
|---|---:|---|
| `ready` | 0 | 正常启动；stderr 仍有 NOTICE 提示 |
| `model-missing` | 10 | 模型文件不存在 |
| `camera-denied` | 20 | 模拟设备文件不可读 |

学生保存 `stdout.log`、`stderr.log`、`exit-code.txt`、`report.txt`。完整输出要求见 PDF；失败程序的原始退出码须保留，学生答题脚本整理完记录后正常退出 0。

运行 `bash tools/test.sh --question Q5 --verbose` 可以看到各场景的详细反馈。不要自行改测试器创建的模型或设备权限。
