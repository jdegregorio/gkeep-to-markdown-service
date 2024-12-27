import pytest
import os
from unittest.mock import patch, MagicMock
from app.clients.git_client import setup_ssh_for_git, clone_repo_if_needed, commit_and_push_new_files

def test_setup_ssh_for_git(tmp_path):
    fake_key = "FAKE_SSH_KEY_CONTENT"
    # Just ensure we don't raise an error
    setup_ssh_for_git(fake_key)
    # Check that environment variable is set
    assert "GIT_SSH_COMMAND" in os.environ


@patch("app.clients.git_client.Git")
def test_clone_repo_if_needed(mock_git_class, tmp_path):
    local_dir = tmp_path / "repo_dir"
    remote_url = "git@github.com:someone/repo.git"

    # Not existing: should attempt to clone
    clone_repo_if_needed(remote_url, str(local_dir))
    mock_git_class.assert_called_once()
    mock_git_class.return_value.clone.assert_called_with(remote_url)


@patch("app.clients.git_client.Repo")
def test_commit_and_push_new_files(mock_repo_class):
    mock_repo_instance = MagicMock()
    mock_repo_class.return_value = mock_repo_instance

    commit_and_push_new_files(mock_repo_instance, "Test commit")

    # We expect a checkout, pull, add, commit, push workflow
    assert mock_repo_instance.git.add.called
    assert mock_repo_instance.git.commit.called
    assert mock_repo_instance.git.push.called
