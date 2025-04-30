import os
from embedchain import App
from dotenv import load_dotenv
load_dotenv()
ok = os.getenv('openai')

os.environ["OPENAI_API_KEY"] = ok
# elon_musk_bot = App()

# Embed Online Resources


def embbding(file_list_in_sandbox):

    elon_musk_bot = App()

    from .utilities import path_to_sandbox_folder
    # from .utilities import file_list_in_sandbox

    for i, file_name in enumerate(file_list_in_sandbox):

        file_path = os.path.join(path_to_sandbox_folder, file_name)

        try:
            print(i+1, file_path)
            elon_musk_bot.add(file_path, data_type='pdf_file')
            print(i+1, "added")
        except:
            pass

    # what is in the text.txt embed file?
    # elon_musk_bot.add("https://en.wikipedia.org/wiki/Elon_Musk")
    # elon_musk_bot.add("https://www.tesla.com/elon-musk")

    return elon_musk_bot


def chat(text):
    print("text", text)
    response = elon_musk_bot.query(text)
    print("response", response)
    return (response)

# Answer: 'Elon Musk runs four companies: Tesla, SpaceX, Neuralink, and The Boring Company.'
