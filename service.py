import os
import re
import requests
import gkeepapi
import mimetypes
from dotenv import load_dotenv
import shutil
from pathlib import Path
import openai
import json
from tenacity import retry, stop_after_attempt, stop_after_delay, wait_fixed, before_log
import logging
import sys

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

# Define config variables
READY_TO_EXPORT_LABEL = 'Ready to Export'
SUCCESSFUL_EXPORT_LABEL = 'Succesfully Exported'
EXPORT_NOTE_TYPE = gkeepapi.node.NodeType.Note  # define the type of note you want to export
OUTPUT_DIR = './notes/'
MEDIA_DIR = './media/'

# Define illegal characters
ILLEGAL_FILE_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '&', '\n', '\r', '\t']
ILLEGAL_TAG_CHARS = ['~', '`', '!', '@', '$', '%', '^', '(', ')', '+', '=', '{', '}', '[', \
    ']', '<', '>', ';', ':', ',', '.', '"', '/', '\\', '|', '?', '*', '&', '\n', '\r']

# Maximum filename length
MAX_FILENAME_LENGTH = 255

# A list to store all note names
namelist = []

# Authenticate Google Account
load_dotenv()
user = os.getenv('GOOGLE_KEEP_USERNAME')
password = os.getenv('GOOGLE_KEEP_PASSWORD')

# Authenticate
keep = gkeepapi.Keep()
keep.login(user, password)
token = keep.getMasterToken()

# Clear the notes and media directory before running the script
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR)

if os.path.exists(MEDIA_DIR):
    shutil.rmtree(MEDIA_DIR)
os.makedirs(MEDIA_DIR)

# Function to format the note title
def format_title(title):
    return re.sub(
        '[' + re.escape(''.join(ILLEGAL_FILE_CHARS)) + ']', 
        ' ', 
        title[0:MAX_FILENAME_LENGTH]
    )

# Function to check and handle duplicate note names
def handle_duplicate_name(note_title):
    base_title = note_title
    index = 1

    while note_title in namelist:
        note_title = f"{base_title}_{index}"
        index += 1

    namelist.append(note_title)

    return note_title


import re

def parse_generated_content(string_object):
    # regular expression patterns for the keys and values
    pattern = r'"(note_title|note_type|note_rewrite|note_prompts|note_expanded|note_topics)":(.*?)(?="note_title"|"note_type"|"note_rewrite"|"note_prompts"|"note_expanded"|"note_topics"|}$)'
    
    matches = re.findall(pattern, string_object, re.DOTALL)
    dict_obj = {}
    
    for key, value in matches:
        # remove leading and trailing spaces, quotes, and trailing commas
        value = value.strip(" \n\",")

        # replace escaped newline characters
        value = value.replace('\\n', '\n')
        
        # if it's an array (note_topics), convert to list
        if key == "note_topics":
            value = value.strip("[]").split(",")
            value = [item.strip(" \"") for item in value]
        
        dict_obj[key] = value
    
    return dict_obj


@retry(wait=wait_fixed(0.5), stop=stop_after_attempt(5), before=before_log(logger, logging.INFO))
def generate_note_fields(note):

    functions = [
        {
            "name": "generate_note_fields",
            "description": "Function for summarizing a personal note, constructing all of the required fields, context, and attributes for personal knowledge management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_title": {
                        "type": "string",
                        "description": "A short and concise filename (i.e. title of the note) based on the title, text, and type of a note. If the note contains a primary core idea, the title should reflect the core idea being represented in a declarative style. The name should be 4 or fewer words. Maximum of 6 if absolutely necessary.",
                    },
                    "note_type": {
                        "type": "string",
                        "enum": ["source", "idea", "entity", "definition"],
                        "description": "The type of note that is provided. There are four primary types, including source, idea, entity, and definition. Source notes are notes taken about source material or content. They are strictily a summary of the content, and ussually contain a link to the source material. Idea notes containa higher level (i.e. second order) synthesis, and typically include declarative statements, claims, imperitives, or questions. An Entity note describes a proper noun (person place or thing). Finally, a Definition Note is simply a definition of a term or topic, with little to no new sythesized thoughts. Most notes will be either source notes or idea notes.",
                    },
                    "note_rewrite": {
                        "type": "string",
                        "description": "This field is a rewritten version of the provided note body. The provided note text is often a very rough representation of ideas and thoughts (i.e. voice transcripts, back of napkin idea, etc.). The goal is to represent the original text in a more organized and well written manner. It is not a summary, it is an improved and edited revision which maximizes clarity and readability. This field should only reflect the information and ideas provided in the input and should not extrapolate beyond the information provided in the text. Use rich markdown formatting, leveraging bold, italics, and bulleted (unordered) or numbered (ordered) lists where it helps to provide clarity and easy of reading."
                    },
                    "note_prompts": {
                        "type": "string",
                        "description": "A bulleted list (markdown format) of writing prompts to consider expanding on the idea or information represented in the provided text. For example, it may provide suggestions of how to expand the idea, find connections to related concepts, poke holes in or challenge the idea, or suggest other areas of research"
                    },
                    "note_expanded": {
                        "type": "string",
                        "description": "This field is a rewritten version of the provided note body. The provided note text is often a very rough representation of ideas and thoughts (i.e. voice transcripts, back of napkin idea, etc.). The goal is to represent the original text and expand where gaps exist, or related concepts or information would be benefitial. This is an improved and edited revision which maximizes clarity and readability. Use rich markdown formatting, leveraging bold, italics, and bulleted (unordered) or numbered (ordered) lists where it helps to provide clarity and easy of reading."
                    },
                    "note_topics": {
                        "type": "array",
                        "description": "An array of discrete topics that are discussed in the note. Each topic should be a high level concept, entity, or definition.",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 5
                    }
                },
                "required": ["note_title", "note_type", "note_rewrite", "note_prompts", "note_expanded", "note_topics"],
            },
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": "You are a highly experienced assistant specializing in Zettlekasten note taking, as well as other personal knowledge management (PKM) systems (i.e. PARA). You are highly trained in reviewing and sythesizing information, and organizing knowlege in an intuitive and clean manner."},
            {"role": "user", "content": f"Please review the contents of the following note.\n\nNOTE TITLE:  {note.title}\n\nNOTE CONTENTS:\n'''\n{note.text}\n'''"}
        ],
        functions=functions,
        function_call={"name": "generate_note_fields"},
        temperature=0
    )

    print(response)

    # Get the function response message
    output = parse_generated_content(response['choices'][0]['message']['function_call']['arguments'])
    return output


# Sync and download all notes with the "export" label
keep.sync()
label = keep.findLabel(READY_TO_EXPORT_LABEL)

# Find all notes that are ready to export
# notes =  keep.find(labels=[label])
notes = keep.find(archived=False, trashed=False, func=lambda x: x.type == EXPORT_NOTE_TYPE)
notes = list(notes)
len(notes)
import random
random.seed(1989)
random.shuffle(notes)
notes = notes[0:10]
i = -1
for note in notes:
    i += 1
    logger.info(f'Starting Note: {note.title}, Note Text Length: {len(note.text)}, Index: {i}')

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
    generated_attr = generate_note_fields(note)    
    title = generated_attr['note_title'] + ' (Generated)'
    type = generated_attr['note_type']
    rewrite = generated_attr['note_rewrite']
    prompts = generated_attr['note_prompts']
    expanded = generated_attr['note_expanded']
    topics = generated_attr['note_topics']
    
    if not note.title:
        note.title = title

    # Handle duplicate names
    formatted_title = format_title(note.title)
    unique_title = handle_duplicate_name(formatted_title)

    # Append generated fields
    text += '\n\n-------------------------------------------------\n\n'
    text += f'Generated Title: {title}\n\n'
    text += f'Generated Type: {type}\n\n'
    text += f'Generated Rewrite: \n{rewrite}\n\n'
    text += f'Generated Prompts: \n{prompts}\n\n'
    text += f'Generated Expansion: \n{expanded}\n\n'
    text += f'Generated Topics: \n{topics}'

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

    # # Once successfully saved, add a "Successfully Exported" label to the Google Keep Note
    # label_success = keep.findLabel(SUCCESSFUL_EXPORT_LABEL)
    # if not label_success:
    #     label_success = keep.createLabel(SUCCESSFUL_EXPORT_LABEL)
    # note.labels.add(label_success)

    # # Remove the "Ready to Export" label
    # note.labels.remove(label)

    keep.sync()
