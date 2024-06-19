import os
import re
import requests
import time
import gkeepapi
import mimetypes
from dotenv import load_dotenv

import logging
from loguru import logger

import sys
from generate import generate_note_fields, parse_generated_content
from git_utils import clone_repo, commit_and_push_new_files
from git import Repo
from utils import format_title, markdown_bulletize_list, handle_duplicate_name

# Load environment variables (i.e. secrets)
load_dotenv()

# Configure logging
logger.add("service.log", rotation="10 MB")

# Define config variables
READY_TO_EXPORT_LABEL = 'Ready to Export'
SUCCESSFUL_EXPORT_LABEL = 'Succesfully Exported'
EXPORT_NOTE_TYPE = gkeepapi.node.NodeType.Note  # define the type of note you want to export
OUTPUT_DIR = './second-brain/Inbox/'
MEDIA_DIR = './second-brain/Attachments/'

# Define git repo parameters
REPO_REMOTE_URL = 'git@github.com:jdegregorio/second-brain.git'
REPO_NAME = 'second-brain'
REPO_DIR = f'./{REPO_NAME}'
GIT_REMOTE = 'origin'
GIT_BRANCH = 'gkeep-exported-notes'

# Prepare git repo
if not os.path.exists(OUTPUT_DIR):
    clone_repo(REPO_REMOTE_URL)
repo = Repo(REPO_DIR)

# Authenticate Google Account
user = os.getenv('GOOGLE_KEEP_USERNAME')
password = os.getenv('GOOGLE_KEEP_PASSWORD')
master_token = os.getenv('GOOGLE_KEEP_MASTER_TOKEN')

# Authenticate
keep = gkeepapi.Keep()
keep.authenticate('user@gmail.com', master_token)

while True:

    # Sync and download all notes with the "export" label
    keep.sync()
    label = keep.findLabel(READY_TO_EXPORT_LABEL)

    # Find all notes that are ready to export
    notes = keep.find(archived=False, trashed=False, func=lambda x: x.type == EXPORT_NOTE_TYPE, labels=[label])
    notes = list(notes)

    for note in notes:

        # Convert note to markdown
        text = note.text

        # Format checkboxes
        text = text.replace(u"\u2610", '- [ ]').replace(u"\u2611", ' - [x]')

        # Format URLs
        urls = re.findall(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[~#$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            text
        )
        for url in urls:
            text = text.replace(url, f"[{url}]({url})")

        # Generate note attributes
        generated_response = generate_note_fields(note)
        generated_attr = parse_generated_content(generated_response)

        if not note.title:
            note.title = generated_attr['note_title']

        # Handle duplicate names
        formatted_title = format_title(note.title)
        unique_title = handle_duplicate_name(formatted_title, OUTPUT_DIR)

        # Save note
        with open(os.path.join(OUTPUT_DIR, unique_title + '.md'), 'w') as f:
            f.write(text)

        # Save blobs
        for idx, blob in enumerate(note.blobs):
            blob_name = unique_title.lower().replace(' ', '-') + '-' + str(idx)
            url = keep.getMediaLink(blob)

            response = requests.get(url, allow_redirects=True)

            # Identify the extension of the file from the Content-Type header
            content_type = response.headers['content-type']
            ext = mimetypes.guess_extension(content_type)

            with open(os.path.join(MEDIA_DIR, blob_name + ext), 'wb') as media_file:
                media_file.write(response.content)

            # Append the media link at the end of the note
            with open(os.path.join(OUTPUT_DIR, unique_title + '.md'), 'a') as f:
                f.write(f"\n![{blob_name}]({os.path.join(MEDIA_DIR, blob_name + ext)})")


        # Parse/Process generated attributes
        title = generated_attr['note_title']
        type = generated_attr['note_type']
        rewrite = generated_attr['note_rewrite']
        ideas = generated_attr['note_ideas']
        topics_related = generated_attr['note_topics_related']
        topics_related = markdown_bulletize_list(topics_related, double_brackets=True)
        topics_contained = generated_attr['note_topics_contained']
        topics_contained = markdown_bulletize_list(topics_contained, double_brackets=True)

        # Append generated attributes
        text_generated = ''
        text_generated += '\n\n---\n'
        text_generated += f'#type/{type} (generated)\n\n'
        text_generated += f'**Contained Topics**:\n{topics_contained}\n\n'
        text_generated += f'**Related Topics:**: \n{topics_related}\n\n'
        text_generated += '---\n\n'
        text_generated += f'**Suggested Title**: {title}\n\n'
        text_generated += f'**Key Ideas**: \n{ideas}\n\n'
        text_generated += f'**Rewritten Note**: \n{rewrite}\n\n'

        # Write/append to file
        with open(os.path.join(OUTPUT_DIR, unique_title + '.md'), 'a') as f:
            f.write(text_generated)

        # Backup to remote git repo
        commit_and_push_new_files(repo, f'Adding note {unique_title}', GIT_REMOTE, GIT_BRANCH)

        # Once successfully saved, add a "Successfully Exported" label to the Google Keep Note
        label_success = keep.findLabel(SUCCESSFUL_EXPORT_LABEL)
        if not label_success:
            label_success = keep.createLabel(SUCCESSFUL_EXPORT_LABEL)
        note.labels.add(label_success)
        note.archived = True

        # Remove the "Ready to Export" label
        note.labels.remove(label)

        keep.sync()

    logger.info(f'Processed {len(notes)} notes.')
    time.sleep(60)