import tempfile
import zipfile
from pathlib import Path

from vise_logger.main import _create_zip_archive


def get_zip_contents(zip_file_path):
    """Helper function to get the contents of a zip file."""
    contents = {}
    with zipfile.ZipFile(zip_file_path, "r") as zf:
        for name in zf.namelist():
            contents[name] = zf.read(name)
    return contents


def test_create_zip_archive():
    """
    Tests that _create_zip_archive creates a zip file with the correct contents.
    """
    source_path = Path(
        "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/1754078015636"
    ).expanduser()
    log_path = source_path / "api_conversation_history.json"
    reference_zip_path = Path("tests/1754078015636.zip")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as temp_zip:
        _create_zip_archive(temp_zip.name, source_path, log_path)

        # Compare the contents of the generated zip file with the reference zip file
        generated_zip_contents = get_zip_contents(temp_zip.name)
        reference_zip_contents = get_zip_contents(reference_zip_path)

        # Sort the items by name to ensure consistent comparison
        sorted_generated_list = sorted(generated_zip_contents.items())
        sorted_reference_list = sorted(reference_zip_contents.items())

        assert sorted_generated_list == sorted_reference_list
