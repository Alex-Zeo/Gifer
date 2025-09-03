from pathlib import Path
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveUploader:
    def __init__(self, credentials_path: str = settings.GOOGLE_DRIVE_CREDENTIALS_JSON):
        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            self.service = build("drive", "v3", credentials=creds)
        except FileNotFoundError:
            logger.error(
                "Google Drive credentials file not found.",
                path=credentials_path,
            )
            self.service = None
        except Exception as e:
            logger.error("Failed to initialize Google Drive service.", error=e)
            self.service = None

    def upload(
        self,
        local_path: Path,
        folder_id: Optional[str] = None,
        share_anyone_reader: bool = False,
    ) -> Optional[str]:
        if not self.service:
            logger.warning("Google Drive service not available. Skipping upload.")
            return None

        file_metadata = {"name": local_path.name}
        if folder_id:
            file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(local_path, resumable=True)

        try:
            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            file_id = file.get("id")

            if share_anyone_reader:
                self.service.permissions().create(
                    fileId=file_id, body={"role": "reader", "type": "anyone"}
                ).execute()

            logger.info("File uploaded to Google Drive", file_id=file_id)
            return file_id
        except Exception as e:
            logger.error("Failed to upload file to Google Drive", error=e)
            return None


