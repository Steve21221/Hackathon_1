# Mentor data

This folder contains the version-controlled starting prompts for every built-in mentor listed in Promptly.

Each mentor has a lowercase, hyphenated directory containing three reviewed prompt files: `meeting_research_pi.txt`, `paper_proposal_pi.txt`, and `slides_talk_pi.txt`. The matching `app.py` mentor entry maps feedback categories to those files. Do not store API keys, private source documents, or confidential personal data here.

## Source-document intake

The website's separate **Mentor data** page saves authorized source documents under `Source_Documents/<mentor-id>/pending/<batch-id>/`. Each batch includes the original files and a `manifest.json` containing the mentor, notes, file hashes, and `pending` status.

`Source_Documents` is excluded from Git because it may contain private or unpublished material. Prompt changes derived from reference documents should be human-reviewed before replacing any of the three version-controlled files.
