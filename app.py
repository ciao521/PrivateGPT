from .file_list import get_file_list
from .utilities import convert_size, CLIENT_ID
from .views import fetch_files_from_drive
from .drive_operations import upload_file_to_drive
from .google_auth_helpers import flow, credentials_to_dict, get_credentials_from_session
from googleapiclient.discovery import build
from starlette.websockets import WebSocketDisconnect
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi import FastAPI, Depends, Request, File, UploadFile, WebSocket, HTTPException
import logging
import datetime
import traceback
import redis
import json
import os

# from fastapi import APIRouter
# router = APIRouter()
# this part should be in the module file to be imported here

from .ws import chat

# Logging Configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Logging is set up and working correctly.")


# Initialize Redis client
r = redis.Redis(host='192.168.1.99', port=6379, db=0)
print(r)

# # Setup in-memory session backend
# session_backend = InMemorySessionBackend()

# # Setting up templates for rendering HTML
# templates = Jinja2Templates(directory="templates")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("BASE_DIR", BASE_DIR)
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
print("TEMPLATE_DIR", TEMPLATE_DIR)
templates = Jinja2Templates(directory=TEMPLATE_DIR)
# templates = Jinja2Templates(directory="pp/templates")
print("templates", templates)
templates.env.filters["convert_size"] = convert_size

app = FastAPI()

app.include_router(chat.router)
# app.include_router(chat.router, prefix="/chatline")
# router object will be imported

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

# Middleware for session management
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# app.mount("/", StaticFiles(directory="site", html=True), name="site")
app.mount("/static", StaticFiles(directory="pp/static"), name="static")

# @app.get("/items/{id}", response_class=HTMLResponse)
# async def read_item(request: Request, id: str):
#     return templates.TemplateResponse("item.html", {"request": request, "id": id})


@app.get("/termsofservice", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("tos.html", {"request": request})


@app.get("/privacypolicy", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("pp.html", {"request": request})


@app.post("/contact", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("logo.html", {"request": request})


@app.get("/chat", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("chatline.html", {"request": request})


@app.get("/code", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("code.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Route to initiate Google OAuth2 login."""
    authorization_url, _ = flow.authorization_url(prompt="consent")
    return templates.TemplateResponse("index.html", {"request": request,
                                                     "authorization_url": authorization_url,
                                                     "CLIENT_ID": CLIENT_ID}
                                      )


@app.get("/login/")
def login(request: Request):
    """Route to initiate Google OAuth2 login."""
    authorization_url, _ = flow.authorization_url(prompt="consent")
    return RedirectResponse(authorization_url)


@app.get("/login/callback/")
def callback(request: Request, code: str):
    """Callback route after successful Google OAuth2 authentication."""
    flow.fetch_token(code=code)
    credentials = flow.credentials
    request.session["token"] = credentials_to_dict(credentials)
    return RedirectResponse(url="/landing/")


@app.get("/landing/")
async def landing_page(request: Request):
    credentials = get_credentials_from_session(request.session)
    if not credentials:
        return RedirectResponse(url="/login/")
    return templates.TemplateResponse("landing.html", {"request": request})


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    credentials = get_credentials_from_session(request.session)
    if not credentials:

        folder_name = "/kim/pp/sandbox"
        file_path = os.path.join(folder_name, file.filename)

        # if not os.path.exists(folder_name):
        #     os.mkdir(folder_name)

        with open(file_path, "wb") as f:
            f.write(file.file.read())

        data_dict = {"request": request,
                     "file_id": "sandbox",
                     "file_name": file.filename}
        return templates.TemplateResponse("upload_success.html", data_dict)
        # return RedirectResponse(url="/login/")

    drive_service = build("drive", "v3", credentials=credentials)
    file_id = await upload_file_to_drive(drive_service, file)
    return templates.TemplateResponse("upload_success.html", {"request": request, "file_id": file_id})

# @app.get("/landing/")
# async def landing_page_route(request: Request):
#     """Landing page after successful login."""
#     return await landing_page(request)

# @app.post("/upload/")
# async def upload_file_route(request: Request, file: UploadFile = File(...)):
#     """Route to upload a file to Google Drive."""
#     return await upload_file(request, file)


@app.get("/files/")
async def list_files_route(request: Request):

    try:
        # if token:
        token = r.get(request.session["token"]["token"])
        print("token", token)
        fetched_data = json.loads(token)
        print("fetched_data")  # , fetched_data
        for i in fetched_data.keys():
            print(i, fetched_data[i])

        # we still cannot send file to emdding directly as we need to download the files first
        print("frl")
        frl = [f['name'] if f['mimeType'] !=
               "application/vnd.google-apps.folder" else None for f in fetched_data['items']]
        # for f in fetched_data['items']:
        #     print(type(f))
        #     print(f['name'], f['mimeType'])
        # print("f", f)
        print("frl", frl)
        # frl_ = download_from_gd(frl)
        # embbding(frl_)
        return templates.TemplateResponse("files.html", {"request": request, "fetched_data": fetched_data})

    except:

        # from .chat import chat, embbding

        # if not fetched_data:
        # if not token:
        # return RedirectResponse('/login')

        items_ = get_file_list()
        print("items_", items_)
        # embbding([f['name'] for f in items])

        # from .utilities import file_list_in_sandbox
        # embbding(file_list_in_sandbox)

        fetched_data_ = {
            "items": items_,
            "user_name": "user_name",
            "user_email": "user_email",
            "root_folders_count": 0,
            "total_subfolders_count": 0,
            "total_files": len(items_),
            "total_size": sum([s['size'] for s in items_]),
            "elapsed_time": 0,
        }
        return templates.TemplateResponse("files.html", {"request": request, "fetched_data": fetched_data_})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    print("websocket.accept() accepted")

    session = websocket.scope.get("session")
    print('websocket.scope.get("session")', session)

    session_token = session.get("token")
    print("session_token", session_token)

    if not session_token:
        # logging.warning("WebSocket connection attempt without session token.")
        await websocket.close(code=1003)  # Forbidden
        print("websocket.close(code=1003) no session_token")
        return

    logging.info("WebSocket connection established.")
    await websocket.send_text("WebSocket Connected")

    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received WebSocket message: {data}")

            if data == "start":
                logging.info("Starting file fetch process...")
                await websocket.send_text("Fetching files...")

                file_data = await fetch_files_from_drive(websocket.scope.get("session"), websocket)
                print('file_data', file_data)

                if file_data:
                    r.set(session_token['token'], json.dumps(file_data))
                    total_files = file_data.get("total_files", 0)
                    fetched_files = f"Fetched {total_files} files from Google Drive."
                    logging.info(fetched_files)
                    await websocket.send_text(fetched_files)
                    await websocket.send_text(f"Fetched {total_files} files.")
                else:
                    logging.warning(
                        "No file data received from fetch_files_from_drive function.")

    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket disconnected with code: {e.code}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # This will log the full traceback of the exception
        logging.error(traceback.format_exc())
        await websocket.send_text(f"Error: {e}")


@app.websocket("/chat")
async def websocket_endpoint_chat(websocket: WebSocket):

    await websocket.accept()
    print("websocket.accept() accepted")

    # session = websocket.scope.get("session")
    # print('websocket.scope.get("session")', session)

    # session_token = session.get("token")
    # print("session_token", session_token)

    # if not session_token:
    #     # logging.warning("WebSocket connection attempt without session token.")
    #     await websocket.close(code=1003)  # Forbidden
    #     print("websocket.close(code=1003) no session_token")
    #     return

    logging.info("WebSocket connection established.")
    await websocket.send_text("WebSocket Connected")

    try:

        # from .chat import chat, embbding
        # from .utilities import file_list_in_sandbox
        # elon_musk_bot = embbding(file_list_in_sandbox)
        # # embbding([f['name'] for f in items])

        from embedchain import App
        from dotenv import load_dotenv
        load_dotenv()
        ok = os.getenv('openai')
        os.environ["OPENAI_API_KEY"] = ok
        elon_musk_bot = App()

        # from .utilities import path_to_sandbox_folder
        # from .utilities import file_list_in_sandbox
        from .utilities import refresh_file
        path_to_sandbox_folder, file_list_in_sandbox = refresh_file()

        for i, file_name in enumerate(file_list_in_sandbox):
            file_path = os.path.join(path_to_sandbox_folder, file_name)
            try:
                print(i+1, file_path)
                elon_musk_bot.add(file_path, data_type='pdf_file')
                print(i+1, "added")
            except:
                pass

        while True:
            data = await websocket.receive_text()
            logging.info(f"Received WebSocket message: {data}")

            # if data == "start":
            #     logging.info("Starting file fetch process...")
            #     await websocket.send_text("Fetching files...")

            prompt = "<promptpl.us>"+data
            print("prompt", prompt)
            await websocket.send_text(prompt)

            # do some lang chain here now
            text = "How many companies does Elon Musk run?"
            text = data
            res = "error"
            try:
                print("text", text)
                # res = chat(text)
                # do you have embed files?
                res = elon_musk_bot.query(text)
                print("res", res)
                await websocket.send_text(res)
            except:
                await websocket.send_text(res)

    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket disconnected with code: {e.code}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # This will log the full traceback of the exception
        logging.error(traceback.format_exc())
        await websocket.send_text(f"Error: {e}")
