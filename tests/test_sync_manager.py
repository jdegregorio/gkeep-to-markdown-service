import pytest
from unittest.mock import patch, MagicMock
from app.sync_manager import run_sync

@patch("app.sync_manager.authenticate_keep")
@patch("app.sync_manager.clone_repo_if_needed")
@patch("app.sync_manager.setup_ssh_for_git")
@patch("app.sync_manager.get_ready_notes")
@patch("app.sync_manager.process_note_and_save")
def test_run_sync(
    mock_process_note_and_save,
    mock_get_ready_notes,
    mock_setup_ssh_for_git,
    mock_clone_repo_if_needed,
    mock_auth_keep
):
    """
    Ensures run_sync() orchestrates the steps and returns the
    number of processed notes.
    """
    # Setup mocks
    mock_note = MagicMock()
    mock_get_ready_notes.return_value = [mock_note, mock_note]  # 2 notes

    # Exercise
    count = run_sync()

    # Verify
    assert count == 2
    mock_process_note_and_save.assert_called()
    mock_setup_ssh_for_git.assert_called_once()
    mock_clone_repo_if_needed.assert_called_once()
    mock_auth_keep.assert_called_once()
