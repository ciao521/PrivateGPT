from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from .utilities import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

# Google Drive and authentication scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid"
]

# Setting up OAuth2 flow for Google authentication
flow = Flow.from_client_config(
    {
        "web": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=SCOPES,
    redirect_uri=REDIRECT_URI
)


def credentials_to_dict(credentials):
    """Converts Google credentials object to dictionary."""
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }


def get_credentials_from_session(session):
    """Retrieves Google credentials from session."""
    if "token" not in session:
        print('"token" not in session')
        return None
    creds = Credentials(**session["token"])
    print("creds", creds)
    return creds
