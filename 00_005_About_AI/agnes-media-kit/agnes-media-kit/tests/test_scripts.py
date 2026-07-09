#!/usr/bin/env python3
"""
Basic smoke tests for Agnes Media Kit scripts.
Run: python3 tests/test_scripts.py

Tests:
  - Script importability (no syntax errors)
  - Argument parser setup (can parse --help)
  - Dry-run mode works (no API call)
  - Environment variable fallback logic
"""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")


def _script_path(name):
    return os.path.join(SCRIPTS_DIR, name)


def _run(*args, env=None, timeout=15):
    """Run a script with given args, return (stdout, stderr, code).
    When env is provided, it REPLACES the environment (not merge)."""
    merged_env = os.environ.copy()
    if env is not None:
        merged_env = env
    proc = subprocess.run(
        [sys.executable, _script_path(args[0])] + list(args[1:]),
        capture_output=True,
        timeout=timeout,
        env=merged_env,
    )
    return proc.stdout.decode(), proc.stderr.decode(), proc.returncode


class TestScripts(unittest.TestCase):

    def setUp(self):
        # Ensure scripts directory exists
        self.assertTrue(os.path.isdir(SCRIPTS_DIR), f"Scripts dir not found: {SCRIPTS_DIR}")

    # ── importability ──────────────────────────────

    def test_generate_image_import(self):
        spec = importlib.util.spec_from_file_location("generate_image", _script_path("generate_image.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "parse_args"))
        self.assertTrue(hasattr(mod, "main"))

    def test_generate_video_import(self):
        spec = importlib.util.spec_from_file_location("generate_video", _script_path("generate_video.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "parse_args"))
        self.assertTrue(hasattr(mod, "main"))

    def test_check_task_import(self):
        spec = importlib.util.spec_from_file_location("check_task", _script_path("check_task.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "extract_real_video_id"))

    def test_batch_generate_import(self):
        spec = importlib.util.spec_from_file_location("batch_generate", _script_path("batch_generate.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertTrue(hasattr(mod, "main"))

    # ── argparse (--help doesn't crash) ────────────

    def test_generate_image_help(self):
        stdout, stderr, code = _run("generate_image.py", "--help")
        self.assertIn("usage:", stdout.lower())

    def test_generate_video_help(self):
        stdout, stderr, code = _run("generate_video.py", "--help")
        self.assertIn("usage:", stdout.lower())

    def test_check_task_help(self):
        stdout, stderr, code = _run("check_task.py", "--help")
        self.assertIn("usage:", stdout.lower())

    def test_batch_generate_help(self):
        stdout, stderr, code = _run("batch_generate.py", "--help")
        self.assertIn("usage:", stdout.lower())

    # ── dry-run (no API key needed) ────────────────

    def test_generate_image_dryrun(self):
        stdout, stderr, code = _run(
            "generate_image.py",
            "--project", "test_dryrun",
            "--prompt", "A test cat",
            "--output", "test.png",
            "--dry-run",
            env={"AGNES_API_KEY": "sk-test-dryrun"},
        )
        self.assertEqual(0, code, f"Dry run failed:\n{stderr}")
        # Should output JSON payload
        self.assertIn('"model"', stdout)
        self.assertIn("agnes-image", stdout)

    def test_generate_video_dryrun(self):
        stdout, stderr, code = _run(
            "generate_video.py",
            "--project", "test_dryrun",
            "--prompt", "A test cat video",
            "--output", "test.mp4",
            "--dry-run",
            env={"AGNES_API_KEY": "sk-test-dryrun"},
        )
        self.assertEqual(0, code, f"Dry run failed:\n{stderr}")
        self.assertIn('"model"', stdout)
        self.assertIn("agnes-video", stdout)

    # ── video_id extraction ────────────────────────

    def test_extract_real_video_id(self):
        spec = importlib.util.spec_from_file_location("check_task", _script_path("check_task.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Simulated base64 that decodes to the expected format
        import base64
        inner = "litellm:custom_llm_provider:openai;model_id:agnes-video-v2.0;video_id:video_d39354f7abc123"
        encoded = "video_" + base64.b64encode(inner.encode()).decode()

        result = mod.extract_real_video_id(encoded)
        self.assertEqual("video_d39354f7abc123", result)

    # ── env variable fallback ──────────────────────

    def test_env_variable_fallback(self):
        """Confirm scripts can read AGNES_API_KEY from environment."""
        stdout, stderr, code = _run(
            "generate_image.py",
            "--project", "test_env",
            "--prompt", "test",
            "--output", "test.png",
            "--dry-run",
            env={"AGNES_API_KEY": "sk-test-env-read"},
        )
        self.assertEqual(0, code, f"ENV test failed:\n{stderr}")
        # Dry-run prints JSON payload; check model name is present
        self.assertIn("agnes-image", stdout)

    def test_missing_api_key(self):
        """Should fail gracefully when no API key."""
        # Use bare-minimum env so the subprocess can run Python
        min_env = {"PATH": os.environ.get("PATH", "/usr/bin")}
        stdout, stderr, code = _run(
            "generate_image.py",
            "--project", "test",
            "--prompt", "test",
            "--output", "test.png",
            env=min_env,  # No AGNES_API_KEY
        )
        self.assertNotEqual(0, code)
        self.assertIn("AGNES_API_KEY", stderr)

    # ── project name validation ────────────────────

    def test_invalid_project_name(self):
        stdout, stderr, code = _run(
            "generate_image.py",
            "--project", "../../etc/passwd",
            "--prompt", "test",
            "--output", "test.png",
            "--dry-run",
            env={"AGNES_API_KEY": "sk-test"},
        )
        self.assertNotEqual(0, code)
        self.assertIn("Invalid project name", stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)