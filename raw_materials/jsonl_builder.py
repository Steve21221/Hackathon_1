from __future__ import annotations

import json
import re
from pathlib import Path


SOURCE_TYPE_TO_MENTOR_MODE = {
    "Papers_Proposal": "research_problem_feedback",
    "Research_Meeting_Minutes": "research_problem_feedback",
    "Talk_Presentation_Slides": "presentation_feedback",
}


def default_mentor_mode(source_type: str) -> str:
    if source_type not in SOURCE_TYPE_TO_MENTOR_MODE:
        allowed = ", ".join(SOURCE_TYPE_TO_MENTOR_MODE)
        raise ValueError(f"Unknown source type: {source_type}. Use one of: {allowed}.")
    return SOURCE_TYPE_TO_MENTOR_MODE[source_type]


def slugify(text: str, max_words: int = 6) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    if not words:
        return "sample"
    return "_".join(words[:max_words])


def _first_sentence(chunk: str, max_chars: int = 220) -> str:
    first = re.split(r"(?<=[.!?。！？])\s+", chunk.strip())[0]
    return first[:max_chars].strip()


def infer_main_concern(chunk: str, source_type: str) -> str:
    first = _first_sentence(chunk)
    if source_type == "Papers_Proposal":
        return f"Strengthen the proposal or paper direction based on this raw material: {first}"
    if source_type == "Research_Meeting_Minutes":
        return f"Clarify the research decision, concern, or next step implied by this meeting note: {first}"
    if source_type == "Talk_Presentation_Slides":
        return f"Improve the talk narrative or slide communication based on this raw material: {first}"
    return f"Turn this raw material into actionable mentor-style feedback: {first}"


def infer_action_items(chunk: str) -> list[str]:
    action_verbs = [
        "add",
        "revise",
        "change",
        "remove",
        "delete",
        "include",
        "clarify",
        "cite",
        "show",
        "highlight",
        "move",
        "align",
        "make",
        "compare",
        "explain",
        "修改",
        "加入",
        "删除",
        "强调",
        "说明",
        "引用",
        "展示",
        "调整",
    ]
    sentences = re.split(r"(?<=[.!?。！？])\s+", chunk.strip())
    actions: list[str] = []
    for sentence in sentences:
        clean = sentence.strip(" -•\t")
        lower = clean.lower()
        if 8 <= len(clean) <= 260 and any(verb in lower for verb in action_verbs):
            actions.append(clean)
    if actions:
        return actions[:5]
    return ["Review this raw material and convert the key point into a concrete next action."]


def build_records(
    *,
    chunks: list[str],
    project_name: str,
    source_type: str,
    source_date: str,
    source_file: str,
    mentor_mode: str,
) -> list[dict]:
    project_slug = slugify(project_name, max_words=5)
    type_slug = slugify(source_type, max_words=5)
    file_slug = slugify(Path(source_file).stem, max_words=5)

    records: list[dict] = []
    for index, chunk in enumerate(chunks, start=1):
        record_id = f"{project_slug}_{type_slug}_{file_slug}_{index:03d}"
        records.append(
            {
                "id": record_id,
                "project_name": project_name,
                "source_type": source_type,
                "source_date": source_date,
                "source_file": source_file,
                "mentor_mode": mentor_mode,
                "training_input": {
                    "context": chunk,
                    "task": "Generate mentor-style feedback, critique questions, and concrete action items from this raw material.",
                },
                "training_output": {
                    "main_concern": infer_main_concern(chunk, source_type),
                    "advisor_questions": [
                        "What is the central issue, decision, or opportunity in this raw material?",
                        "What would make the work clearer, stronger, or more convincing?",
                        "What specific next action should the researcher take?",
                    ],
                    "critique_points": [
                        "This is an automatically generated draft record and should be reviewed by a human.",
                        "Check whether the extracted context captures one coherent feedback unit.",
                    ],
                    "missing_or_weak_elements": [
                        "Human verification is still needed before using this record for training."
                    ],
                    "action_items": infer_action_items(chunk),
                    "ideal_response": (
                        "Draft mentor response: identify the core concern, explain why it matters, "
                        "ask clarifying questions, and convert the raw material into specific next steps."
                    ),
                },
                "tags": [source_type, "draft", "needs_review"],
                "persona_patterns": [
                    "direct but constructive advisor feedback",
                    "convert vague comments into concrete revision actions",
                    "ask clarifying questions before over-claiming",
                ],
                "metadata": {
                    "source_section": f"{source_file} / chunk {index}",
                    "needs_anonymization": True,
                    "verified_by_human": False,
                    "confidence": "draft",
                },
            }
        )
    return records


def records_to_jsonl(records: list[dict]) -> str:
    return "\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n"


def records_to_pretty_json(records: list[dict]) -> str:
    return json.dumps(records, ensure_ascii=False, indent=2)


def records_to_preview_markdown(records: list[dict]) -> str:
    lines = ["# Draft JSONL Preview", "", f"- Total draft records: {len(records)}", ""]
    for index, record in enumerate(records, start=1):
        lines.extend(
            [
                f"## {index}. {record['id']}",
                "",
                f"- Project: {record['project_name']}",
                f"- Source type: {record['source_type']}",
                f"- Source file: {record['source_file']}",
                f"- Source section: {record['metadata']['source_section']}",
                "- verified_by_human: false",
                "",
                "### Main concern",
                "",
                record["training_output"]["main_concern"],
                "",
                "### Action items",
                "",
            ]
        )
        for item in record["training_output"]["action_items"]:
            lines.append(f"- {item}")
        lines.extend(["", "---", ""])
    return "\n".join(lines)
