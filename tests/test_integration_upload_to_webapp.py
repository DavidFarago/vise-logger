import unittest
import io
import zipfile
import json
import requests


class TestWebAppUpload(unittest.TestCase):

    def test_upload_session_to_webapp(self):
        """
        Tests the successful upload of a session to the web application's POST endpoint.
        """
        # Create an in-memory zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("session.foo", "just a test contents")
        zip_buffer.seek(0)

        # Prepare metadata
        metadata = {
            "marker": "test_marker",
            "tool": "test_tool",
            "stars": 1,
            "comment": "This is a test comment.",
        }
        files = {
            "file": ("session.zip", zip_buffer, "application/zip"),
            "metadata": (None, json.dumps(metadata), "application/json"),
        }

        try:
            response = requests.post(
                "https://studio--viselog.us-central1.hosted.app/api/v1/sessions",
                files=files,
                timeout=30,
            )
            response.raise_for_status()

            self.assertEqual(response.status_code, 200)
            print(
                f"Successfully uploaded test session. Server response: {response.text}"
            )

        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to upload session to webapp: {e}")


if __name__ == "__main__":
    unittest.main()
