import os
from io import BytesIO
from pathlib import Path

from app import app, build_feedback_prompt


def client_with_tmp_outputs(tmp_path):
    os.environ.pop("MODEL_API_URL", None)
    app.config.update(TESTING=True, OUTPUT_DIR=tmp_path)
    return app.test_client()


def test_home_page_uses_hackathon1_feedback_shell_and_keeps_pi_library(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.get("/")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Promptly" in html
    assert "Bring your work." in html
    assert "Choose your mentor" not in html
    assert "Dr. Nanshu Lu" not in html
    assert "Document" in html
    assert "Transcript" in html
    assert "PowerPoint" in html
    assert "Build Your PI Style Library" in html
    assert "Generate PI-Style Prompts" in html
    assert 'name="project_name"' not in html
    assert "Project name" not in html
    assert 'name="research_files"' in html and "multiple" in html
    assert 'name="slide_files"' in html and "multiple" in html
    assert 'name="paper_files"' in html and "multiple" in html
    assert "No files selected yet" in html
    assert "library_uploads.js" in html
    assert 'class="file-hint"' not in html
    assert "Supported:" in html
    assert html.index("Supported:") < html.index("Generate PI-Style Prompts")
    assert "meeting_research_pi" not in html
    assert "slides_talk_pi" not in html
    assert "paper_proposal_pi" not in html
    assert "Generate JSONL" not in html
    assert "legacy JSONL extractor" not in html


def test_clicking_type_shows_hackathon1_upload_form(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.get("/?type=transcript#upload")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert html.count('name="file"') == 1
    assert "Choose a transcript" in html
    assert 'name="mentor_id" value="dr-nanshu-lu"' in html
    assert "Choose your mentor" not in html


def test_transcript_feedback_returns_demo_feedback(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/feedback",
        data={
            "content_type": "transcript",
            "mentor_id": "dr-nanshu-lu",
            "focus": "key decisions",
            "file": (BytesIO(b"Speaker one: We approved the project."), "meeting.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "uploaded and read successfully" in html
    assert "Feedback from Dr. Nanshu Lu" in html


def test_feedback_rejects_wrong_file_type(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/feedback",
        data={
            "content_type": "powerpoint",
            "mentor_id": "dr-nanshu-lu",
            "file": (BytesIO(b"not a presentation"), "notes.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert b"not supported" in response.data


def test_api_generate_validates_empty_prompt(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post("/api/generate", json={"prompt": ""})

    assert response.status_code == 400
    assert response.json["error"] == "Please enter a prompt."


def test_library_card_css_aligns_upload_rows_and_keeps_hover_dark():
    css = Path("static/style.css").read_text(encoding="utf-8")

    assert "grid-template-rows: auto minmax(92px, 1fr) auto auto;" in css
    assert ".upload-row" in css
    assert "align-self: end;" in css
    assert ".primary-action:hover" in css
    assert "background: #203a2f;" in css
    assert "box-shadow: 0 10px 22px rgba(32,58,47,.18);" in css
    assert ".prompt-library-form .privacy-note" in css
    assert "margin: -6px 0 0;" in css


def test_feedback_prompt_identifies_mentor():
    prompt = build_feedback_prompt(
        "document",
        "example.txt",
        "Example content",
        "clarity",
        "dr-nanshu-lu",
    )

    assert "Dr. Nanshu Lu" in prompt
    assert "specialty, thinking process, and feedback style" in prompt


def test_generate_prompts_creates_three_txt_prompt_downloads(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Clarify the next experiment and add a missing control."),
                "meeting.txt",
            ),
            "slide_files": (
                BytesIO(b"Remove duplicate panels and state the slide takeaway."),
                "slides.txt",
            ),
            "paper_files": (
                BytesIO(b"The claim is too broad for the current evidence."),
                "proposal.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "PI Style Prompts Ready" in html
    assert html.count('class="prompt-card compact-prompt-card"') == 3
    assert "Research Ideas / Meeting Minutes" in html
    assert "Talks / Presentations / Slides" in html
    assert "Papers / Proposals" in html
    assert "meeting_research_pi_prompt.txt" not in html
    assert "slides_talk_pi_prompt.txt" not in html
    assert "paper_proposal_pi_prompt.txt" not in html
    assert "<pre" not in html
    assert "<dt>Chunks</dt>" not in html
    assert "Download all prompts TXT" not in html
    assert "TXT files saved locally in" in html
    assert "history.replaceState" in html
    assert "performance.getEntriesByType" in html
    assert "window.location.replace" in html
    run_id = response.headers["X-Prompt-Run-Id"]
    assert run_id in html

    download_response = client.get(f"/download/{run_id}/meeting_research_pi_prompt")
    assert download_response.status_code == 200
    assert download_response.headers["Content-Type"].startswith("text/plain")
    body = download_response.data.decode("utf-8")
    assert "MODE: meeting_research_pi" in body
    assert "Clarify the next experiment" in body


def test_generated_prompt_txt_files_are_saved_under_run_output_dir(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Clarify the next experiment and add a missing control."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    run_id = response.headers["X-Prompt-Run-Id"]
    run_dir = tmp_path / run_id

    assert (run_dir / "meeting_research_pi_prompt.txt").exists()
    assert (run_dir / "all_pi_style_prompts.txt").exists()
    assert str(run_dir) in response.data.decode("utf-8")


def test_clean_home_after_refresh_has_no_prompt_ready_output(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Clarify the next experiment and add a missing control."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    response = client.get("/")
    html = response.data.decode("utf-8")

    assert response.status_code == 200
    assert "PI Style Prompts Ready" not in html
    assert "TXT files saved locally in" not in html
    assert "prompt-output-title" not in html


def test_post_feedback_result_resets_to_clean_home_on_browser_refresh(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/feedback",
        data={
            "content_type": "document",
            "mentor_id": "dr-nanshu-lu",
            "file": (BytesIO(b"Draft paragraph."), "draft.txt"),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "history.replaceState" in html
    assert "url_for('home')" not in html


def test_prompt_output_section_has_visual_gap_before_review_upload_section():
    css = Path("static/style.css").read_text(encoding="utf-8")

    assert ".prompt-output-section + .upload-section" in css
    assert "margin-top: 44px" in css


def test_generate_prompts_only_displays_modes_with_uploaded_content(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Clarify the next experiment and add a missing control."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    output_html = html.split('id="prompt-output-title"', 1)[1].split('<section class="upload-section"', 1)[0]
    assert output_html.count('class="prompt-card compact-prompt-card"') == 1
    assert "Research Ideas / Meeting Minutes" in output_html
    assert "Talks / Presentations / Slides" not in output_html
    assert "Papers / Proposals" not in output_html

def test_generate_prompts_preview_uses_uploaded_professor_concerns(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(
                    b"Professor repeatedly asks for a missing control before trusting the WVTR mechanism. "
                    b"Clarify the next experiment, sample size, and whether the hypothesis can be falsified."
                ),
                "meeting_notes.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    output_html = html.split('id="prompt-output-title"', 1)[1].split('<section class="upload-section"', 1)[0]
    assert "controls" in output_html
    assert "falsifiable" in output_html
    assert "next experiment" in output_html or "next experiments" in output_html
    assert "When reviewing research ideas or meeting minutes" in output_html
    assert "WVTR" not in output_html

def test_compact_prompt_preview_does_not_cut_mid_word():
    from app import compact_prompt_preview
    from raw_materials.prompt_builder import PromptArtifact

    generated = "Generated PI-style prompt:\n" + (
        "Use the professor's style with complete sentences. " * 30
    )
    artifact = PromptArtifact(
        mode="meeting_research_pi",
        label="Research Ideas / Meeting Minutes",
        filename="meeting_research_pi_prompt.txt",
        content=generated,
        source_files=["meeting.txt"],
        record_count=1,
    )

    preview = compact_prompt_preview(artifact)

    assert len(preview) <= 1100
    assert preview.endswith(".") or preview.endswith("...")
    assert not preview.endswith("sentenc")

def test_ollama_generate_uses_local_api(monkeypatch):
    import importlib

    app_module = importlib.import_module("app")
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"response": "A polished Llama prompt."}

    def fake_post(url, json, headers, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setattr(app_module.requests, "post", fake_post)

    result = app_module.call_ollama_generate("Build a PI prompt from these notes.")

    assert result == "A polished Llama prompt."
    assert calls["url"] == "http://127.0.0.1:11434/api/generate"
    assert calls["json"]["model"] == "llama3.1:8b"
    assert calls["json"]["prompt"] == "Build a PI prompt from these notes."
    assert calls["json"]["stream"] is False
    assert calls["json"]["options"]["temperature"] == 0.2


def test_generate_prompts_uses_ollama_prompt_when_enabled(monkeypatch, tmp_path):
    import importlib

    app_module = importlib.import_module("app")
    client = client_with_tmp_outputs(tmp_path)
    monkeypatch.setenv("PROMPT_LLM_PROVIDER", "ollama")
    monkeypatch.setattr(
        app_module,
        "generate_llm_prompt_for_mode",
        lambda mode, source_files, chunks, deterministic_prompt: (
            "Use the professor's Llama-generated style for meeting notes. "
            "Focus on falsifiable mechanism, controls, and next experiments."
            if mode == "meeting_research_pi"
            else None
        ),
    )

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"The PI asks for falsifiable mechanism and proper controls."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Use the professor" in html and "Llama-generated style" in html
    run_id = response.headers["X-Prompt-Run-Id"]
    body = client.get(f"/download/{run_id}/meeting_research_pi_prompt").data.decode("utf-8")
    assert "Use the professor's Llama-generated style for meeting notes" in body

def test_ollama_request_requires_project_agnostic_style_distillation():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "meeting_research_pi",
        ["breathable_architecture_notes.txt"],
        [
            "The PI asks about pore topology, vapor transport, liquid sweat transport, "
            "evaporation under fixed porosity, and AI-assisted topology optimization."
        ],
        "Review the breathable architecture project and address pore topology.",
    )

    assert "Do not write a prompt for the uploaded project" in request_prompt
    assert "general-purpose" in request_prompt
    assert "future project" in request_prompt
    assert "Do NOT mention project-specific nouns" in request_prompt
    assert "breathable architecture" in request_prompt


def test_deterministic_generated_prompt_is_mode_specific_not_project_specific():
    from raw_materials.prompt_builder import build_mode_prompt_artifacts

    grouped_chunks = {
        "meeting_research_pi": [
            {
                "source_file": "breathable_architecture_notes.txt",
                "chunks": [
                    (
                        "The professor asks about pore topology's effect on vapor transport, "
                        "liquid sweat transport, evaporation under fixed porosity, and AI-assisted "
                        "topology optimization for breathable pore architectures."
                    )
                ],
            }
        ],
        "slides_talk_pi": [],
        "paper_proposal_pi": [],
    }

    artifact = build_mode_prompt_artifacts(grouped_chunks)["meeting_research_pi"]
    generated = artifact.content.split("Generated PI-style prompt:", 1)[1].split("PI-style response rules:", 1)[0].lower()

    assert "research ideas or meeting minutes" in generated
    assert "breathable" not in generated
    assert "pore topology" not in generated
    assert "vapor transport" not in generated
    assert "liquid sweat" not in generated
    assert "ai-assisted topology" not in generated
    assert "falsifiable" in generated
    assert "controls" in generated
    assert "next experiments" in generated

def test_ollama_request_demands_refined_non_redundant_prompt():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "meeting_research_pi",
        ["meeting_notes.txt"],
        ["The PI repeatedly asks for a clear hypothesis, controls, and decisive next experiments."],
        "When reviewing research ideas, test whether the question is falsifiable.",
    )

    assert "single refined paragraph" in request_prompt
    assert "silently revise your draft" in request_prompt
    assert "Do not repeat the same checklist" in request_prompt
    assert "for a project in this mode" in request_prompt
    assert "Specifically, test whether" in request_prompt


def test_polish_llm_prompt_output_removes_internal_phrases_and_redundant_specific_sentence():
    from app import polish_llm_prompt_output

    raw = (
        "When reviewing research ideas or meeting minutes for a project in this mode, prioritize a "
        "falsifiable research question that clearly articulates the central hypothesis and mechanism of action. "
        "Ensure that the discussion leads to a real decision by identifying concrete next experiments. "
        "Specifically, test whether the central question is sharp, whether the mechanism or claim is falsifiable, "
        "whether controls are adequate, and whether evidence aligns with the conclusion.  "
    )

    polished = polish_llm_prompt_output(raw)

    assert "for a project in this mode" not in polished
    assert "Specifically, test whether" not in polished
    assert "  " not in polished
    assert polished.startswith("When reviewing research ideas or meeting minutes, prioritize")
    assert "concrete next experiments" in polished
    assert polished.endswith(".")

def test_ollama_style_distillation_request_extracts_concrete_review_moves():
    from app import build_ollama_style_distillation_request

    request_prompt = build_ollama_style_distillation_request(
        "meeting_research_pi",
        ["meeting_notes.txt"],
        ["Advisor reframed the work through industry standards, mechanism comparisons, roadmap priority, and action items."],
    )

    assert "Extract reusable review moves" in request_prompt
    assert "reframe" in request_prompt.lower()
    assert "ground" in request_prompt.lower()
    assert "decompose" in request_prompt.lower()
    assert "compare mechanisms" in request_prompt.lower()
    assert "prioritize" in request_prompt.lower()
    assert "action items" in request_prompt.lower()
    assert "Do not write the final reusable prompt" in request_prompt


def test_generate_llm_prompt_for_mode_uses_two_step_style_distillation(monkeypatch):
    import importlib

    app_module = importlib.import_module("app")
    calls = []

    def fake_call_ollama(prompt):
        calls.append(prompt)
        if len(calls) == 1:
            return (
                "PI review moves: reframe the idea as a broader opportunity; ground it in standards, "
                "literature, users, or industry; decompose variables; compare mechanisms; prioritize roadmap; "
                "assign concrete action items."
            )
        return (
            "When reviewing research ideas or meeting minutes, reframe the idea as a broader research "
            "opportunity, ground it in practical context, decompose key variables, compare mechanisms, "
            "prioritize the roadmap, and turn discussion into concrete action items."
        )

    monkeypatch.setenv("PROMPT_LLM_PROVIDER", "ollama")
    monkeypatch.setattr(app_module, "call_ollama_generate", fake_call_ollama)

    result = app_module.generate_llm_prompt_for_mode(
        "meeting_research_pi",
        ["meeting.txt"],
        ["Breathable architecture reference notes about pore topology and vapor transport."],
        "Use the professor's style.",
    )

    assert len(calls) == 2
    assert "Extract reusable review moves" in calls[0]
    assert "Distilled PI review pattern" in calls[1]
    assert "reframe the idea as a broader opportunity" in calls[1]
    assert "Breathable architecture" not in calls[1]
    assert "pore topology" not in calls[1]
    assert "reframe the idea as a broader research opportunity" in result
    assert "action items" in result

def test_final_prompt_request_requires_concrete_advisor_moves_not_generic_checklist():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "meeting_research_pi",
        ["meeting_notes.txt"],
        [],
        "Use the professor's style.",
        distilled_pattern=(
            "reframe the idea as a broader opportunity; ground it in standards and industry; "
            "decompose variables; compare mechanisms; prioritize roadmap; assign action items"
        ),
    )

    assert "must preserve the concrete advisor moves" in request_prompt
    assert "reframe the research opportunity" in request_prompt
    assert "ground it in practical context" in request_prompt
    assert "decompose the problem into variables" in request_prompt
    assert "compare mechanisms" in request_prompt
    assert "prioritize roadmap" in request_prompt
    assert "action items" in request_prompt
    assert "Do not collapse everything into a generic hypothesis-controls-evidence checklist" in request_prompt

def test_final_prompt_request_requires_six_move_sequence_explicitly():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "meeting_research_pi",
        ["meeting_notes.txt"],
        [],
        "Use the professor's style.",
        distilled_pattern=(
            "reframe; ground; decompose; compare mechanisms; prioritize roadmap; assign action items"
        ),
    )

    assert "final prompt should explicitly cover this six-move sequence" in request_prompt
    assert "reframe -> ground -> decompose -> compare -> prioritize -> action items" in request_prompt
    assert "Do not let falsifiability, controls, or evidence dominate the paragraph" in request_prompt
    assert "Use action verbs" in request_prompt
    assert "papers to read" in request_prompt
    assert "data to collect" in request_prompt
    assert "collaborators to contact" in request_prompt

def test_research_meeting_final_request_uses_polished_rhetorical_skeleton():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "meeting_research_pi",
        ["meeting_notes.txt"],
        [],
        "Use the professor's style.",
        distilled_pattern="reframe, ground, decompose, compare, prioritize, action items",
    )

    assert "Use this rhetorical skeleton" in request_prompt
    assert "I first ask whether" in request_prompt
    assert "reframed from a technical task into a broader research opportunity" in request_prompt
    assert "grounded in real context" in request_prompt
    assert "clean decomposition" in request_prompt
    assert "distinguish immediate roadmap priorities from later variables or side projects" in request_prompt
    assert "Ultimately, the next experiment should be capable of changing the project direction" in request_prompt
    assert "Avoid repeating user needs" in request_prompt

def test_prompt_preview_segments_pi_review_text_without_highlights():
    from app import render_prompt_preview

    preview = (
        "I first ask whether the research idea has been reframed from a technical task. "
        "The discussion should be grounded in real context with clean decomposition, "
        "comparison of mechanisms, roadmap priorities, action items, next experiment, "
        "and missing controls."
    )

    rendered = str(render_prompt_preview(preview))

    assert 'class="prompt-highlight"' not in rendered
    assert rendered.count('class="prompt-segment"') == 1
    assert "reframed" in rendered
    assert "grounded" in rendered
    assert "action items" in rendered
    assert "missing controls" in rendered


def test_prompt_preview_groups_long_generated_prompt_into_two_or_three_segments():
    from app import render_prompt_preview

    preview = (
        "When reviewing papers or proposals, I first look for whether the title, abstract, and opening narrative clearly communicate practical value. "
        "The manuscript should build a coherent argument across literature positioning, figures, discussion, and conclusion. "
        "I pay close attention to applicable range, boundary conditions, experimental setup, and usage guidance. "
        "The paper should be grounded in relevant literature, materials comparisons, standards, citations, or application scenarios. "
        "Figures should actively prove the main claim by showing motivation, mechanism, comparison, transition, and decisive evidence. "
        "I also evaluate whether terminology is precise and labels, captions, legends, colors, axes, panel alignment, and font sizes are consistent. "
        "The review should translate these issues into concrete revisions to the title, abstract, figures, captions, discussion, references, or manuscript structure."
    )

    rendered = str(render_prompt_preview(preview))

    assert 'class="prompt-highlight"' not in rendered
    assert 2 <= rendered.count('class="prompt-segment"') <= 3
    assert "practical value" in rendered
    assert "concrete revisions" in rendered

def test_prompt_preview_segmentation_escapes_user_text():
    from app import render_prompt_preview

    rendered = render_prompt_preview('<script>alert(1)</script> reframe action items')

    assert '<script>' not in rendered
    assert '&lt;script&gt;' in rendered
    assert 'class="prompt-highlight"' not in rendered
    assert 'class="prompt-segment"' in rendered
    assert 'reframe action items' in rendered


def test_home_page_renders_segmented_prompt_preview(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Reframe the opportunity and translate discussion into action items."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'class="prompt-segment"' in html
    assert 'class="prompt-highlight"' not in html

def test_paper_proposal_request_uses_manuscript_specific_skeleton():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "paper_proposal_pi",
        ["paper_feedback.docx"],
        [],
        "Use the professor's manuscript feedback style.",
        distilled_pattern="title value; storyline; boundaries; figures prove claims; visual precision",
    )

    assert "Use this Papers/Proposals rhetorical skeleton" in request_prompt
    assert "practical value" in request_prompt
    assert "coherent argument" in request_prompt
    assert "applicable range" in request_prompt
    assert "figures actually prove the main claim" in request_prompt
    assert "precise terminology" in request_prompt
    assert "claim-evidence alignment" in request_prompt
    assert "title, figures, captions, discussion, references, or manuscript structure" in request_prompt
    assert "avoid a checklist-like sequence of repeated 'I expect', 'I require', or 'should' sentences" in request_prompt


def test_paper_proposal_request_refines_reusable_revision_language():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "paper_proposal_pi",
        ["paper_feedback.docx"],
        [],
        "Use the professor's manuscript feedback style.",
        distilled_pattern="value; central claim; literature context; figures; revisions",
    )

    assert "what central claim the manuscript is trying to establish" in request_prompt
    assert "evidence behind each claim" in request_prompt
    assert "checking whether the context is properly supported" in request_prompt
    assert "The review should ultimately translate these issues into concrete revisions" in request_prompt
    assert "replicate the work" not in request_prompt


def test_paper_proposal_request_does_not_include_meeting_specific_six_move_sequence():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "paper_proposal_pi",
        ["paper_feedback.docx"],
        [],
        "Use the professor's manuscript feedback style.",
        distilled_pattern="title value; storyline; boundaries; figures prove claims; visual precision",
    )

    assert "For research ideas or meeting minutes" not in request_prompt
    assert "reframe -> ground -> decompose -> compare -> prioritize -> action items" not in request_prompt
    assert "Do not let falsifiability, controls, or evidence dominate the paragraph" not in request_prompt


def test_slides_talk_request_uses_presentation_specific_skeleton():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "slides_talk_pi",
        ["Feedback on talk slides_251010.txt", "Feedback on talk slides_251008.txt"],
        [],
        "Use the professor's talk-slide feedback style.",
        distilled_pattern=(
            "audience comprehension; precise titles; citations; consistent visual formats; "
            "takeaway messages; delete weak figures; layout and color fixes"
        ),
    )

    assert "Use this Talks/Presentations/Slides rhetorical skeleton" in request_prompt
    assert "audience can follow the story" in request_prompt
    assert "title and opening framing" in request_prompt
    assert "does not artificially narrow the significance" in request_prompt
    assert "cite every non-original figure, claim, chronology, or comparison" in request_prompt
    assert "labels, annotations, colors, legends, and plot formats" in request_prompt
    assert "takeaway message" in request_prompt
    assert "delete weak, confusing, amateur-looking, or low-information slides" in request_prompt
    assert "layout fixes" in request_prompt


def test_slides_talk_request_refines_audience_first_prompt_language():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "slides_talk_pi",
        ["Feedback on talk slides_251010.txt", "Feedback on talk slides_251008.txt"],
        [],
        "Use the professor's talk-slide feedback style.",
        distilled_pattern="audience; title; citations; takeaway; delete weak figures",
    )

    assert "Each slide should help the audience understand the need, logic, and takeaway" in request_prompt
    assert "rather than simply display information" in request_prompt
    assert "avoid a chain of question-form sentences" in request_prompt
    assert "Weak curves, decorative figures, amateur-looking illustrations, or low-information slides" in request_prompt
    assert "The review should ultimately translate into concrete slide-level edits" in request_prompt


def test_slides_talk_request_does_not_include_other_mode_skeletons():
    from app import build_ollama_prompt_request

    request_prompt = build_ollama_prompt_request(
        "slides_talk_pi",
        ["talk_feedback.txt"],
        [],
        "Use the professor's talk-slide feedback style.",
        distilled_pattern="audience comprehension; citations; takeaway messages",
    )

    assert "For research ideas or meeting minutes" not in request_prompt
    assert "Use this Papers/Proposals rhetorical skeleton" not in request_prompt
    assert "reframe -> ground -> decompose -> compare -> prioritize -> action items" not in request_prompt


def test_slides_talk_style_distillation_uses_presentation_review_moves():
    from app import build_ollama_style_distillation_request

    request_prompt = build_ollama_style_distillation_request(
        "slides_talk_pi",
        ["Feedback on talk slides_251010.txt"],
        ["Add labels, cite non-original figures, delete weak curves, and add takeaway messages."],
    )

    assert "Extract reusable slide/talk review moves" in request_prompt
    assert "audience comprehension" in request_prompt
    assert "titles and significance framing" in request_prompt
    assert "citation discipline" in request_prompt
    assert "visual consistency" in request_prompt
    assert "takeaway messages" in request_prompt
    assert "remove weak or amateur-looking visuals" in request_prompt
    assert "- reframe:" not in request_prompt


def test_prompt_preview_is_segmented_not_highlighted():
    from app import render_prompt_preview

    preview = (
        "I first ask whether the research idea has been reframed from a technical task into a broader opportunity. "
        "The discussion should be grounded in real context. "
        "I then look for a clean decomposition of the problem. "
        "The feedback should translate into concrete action items."
    )

    rendered = str(render_prompt_preview(preview))

    assert 'class="prompt-highlight"' not in rendered
    assert 'class="prompt-segment"' in rendered
    assert rendered.count('class="prompt-segment"') >= 2
    assert "reframed" in rendered
    assert "action items" in rendered


def test_home_page_renders_segmented_prompt_preview_without_highlights(tmp_path):
    client = client_with_tmp_outputs(tmp_path)

    response = client.post(
        "/generate-prompts",
        data={
            "research_files": (
                BytesIO(b"Reframe the opportunity. Ground it in context. Translate discussion into action items."),
                "meeting.txt",
            ),
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'class="prompt-segment"' in html
    assert 'class="prompt-highlight"' not in html

