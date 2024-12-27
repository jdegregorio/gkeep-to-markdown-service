import os
import stat
import tempfile
from git import Repo, GitCommandError, Git, InvalidGitRepositoryError
from loguru import logger
from app.config import Config

def setup_ssh_for_git(ssh_key_str: str):
    """
    Create a temporary file for the SSH key, set correct permissions,
    and configure GIT_SSH_COMMAND environment variable so Git uses it.
    """
    if not ssh_key_str:
        logger.error("No SSH key provided for Git operations.")
        raise ValueError("Missing SSH key for Git.")

    # Create temporary file
    ssh_key_file = os.path.join(tempfile.gettempdir(), "git_ssh_key")
    with open(ssh_key_file, "w") as f:
        f.write(ssh_key_str)
    os.chmod(ssh_key_file, stat.S_IRUSR | stat.S_IWUSR)

    # Force Git to use our SSH key
    ssh_wrapper = os.path.join(tempfile.gettempdir(), "git_ssh_wrapper.sh")
    with open(ssh_wrapper, "w") as f:
        f.write("#!/bin/sh\n")
        f.write(f'exec ssh -i "{ssh_key_file}" -o StrictHostKeyChecking=no "$@"\n')
    os.chmod(ssh_wrapper, 0o700)

    os.environ["GIT_SSH_COMMAND"] = f'ssh -i "{ssh_key_file}" -o StrictHostKeyChecking=no'

def clone_repo_if_needed(remote_url: str, local_dir: str):
    """
    Clone the Git repo if local_dir doesn't exist or isn't a valid repo.
    Otherwise, do a git pull.
    """
    if not os.path.exists(local_dir):
        logger.info(f"Local repo directory {local_dir} not found. Cloning...")
        os.makedirs(local_dir, exist_ok=True)
        try:
            Git(local_dir).clone(remote_url)
        except GitCommandError as e:
            logger.error(f"Error cloning repository: {e}")
            raise
    else:
        # Check if it's a valid repo
        try:
            repo = Repo(local_dir)
            logger.info(f"Found existing repo at {local_dir}, pulling latest...")
            repo.git.pull()
        except InvalidGitRepositoryError:
            logger.warning(f"{local_dir} is not a valid Git repo. Re-cloning.")
            # Clean up and re-clone
            for item in os.listdir(local_dir):
                item_path = os.path.join(local_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    # recursively remove directories
                    pass  # or use shutil.rmtree(item_path) carefully
            Git(local_dir).clone(remote_url)

def commit_and_push_new_files(repo: Repo, commit_message: str):
    """
    Commit and push changes to the configured branch, pulling from main if branch doesn't exist.
    """
    try:
        branches = repo.git.branch("-a")
        if Config.GIT_BRANCH in branches:
            repo.git.checkout(Config.GIT_BRANCH)
            repo.git.pull(Config.GIT_REMOTE, Config.GIT_BRANCH)
        else:
            repo.git.checkout("main")
            repo.git.pull(Config.GIT_REMOTE, "main")
            repo.git.checkout("-b", Config.GIT_BRANCH)
            repo.git.push("-u", Config.GIT_REMOTE, Config.GIT_BRANCH)

        repo.git.add(all=True)  # or repo.git.add("--all")
        repo.git.commit("-m", commit_message)
        repo.git.push(Config.GIT_REMOTE, Config.GIT_BRANCH)
    except GitCommandError as e:
        logger.error(f"Error during commit/push: {e}")
        # Depending on your preference, raise or handle
        raise
