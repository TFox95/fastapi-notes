from uvicorn import run, main
from core.config import settings

if __name__ == "__main__":

    run("main:app", host=settings.BACKEND_HOST ,port=settings.BACKEND_PORT, 
        reload=True, debug=True)