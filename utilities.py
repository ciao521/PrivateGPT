import os
import pytz
import math
import tempfile
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()


def refresh_file():
    path_to_sandbox_folder = '/kim/pp/sandbox/'
    file_list_in_sandbox = os.listdir(path_to_sandbox_folder)
    return path_to_sandbox_folder, file_list_in_sandbox


# REDIRECT_URI = "https://linkpay.to/login/callback"
REDIRECT_URI = "https://promptpl.us/login/callback"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# beware folder path

MAX_DEPTH = 3
# Function to convert bytes to a human-readable format


def get_user_profile(service):
    profile = service.people().get(resourceName="people/me",
                                   personFields="names,emailAddresses").execute()
    user_name = profile["names"][0]["displayName"]
    user_email = profile["emailAddresses"][0]["value"]
    return user_name, user_email


def convert_size(size_bytes):
    if size_bytes == "N/A" or size_bytes is None:
        return "N/A"

    try:
        size_bytes = int(size_bytes)
    except ValueError:
        return "N/A"

    if size_bytes == 0:
        return "0B"

    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"
