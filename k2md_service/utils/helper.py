import os
import re

MAX_FILENAME_LENGTH = 255
ILLEGAL_FILE_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '&', '\n', '\r', '\t']

def get_file_names_without_extension(directory: str):
    """
    Returns a list of file basenames (without extension) in the directory.
    """
    if not os.path.exists(directory):
        return []
    file_names = []
    for file in os.listdir(directory):
        name, _ = os.path.splitext(file)
        file_names.append(name)
    return file_names

def format_title(title: str):
    """
    Remove illegal characters from the filename and limit length.
    """
    title = title.strip()
    # Remove illegal chars
    title = re.sub(
        '[' + re.escape(''.join(ILLEGAL_FILE_CHARS)) + ']',
        ' ',
        title[0:MAX_FILENAME_LENGTH]
    )
    return title

def handle_duplicate_name(note_title: str, note_directory: str):
    """
    If a file with note_title already exists, append _1, _2, etc.
    """
    base_title = note_title
    index = 1
    existing = get_file_names_without_extension(note_directory)

    while note_title in existing:
        note_title = f"{base_title}_{index}"
        index += 1

    return note_title

def markdown_bulletize_list(items, double_brackets=False):
    """
    Returns a markdown-formatted bullet list for each item in 'items'.
    If double_brackets=True, wraps each item in [[item]].
    """
    lines = []
    for item in items:
        line_content = f"[[{item}]]" if double_brackets else item
        lines.append(f"- {line_content}")
    return "\n".join(lines) + "\n"
