import unittest
from pathlib import Path
import uuid
from vise_logger.search import find_log_path_with_marker


class TestSearchStages(unittest.TestCase):

    def test_stage1_predefined_location(self):
        """Test finding a log file in a predefined location."""
        marker = "Rated session at 2025-07-27-11-11-59: 4.7 stars. Now uploading session to server."
        # This file is expected to exist in the test environment
        expected_parent_dir = (
            Path.home()
            / ".config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/"
        )

        found_result = find_log_path_with_marker(marker)

        self.assertIsNotNone(found_result)
        found_log_path, found_path_to_zip, tool = found_result
        self.assertEqual(found_log_path.parent, found_path_to_zip)
        self.assertEqual(found_path_to_zip.parent, expected_parent_dir)
        self.assertEqual(tool, "cline")
 

    # def test_stage2_home_directory(self):
    #     """Test finding a log file in the home directory."""
    #     test_dir = Path.home() / f"test_vise_logger_{uuid.uuid4()}"
    #     test_dir.mkdir(exist_ok=True)
    #     log_file = test_dir / "test.log"
    #     marker = f"unique_marker_stage2_{uuid.uuid4()}"
    #     with open(log_file, "w") as f:
    #         f.write(marker)

    #     try:
    #         found_result = find_log_path_with_marker(marker)

    #         self.assertIsNotNone(found_result)
    #         found_log_path, found_path_to_zip, tool = found_result
    #         self.assertEqual(found_log_path, log_file)
    #         self.assertEqual(found_path_to_zip, log_file) # as only 1 file in directory
    #         self.assertEqual(tool, "unknown")
    #     finally: # Cleanup
    #         if log_file.exists():
    #             log_file.unlink()
    #         if test_dir.exists():
    #             test_dir.rmdir()


if __name__ == "__main__":
    unittest.main()
