import unittest
from pathlib import Path
import uuid
from vise_logger.search import find_log_file_with_marker


class TestSearchStages(unittest.TestCase):

    def test_stage1_predefined_location(self):
        """Test finding a log file in a predefined location."""
        marker = "Rated session at 2025-07-27-11-11-59: 4.7 stars. Now uploading session to server."
        # This file is expected to exist in the test environment
        expected_parent_dir = (
            Path.home()
            / ".config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/"
        )

        found_result = find_log_file_with_marker(marker)
        self.assertIsNotNone(found_result)
        found_path, _ = found_result
        self.assertTrue(str(found_path).startswith(str(expected_parent_dir)))

    def test_stage2_home_directory(self):
        """Test finding a log file in the home directory."""
        test_dir = Path.home() / f"test_vise_logger_{uuid.uuid4()}"
        test_dir.mkdir(exist_ok=True)
        log_file = test_dir / "test.log"
        marker = f"unique_marker_stage2_{uuid.uuid4()}"

        with open(log_file, "w") as f:
            f.write(marker)

        try:
            found_result = find_log_file_with_marker(marker)
            self.assertIsNotNone(found_result)
            found_path, _ = found_result
            self.assertEqual(found_path, test_dir)
        finally:
            # Cleanup
            if log_file.exists():
                log_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
