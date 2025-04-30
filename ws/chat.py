from string import Template
from fastapi import APIRouter
from fastapi.websockets import WebSocket
import logging
import os
print(os.getcwd())

router = APIRouter()

# with open('foo.txt', 'r') as f:
#     src = Template(f.read())
#     result = src.substitute(d)
#     print(result)

chatuser = open("pp/templates/chatuser.html", "r")
chatuser = Template(chatuser.read())
print(chatuser)

chatbot = open("pp/templates/chatbot.html", "r")
chatbot = Template(chatbot.read())
print(chatbot)

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# print("BASE_DIR", BASE_DIR)
# TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
# print("TEMPLATE_DIR", TEMPLATE_DIR)
# templates = Jinja2Templates(directory=TEMPLATE_DIR)
# # templates = Jinja2Templates(directory="pp/templates")
# print("templates", templates)


# @router.websocket_route("/ws")
@router.websocket_route("/chatline")
async def websocket_endpoint_chatline(websocket: WebSocket):

    await websocket.accept()
    print("websocket.accept() accepted")

    logging.info("WebSocket connection established.")
    await websocket.send_text("promptplus_id: WebSocket Connected")

    try:

        from embedchain import App
        from dotenv import load_dotenv
        load_dotenv()
        ok = os.getenv('openai')
        os.environ["OPENAI_API_KEY"] = ok
        elon_musk_bot = App()

        from ..utilities import refresh_file
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

            prompt = chatuser.substitute({"data": data})
            print("prompt", prompt)
            await websocket.send_text(prompt)

            # do some lang chain here now
            # text = "How many companies does Elon Musk run?"
            text = data
            res = "error"
            try:
                print("text", text)
                # res = chat(text)
                # do you have embed files?
                res = elon_musk_bot.query(text)
                print("res", res)
                ref_fmt = chatbot.substitute({"res": res})
                await websocket.send_text(ref_fmt)
            except:
                await websocket.send_text(res)

    except WebSocketDisconnect as e:
        logging.warning(f"WebSocket disconnected with code: {e.code}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        # This will log the full traceback of the exception
        logging.error(traceback.format_exc())
        await websocket.send_text(f"Error: {e}")
