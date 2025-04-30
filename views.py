import traceback  # Add this at the top with other imports
from googleapiclient.discovery import build
from .google_auth_helpers import get_credentials_from_session
from .drive_operations import get_folder_contents  # , upload_file_to_drive
from .utilities import get_user_profile
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
import pytz
import logging
import traceback
import time
import asyncio


async def fetch_files_from_drive(session, websocket=None):
    start_time = time.time()

    if websocket:
        await websocket.send_text(f"Fetching started in {start_time} !")

    try:
        credentials = get_credentials_from_session(session)
        if not credentials:
            logging.warning("No credentials found in session.")
            return None

        drive_service = build("drive", "v3", credentials=credentials)
        people_service = build("people", "v1", credentials=credentials)
        user_name, user_email = get_user_profile(people_service)

        items = []
        total_size = 0
        total_subfolders_count = 0

        page_token = None
        while True:
            response = drive_service.files().list(
                q="'root' in parents and trashed=false", spaces="drive",
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)", pageToken=page_token
            ).execute()

            text = f"Fetched {len(response.get('files', []))} items from root."
            logging.info(text)
            if websocket:
                await websocket.send_text(text)
                await asyncio.sleep(0.1)

            for item in response.get("files", []):
                utc_time = datetime.strptime(
                    item["modifiedTime"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                bangkok_time = utc_time.astimezone(
                    pytz.timezone('Asia/Bangkok'))
                item["modifiedTime"] = bangkok_time.strftime(
                    "%Y-%m-%d %H:%M:%S")

                if item["mimeType"] == "application/vnd.google-apps.folder":
                    folder_size, folder_files, folder_subfolders = await get_folder_contents(drive_service, item["id"], websocket=websocket)
                    item["totalSize"] = folder_size
                    item["totalFiles"] = folder_files
                    item["totalSubFolders"] = folder_subfolders
                    total_subfolders_count += folder_subfolders
                    total_size += folder_size
                else:
                    total_size += int(item.get('size', 0))

                items.append(item)

            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        root_folders_count = sum(
            1 for item in items if item["mimeType"] == "application/vnd.google-apps.folder")

        root_files_count = sum(
            1 for item in items if item["mimeType"] != "application/vnd.google-apps.folder")
        total_files = root_files_count + \
            sum(item.get("totalFiles", 0) for item in items)

        elapsed_time = time.time() - start_time
        elapsed_time = round(elapsed_time, 2)

        if websocket and websocket.client_state != "DISCONNECTED":
            await websocket.send_text(f"Fetching completed in {elapsed_time:.2f} seconds!")
            await websocket.send_text("Fetching completed!")

        session_data = {
            "items": items,
            "user_name": user_name,
            "user_email": user_email,
            "root_folders_count": root_folders_count,
            "total_subfolders_count": total_subfolders_count,
            "total_files": total_files,
            "total_size": total_size,
            "elapsed_time": elapsed_time,
        }

        logging.info(f"Stored fetched data in session: {session_data}")
        return session_data

    except Exception as e:
        logging.error(f"Error in fetch_files_from_drive: {e}")
        if websocket and websocket.client_state != "DISCONNECTED":
            await websocket.send_text(f"Error during fetching: {e}")
        return None
