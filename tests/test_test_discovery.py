from pathlib import Path
import unittest

import testing


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / "tests"


def iter_test_cases(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_test_cases(item)
        else:
            yield item


def expected_test_modules():
    return {
        ".".join(path.relative_to(PROJECT_ROOT).with_suffix("").parts)
        for path in TEST_ROOT.rglob("test_*.py")
    }


def discovered_test_modules(suite):
    return {test.__class__.__module__ for test in iter_test_cases(suite)}


class TestTestDiscovery(unittest.TestCase):
    def test_all_test_modules_are_discoverable(self):
        suite = unittest.TestLoader().discover(
            str(TEST_ROOT), top_level_dir=str(PROJECT_ROOT)
        )

        self.assertEqual(discovered_test_modules(suite), expected_test_modules())

    def test_legacy_runner_uses_the_canonical_discovery_suite(self):
        suite = testing.discover_tests()

        self.assertEqual(discovered_test_modules(suite), expected_test_modules())

    def test_ci_runs_canonical_test_discovery(self):
        workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
        command = "python -m unittest discover -s tests -t ."

        self.assertEqual(workflow.count(command), 2)
        self.assertNotIn("python3 testing.py", workflow)
