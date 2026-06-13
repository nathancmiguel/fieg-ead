import os

from dotenv import load_dotenv

class Env:
    def __init__(self):
        load_dotenv()
        self.cpf = os.getenv("CPF")
        self.senha = os.getenv("SENHA")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

env = Env()