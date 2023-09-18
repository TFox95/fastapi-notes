import dotenv
from os import getenv
from typing import List
from pydantic import AnyHttpUrl
from fastapi.responses import JSONResponse

dotenv.load_dotenv()


class Settings():
    PROJECT_NAME: str = getenv("PROJECT_NAME") or "test"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        getenv("BACKEND_CORS_ORIGINS")] or None
    BACKEND_PORT: int = int(getenv("UVICORN_PORT")) or 8000
    BACKEND_HOST: str = getenv("UVICORN_HOST") or "127.0.0.1"

    DB_USER: str = getenv("DB_USER")
    DB_PASS: str = getenv("DB_PASS")
    DB_NAME: str = getenv("DB_NAME")
    DB_HOST: str = getenv("DB_HOST")
    DB_PORT: int = getenv("DB_PORT")
    DB_DRIVER: str = getenv("DB_DRIVER")
    #MySQL structure
    DB_URL: str = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    #Postgress Structure
    #DB_URL: str = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}{DB_NAME}"

    PEPPER: str = getenv("HASH_PEPPER")
    SALT: str = getenv("HASH_SALT")

    AUTH_SECRET = str = getenv("AUTH_SECRET")


settings = Settings()


class JsonRender(JSONResponse):
    """
    This Class was created to return certain content that would
    allow content that needs to be return as an object to utilize
    the reponse_model argument on an API Endpoint but it keeps 
    consistency of the Apps Json-scheme. 
    """
    def render(self, content) -> bytes:
        # Here you can modify the response content or headers as needed
        return super().render({'data': content})
