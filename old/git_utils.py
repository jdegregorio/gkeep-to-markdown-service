import os
from git import Repo, Git, GitCommandError, InvalidGitRepositoryError


def clone_repo(remote_url, local_path='./'):
    # Check if local_path exists, create it if it doesn't
    if not os.path.exists(local_path):
        try:
            os.makedirs(local_path)
        except OSError as e:
            print(f"Error: Creation of the directory {local_path} failed. Details: {e}")
            return
        else:
            print(f"Successfully created the directory {local_path}")

    try:
        Git(local_path).clone(remote_url)
    except GitCommandError as e:
        print(f"Error: Unable to clone repository. Details: {e}")

def branch_exists(repo, branch_name):
    """
    Check if the branch exists in the repository.

    Parameters
    ----------
    repo : Repo
        The git repository.
    branch_name : str
        The name of the branch.

    Returns
    -------
    bool
        True if the branch exists, False otherwise.
    """
    existing_branches = repo.git.branch('-a')
    return branch_name in existing_branches.split()


def commit_and_push_new_files(repo, commit_message, remote_name, branch_name):
    if branch_exists(repo, branch_name):
        repo.git.checkout(branch_name)
        repo.git.pull(remote_name, branch_name)
    else:
        repo.git.pull(remote_name, 'main')
        repo.git.checkout('-b', branch_name)
        repo.git.push('-u', remote_name, branch_name)

    try:
        repo.git.add('*')
    except GitCommandError as e:
        print(f"Error: Unable to add new file(s) to git. Details: {e}")
        return

    try:
        repo.git.commit('-m', commit_message)
    except GitCommandError as e:
        print(f"Error: Unable to commit. Details: {e}")
        return

    try:
        repo.git.push(remote_name, branch_name)
    except GitCommandError as e:
        print(f"Error: Unable to push to {branch_name} at {remote_name}. Details: {e}")
        return
