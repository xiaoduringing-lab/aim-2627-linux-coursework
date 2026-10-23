# AIM 2627 Linux Coursework - 哨兵开发机交接

**先读 [Problem.pdf](Problem.pdf)，再填写 `src/main/` 中的 Bash 脚本。** PDF 是任务、接口和评分要求的唯一学生题面。本 README 说明环境、仓库结构、自测和提交流程。

正式成绩只由 GitHub Actions 产生：8 道必做题共 100 分，Bonus 额外最多 10 分。通过条件是 **必做至少 60 分，且 Q7、Q8 的全部检查通过**。所有评分测试公开。

## 1. 从哪里开始

1. 在 [课程模板仓库](https://github.com/unnc-aim/aim-2627-linux-coursework) 点击 **Use this template → Create a new repository**，创建自己的仓库。不要直接在教师仓库作答，也不要用 Fork 代替模板创建。
2. 克隆你创建的仓库，在 main 分支开发：

   ```bash
   git clone https://github.com/<你的用户名>/<你的仓库名>.git
   cd <你的仓库名>
   ```

3. 打开 [Problem.pdf](Problem.pdf)，从 Q1 开始填写对应的 `src/main/q1.sh`。Q2–Q8 分别对应 `q2.sh`–`q8.sh`，选做题对应 `bonus.sh`。
4. 每题骨架已提供参数读取和 `set -eu`。实现时删除末尾的提示语句和 `exit 77`，填写自己的命令。
5. 自测或推送到 GitHub CI，按反馈修改。最后提交对应的 Actions run 链接。

`exit 77` 表示“未实现”，该题记 0 分。原始模板可以初始化成功，但不代表通过考核；开始答题后，未达到通过条件的完整 CI 会失败，仍会显示分项成绩。

## 2. 各个目录做什么

```text
仓库根目录/
├── README.md                    # 环境、使用方式和提交步骤
├── Problem.pdf                  # 完整题面，只读
├── src/main/
│   ├── q1.sh … q8.sh            # 必做题：你填写的脚本
│   └── bonus.sh                 # 选做题：你填写的脚本
├── samples/                     # 静态输入样例，帮助阅读和练习
├── tests/
│   ├── coursework.py            # 全部公开场景、断言和评分权重
│   └── skeleton-sha256.json     # 原始骨架识别数据
├── tools/                       # 测试入口和教师训练程序
├── .github/workflows/ci.yml     # GitHub Actions 自动评估
├── .vscode/                     # 推荐的编辑器设置
└── generated/                   # 自测生成的成绩与产物，自动创建
```

| 内容 | 你需要做什么 | 是否提交修改 |
|---|---|---|
| `src/main/q1.sh`–`q8.sh`、`bonus.sh` | 阅读骨架并填写命令 | **是，这是答题区域** |
| `Problem.pdf`、`README.md` | 阅读题目与操作说明 | 否 |
| `samples/` | 打开样例文件，理解输入 | 否 |
| `tests/` | 可阅读测试和权重，理解反馈 | 否 |
| `tools/`、`.github/`、其余配置 | 使用提供的入口 | 否 |
| `generated/` | 查看本地结果 | 否，已被 Git 忽略 |
| `.agent-sessions/` | 可选 AI 会话归档 | 可提交，归档不计分 |

保留全部 9 个答题文件，未做的题保留骨架。不要删除、改名、增加其他答题文件或换成符号链接。答题脚本由 Bash 调用，不需要给它们增加执行权限。

## 3. 答题脚本如何运行

Q1–Q7 接收输入目录和输出目录两个参数：

```bash
bash src/main/qN.sh INPUT_DIRECTORY OUTPUT_DIRECTORY
```

Q8 额外接收 `repair`／`cleanup`，Bonus 额外接收 `start`／`stop`。具体文件格式、输出和动作要求看 PDF 对应题目。

**测试器会自动准备并传入这些参数。** 它会创建本题的输入、输出和临时环境，再执行你的脚本。不要把用户名、仓库位置、端口、PID 或包版本写死；路径可能包含空格，使用骨架中的 `input`、`output` 并正确引用。

`source` 读取的 `.env` 文件也是测试器为本次场景生成的参数。Q7 使用临时 SSH 密钥，Q8 使用训练进程，不需要学生设置真实机器人或个人 SSH 服务。

Q5 是启动故障诊断：运行提供的启动前检查，分别记录 stdout/stderr、真实退出码和诊断报告。检查程序可能正常退出，也可能因缺少模型或设备不可读而失败；答题脚本处理并记录这些结果后仍应正常退出。具体字段和分值看 PDF 的 Q5。

[samples/README.md](samples/README.md) 解释了静态样例的用途和单次练习方法。样例不是完整自测环境；CI 使用的变化数据、空日志和动态参数由 [tests/coursework.py](tests/coursework.py) 生成。仅让一个样例跑通不等于该题通过。

## 4. 在 GitHub 查看结果

在仓库根目录提交答题文件：

```bash
bash -n src/main/q1.sh           # 可选：先检查 Bash 语法

git add src/main
git commit -m "Complete Q1 path navigation"
git push origin main
```

打开 **Actions → Linux Coursework CI → 与本次 commit 对应的运行**：

1. 在 Summary 查看必做总分、Bonus、每题状态和通过结论。
2. 如果某题失败，查看反馈中的小项、场景和实际结果。
3. 下载页面底部的 artifact，查看执行输出和指定文本产物。

| 输出 | 用途 |
|---|---|
| `summary.md` | 分题成绩及失败反馈，与 Actions Summary 一致 |
| `score.json` | 每个小项的分数，以及 `assessment_passed` 通过状态 |
| `runs.json` | 脚本退出状态、stdout 和 stderr |
| `artifacts/` | 指定的文本产物，便于对照 PDF |

未实现的小项记 0 分；通过某题的部分小项可以取得部分分数。**正式通过结论看 Summary 和 `assessment_passed`**；不要把原始模板的初始化成功当成考核通过，也不要用单题本地测试代替完整 CI。

如果基础设施检查或环境准备失败，可能没有有效成绩，先查看失败步骤。学生仓库只允许修改答题文件和可选会话归档；CI 以初始模板提交检查累计变更，并从该版本提取可信测试。不要修改测试、校验表、PDF、README 或工作流，也不要重建 Git 历史。

## 5. 本地自测（可选）

正式 CI 直接运行在 GitHub hosted `ubuntu-24.04` runner，**不需要 Docker**。Windows／macOS 可以编辑脚本并通过推送自测。需要本地完整自测时，进入课程要求的 Ubuntu 24.04 LTS 训练虚拟机；支持 amd64／arm64。

在 Ubuntu 安装一次测试依赖：

```bash
sudo apt-get update
sudo apt-get install -y git python3 openssh-client openssh-server tmux procps curl dpkg
```

在仓库根目录运行：

```bash
bash tools/test.sh                               # 全部题目
bash tools/test.sh --question Q4                 # 单题
bash tools/test.sh --question Q7 --question Q8    # 多题
bash tools/test.sh --question B                  # Bonus
bash tools/test.sh --question Q3 --verbose       # 同时查看成功执行的 stdout/stderr
```

默认终端输出包括每次运行的场景与状态、每个评分小项的分数，以及失败原因。脚本执行失败时会显示退出码、stdout、stderr；Bash 命令失败时还会提示脚本行号和命令。权限不符会显示期望／实际权限，文本不符会定位第一处差异。`--verbose` 额外显示成功执行的输出。

示例（只做输出格式说明）：

```text
Q3 整理与权限
  [PASS] 复制和备份：3/3
  [FAIL] 精确权限：0/2
    normal：
      输出/sentry_ws/scripts/hello.sh：期望权限 750，实际权限 777
    changed：
      输出/sentry_ws/scripts/hello.sh：期望权限 750，实际权限 777
  结果：failed，8/10
```

如果某个场景的脚本中断，该场景未进入产物检查，会导致对应小项失败；先处理上方“场景失败”的执行错误。特别注意第 2 次运行失败，通常与重复创建、重复追加或删除不存在的文件有关。

结果同时写入 `generated/`，文件含义与 CI artifact 相同。`runs.json` 包含执行轮次与捕获的输出，`score.json` 的每个小项包含分场景结果。终端和报告中超过捕获长度的执行输出会标明截断。单题自测只用于调试，正式成绩仍取完整 GitHub CI。

测试器需要 sudo 创建临时账户和 SSH 服务；**学生脚本以临时普通用户执行，没有 sudo 权限**。测试会自动准备本地 Debian 包、SSH 连接、进程、HTTP 服务和 tmux 参数，并在结束后清理本次临时环境。正式题目用例使用回环网络，不依赖公网网站；首次安装依赖需要网络。

答题文件使用 Bash、UTF-8 和 LF 换行。学生不需要编写 Python，`tests/` 和 `tools/` 中的 Python 是教师提供的测试与训练程序。

## 6. 提交

完成后确认最新代码已推送到 main，打开与这个 commit 对应的完整 CI，复制 Actions run 链接并填写：

**[AIM 2627 Linux Coursework 回执](https://docs.qq.com/form/page/DWlZKTFBibGR2T2tG)**

填写表单要求的信息；如需仓库或 commit 链接，一并提交。截止日期以培训通知为准。请提交本次实际评估的运行，不提交其他 commit 的成功截图或本地单题结果。

## 7. AI 辅助与可选归档

允许使用课程资料、命令手册和 AI 辅助。正式分数由 CI 的公开行为检查产生，不设置人工答辩分或独立 grader。

模板提供与 Python 作业一致的可选 AgentLedger 归档配置；不启用也不影响分数。需要归档时自行配置：

```bash
python3 -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit
```

归档会作为 Git 内容提交，使用前确认没有密码、令牌或个人密钥。不要为启用归档改动教师提供的配置文件。

## 8. 常见问题

- **刚开始 CI 成功，为什么是 0 分？** 原始骨架只验证环境能启动，所有题仍未实现。
- **`grep` 没匹配就退出？** 骨架启用了 `set -e`；无匹配通常返回 1，但 Q4 的无错误日志是正常输入，需按题面处理。
- **为什么不能只运行 `bash src/main/q4.sh`？** 脚本需要输入／输出参数。完整自测用 `tools/test.sh`；单次样例练习看 samples 的说明。
- **Q6 为什么不能 sudo 安装？** 题目要求安装到自己的 sysroot，按 PDF 使用 dpkg 的非 root 选项。
- **Q5 检查程序失败，答题脚本也该失败吗？** 不应该。按题面捕获检查程序的退出码，完成日志和报告；不要用 `|| true` 后的 `$?` 当作原始退出码，也不要仅凭 stderr 是否非空判断成功。
- **Q7 密钥或连接参数在哪？** 测试器生成的 `remote.env` 中，不用个人 SSH 密钥。
- **Q8 修好后应立即停服务吗？** `repair` 返回时保留运行，测试器会独立发 HTTP 请求；`cleanup` 才停止。
- **Actions 没有运行？** 确认推送到 main，仓库已允许 Actions；也可从工作流页面手动运行。
- **CI 红了，还能看到分数吗？** 答题检查失败时通常可以；环境准备失败则没有有效成绩。先看 Summary，再看失败步骤。
