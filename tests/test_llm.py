import pytest
from unittest.mock import patch, MagicMock
from app.clients.llm_client import parse_generated_content, generate_note_fields

def test_parse_generated_content():
    fake_response = (
        '"note_title":"Test Title",'
        '"note_type":"idea",'
        '"note_rewrite":"Some text",'
        '"note_ideas":"- Idea one\\n- Idea two",'
        '"note_topics_related":["TopicA","TopicB"],'
        '"note_topics_contained":["TopicC"]'
    )
    result = parse_generated_content(fake_response)
    assert result["note_title"] == "Test Title"
    assert result["note_type"] == "idea"
    assert result["note_rewrite"] == "Some text"
    assert result["note_ideas"] == "- Idea one\n- Idea two"
    assert result["note_topics_related"] == ["TopicA", "TopicB"]
    assert result["note_topics_contained"] == ["TopicC"]


@patch("openai.ChatCompletion.create")
def test_generate_note_fields(mock_openai_create):
    # Mock the API response
    mock_openai_create.return_value = MagicMock(
        choices=[MagicMock(
            message=MagicMock(
                function_call=MagicMock(
                    arguments=(
                        '"note_title":"Mocked Title",'
                        '"note_type":"idea",'
                        '"note_rewrite":"Mocked text",'
                        '"note_ideas":"- Mocked Idea",'
                        '"note_topics_related":["MockRelated"],'
                        '"note_topics_contained":["MockContained"]'
                    )
                )
            )
        )]
    )
    output = generate_note_fields("Example Title", "Example Text")
    # We just verify it returns the raw string from the mocked function call
    assert '"note_title":"Mocked Title"' in output
    mock_openai_create.assert_called_once()
