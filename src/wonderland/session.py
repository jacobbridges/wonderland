from pydantic import BaseModel
from sqlmodel import Session as OrmSession


class Session(BaseModel):
    orm: OrmSession
