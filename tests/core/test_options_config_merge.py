# -*- coding: utf-8 -*-

import sys
import tempfile

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from lib.core.options import merge_config
from lib.parse.cmdline import parse_arguments


CONFIG = """
[general]
filter-threshold = 17
max-recursion-depth = 4
max-time = 60
target-max-time = 30

[connection]
delay = 0.5
max-retries = 3
max-rate = 9
"""


class TestOptionsConfigMerge(TestCase):
    def merge(self, *arguments):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.ini"
            config_path.write_text(CONFIG, encoding="utf-8")
            argv = ["dirsearch.py", "--config", str(config_path), *arguments]
            with patch.object(sys, "argv", argv):
                return merge_config(parse_arguments())

    def test_explicit_zero_values_override_nonzero_config_values(self):
        options = self.merge(
            "--filter-threshold",
            "0",
            "--max-recursion-depth",
            "0",
            "--max-time",
            "0",
            "--target-max-time",
            "0",
            "--delay",
            "0",
            "--retries",
            "0",
            "--max-rate",
            "0",
        )

        self.assertEqual(options.filter_threshold, 0)
        self.assertEqual(options.recursion_depth, 0)
        self.assertEqual(options.max_time, 0)
        self.assertEqual(options.target_max_time, 0)
        self.assertEqual(options.delay, 0.0)
        self.assertEqual(options.max_retries, 0)
        self.assertEqual(options.max_rate, 0)

    def test_unset_values_still_use_config_values(self):
        options = self.merge()

        self.assertEqual(options.filter_threshold, 17)
        self.assertEqual(options.recursion_depth, 4)
        self.assertEqual(options.max_time, 60)
        self.assertEqual(options.target_max_time, 30)
        self.assertEqual(options.delay, 0.5)
        self.assertEqual(options.max_retries, 3)
        self.assertEqual(options.max_rate, 9)
