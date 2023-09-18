from fastapi import APIRouter, HTTPException, Depends, status, Request, Body, Header
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder as jEnc
from sqlalchemy.orm import Session
from sql_app.database import get_db, engine
from auth import models as aModels

router = APIRouter(
    prefix="/db", 
    tags=["database"]
)


@router.get("/")
async def get_sql_app(res=JSONResponse, req=Request, db: Session = Depends(get_db)):

    try:
        content = "Database was successful reached"
        return res({"sucess": content}, status.HTTP_201_CREATED)

    except Exception as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"{jEnc(e)}")
    

@router.post("/create_tables")
async def createTables(req:Request, db: Session= Depends(get_db)):
    try:
        aModels.User.metadata.create_all(engine)
        aModels.Profile.metadata.create_all(engine)
        aModels.Address.metadata.create_all(engine)
        aModels.CountryCode.metadata.create_all(engine)
        content = {"success" : "Tables created successfully! within Mysql Cloud Database."}
        return JSONResponse(content, status.HTTP_201_CREATED)
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e))
