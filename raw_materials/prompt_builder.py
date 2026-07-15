from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Iterable


@dataclass(frozen=True)
class PromptArtifact:
    mode: str
    label: str
    filename: str
    content: str
    source_files: list[str]
    record_count: int


MODE_DEFINITIONS = {
    "meeting_research_pi": {
        "label": "Research Ideas / Meeting Minutes",
        "review_target": "research ideas or meeting minutes",
        "priority_sentence": (
            "Prioritize a falsifiable research question, explicit controls, concrete next experiments, "
            "and whether the discussion leads to a real decision."
        ),
        "deliverable_sentence": (
            "Return one concise PI assessment, three technical corrections, and two critical questions "
            "or next experiments."
        ),
        "lens": (
            "For research ideas and meeting minutes, prioritize whether the research question is "
            "falsifiable, whether controls and next experiments are clear, and whether the discussion "
            "led to a concrete decision."
        ),
        "fallback_focus": [
            "research question clarity",
            "hypothesis logic",
            "missing controls",
            "feasibility",
            "next experiment",
            "whether a real decision was made",
        ],
        "instruction": (
            "You are reviewing research ideas, meeting notes, experiment plans, and lab discussion "
            "records in a strict PI style. Focus on research logic, feasibility, missing controls, "
            "decision clarity, and concrete next experiments."
        ),
    },
    "slides_talk_pi": {
        "label": "Talks / Presentations / Slides",
        "review_target": "talks, presentations, or slides",
        "priority_sentence": (
            "Prioritize one clear takeaway per slide, figure-to-message alignment, visual hierarchy, "
            "and whether the scientific story can be followed without extra explanation."
        ),
        "deliverable_sentence": (
            "Return one concise PI assessment, three slide-level fixes, and two questions that expose "
            "weak story logic."
        ),
        "lens": (
            "For talks and slides, prioritize whether every slide has one takeaway, whether figures "
            "prove the message, and whether visual hierarchy makes the scientific story obvious."
        ),
        "fallback_focus": [
            "slide layout",
            "visual hierarchy",
            "title and takeaway alignment",
            "duplicate panels",
            "figure clarity",
            "storyline",
        ],
        "instruction": (
            "You are reviewing talks, presentation slides, figure sets, and visual scientific stories "
            "in a strict PI style. Focus on layout, figure clarity, visual hierarchy, duplicated panels, "
            "and whether each slide supports one message."
        ),
    },
    "paper_proposal_pi": {
        "label": "Papers / Proposals",
        "review_target": "papers, proposals, or manuscripts",
        "priority_sentence": (
            "Prioritize claim strength, evidence-to-claim alignment, novelty, mechanism support, "
            "and whether the writing overclaims beyond the data."
        ),
        "deliverable_sentence": (
            "Return one concise PI assessment, three manuscript-level revisions, and two critical "
            "questions for strengthening the argument."
        ),
        "lens": (
            "For papers and proposals, prioritize claim strength, evidence-to-claim alignment, novelty, "
            "mechanistic support, and whether the writing overclaims beyond the data."
        ),
        "fallback_focus": [
            "claim strength",
            "evidence quality",
            "novelty",
            "logic gaps",
            "overclaiming",
            "mechanism support",
            "citation or comparison needs",
        ],
        "instruction": (
            "You are reviewing papers, proposals, manuscripts, and written scientific arguments in a "
            "strict PI style. Focus on claim strength, evidence quality, novelty, logical gaps, "
            "overclaiming, mechanism support, and missing comparisons."
        ),
    },
}

ACTION_VERBS = {
    "add", "remove", "revise", "change", "clarify", "show", "include", "move",
    "compare", "explain", "support", "strengthen", "define", "separate", "cite",
}
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "you", "are", "was",
    "were", "have", "has", "not", "but", "into", "more", "than", "then", "they", "their",
    "current", "should", "could", "would", "about", "when", "where", "which", "what",
    "like", "just", "because", "okay", "yeah", "also", "really", "actually", "maybe",
    "kind", "sort", "thing", "things", "professor", "asks", "asked",
}

INCOMPLETE_ENDINGS = (
    " as a", " as an", " as the", " such as", " because", " due to", " based on",
    " with", " without", " for", " from", " into", " and", " or", " to", " of", " by",
)

LEADING_FILLER_PATTERN = re.compile(
    r"^(so|like|okay|ok|yeah|um|uh|actually|basically|i think|you know)[,:\s]+",
    flags=re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text.strip())
    return [part.strip(" -•\t") for part in parts if len(part.strip()) >= 8]


def _clean_sentence(sentence: str) -> str | None:
    """Return a polished sentence fragment, or None when the input is filler/incomplete."""
    cleaned = re.sub(r"\s+", " ", sentence).strip(" -•\t")
    while True:
        updated = LEADING_FILLER_PATTERN.sub("", cleaned).strip()
        if updated == cleaned:
            break
        cleaned = updated
    cleaned = re.sub(r"\b(ok|okay|yeah|um|uh)\b,?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()
    lower = cleaned.lower().rstrip(".。!?！？")
    if lower.startswith(("just because", "because ")):
        return None
    if len(cleaned.split()) < 5:
        return None
    if any(lower.endswith(ending) for ending in INCOMPLETE_ENDINGS):
        return None
    filler_count = sum(1 for word in re.findall(r"[a-z]+", lower) if word in STOPWORDS)
    word_count = max(1, len(re.findall(r"[a-z]+", lower)))
    if word_count >= 5 and filler_count / word_count > 0.55:
        return None
    return cleaned[:260]


def _iter_chunks(grouped_chunks: dict[str, list[dict]]) -> Iterable[tuple[str, str, str]]:
    for mode, file_groups in grouped_chunks.items():
        for group in file_groups:
            source_file = str(group.get("source_file", "unknown"))
            for chunk in group.get("chunks", []):
                if str(chunk).strip():
                    yield mode, source_file, str(chunk).strip()


def extract_keywords(chunks: list[str], limit: int = 12) -> list[str]:
    counts: dict[str, int] = {}
    for chunk in chunks:
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", chunk.lower()):
            if word in STOPWORDS:
                continue
            if word.endswith(("ing", "ed")) and word in {"using", "being", "going"}:
                continue
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _count in ranked[:limit]]


def extract_key_sentences(chunks: list[str], limit: int = 6) -> list[str]:
    selected: list[str] = []
    fallback: list[str] = []
    for chunk in chunks:
        for sentence in _sentences(chunk):
            cleaned = _clean_sentence(sentence)
            if not cleaned:
                continue
            lower = cleaned.lower()
            if any(verb in lower for verb in ACTION_VERBS) or len(selected) < 2:
                selected.append(cleaned)
            else:
                fallback.append(cleaned)
            if len(selected) >= limit:
                return selected
    return (selected + fallback)[:limit]


def extract_professor_concerns(chunks: list[str], limit: int = 5) -> list[str]:
    """Extract concrete concerns that look like PI/professor feedback patterns."""
    concern_markers = (
        "professor", "pi", "ask", "asks", "concern", "worry", "missing", "control",
        "clarify", "revise", "remove", "add", "claim", "evidence", "hypothesis",
        "mechanism", "sample size", "next experiment", "takeaway", "overclaim",
    )
    concerns: list[str] = []
    for chunk in chunks:
        for sentence in _sentences(chunk):
            cleaned = _clean_sentence(sentence)
            if not cleaned:
                continue
            lower = cleaned.lower()
            if any(marker in lower for marker in concern_markers):
                concerns.append(cleaned)
            if len(concerns) >= limit:
                return concerns
    return extract_key_sentences(chunks, limit=limit)


def _join_signals(items: list[str], limit: int = 2) -> str:
    signals = [item.rstrip(".。!?！？") for item in items[:limit] if item.strip()]
    if not signals:
        return "the recurring expectations in the uploaded reference materials"
    if len(signals) == 1:
        return signals[0]
    return "; ".join(signals)


def build_specific_prompt_paragraph(mode: str, concerns: list[str], keywords: list[str]) -> str:
    definition = MODE_DEFINITIONS[mode]
    priority_sentence = str(definition["priority_sentence"])
    priority_sentence = priority_sentence[:1].lower() + priority_sentence[1:]
    return (
        f"Use the professor's style: direct, skeptical, evidence-driven, and specific. "
        "Use the uploaded files only as reference examples for the PI's review habits; do not assume "
        "the future project has the same topic, material system, mechanism, or dataset. "
        f"When reviewing {definition['review_target']}, {priority_sentence} "
        "Translate the learned style into general checks: test whether the central question is sharp, "
        "whether the mechanism or claim is falsifiable, whether controls isolate the key variable, "
        "whether evidence actually supports the conclusion, and whether the next experiment would "
        "change the decision. Name the missing control, weak claim, unclear mechanism, unsupported "
        f"comparison, or decisive next experiment instead of giving generic encouragement. "
        f"{definition['deliverable_sentence']}"
    )


def build_prompt_content(
    mode: str,
    source_files: list[str],
    chunks: list[str],
    generated_prompt_override: str | None = None,
) -> str:
    definition = MODE_DEFINITIONS[mode]
    keywords = extract_keywords(chunks)
    key_sentences = extract_key_sentences(chunks)
    professor_concerns = extract_professor_concerns(chunks)
    focus_items = definition["fallback_focus"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    reference_lines = key_sentences or [
        "Use the uploaded reference materials to infer concise, concrete PI-style criticism."
    ]
    keyword_lines = keywords or focus_items
    concern_lines = professor_concerns or reference_lines
    generated_prompt = (
        generated_prompt_override.strip()
        if generated_prompt_override and generated_prompt_override.strip()
        else build_specific_prompt_paragraph(mode, concern_lines, keyword_lines)
    )

    return "\n".join(
        [
            f"MODE: {mode}",
            f"SOURCE CATEGORY: {definition['label']}",
            f"SOURCE FILES: {'; '.join(source_files) if source_files else 'No uploaded references; using default mode prompt.'}",
            f"CREATED AT: {created_at}",
            "",
            definition["instruction"],
            definition["lens"],
            "",
            "Focus on:",
            *[f"- {item}" for item in focus_items],
            "",
            "Professor concern profile learned from uploaded files:",
            *[f"- {item}" for item in concern_lines],
            "",
            "Keywords extracted from uploaded raw materials:",
            *[f"- {item}" for item in keyword_lines],
            "",
            "Reference patterns extracted from uploaded raw materials:",
            *[f"- {item}" for item in reference_lines],
            "",
            "Generated PI-style prompt:",
            generated_prompt,
            "",
            "PI-style response rules:",
            "- Be direct, concise, critical, and specific.",
            "- Use short sentences and concrete edits.",
            "- Prefer commands such as change, remove, add, move, show, clarify, and do not show.",
            "- Focus on clarity, evidence quality, plausibility, structure, technical consistency, and actionable next steps.",
            "- Do not sound generic or overly polite.",
            "",
            "Required response structure:",
            "PI: <one concise assessment sentence>",
            "",
            "Technical corrections needed:",
            "- <bullet>",
            "- <bullet>",
            "- <bullet>",
            "",
            "Implementation issues:",
            "- <bullet>",
            "- <bullet>",
            "- <bullet>",
            "",
            "Critical questions:",
            "- <bullet>",
        ]
    ) + "\n"


def build_mode_prompt_artifacts(
    grouped_chunks: dict[str, list[dict]],
    generated_prompts: dict[str, str] | None = None,
) -> dict[str, PromptArtifact]:
    artifacts: dict[str, PromptArtifact] = {}
    generated_prompts = generated_prompts or {}
    for mode, definition in MODE_DEFINITIONS.items():
        file_groups = grouped_chunks.get(mode, [])
        source_files: list[str] = []
        chunks: list[str] = []
        for group in file_groups:
            source_file = str(group.get("source_file", "unknown"))
            if source_file not in source_files:
                source_files.append(source_file)
            chunks.extend(str(chunk).strip() for chunk in group.get("chunks", []) if str(chunk).strip())
        content = build_prompt_content(
            mode,
            source_files,
            chunks,
            generated_prompt_override=generated_prompts.get(mode),
        )
        artifacts[mode] = PromptArtifact(
            mode=mode,
            label=str(definition["label"]),
            filename=f"{mode}_prompt.txt",
            content=content,
            source_files=source_files,
            record_count=len(chunks),
        )
    return artifacts


def build_combined_prompt_text(artifacts: dict[str, PromptArtifact]) -> str:
    sections: list[str] = []
    for mode in MODE_DEFINITIONS:
        artifact = artifacts[mode]
        sections.append("=" * 80)
        sections.append(artifact.content.strip())
    return "\n\n".join(sections) + "\n"
