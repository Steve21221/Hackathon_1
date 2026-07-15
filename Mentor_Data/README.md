# Mentor data

This folder contains the extracted style prompt for every mentor listed in Promptly.

Each mentor entry in `app.py` must identify a prompt file from this folder. Use the mentor's lowercase, hyphenated identifier as the filename, such as `dr-nanshu-lu.txt`. Do not store API keys, private source documents, or confidential personal data here.

## Source-document intake

The website's separate **Mentor data** page saves authorized source documents under `Source_Documents/<mentor-id>/pending/<batch-id>/`. Each batch includes the original files and a `manifest.json` containing the mentor, notes, file hashes, and `pending` status.

`Source_Documents` is excluded from Git because it may contain private or unpublished material. A separate extraction program can watch the pending folders, derive a proposed mentor-style prompt, and update the corresponding `<mentor-id>.txt` file only after review.
