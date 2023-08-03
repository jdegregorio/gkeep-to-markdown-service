import re
import os

# Maximum filename length
MAX_FILENAME_LENGTH = 255

# Define illegal characters
ILLEGAL_FILE_CHARS = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '&', '\n', '\r', '\t']
ILLEGAL_TAG_CHARS = ['~', '`', '!', '@', '$', '%', '^', '(', ')', '+', '=', '{', '}', '[', \
    ']', '<', '>', ';', ':', ',', '.', '"', '/', '\\', '|', '?', '*', '&', '\n', '\r']


def get_file_names_without_extension(directory):
  """Returns a list of all of the file names in the specified directory, excluding the extension."""
  file_names = []
  for file in os.listdir(directory):
    name, extension = os.path.splitext(file)
    file_names.append(name)
  return file_names

# Function to format the note title
def format_title(title):
    return re.sub(
        '[' + re.escape(''.join(ILLEGAL_FILE_CHARS)) + ']', 
        ' ', 
        title[0:MAX_FILENAME_LENGTH]
    )

# Function to check and handle duplicate note names
def handle_duplicate_name(note_title, note_directory):
    base_title = note_title
    index = 1
    namelist = get_file_names_without_extension(note_directory)

    while note_title in namelist:
        note_title = f"{base_title}_{index}"
        index += 1

    return note_title

def markdown_bulletize_list(input_list, double_brackets=False):
    bullets = ''
    for item in input_list:
        item = item.replace('\\n', '')
        item = item.replace('\n', '')
        if double_brackets:
            bullets += f'- [[{item}]]\n'
        else:
            bullets += f'- {item}\n'
    return bullets