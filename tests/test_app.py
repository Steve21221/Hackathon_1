import json
import os
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app import app, build_feedback_prompt, call_model, load_mentor_prompt
from docx import Document
from pptx import Presentation


class PromptlyTestCase(unittest.TestCase):
    def setUp(self):
        os.environ.pop("MODEL_PROVIDER", None)
        os.environ.pop("OPENAI_API_KEY", None)
        os.environ.pop("OPENAI_MODEL", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)
        os.environ.pop("CLAUDE_MODEL", None)
        app.config.update(TESTING=True)
        self.original_source_directory = app.config["MENTOR_SOURCE_DIRECTORY"]
        self.source_temp = tempfile.TemporaryDirectory()
        app.config["MENTOR_SOURCE_DIRECTORY"] = Path(self.source_temp.name) / "Source_Documents"
        self.client = app.test_client()

    def tearDown(self):
        app.config["MENTOR_SOURCE_DIRECTORY"] = self.original_source_directory
        self.source_temp.cleanup()

    def test_home_page_has_three_feedback_categories(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Papers &amp; proposals", response.data)
        self.assertIn(b"Research ideas", response.data)
        self.assertIn(b"Talks &amp; slides", response.data)
        self.assertIn(b"Dr. Nanshu Lu", response.data)
        self.assertNotIn(b'name="file"', response.data)

    def test_clicking_type_shows_one_upload_form(self):
        response = self.client.get("/?type=research-ideas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.count(b'name="file"'), 1)
        self.assertIn(b"Choose a research idea", response.data)

    def test_research_idea_upload_returns_demo_feedback(self):
        response = self.client.post(
            "/feedback",
            data={
                "content_type": "research-ideas",
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
            data={"content_type": "papers-proposals", "file": (BytesIO(b"not a paper"), "notes.pptx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"not supported", response.data)

    def test_rejects_unknown_mentor(self):
        response = self.client.post(
            "/feedback",
            data={
                "content_type": "papers-proposals",
                "mentor_id": "unknown-mentor",
                "file": (BytesIO(b"Example content"), "example.txt"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"available mentor", response.data)

    def test_feedback_prompt_identifies_mentor(self):
        prompt = build_feedback_prompt(
            "papers-proposals",
            "example.txt",
            "Example content",
            "clarity",
            "dr-nanshu-lu",
        )
        self.assertIn("Dr. Nanshu Lu", prompt)
        self.assertIn("specialty, thinking process, and feedback style", prompt)
        self.assertIn("strength of the argument", prompt)

    def test_mentor_style_prompt_is_available(self):
        prompt = load_mentor_prompt("dr-nanshu-lu")
        self.assertIn("research mentor", prompt)

    def test_mentor_data_page_is_separate_from_feedback_workspace(self):
        response = self.client.get("/mentor-data")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Upload mentor source documents", response.data)
        self.assertIn(b"Feedback workspace", response.data)
        self.assertNotIn(b"Get mentor feedback", response.data)

    def test_mentor_source_upload_creates_pending_batch_manifest(self):
        response = self.client.post(
            "/mentor-data/upload",
            data={
                "mentor_id": "dr-nanshu-lu",
                "notes": "Examples of critical research feedback.",
                "files": [
                    (BytesIO(b"First mentor source"), "review one.txt"),
                    (BytesIO(b"Second mentor source"), "comments.vtt"),
                ],
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Saved 2 documents", response.data)

        pending_root = (
            Path(app.config["MENTOR_SOURCE_DIRECTORY"]) / "dr-nanshu-lu" / "pending"
        )
        batches = list(pending_root.iterdir())
        self.assertEqual(len(batches), 1)
        manifest = json.loads((batches[0] / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "pending")
        self.assertEqual(manifest["mentor_id"], "dr-nanshu-lu")
        self.assertEqual(len(manifest["documents"]), 2)
        self.assertTrue((batches[0] / "01-review_one.txt").is_file())
        self.assertTrue((batches[0] / "02-comments.vtt").is_file())

    def test_mentor_source_upload_rejects_unsupported_file(self):
        response = self.client.post(
            "/mentor-data/upload",
            data={
                "mentor_id": "dr-nanshu-lu",
                "files": (BytesIO(b"executable"), "unsafe.exe"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"not supported", response.data)
        self.assertFalse(Path(app.config["MENTOR_SOURCE_DIRECTORY"]).exists())

    @patch("app.OpenAI")
    def test_openai_receives_mentor_profile_and_review(self, mock_openai):
        os.environ["MODEL_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "test-key"
        mock_openai.return_value.responses.create.return_value = SimpleNamespace(
            output_text="Focused mentor feedback"
        )

        result = call_model(
            "Review category: Research ideas\nContent: A testable idea.",
            mentor_id="dr-nanshu-lu",
        )

        self.assertEqual(result, "Focused mentor feedback")
        request = mock_openai.return_value.responses.create.call_args.kwargs
        self.assertEqual(request["model"], "gpt-5-mini")
        self.assertIn("Dr. Nanshu Lu", request["instructions"])
        self.assertIn("rigorous, supportive", request["instructions"])
        self.assertIn("A testable idea", request["input"])
        self.assertFalse(request["store"])

    @patch("app.requests.post")
    def test_ollama_receives_thinking_prompt_locally(self, mock_post):
        os.environ["MODEL_PROVIDER"] = "ollama"
        os.environ["OLLAMA_MODEL"] = "qwen3.5:9b"
        mock_post.return_value.json.return_value = {
            "message": {"content": "Critical local feedback", "thinking": "hidden reasoning"}
        }

        result = call_model(
            "Review category: Research ideas\nContent: A testable idea.",
            mentor_id="dr-nanshu-lu",
        )

        self.assertEqual(result, "Critical local feedback")
        request = mock_post.call_args
        self.assertEqual(request.args[0], "http://127.0.0.1:11434/api/chat")
        payload = request.kwargs["json"]
        self.assertEqual(payload["model"], "qwen3.5:9b")
        self.assertTrue(payload["think"])
        self.assertFalse(payload["stream"])
        self.assertIn("Dr. Nanshu Lu", payload["messages"][0]["content"])
        self.assertIn("A testable idea", payload["messages"][1]["content"])

    @patch("app.Anthropic")
    def test_claude_receives_mentor_profile_and_review(self, mock_anthropic):
        os.environ["MODEL_PROVIDER"] = "claude"
        os.environ["ANTHROPIC_API_KEY"] = "test-key"
        mock_anthropic.return_value.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Focused Claude mentor feedback")]
        )

        result = call_model(
            "Review category: Research ideas\nContent: A testable idea.",
            mentor_id="dr-nanshu-lu",
        )

        self.assertEqual(result, "Focused Claude mentor feedback")
        request = mock_anthropic.return_value.messages.create.call_args.kwargs
        self.assertEqual(request["model"], "claude-sonnet-4-5")
        self.assertEqual(request["max_tokens"], 2_000)
        self.assertIn("Dr. Nanshu Lu", request["system"])
        self.assertIn("rigorous, supportive", request["system"])
        self.assertEqual(request["messages"][0]["role"], "user")
        self.assertIn("A testable idea", request["messages"][0]["content"])

    def test_word_document_upload_is_read(self):
        file_data = BytesIO()
        document = Document()
        document.add_paragraph("A proposal that needs feedback.")
        document.save(file_data)
        file_data.seek(0)
        response = self.client.post(
            "/feedback",
            data={"content_type": "papers-proposals", "file": (file_data, "proposal.docx")},
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
            data={"content_type": "talks-slides", "file": (file_data, "update.pptx")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"uploaded and read successfully", response.data)

    def test_json_api_validates_empty_prompt(self):
        response = self.client.post("/api/generate", json={"prompt": ""})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
