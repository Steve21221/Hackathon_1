from __future__ import annotations



import re



from raw_materials.prompt_builder import MODE_DEFINITIONS





MAX_OLLAMA_REFERENCE_CHARS = 12_000





def build_ollama_style_distillation_request(
    mode: str,
    source_files: list[str],
    chunks: list[str],
) -> str:
    """Ask Ollama to extract reusable PI review moves before writing a prompt."""
    definition = MODE_DEFINITIONS[mode]
    reference_text = "\n\n".join(chunks)[:MAX_OLLAMA_REFERENCE_CHARS]
    source_line = "; ".join(source_files) if source_files else "uploaded reference materials"
    if mode == "slides_talk_pi":
        extraction_guidance = (
            "Extract reusable slide/talk review moves in this exact spirit:\n"
            "- audience comprehension: how the PI makes the talk easy to follow through labels, callouts, and visual cues\n"
            "- titles and significance framing: how titles, opening context, and background slides communicate broad importance without narrowing impact\n"
            "- citation discipline: how every non-original figure, chronology, comparison, or claim is cited in the right place\n"
            "- visual consistency: how similar plots, colors, labels, legends, and formats stay consistent across slides\n"
            "- takeaway messages: how each slide or section tells the audience what to remember\n"
            "- remove weak or amateur-looking visuals: how the PI deletes poor curves, decorative figures, clutter, or unprofessional illustrations\n"
            "- slide-level fixes: how the PI gives concrete layout, color, label, citation, and figure-placement edits\n\n"
        )
    elif mode == "paper_proposal_pi":
        extraction_guidance = (
            "Extract reusable manuscript/proposal review moves in this exact spirit:\n"
            "- practical value: how the title, abstract, and opening explain why the work matters\n"
            "- coherent argument: how literature, figures, discussion, and conclusion reinforce one central claim\n"
            "- boundaries: how applicable range, setup, controls, and usage guidance are clarified\n"
            "- context: how literature, materials comparisons, standards, citations, and applications broaden the frame\n"
            "- figure proof: how figures prove the main claim through motivation, mechanism, comparisons, transitions, and decisive evidence\n"
            "- precision: how terminology, labels, captions, legends, axes, colors, and layout are made publication-ready\n"
            "- concrete revisions: how feedback turns into edits to title, figures, captions, discussion, references, or structure\n\n"
        )
    else:
        extraction_guidance = (
            "Extract reusable review moves in this exact spirit:\n"
            "- reframe: how the PI reframes a technical task as a broader research opportunity\n"
            "- ground: how the PI grounds the idea in standards, literature, user needs, industry examples, or practical context\n"
            "- decompose: how the PI breaks the problem into variables, design parameters, constraints, and measurable outcomes\n"
            "- compare mechanisms: how the PI asks for competing mechanisms, alternative explanations, and necessary comparisons\n"
            "- prioritize: how the PI separates immediate roadmap priorities from later variables or side projects\n"
            "- action items: how the PI turns discussion into papers to read, data to collect, collaborators to contact, or experiments to run\n\n"
        )
    return (
        "You are distilling a professor's review style from raw reference materials.\n"
        "Do not write the final reusable prompt yet. Extract reusable review moves only.\n"
        "The uploaded project is an example for style distillation, not the future review target.\n"
        "Do not copy project-specific nouns, material systems, sample names, mechanisms, or project goals.\n\n"
        f"Mode: {definition['label']}\n"
        f"Source files: {source_line}\n\n"
        f"{extraction_guidance}"
        "Return 5-7 concise bullets. Each bullet must describe a reusable review habit, not a project detail.\n\n"
        f"Uploaded reference material excerpts:\n{reference_text}"
    )

def build_ollama_prompt_request(
    mode: str,
    source_files: list[str],
    chunks: list[str],
    deterministic_prompt: str,
    distilled_pattern: str | None = None,
) -> str:
    definition = MODE_DEFINITIONS[mode]
    source_line = "; ".join(source_files) if source_files else "uploaded reference materials"
    pattern = distilled_pattern.strip() if distilled_pattern and distilled_pattern.strip() else (
        "Use the mode priorities and deterministic draft as the style pattern."
    )
    rhetorical_skeleton = ""
    mode_specific_guidance = ""
    if mode == "meeting_research_pi":
        mode_specific_guidance = (
            "The final paragraph must preserve the concrete advisor moves when they are present in the pattern: "
            "reframe the research opportunity, ground it in practical context such as standards/literature/user needs/industry, "
            "decompose the problem into variables or design parameters, compare mechanisms or competing explanations, "
            "prioritize roadmap and scope, and convert the discussion into concrete action items. "
            "Do not collapse everything into a generic hypothesis-controls-evidence checklist; hypothesis, controls, "
            "and evidence are useful only when integrated with framing, mechanism comparison, prioritization, and next actions.\n\n"
            "A strong final paragraph should use concrete verbs like reframe, ground, decompose, compare, prioritize, "
            "and translate into action items when the distilled pattern supports them.\n\n"
            "For research ideas or meeting minutes, the final prompt should explicitly cover this six-move sequence: "
            "reframe -> ground -> decompose -> compare -> prioritize -> action items. "
            "Do not let falsifiability, controls, or evidence dominate the paragraph; include them only as part of the "
            "broader advisor workflow. Use action verbs. Make the final clause emphasize concrete next steps such as "
            "papers to read, data to collect, collaborators to contact, comparisons to run, or experiments to prioritize.\n\n"
        )
        rhetorical_skeleton = (
            "Use this rhetorical skeleton for the final paragraph, adapting wording but preserving the logic: "
            "I first ask whether the idea has been reframed from a technical task into a broader research opportunity "
            "with clear practical relevance. The discussion should be grounded in real context, such as standards, "
            "literature, industry examples, user needs, or measurable pain points. I then look for a clean decomposition "
            "of the problem into variables, design parameters, constraints, and measurable outcomes, followed by a "
            "comparison of competing mechanisms or alternative explanations. The feedback should distinguish immediate "
            "roadmap priorities from later variables or side projects before judging detailed experiments, and translate the discussion into concrete action "
            "items: papers to read, data to collect, collaborators to contact, comparisons to run, or experiments to "
            "prioritize. Ultimately, the next experiment should be capable of changing the project direction. "
            "Avoid repeating user needs or any other criterion twice.\n\n"
        )
    elif mode == "slides_talk_pi":
        rhetorical_skeleton = (
            "Use this Talks/Presentations/Slides rhetorical skeleton for the final paragraph, adapting wording but preserving "
            "the logic; avoid a generic design-polish checklist and avoid a chain of question-form sentences. Begin with whether "
            "the audience can follow the story and immediately understand the scientific logic from the title and opening framing, as well as the slide sequence. "
            "Each slide should help the audience understand the need, logic, and takeaway of the work rather than simply display "
            "information. Emphasize specific slide titles, broad significance framing that does not artificially narrow the "
            "significance of the work, and background or chronology slides that establish a clear need for the research. "
            "The prompt should require the reviewer to cite every non-original figure, claim, chronology, or comparison in the "
            "right visual location, and to add labels, annotations, parentheses, callouts, and visual cues wherever they help "
            "the audience follow. Similar concepts should use consistent labels, annotations, colors, legends, and plot formats "
            "across the talk. The prompt should explicitly delete weak, confusing, amateur-looking, or low-information slides. "
            "Weak curves, decorative figures, amateur-looking illustrations, or low-information slides should be removed or replaced with concise summaries. "
            "The review should ultimately translate into concrete slide-level "
            "edits to titles, citations, labels, figure choices, layout fixes, visual consistency, takeaway messages, and "
            "audience guidance.\n\n"
        )
    elif mode == "paper_proposal_pi":
        rhetorical_skeleton = (
            "Use this Papers/Proposals rhetorical skeleton for the final paragraph, adapting wording but preserving the logic; "
            "avoid a checklist-like sequence of repeated 'I expect', 'I require', or 'should' sentences. Begin with whether "
            "the title, abstract, and opening narrative clearly communicate the practical value of the work, why the reader "
            "should care, and what central claim the manuscript is trying to establish. Then evaluate whether the manuscript "
            "builds a coherent argument in which literature positioning, figures, discussion, and conclusion reinforce the same "
            "claim rather than functioning as separate sections. Pay close attention to the applicable range, boundary conditions, "
            "experimental setup, and evidence behind each claim while checking whether the context is properly supported by "
            "relevant literature, materials comparisons, standards, citations, or application scenarios. Examine whether the "
            "figures actually prove the main claim through motivation, mechanism, comparison, transitions, and decisive evidence "
            "rather than decorative or low-information panels. Also evaluate precise terminology and consistent captions, labels, "
            "legends, colors, axes, panel alignment, and layout so that claim-evidence alignment is maintained throughout. "
            "The review should ultimately translate these issues into concrete revisions to the title, figures, captions, "
            "discussion, references, or manuscript structure, including the abstract when needed.\n\n"
        )
    return (
        "You are helping build a reusable PI-style review prompt from raw reference materials.\n"
        "Do not write a prompt for the uploaded project. The uploaded project is only a reference example "
        "for learning the professor's thinking pattern.\n"
        "Task: write ONE polished, professional, copy-ready, general-purpose prompt paragraph for a future project reviewer.\n"
        "Do not summarize the files for the user. Do not mention that you are an AI. Do not use markdown.\n"
        "The paragraph must be fluent, mode-specific, directly useful, and reusable across projects.\n"
        "Do NOT mention project-specific nouns, material systems, sample names, device names, project names, "
        "or mechanisms from the uploaded reference. Generalize project-specific content into broad review habits, "
        "not topic details.\n"
        "Write a single refined paragraph, not a checklist. Do not repeat the same checklist in different words. "
        "Avoid internal or mechanical phrases such as 'for a project in this mode', 'Specifically, test whether', "
        "'this uploaded-material signal', or 'mode priorities'. Before returning, silently revise your draft once "
        "for elegance, concision, non-redundancy, and copy-ready wording.\n"
        "Bad output: a prompt about the uploaded project itself. Good output: a prompt that can review any future project "
        "in the same mode using the learned PI style.\n\n"
        f"Mode: {definition['label']}\n"
        f"Source files: {source_line}\n"
        f"Mode priorities, to include only if they fit the pattern naturally: {definition['priority_sentence']}\n"
        f"Expected response shape, as optional guidance only: {definition['deliverable_sentence']}\n\n"
        "Use the distilled PI review pattern below as the main input. It already abstracts away project details.\n\n"
        f"Distilled PI review pattern:\n{pattern}\n\n"
        f"{mode_specific_guidance}"
        f"{rhetorical_skeleton}"
        f"General deterministic draft to improve:\n{deterministic_prompt}\n\n"
        "Return only the final general-purpose single refined paragraph, 90-140 words."
    )

def polish_llm_prompt_output(text: str) -> str:
    """Remove common mechanical LLM artifacts from generated prompt paragraphs."""
    polished = text.strip().strip('"').strip("'").strip()
    polished = polished.replace("\n", " ")
    mechanical_phrases = [
        " for a project in this mode",
        " in this mode",
        " this uploaded-material signal",
        " mode priorities",
    ]
    for phrase in mechanical_phrases:
        polished = polished.replace(phrase, "")
        polished = polished.replace(phrase.title(), "")
    polished = re.sub(
        r"\s*Specifically,\s+test whether\b.*?(?:\.\s*|$)",
        " ",
        polished,
        flags=re.IGNORECASE,
    )
    polished = re.sub(r"\s+", " ", polished).strip()
    polished = re.sub(r"\s+([,.;:])", r"\1", polished)
    if polished and polished[-1] not in ".!?":
        polished += "."
    return polished
