"""The single public test runner used locally and in GitHub CI."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests.coursework import TASKS, evaluate  # noqa: E402
from tools.feedback import execution_lines  # noqa: E402


class Runtime:
    def __init__(self, submission, results, verbose=False):
        self.results = results
        self.verbose = verbose
        self.base = Path(tempfile.mkdtemp(prefix="aim-linux public tests "))
        self.base.chmod(0o755)
        suffix = f"{os.getpid():x}"
        self.user, self.remote_user = f"aimcw{suffix}", f"aimrm{suffix}"
        self.created = []
        self.records = []
        try:
            for user in (self.user, self.remote_user):
                subprocess.run(["useradd", "--create-home", "--shell", "/bin/bash", user], check=True, capture_output=True)
                self.created.append(user)
            subprocess.run(["passwd", "-d", self.remote_user], check=True, capture_output=True)
            me, remote = pwd.getpwnam(self.user), pwd.getpwnam(self.remote_user)
            self.uid, self.gid = me.pw_uid, me.pw_gid
            self.remote_uid, self.remote_gid = remote.pw_uid, remote.pw_gid
            self.home = me.pw_dir
            self.tools = self.base / "tools"
            shutil.copytree(ROOT / "tools", self.tools, ignore=shutil.ignore_patterns("__pycache__"))
            self.submission = self.base / "answers"
            self.submission.mkdir()
            for filename in [f"q{n}.sh" for n in range(1, 9)] + ["bonus.sh"]:
                source = submission / filename
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"缺少普通答题文件：{filename}")
                destination = self.submission / filename
                shutil.copyfile(source, destination)
                destination.chmod(0o644)
            for path in self.tools.rglob("*"):
                path.chmod(0o755 if path.is_dir() or path.suffix == ".sh" else 0o644)
            Path("/run/sshd").mkdir(exist_ok=True)
        except Exception:
            self.close()
            raise

    def drop_privileges(self):
        os.setgroups([])
        os.setgid(self.gid)
        os.setuid(self.uid)
        resource.setrlimit(resource.RLIMIT_CPU, (12, 12))
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
        resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))

    @property
    def env(self):
        return {"PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin", "HOME": self.home, "USER": self.user, "LOGNAME": self.user, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}

    def spawn_student(self, args, cwd=None, stdout=None, stderr=None, diagnose=False):
        env = self.env
        if diagnose:
            env["BASH_ENV"] = str(self.tools / "bash_diagnostics.sh")
        return subprocess.Popen(args, cwd=cwd or self.base, env=env, preexec_fn=self.drop_privileges, start_new_session=True, stdin=subprocess.DEVNULL, stdout=stdout if stdout is not None else subprocess.PIPE, stderr=stderr if stderr is not None else subprocess.PIPE, text=True)

    def student(self, args, cwd=None, timeout=5, diagnose=False):
        proc = self.spawn_student(args, cwd, diagnose=diagnose)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
            return subprocess.CompletedProcess(args, 124, stdout, stderr + "\n超过执行时间限制")
        return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)

    def progress(self, message):
        print(message, flush=True)

    def record(self, case, action, proc):
        script = "bonus.sh" if case.question == "B" else case.question.lower() + ".sh"
        record = {"question": case.question, "case": case.name, "action": action,
                  "attempt": case.attempts, "script": script, "exit_code": proc.returncode,
                  "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-4000:],
                  "stdout_truncated": len(proc.stdout) > 4000,
                  "stderr_truncated": len(proc.stderr) > 4000}
        self.records.append(record)
        for line in execution_lines(record, self.verbose):
            self.progress(line)

    def archive(self, case):
        # Only designated text outputs, never private keys or test inputs.
        names = {
            "Q1": ["location.txt", "robot-id.txt", "welcome.txt"],
            "Q2": ["sentry_ws/scripts/hello.sh", "sentry_ws/config/robot.conf"],
            "Q3": ["hello-output.txt", "sentry_ws/config/robot.conf", "sentry_ws/archive/draft.conf.old"],
            "Q4": ["all.log", "errors.log", "attention.log", "recent.log", "first-errors.log", "error-count.txt"],
            "Q5": ["stdout.log", "stderr.log", "exit-code.txt", "report.txt"],
            "Q6": ["tool-output.txt"], "Q7": ["remote-user.txt", "received/errors.log"],
            "Q8": ["process.txt", "collector-sample.log", "server.conf", "http-status.txt", "http-body.txt"],
            "B": ["bonus.log"],
        }[case.question]
        for name in names:
            source = case.output / name
            if source.is_file() and not source.is_symlink() and not any(p.is_symlink() for p in source.parents) and source.stat().st_size <= 100_000:
                data = source.read_bytes()
                if b"PRIVATE KEY" in data:
                    continue
                dest = self.results / "artifacts" / case.question / case.name / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

    def close(self):
        # Stop only the two accounts created by this invocation; do not touch other users.
        uids = set()
        for user in self.created:
            try:
                uids.add(pwd.getpwnam(user).pw_uid)
            except KeyError:
                pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            for path in Path("/proc").iterdir():
                if path.name.isdigit():
                    try:
                        if path.stat().st_uid in uids:
                            os.kill(int(path.name), sig)
                    except (ProcessLookupError, FileNotFoundError):
                        pass
            time.sleep(0.1)
        for user in reversed(self.created):
            subprocess.run(["userdel", "--remove", user], capture_output=True)
        self.created.clear()
        shutil.rmtree(self.base, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", type=Path, default=ROOT / "src/main")
    parser.add_argument("--results", type=Path, default=ROOT / "generated")
    parser.add_argument("--question", choices=list(TASKS), action="append")
    parser.add_argument("--verbose", action="store_true", help="同时显示成功执行时的 stdout/stderr")
    args = parser.parse_args()
    if sys.platform != "linux" or os.geteuid() != 0:
        parser.error("请在 Ubuntu 上通过 bash tools/test.sh 运行。测试器需要 sudo，学生脚本以临时普通用户执行。")
    for command in ("useradd", "userdel", "passwd", "dpkg", "dpkg-deb", "dpkg-query", "ssh", "ssh-keygen", "scp", "tmux", "curl", "ps"):
        if shutil.which(command) is None:
            parser.error(f"缺少教师测试依赖：{command}，请参照 README 安装。")
    if not Path("/usr/sbin/sshd").exists():
        parser.error("需要 openssh-server")
    if args.results.is_symlink():
        parser.error("成绩目录不可是符号链接")
    args.results.mkdir(parents=True, exist_ok=True)
    # Remove reports from an earlier run so failed startup cannot look like fresh success.
    for filename in ("score.json", "summary.md", "runs.json"):
        (args.results / filename).unlink(missing_ok=True)
    shutil.rmtree(args.results / "artifacts", ignore_errors=True)
    runtime = None
    try:
        runtime = Runtime(args.submission.resolve(), args.results.resolve(), verbose=args.verbose)
        selected = list(dict.fromkeys(args.question or list(TASKS)))
        questions = evaluate(runtime, selected)
        required = [q for q in questions if q["question"] != "B"]
        points = sum(q["points"] for q in required)
        bonus = sum(q["points"] for q in questions if q["question"] == "B")
        all_pending = all(q["status"] == "pending" for q in questions)
        skeleton_hashes = json.loads((ROOT / "tests/skeleton-sha256.json").read_text())
        pristine = all(hashlib.sha256((runtime.submission / name).read_bytes()).hexdigest() == expected for name, expected in skeleton_hashes.items())
        complete = len(required) == 8 and all(q["status"] == "passed" for q in required)
        passed = len(required) == 8 and points >= 60 and all(any(q["question"] == key and q["status"] == "passed" for q in required) for key in ("Q7", "Q8"))
        report = {"schema_version": 1, "mode": "selected" if args.question else "full", "required_score": points, "required_max": 100, "bonus_score": bonus, "bonus_max": 10, "assessment_passed": passed, "all_required_complete": complete, "template_pending": all_pending and pristine, "questions": questions}
        (args.results / "score.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        (args.results / "runs.json").write_text(json.dumps(runtime.records, ensure_ascii=False, indent=2) + "\n")
        conclusion = "未开始：0 分；模板初始化成功不代表考核通过" if all_pending and pristine else "通过" if passed else "未通过"
        if args.question:
            conclusion = "单题自测，不是正式总成绩"
        lines = ["## AIM Linux Coursework", "", f"**必做 {points}/100；Bonus {bonus}/10；评估结论：{conclusion}。**", "", "| 题目 | 状态 | 得分 |", "|---|---|---:|"]
        labels = {"passed": "通过", "pending": "未实现", "failed": "未全部通过"}
        for q in questions:
            lines.append(f"| {q['question']} {q['title']} | {labels[q['status']]} | {q['points']}/{q['max_points']} |")
        lines += ["", "通过条件：必做至少 60 分，且 Q7、Q8 的全部检查通过。全部测试公开；没有人工分或独立 grader。", "", "未实现的脚本退出 77：跳过检查但记 0 分。只有原始模板允许以未开始状态初始化成功；开始答题后未达到通过条件，完整 CI 将失败。", ""]
        for q in questions:
            failures = [c for c in q["checks"] if c["status"] == "failed"]
            if failures:
                lines += [f"### {q['question']} 反馈", ""]
                for check in failures:
                    lines += [f"- {check['name']}（{check['max_points']} 分）：", "", "```text", check["feedback"].replace("```", "'''"), "```", ""]
        lines += ["完整分项见 score.json，执行输出见 runs.json，指定文本产物见 artifacts/。", "", "正式提交请提交本仓库的对应 Actions run 链接【腾讯文档】AIM 2627 Linux Coursework 回执 https://docs.qq.com/form/page/DWlZKTFBibGR2T2tG", ""]
        (args.results / "summary.md").write_text("\n".join(lines))
        print(f"必做 {points}/100，Bonus {bonus}/10；{conclusion}")
        print(f"完整报告：{args.results.resolve() / 'summary.md'}")
        print(f"逐次执行输出：{args.results.resolve() / 'runs.json'}")
        if args.question:
            return 0 if all(q["status"] in {"passed", "pending"} for q in questions) else 1
        return 0 if passed or (all_pending and pristine) else 1
    except Exception as exc:
        print(f"测试基础设施异常：{exc}", file=sys.stderr)
        return 2
    finally:
        if runtime is not None:
            runtime.close()


if __name__ == "__main__":
    sys.exit(main())
