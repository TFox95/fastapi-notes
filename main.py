from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import time

NAMESPACE: str = f"Base Server"

def get_application():
    _app = FastAPI(
        description="MicroService for handling Authentication",
        version="0.3.1"
                    )
    _app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["POST", "PATCH", "GET", "DELETE", "PUT", "OPTIONS"],
        allow_headers=["Access-Control-Allow-Headers", "Origin", "X-Requested-Width", "Content-Type", "Accept", "Authorization"],
    )
    return _app

app = get_application()


# Creates Header named X-Process-Time to report the time to a calls completion.
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f"{process_time}/s")
    return response


# Error Handling
@app.middleware("http")
async def errors_handling(request: Request, call_next):
    try:
        return await call_next(request)
    except KeyError:
        raise HTTPException(status_code=404, detail="The requested resource does not exist")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/")
async def basic(request:Request):
    return "{'hello': 'world'}"

