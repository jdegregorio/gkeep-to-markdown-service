import os

class Config:
    # Secrets from environment
    GOOGLE_KEEP_USERNAME = os.environ.get("GOOGLE_KEEP_USERNAME", "")
    GOOGLE_KEEP_PASSWORD = os.environ.get("GOOGLE_KEEP_PASSWORD", "")
    GOOGLE_KEEP_MASTER_TOKEN = os.environ.get("GOOGLE_KEEP_MASTER_TOKEN", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Git SSH private key as a string
    GIT_SSH_KEY = os.environ.get("GIT_SSH_KEY", "")

    # Git details
    REPO_REMOTE_URL = "git@github.com:jdegregorio/second-brain.git"
    GIT_BRANCH = "gkeep-exported-notes"
    GIT_REMOTE = "origin"
    REPO_NAME = "second-brain"
    REPO_DIR = f"./{REPO_NAME}"

    # File paths
    OUTPUT_DIR = "./second-brain/Inbox/"
    MEDIA_DIR = "./second-brain/Attachments/"
    MEDIA_FOLDER = "Attachments/"

    # Google Keep config
    READY_TO_EXPORT_LABEL = "Ready to Export"
    SUCCESSFUL_EXPORT_LABEL = "Succesfully Exported"
    
    # LLM model name
    OPENAI_MODEL = "gpt-4"
