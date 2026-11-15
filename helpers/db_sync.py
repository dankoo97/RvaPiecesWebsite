import os
import threading

from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from google.cloud import storage

# The database should live in a private bucket, separate from the public media bucket.
# Falls back to GS_BUCKET_NAME for backwards compatibility.
BUCKET = os.environ.get("DB_BUCKET_NAME") or os.environ.get("GS_BUCKET_NAME")
REMOTE_PATH = os.environ.get("REMOTE_DB_PATH")
LOCAL_PATH = os.environ.get("LOCAL_DB_PATH")
USE_REMOTE_DB = os.environ.get("USE_REMOTE_DB", "False")

_upload_scheduled = threading.local()


def get_client():
    return storage.Client()


def download_db():
    """Download SQLite database from Google Cloud Storage if it exists, otherwise create a new one."""
    try:
        client = get_client()
        print(
            f"Connected to Google Cloud Storage. Attempting to connect to bucket: {BUCKET}"
        )
        bucket = client.get_bucket(BUCKET)
        print(
            f"Retrieved bucket. Attempting to download database from path: gs://{BUCKET}/{REMOTE_PATH}"
        )
        blob = bucket.blob(REMOTE_PATH)

        if blob.exists():
            blob.download_to_filename(LOCAL_PATH)
            print(
                f"Downloaded database from Google Cloud Storage and saved to {LOCAL_PATH}."
            )
        else:
            print(
                "Database does not exist in Google Cloud Storage, creating a new one."
            )
    except Exception as e:
        print(f"Error downloading database from Google Cloud Storage: {e}")


def upload_db():
    """Upload SQLite database to Google Cloud Storage."""
    try:
        if not os.path.exists(LOCAL_PATH):
            print("Database does not exist locally, skipping upload.")
            return

        client = get_client()
        bucket = client.get_bucket(BUCKET)
        blob = bucket.blob(REMOTE_PATH)

        blob.upload_from_filename(LOCAL_PATH)
        print("Uploaded database to Google Cloud Storage.")
    except Exception as e:
        print(f"Error uploading database to Google Cloud Storage: {e}")


def schedule_upload():
    """Schedule an upload at the end of the current transaction."""
    if not hasattr(_upload_scheduled, "value"):
        _upload_scheduled.value = False

    if not _upload_scheduled.value:
        _upload_scheduled.value = True
        transaction.on_commit(perform_upload)


def perform_upload():
    """Perform the upload and reset the flag"""
    print("Performing scheduled upload...")
    upload_db()
    _upload_scheduled.value = False


@receiver([post_save, post_delete])
def save_to_cloud(sender, instance, **kwargs):
    """Signal handler to schedule an upload at the end of the current transaction."""
    if USE_REMOTE_DB == "True":
        if (
            sender.__name__ != "CalendarEntry"
        ):  # CalendarEntry updates are calculated each time the page is loaded
            print(f"Database change detected. Scheduling upload for {sender.__name__}")
            schedule_upload()
