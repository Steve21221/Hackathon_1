import os
import unittest
from io import BytesIO

from app import app
from docx import Document
from pptx import Presentation


class PromptlyTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.pop("MODEL_API_URL", None)
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_home_page_has_three_upload_sections(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Document", response.data)
        self.assertIn(b"Transcript", response.data)
        self.assertIn(b"PowerPoint", response.data)
        self.assertNotIn(b'name="file"', response.data)

    def test_clicking_type_shows_one_upload_form(self):
        response = self.client.get("/?type=transcript")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'name="file"'), 1)
        self.assertIn(b"Choose a transcript", response.data)

    def test_transcript_upload_returns_demo_feedback(self):
        response = self.client.post(
            "/feedback",
            data={
                "content_type": "transcript",
                "focus": "key decisions",
                "file": (BytesIO(b"Speaker one: We approved the project."), "meeting.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"uploaded and read successfully", response.data)

    def test_rejects_wrong_file_type(self):
        response = self.client.post(
            "/feedback",
            data={"content_type": "powerpoint", "file": (BytesIO(b"not a presentation"), "notes.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"not supported", response.data)

    def test_word_document_upload_is_read(self):
        file_data = BytesIO()
        document = Document()
        document.add_paragraph("A proposal that needs feedback.")
        document.save(file_data)
        file_data.seek(0)
        response = self.client.post(
            "/feedback",
            data={"content_type": "document", "file": (file_data, "proposal.docx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"uploaded and read successfully", response.data)

    def test_powerpoint_upload_is_read(self):
        file_data = BytesIO()
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = "Project update"
        slide.placeholders[1].text = "The project is on schedule."
        presentation.save(file_data)
        file_data.seek(0)
        response = self.client.post(
            "/feedback",
            data={"content_type": "powerpoint", "file": (file_data, "update.pptx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"uploaded and read successfully", response.data)

    def test_json_api_validates_empty_prompt(self):
        response = self.client.post("/api/generate", json={"prompt": ""})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
