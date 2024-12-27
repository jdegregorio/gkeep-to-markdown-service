import os
import time
import re
import requests
import mimetypes
from loguru import logger
from git import Repo, GitCommandError
import gkeepapi

from app.config import Config
from app.clients.keep_client import authenticate_keep, get_ready_notes, archive_note
from app.clients.llm_client import generate_note_fields, parse_generated_content
from app.clients.git_client import setup_ssh_for_git, clone_repo_if_needed, commit_and_push_new_files
from app.utils.helper import (
    format_title,
    handle_duplicate_name,
    markdown_bulletize_list
)

def run_sync() -> int:
    """
    Main entrypoint to run the sync logic:
    1. Sets up Git SSH
    2. Authenticates to Google Keep
    3. Processes notes with 'READY_TO_EXPORT_LABEL'
    4. Calls LLM for enrichment
    5. Saves to local Git repo, pushes to remote
    6. Archives note in Keep
    Returns: count of processed notes
    """
    # 1. Setup Git SSH
    setup_ssh_for_git(Config.GIT_SSH_KEY)

    # 2. Clone or pull the repo locally if needed
    clone_repo_if_needed(Config.REPO_REMOTE_URL, Config.REPO_DIR)

    # 3. Auth to Google Keep
    keep = authenticate_keep(
        Config.GOOGLE_KEEP_USERNAME,
        Config.GOOGLE_KEEP_MASTER_TOKEN
    )

    # 4. Find notes that are ready to export
    notes = get_ready_notes(keep, Config.READY_TO_EXPORT_LABEL)
    notes = list(notes)

    if not notes:
        logger.info("No notes found for export.")
        return 0

    repo = Repo(Config.REPO_DIR)

    processed_count = 0
    for note in notes:
        note_title, saved_file = process_note_and_save(note, keep, repo)
        logger.info(f"Processed note: {note_title} -> {saved_file}")
        processed_count += 1

    logger.info(f"Processed {processed_count} notes total.")
    return processed_count

def process_note_and_save(note, keep, repo):
    """
    Process an individual Google Keep note, call LLM, save to Git, archive note.
    """
    text = note.text
    # Convert checkboxes
    text = text.replace(u"\u2610", "- [ ]").replace(u"\u2611", "- [x]")
    # Convert URLs
    urls = re.findall(
        r"https?://(?:[a-zA-Z0-9~#$-_@.&+!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
        text
    )
    for url in urls:
        text = text.replace(url, f"[{url}]({url})")

    # 1. Generate note fields from LLM
    generated_response = generate_note_fields(note.title, note.text)
    generated_attr = parse_generated_content(generated_response)

    # 2. Determine final note title
    if not note.title:
        note_title = generated_attr["note_title"]
    else:
        note_title = note.title

    formatted_title = format_title(note_title)
    unique_title = handle_duplicate_name(formatted_title, Config.OUTPUT_DIR)

    # 3. Write the base note to a markdown file
    md_path = os.path.join(Config.OUTPUT_DIR, unique_title + ".md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(text)

    # 4. Save attachments (blobs)
    for idx, blob in enumerate(note.blobs):
        blob_name = f"{unique_title.lower().replace(' ', '-')}-{idx}"
        url = keep.getMediaLink(blob)
        response = requests.get(url, allow_redirects=True)
        content_type = response.headers.get("content-type", "")
        ext = mimetypes.guess_extension(content_type) or ""

        media_file_path = os.path.join(Config.MEDIA_DIR, blob_name + ext)
        with open(media_file_path, "wb") as media_file:
            media_file.write(response.content)

        # Append reference to media in the .md
        with open(md_path, "a", encoding="utf-8") as f:
            f.write(f"\n![{blob_name}]({os.path.join(Config.MEDIA_FOLDER, blob_name + ext)})\n")

    # 5. Append generated attributes
    with open(md_path, "a", encoding="utf-8") as f:
        f.write("\n\n---\n")
        f.write(f"#type/{generated_attr['note_type']} (generated)\n\n")

        topics_contained = markdown_bulletize_list(generated_attr["note_topics_contained"], double_brackets=True)
        topics_related = markdown_bulletize_list(generated_attr["note_topics_related"], double_brackets=True)

        f.write(f"**Contained Topics**:\n{topics_contained}\n\n")
        f.write(f"**Related Topics**:\n{topics_related}\n\n")

        f.write("---\n\n")
        f.write(f"**Suggested Title**: {generated_attr['note_title']}\n\n")
        f.write(f"**Key Ideas**:\n{generated_attr['note_ideas']}\n\n")
        f.write(f"**Rewritten Note**:\n{generated_attr['note_rewrite']}\n\n")

    # 6. Commit & push changes
    commit_message = f"Adding note {unique_title}"
    commit_and_push_new_files(repo, commit_message)

    # 7. Archive note in Keep
    archive_note(keep, note, Config.READY_TO_EXPORT_LABEL, Config.SUCCESSFUL_EXPORT_LABEL)

    return note_title, md_path
