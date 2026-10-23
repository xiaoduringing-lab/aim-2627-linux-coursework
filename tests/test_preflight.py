"""Self-check the startup training program; no student grading happens here."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "tools/sentry-preflight.sh"


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aim startup input ")
        self.root = Path(self.temp.name).resolve()
        self.model = self.root / "model weights.bin"
        self.camera = self.root / "camera.device"
        self.camera.write_text("simulated device\n")
        self.camera.chmod(0o444)

    def tearDown(self):
        self.temp.cleanup()

    def run_tool(self):
        return subprocess.run(["bash", str(TOOL), str(self.model), str(self.camera)],
                              capture_output=True, text=True, timeout=5)

    def test_success_can_have_stderr_notice(self):
        self.model.write_text("training model\n")
        result = self.run_tool()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.endswith("READY\n"))
        self.assertEqual(result.stderr, "NOTICE: training preflight only\n")

    def test_missing_model_has_real_failure_status(self):
        result = self.run_tool()
        self.assertEqual(result.returncode, 10)
        self.assertIn("ERROR MODEL_MISSING", result.stderr)
        self.assertNotIn("MODEL_READY", result.stdout)

    @unittest.skipIf(os.geteuid() == 0, "权限自检需要普通用户；正式测试会切换到临时普通用户")
    def test_unreadable_device_has_real_failure_status(self):
        self.model.write_text("training model\n")
        self.camera.chmod(0o000)
        result = self.run_tool()
        self.assertEqual(result.returncode, 20)
        self.assertIn("MODEL_READY", result.stdout)
        self.assertIn("ERROR CAMERA_DENIED", result.stderr)


if __name__ == "__main__":
    unittest.main()
