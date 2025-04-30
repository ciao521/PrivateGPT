from functools import lru_cache
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .utilities import MAX_DEPTH
import logging
import tempfile
import asyncio
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)


@lru_cache(maxsize=None)
def fetch_folder_contents(service, folder_id):
    items = []
    query = f"'{folder_id}' in parents and trashed=false"
    page_token = None
    while True:
        response = service.files().list(q=query, corpora="user",
                                        fields="nextPageToken, files(id, mimeType, size)", pageToken=page_token).execute()
        items.extend(response.get("files", []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return items


async def get_folder_contents(service, folder_id, current_depth=0, websocket=None):
    total_size = 0
    total_files = 0
    total_subfolders = 0

    if current_depth > MAX_DEPTH:
        return total_size, total_files, total_subfolders

    items = fetch_folder_contents(service, folder_id)

    text = f"Fetched {len(items)} items from folder {folder_id} at depth {current_depth}."
    logging.info(text)
    if websocket:
        await websocket.send_text(text)
        await asyncio.sleep(0.1)

    for item in items:
        if item["mimeType"] != "application/vnd.google-apps.folder":
            total_files += 1
            total_size += int(item.get("size", 0))
        else:
            subfolder_size, subfolder_files, subfolder_subfolders = await get_folder_contents(service, item["id"], current_depth + 1, websocket)
            total_files += subfolder_files
            total_size += subfolder_size
            total_subfolders += 1 + subfolder_subfolders

    return total_size, total_files, total_subfolders


async def upload_file_to_drive(service, file, websocket=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    with temp_file as buffer:
        buffer.write(file.file.read())
    file_metadata = {"name": file.filename}
    media = MediaFileUpload(temp_file.name, mimetype=file.content_type)
    file = service.files().create(
        body=file_metadata, media_body=media, fields="id").execute()
    os.remove(temp_file.name)

    if websocket:
        await websocket.send_text(f"Uploaded file with ID: {file.get('id')}.")

    return file.get("id")
