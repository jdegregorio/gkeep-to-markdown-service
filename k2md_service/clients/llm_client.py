import os
import re
import openai
from tenacity import retry, stop_after_attempt, wait_fixed, before_log
import logging
from loguru import logger
from app.config import Config

openai.api_key = Config.OPENAI_API_KEY

def parse_generated_content(string_object: str) -> dict:
    """
    Parse the raw JSON-ish string from the LLM function call
    into a Python dict with known keys.
    """
    # Regex pattern
    pattern = r'"(note_title|note_type|note_rewrite|note_ideas|note_topics_related|note_topics_contained)":(.*?)(?="note_title"|"note_type"|"note_rewrite"|"note_ideas"|"note_topics_related"|"note_topics_contained"|}$)'
    matches = re.findall(pattern, string_object, re.DOTALL)
    dict_obj = {}

    for key, value in matches:
        value = value.strip(" \n\",")
        value = value.replace('\\n', '\n')
        if key in ["note_topics_contained", "note_topics_related"]:
            value = value.strip("[]").split(",")
            value = [item.strip(" \"") for item in value]
        dict_obj[key] = value

    return dict_obj

@retry(wait=wait_fixed(0.5), stop=stop_after_attempt(5), before=before_log(logger, logging.INFO))
def generate_note_fields(note_title: str, note_text: str) -> str:
    """
    Calls OpenAI GPT-4 with function calling to produce structured note attributes.
    Returns the raw JSON-like string from the function call response.
    """
    functions = [
        {
            "name": "generate_note_fields",
            "description": "Function for summarizing a personal note, constructing required fields for PKM.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_title": {
                        "type": "string"
                    },
                    "note_type": {
                        "type": "string",
                        "enum": ["source", "idea", "entity", "definition"]
                    },
                    "note_rewrite": {
                        "type": "string"
                    },
                    "note_ideas": {
                        "type": "string"
                    },
                    "note_topics_contained": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 6
                    },
                    "note_topics_related": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 6
                    }
                },
                "required": [
                    "note_title",
                    "note_type",
                    "note_rewrite",
                    "note_ideas",
                    "note_topics_contained",
                    "note_topics_related"
                ]
            },
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert in PKM systems. Review the user's note,"
                " and produce a structured summary with the provided function schema."
            )
        },
        {
            "role": "user",
            "content": f"NOTE TITLE: {note_title}\n\nNOTE CONTENT:\n{note_text}"
        }
    ]

    response = openai.ChatCompletion.create(
        model=Config.OPENAI_MODEL,
        messages=messages,
        functions=functions,
        function_call={"name": "generate_note_fields"},
        temperature=0
    )

    raw_output = response.choices[0].message.function_call.arguments
    return raw_output
