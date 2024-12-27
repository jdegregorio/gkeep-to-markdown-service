import gkeepapi
from loguru import logger

def authenticate_keep(username: str, master_token: str) -> gkeepapi.Keep:
    """
    Authenticates to Google Keep with either username/password or
    an existing master token. In your case, we rely on username + master token.
    """
    keep = gkeepapi.Keep()
    if not username or not master_token:
        logger.error("Google Keep username or master token not provided.")
        raise ValueError("Missing Google Keep credentials.")
    try:
        keep.resume(username, master_token)
        keep.sync()
        logger.info("Authenticated to Google Keep successfully.")
    except Exception as e:
        logger.error(f"Error authenticating to Google Keep: {e}")
        raise
    return keep

def get_ready_notes(keep: gkeepapi.Keep, label_name: str):
    """
    Find all notes that are labeled with label_name (e.g. 'Ready to Export').
    """
    keep.sync()
    label = keep.findLabel(label_name)
    if not label:
        return []
    # Filter notes
    notes = keep.find(
        archived=False,
        trashed=False,
        labels=[label],
        func=lambda x: x.type == gkeepapi.node.NodeType.Note
    )
    return notes

def archive_note(keep: gkeepapi.Keep, note, ready_label_name: str, success_label_name: str):
    """
    1. Remove the 'Ready to Export' label
    2. Add the 'Successful Export' label
    3. Archive the note
    4. keep.sync()
    """
    label_ready = keep.findLabel(ready_label_name)
    label_success = keep.findLabel(success_label_name)

    if not label_success:
        label_success = keep.createLabel(success_label_name)

    note.labels.add(label_success)
    if label_ready in note.labels.all():
        note.labels.remove(label_ready)

    note.archived = True
    keep.sync()
