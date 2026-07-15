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
        self.original_output_directory = app.config["OUTPUT_DIR"]
        self.original_mentor_library_directory = app.config["MENTOR_LIBRARY_DIR"]
        self.output_temp = tempfile.TemporaryDirectory()
        app.config["OUTPUT_DIR"] = Path(self.output_temp.name) / "outputs"
        app.config["MENTOR_LIBRARY_DIR"] = Path(self.output_temp.name) / "mentor_files"
        self.client = app.test_client()

    def tearDown(self):
        app.config["OUTPUT_DIR"] = self.original_output_directory
        app.config["MENTOR_LIBRARY_DIR"] = self.original_mentor_library_directory
        self.output_temp.cleanup()

    def test_home_page_has_three_feedback_categories(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Papers &amp; proposals", response.data)
        self.assertIn(b"Research ideas", response.data)
        self.assertIn(b"Talks &amp; slides", response.data)
        self.assertIn(b"Dr. Nanshu Lu", response.data)
        self.assertNotIn(b'name="file"', response.data)

    def test_home_page_links_to_separate_pi_style_library(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/prompt-library"', response.data)
        self.assertIn(b"nav-link-boxed", response.data)
        self.assertNotIn(b"Mentor data", response.data)
        self.assertNotIn(b'name="research_files"', response.data)
        self.assertNotIn(b"Build your PI-style prompt library", response.data)

        library_response = self.client.get("/prompt-library")
        self.assertEqual(library_response.status_code, 200)
        self.assertIn(b"Build your PI-style", library_response.data)
        self.assertIn(b'name="research_files"', library_response.data)
        self.assertIn(b'name="slide_files"', library_response.data)
        self.assertIn(b'name="paper_files"', library_response.data)
        self.assertIn(b"library_uploads.js", library_response.data)
        self.assertIn(b"Feedback workspace", library_response.data)
        self.assertIn(b"nav-link-boxed", library_response.data)

        self.assertEqual(self.client.get("/mentor-data").status_code, 404)

    def test_pi_style_library_generates_and_downloads_prompt(self):
        response = self.client.post(
            "/generate-prompts",
            data={
                "research_files": (
                    BytesIO(
                        b"Professor asks us to clarify the hypothesis, compare mechanisms, "
                        b"and define the next experiment."
                    ),
                    "meeting-notes.txt",
                )
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PI-style prompts ready", response.data)
        self.assertIn(b"Research Ideas / Meeting Minutes", response.data)
        self.assertNotIn(b"Talks / Presentations / Slides</h3>", response.data)
        run_id = response.headers["X-Prompt-Run-Id"]
        run_directory = Path(app.config["OUTPUT_DIR"]) / run_id
        self.assertTrue((run_directory / "meeting_research_pi_prompt.txt").is_file())
        self.assertTrue((run_directory / "all_pi_style_prompts.txt").is_file())

        download = self.client.get(f"/download/{run_id}/meeting_research_pi_prompt")
        self.assertEqual(download.status_code, 200)
        self.assertIn(b"Generated PI-style prompt", download.data)

    @patch("app.call_prompt_model")
    def test_pi_style_library_uses_configured_model_for_style_distillation(self, mock_prompt_model):
        os.environ["MODEL_PROVIDER"] = "ollama"
        mock_prompt_model.side_effect = [
            "- clarify the framing\n- compare mechanisms\n- convert discussion into actions",
            "Review future research by reframing the opportunity, comparing mechanisms, and ending with decisive actions.",
        ]

        response = self.client.post(
            "/generate-prompts",
            data={"research_files": (BytesIO(b"A detailed professor review example."), "review.txt")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_prompt_model.call_count, 2)
        run_id = response.headers["X-Prompt-Run-Id"]
        generated = (Path(app.config["OUTPUT_DIR"]) / run_id / "meeting_research_pi_prompt.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("Review future research by reframing the opportunity", generated)

    def test_pi_style_library_rejects_unsupported_reference_file(self):
        response = self.client.post(
            "/generate-prompts",
            data={"research_files": (BytesIO(b"binary"), "unsafe.exe")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"not supported", response.data)

    def test_named_prompt_library_persists_files_and_stable_prompts(self):
        response = self.client.post(
            "/generate-prompts",
            data={
                "prompt_mentor_name": "Dr. Custom Mentor",
                "research_files": (
                    BytesIO(b"Clarify the hypothesis and define the next experiment."),
                    "meeting-notes.txt",
                ),
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        library = Path(app.config["MENTOR_LIBRARY_DIR"]) / "dr-custom-mentor"
        self.assertTrue((library / "mentor.json").is_file())
        self.assertTrue(
            (library / "meeting_research_pi" / "raw" / "meeting-notes.txt").is_file()
        )
        self.assertTrue((library / "meeting_research_pi" / "prompt.txt").is_file())
        self.assertTrue((library / "all_pi_style_prompts.txt").is_file())
        self.assertIn(b"Dr. Custom Mentor", response.data)
        self.assertIn(b"meeting-notes.txt", response.data)

    def test_existing_prompt_library_can_regenerate_without_new_uploads(self):
        self.client.post(
            "/generate-prompts",
            data={
                "prompt_mentor_name": "Existing Mentor",
                "research_files": (BytesIO(b"Ask for missing controls."), "first.txt"),
            },
            content_type="multipart/form-data",
        )

        response = self.client.post(
            "/generate-prompts",
            data={"selected_prompt_mentor": "existing-mentor"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PI-style prompts ready", response.data)
        self.assertIn(b"first.txt", response.data)

    def test_prompt_library_selection_and_delete_flow(self):
        self.client.post(
            "/generate-prompts",
            data={
                "prompt_mentor_name": "Delete Mentor",
                "paper_files": (BytesIO(b"Tighten the argument."), "review.txt"),
            },
            content_type="multipart/form-data",
        )
        library = Path(app.config["MENTOR_LIBRARY_DIR"]) / "delete-mentor"

        selected = self.client.get("/prompt-library?prompt_mentor=delete-mentor")
        self.assertEqual(selected.status_code, 200)
        self.assertIn(b"Delete Mentor", selected.data)
        self.assertIn(b"Delete library", selected.data)
        self.assertIn(b"review.txt", selected.data)

        deleted = self.client.post(
            "/delete-mentor",
            data={"selected_prompt_mentor": "delete-mentor"},
            follow_redirects=True,
        )
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(library.exists())
        self.assertNotIn(b"review.txt", deleted.data)

    def test_delete_prompt_library_rejects_unsafe_selection(self):
        response = self.client.post(
            "/delete-mentor",
            data={"selected_prompt_mentor": "../outside"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"existing mentor", response.data)

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
