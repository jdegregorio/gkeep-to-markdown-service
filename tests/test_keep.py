import pytest
from unittest.mock import patch, MagicMock
from app.clients.keep_client import authenticate_keep, get_ready_notes, archive_note

@patch("gkeepapi.Keep")
def test_authenticate_keep(mock_keep_class):
    mock_keep_instance = MagicMock()
    mock_keep_class.return_value = mock_keep_instance
    
    username = "test@example.com"
    master_token = "fake-master-token"
    
    result = authenticate_keep(username, master_token)
    mock_keep_instance.resume.assert_called_with(username, master_token)
    mock_keep_instance.sync.assert_called_once()
    assert result == mock_keep_instance


@patch("app.clients.keep_client.authenticate_keep")  # We can chain calls to test separately
def test_get_ready_notes(mock_auth_keep):
    mock_keep = MagicMock()
    mock_label = MagicMock()
    mock_keep.findLabel.return_value = mock_label

    note_mock = MagicMock()
    mock_keep.find.return_value = [note_mock]
    mock_auth_keep.return_value = mock_keep

    # If we just want to test get_ready_notes directly:
    from app.clients.keep_client import get_ready_notes  # local import to avoid confusion
    notes = get_ready_notes(mock_keep, "Ready to Export")
    assert len(notes) == 1
    mock_keep.find.assert_called()


def test_archive_note():
    mock_keep = MagicMock()
    mock_note = MagicMock()
    mock_label_ready = MagicMock()
    mock_label_success = MagicMock()

    mock_keep.findLabel.side_effect = [mock_label_ready, mock_label_success]
    from app.clients.keep_client import archive_note  # local import

    archive_note(mock_keep, mock_note, "Ready to Export", "Successfully Exported")

    mock_note.labels.add.assert_called_with(mock_label_success)
    mock_note.labels.remove.assert_called_with(mock_label_ready)
    assert mock_note.archived is True
    mock_keep.sync.assert_called()
