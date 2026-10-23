"""Portable regression tests for diagnostics; these do not award coursework points."""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tests import coursework  # noqa: E402
from tools.feedback import execution_lines  # noqa: E402
from tools.run_tests import Runtime  # noqa: E402


class PortableRuntime(Runtime):
    """Only test private files/Bash locally; never create users or start Linux services."""

    def __init__(self, base, verbose=False):
        self.base = base
        self.submission = base / "answers"
        self.submission.mkdir()
        self.results = base / "results"
        self.tools = ROOT / "tools"
        self.uid, self.gid = os.getuid(), os.getgid()
        self.home = str(base)
        self.user = "test-user"
        self.verbose = verbose
        self.records = []

    def spawn_student(self, args, cwd=None, stdout=None, stderr=None, diagnose=False):
        env = dict(os.environ)
        if diagnose:
            env["BASH_ENV"] = str(self.tools / "bash_diagnostics.sh")
        return subprocess.Popen(args, cwd=cwd or self.base, env=env,
                                stdin=subprocess.DEVNULL, stdout=stdout or subprocess.PIPE,
                                stderr=stderr or subprocess.PIPE, text=True, start_new_session=True)

    def archive(self, case):
        pass


class FeedbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aim-feedback tests ")
        self.base = Path(self.temp.name).resolve()
        self.runtime = PortableRuntime(self.base)

    def tearDown(self):
        self.temp.cleanup()

    def script(self, body):
        path = self.runtime.submission / "q3.sh"
        path.write_text("#!/bin/bash\nset -eu\n" + body)
        return path

    def test_bash_failure_includes_line_command_and_output(self):
        diagnostics = self.base / "diagnostic tools"
        diagnostics.mkdir()
        (diagnostics / "bash_diagnostics.sh").write_text((ROOT / "tools/bash_diagnostics.sh").read_text())
        self.runtime.tools = diagnostics
        self.script("printf 'before failure\\n'\nfalse\nprintf 'not reached\\n'\n")
        case = coursework.Case(self.runtime, "Q3", "normal")
        console = io.StringIO()
        with contextlib.redirect_stdout(console), self.assertRaises(AssertionError):
            case.execute()
        record = self.runtime.records[0]
        self.assertEqual(record["exit_code"], 1)
        self.assertIn("q3.sh:4", record["stderr"])
        self.assertIn("命令：false", record["stderr"])
        self.assertIn("before failure", console.getvalue())
        self.assertNotIn("not reached", record["stdout"])

    def test_second_run_identifies_attempt(self):
        self.script('if [ -f "$2/once" ]; then false; fi\ntouch "$2/once"\n')
        case = coursework.Case(self.runtime, "Q3", "changed")
        console = io.StringIO()
        with contextlib.redirect_stdout(console), self.assertRaisesRegex(AssertionError, "第 2 次调用退出 1"):
            case.twice()
        self.assertEqual([r["exit_code"] for r in self.runtime.records], [0, 1])
        self.assertIn("场景 changed / 第 2 次运行", console.getvalue())

    def test_unimplemented_script_keeps_exit_77_and_zero_status(self):
        self.script("exit 77\n")
        case = coursework.Case(self.runtime, "Q3", "pending")
        with contextlib.redirect_stdout(io.StringIO()):
            case.execute()
        self.assertTrue(case.pending)
        self.assertEqual(self.runtime.records[0]["exit_code"], 77)
        self.assertEqual(self.runtime.records[0]["stderr"], "")

    def test_handled_no_match_does_not_become_failure(self):
        self.script("printf 'INFO ok\\n' | grep '^ERROR ' || [ \"$?\" -eq 1 ]\n")
        case = coursework.Case(self.runtime, "Q3", "no-errors")
        with contextlib.redirect_stdout(io.StringIO()):
            case.execute()
        self.assertEqual(self.runtime.records[0]["exit_code"], 0)
        self.assertEqual(self.runtime.records[0]["stderr"], "")

    def test_repeatability_error_lists_changed_output(self):
        self.script('printf "tick\\n" >> "$2/events.log"\n')
        case = coursework.Case(self.runtime, "Q3", "repeat")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(AssertionError, "events.log"):
            case.twice()

    def test_content_diff_finds_mismatch_beyond_old_180_character_limit(self):
        path = self.base / "long.log"
        prefix = "x" * 250 + "\n"
        path.write_text(prefix + "actual\n")
        with self.assertRaises(AssertionError) as caught:
            coursework.equal(path, prefix + "expected\n")
        message = str(caught.exception)
        self.assertIn("第 2 行", message)
        self.assertIn("'expected\\n'", message)
        self.assertIn("'actual\\n'", message)

    def test_missing_file_identifies_full_output_path(self):
        case = coursework.Case(self.runtime, "Q3", "missing")
        with self.assertRaisesRegex(AssertionError, "输出/sentry_ws/backup/robot.conf"):
            coursework.text(case.output / "sentry_ws/backup/robot.conf")

    def test_wrong_permissions_preserve_partial_score_and_show_both_cases(self):
        def fixture(runtime, question, variant):
            case = coursework.Case(runtime, question, variant)
            case.write("robot.conf", f"robot={variant}\n")
            case.write("draft.conf", "mode=draft\n")
            files = {"sentry_ws/scripts/hello.sh": coursework.HELLO,
                     "sentry_ws/config/robot.conf": f"robot={variant}\n",
                     "sentry_ws/backup/robot.conf": f"robot={variant}\n",
                     "sentry_ws/archive/draft.conf.old": "mode=draft\n",
                     "hello-output.txt": "Hello, AIM Linux!\n"}
            for name, content in files.items():
                path = case.output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (case.output / "sentry_ws/scripts/hello.sh").chmod(0o777)
            (case.output / "sentry_ws/config/robot.conf").chmod(0o640)
            return case
        console = io.StringIO()
        with patch.object(coursework, "simple_case", side_effect=fixture), contextlib.redirect_stdout(console):
            result = coursework.evaluate(self.runtime, ["Q3"])[0]
        self.assertEqual(result["points"], 8)
        self.assertIn("[FAIL] 精确权限：0/2", console.getvalue())
        self.assertIn("期望权限 750，实际权限 777", console.getvalue())
        self.assertIn("normal：", console.getvalue())
        self.assertIn("changed：", console.getvalue())
        self.assertIn("[PASS] 移动归档：2/2", console.getvalue())
        self.assertEqual(len(result["checks"][3]["cases"]), 2)

    def test_failed_scene_explains_why_whole_question_is_zero(self):
        def fixture(runtime, question, variant):
            case = coursework.Case(runtime, question, variant)
            case.error = "q3.sh 第 2 次调用退出 1：rm failed"
            return case
        console = io.StringIO()
        with patch.object(coursework, "simple_case", side_effect=fixture), contextlib.redirect_stdout(console):
            result = coursework.evaluate(self.runtime, ["Q3"])[0]
        self.assertEqual(result["points"], 0)
        self.assertIn("[场景失败] normal", console.getvalue())
        self.assertIn("第 2 次调用退出 1", console.getvalue())
        self.assertIn("场景执行失败，见上方退出状态", console.getvalue())

    def test_verbose_includes_successful_output_and_marks_truncation(self):
        record = {"case": "normal", "action": "run", "attempt": 1,
                  "script": "q3.sh", "exit_code": 0, "stdout": "success log",
                  "stderr": "", "stdout_truncated": True}
        self.assertNotIn("success log", "\n".join(execution_lines(record)))
        detail = "\n".join(execution_lines(record, verbose=True))
        self.assertIn("success log", detail)
        self.assertIn("已截断", detail)

    def test_timeout_and_signal_have_clear_labels(self):
        base = {"case": "normal", "action": "run", "script": "q3.sh", "stdout": "", "stderr": ""}
        self.assertIn("超过 15 秒", "\n".join(execution_lines(dict(base, exit_code=124))))
        self.assertIn("被信号 9 终止", "\n".join(execution_lines(dict(base, exit_code=-9))))

    def test_shell_wrapper_preserves_failure_exit_status(self):
        tools = self.base / "wrapper/tools"
        tools.mkdir(parents=True)
        path = tools / "test.sh"
        path.write_text((ROOT / "tools/test.sh").read_text())
        commands = self.base / "commands"
        commands.mkdir()
        for name, body in (("uname", "printf 'Linux\\n'"), ("sudo", "printf 'runner failed\\n'; exit 7")):
            command = commands / name
            command.write_text("#!/bin/bash\n" + body + "\n")
            command.chmod(0o755)
        env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ["PATH"])
        result = subprocess.run(["bash", str(path), "--question", "Q3"], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 7)
        self.assertIn("runner failed", result.stdout)
        self.assertIn("报告保存在", result.stdout)


if __name__ == "__main__":
    unittest.main()
