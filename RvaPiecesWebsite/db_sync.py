import os

from django.db.models.signals import post_save
from django.dispatch import receiver
from google.cloud import storage

BUCKET = os.environ.get("GS_BUCKET_NAME")
REMOTE_PATH = os.environ.get("REMOTE_DB_PATH")
LOCAL_PATH = os.environ.get("LOCAL_DB_PATH")
USE_REMOTE_DB = os.environ.get("USE_REMOTE_DB", "False")


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


@receiver(post_save)
def save_to_cloud(sender, instance, **kwargs):
    if USE_REMOTE_DB == "True":
        upload_db()
