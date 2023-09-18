import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from core.config import settings

NAMESPACE: str = "SQL_APP/Database"

engine = create_engine(url=settings.DB_URL, echo=False)

SessionCloud = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base: DeclarativeMeta = declarative_base()

def get_db():
    db = SessionCloud()
    try:
        yield db
    finally:
        db.close()
