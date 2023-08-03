import sys
import re
import openai
from tenacity import retry, stop_after_attempt, wait_fixed, before_log
import logging

# Configure logging
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_generated_content(string_object):
    # regular expression patterns for the keys and values
    pattern = r'"(note_title|note_type|note_rewrite|note_ideas|note_topics_related|note_topics_contained)":(.*?)(?="note_title"|"note_type"|"note_rewrite"|"note_ideas"|"note_topics_related"|"note_topics_contained"|}$)'
    
    matches = re.findall(pattern, string_object, re.DOTALL)
    dict_obj = {}
    
    for key, value in matches:
        # remove leading and trailing spaces, quotes, and trailing commas
        value = value.strip(" \n\",")

        # replace escaped newline characters
        value = value.replace('\\n', '\n')
        
        # if it's an array (note_topics), convert to list
        if key in ["note_topics_contained", "note_topics_related"]:
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
                        "description": "This field is a rewritten version of the provided note body. The provided note text is often a very rough representation of ideas and thoughts (i.e. voice transcripts, back of napkin idea, etc.). This field represents the original text in a highly organized and clear manner. It is not a summary, it is an improved and edited revision which maximizes clarity and readability. This field should only reflect the information and ideas provided in the input and should not extrapolate beyond the information provided in the text. Use rich markdown formatting, leveraging bold, italics, and bulleted (unordered) or numbered (ordered) lists where it helps to provide clarity and easy of reading."
                    },
                    "note_ideas": {
                        "type": "string",
                        "description": "An bulleted list (markdown format) of discrete key atomic ideas from the provided note content. Ideas can be represented in different styles depending on how confidence. For example, they can be stated as declarative claims or statements if it is a clear idea. It can be stated as advice or imperitives if it is more suggestive, or it could be stated as a question if it is a loose idea that lacks conviction, but is meant to spark future thought or reflection. Each idea is a concise statement, imperitive, or question that is typically only one sentence, but can be up to a maximum of 3 sentences if required to clearly represent the full idea. Ideas should be atomic/singular. If an idea is very complex or multifaceted, break it up into more simple atomic components."
                    },
                    "note_topics_contained": {
                        "type": "array",
                        "description": "An array of discrete topics that are discussed in the note. Each topic should be a high level concept, entity, or definition.",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 6
                    },
                    "note_topics_related": {
                        "type": "array",
                        "description": "An array of discrete topics that are related (tangential, adjacent) to the note or a connected concept/topic in some way. Each topic should be a high level concept, entity, or definition. As an expert in the topics of the note, help the author discover related concepts that would help to expand the their knowledge and expedite their learning.",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 6                    
                    }
                },
                "required": ["note_title", "note_type", "note_rewrite", "note_ideas", "note_topics_contained",  "note_topics_related"]
            },
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=[
            {"role": "system", "content": "You are a highly experienced assistant specializing in Zettlekasten note taking, as well as other personal knowledge management (PKM) systems (i.e. PARA). You are highly trained in reviewing and sythesizing information, and organizing knowlege in an intuitive and clean manner. You are a highly proficient and effective writter and communicator, highly capble of presenting complex ideas and throughts in a clear and understandable way."},
            {"role": "user", "content": f"Please review the contents of the following note.\n\n'''\nNOTE TITLE:  {note.title}\n\nNOTE CONTENTS:\n'''\n{note.text}\n'''"}
        ],
        functions=functions,
        function_call={"name": "generate_note_fields"},
        temperature=0
    )

    print(response)

    # Get the function response message
    output = response['choices'][0]['message']['function_call']['arguments']
    return output
