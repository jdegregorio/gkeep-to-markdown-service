import pytest
import os
from app.utils.helper import (
    get_file_names_without_extension,
    format_title,
    handle_duplicate_name,
    markdown_bulletize_list
)

def test_get_file_names_without_extension(tmp_path):
    file1 = tmp_path / "test1.md"
    file2 = tmp_path / "test2.txt"
    file1.touch()
    file2.touch()
    result = get_file_names_without_extension(str(tmp_path))
    assert "test1" in result
    assert "test2" in result

def test_format_title():
    title = "Hello/World:Test?Title*"
    result = format_title(title)
    # Slashes, colons, question marks, asterisks replaced with spaces
    assert "Hello" in result
    assert "World" in result
    assert "Test" in result
    assert "Title" in result
    assert "/" not in result
    assert "?" not in result
    assert "*" not in result

def test_handle_duplicate_name(tmp_path):
    # Create a file "MyNote.md"
    note_path = tmp_path / "MyNote.md"
    note_path.touch()

    # This should find "MyNote" and rename to "MyNote_1"
    new_name = handle_duplicate_name("MyNote", str(tmp_path))
    assert new_name == "MyNote_1"

def test_markdown_bulletize_list():
    items = ["TopicA", "TopicB"]
    result = markdown_bulletize_list(items)
    # Should produce lines starting with '- '
    assert "- TopicA" in result
    assert "- TopicB" in result

    result_bb = markdown_bulletize_list(items, double_brackets=True)
    assert "- [[TopicA]]" in result_bb
    assert "- [[TopicB]]" in result_bb
