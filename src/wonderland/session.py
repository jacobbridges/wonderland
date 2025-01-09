from pydantic import BaseModel
from sqlmodel import Session as OrmSession

from src.wonderland.models import User


class Session(BaseModel):
    orm: OrmSession
    user: User
