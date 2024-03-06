import os
from dotenv import find_dotenv, load_dotenv

# find .env automatically
dotenv_path = find_dotenv()

# load up the entries as environment variables
load_dotenv(dotenv_path)

API_KEY = os.getenv("API_KEY")
