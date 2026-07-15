from __future__ import annotations

import re


FEEDBACK_HEADING_PATTERN = re.compile(r"(?im)^\s*Feedback\s+\d+\s*:\s*")
NUMBERED_PATTERN = re.compile(r"(?m)^\s*\d+[\.\)]\s+")
HEADING_PATTERN = re.compile(r"(?m)^(?:#{1,4}\s+|[A-Z][A-Za-z0-9 _/-]{3,}:)\s*")


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_by_pattern(text: str, pattern: re.Pattern[str], strip_pattern: bool = False) -> list[str]:
    matches = list(pattern.finditer(text))
    if len(matches) <= 1:
        return []

    chunks: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if strip_pattern:
            chunk = pattern.sub("", chunk, count=1).strip()
        if len(chunk) >= 10:
            chunks.append(chunk)
    return chunks


def _split_paragraph_groups(text: str, max_chars: int = 1800) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n", text) if p.strip()]
    groups: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if current and current_len + len(paragraph) > max_chars:
            groups.append("\n".join(current))
            current = []
            current_len = 0
        current.append(paragraph)
        current_len += len(paragraph)

    if current:
        groups.append("\n".join(current))

    return [group for group in groups if len(group) >= 10]


def chunk_text(text: str, source_type: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    feedback_chunks = _split_by_pattern(normalized, FEEDBACK_HEADING_PATTERN)
    if feedback_chunks:
        return feedback_chunks

    numbered_chunks = _split_by_pattern(normalized, NUMBERED_PATTERN, strip_pattern=True)
    if numbered_chunks:
        return numbered_chunks

    if source_type in {"Papers_Proposal", "Talk_Presentation_Slides"}:
        heading_chunks = _split_by_pattern(normalized, HEADING_PATTERN)
        if heading_chunks:
            return heading_chunks

    return _split_paragraph_groups(normalized)
