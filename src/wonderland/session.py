from pydantic import BaseModel
from sqlmodel import Session as OrmSession

from src.wonderland.models import User


class Session(BaseModel):
    user: User

    @classmethod
    def get_orm(cls) -> OrmSession:
        return getattr(cls, "orm")

    @classmethod
    def set_orm(cls, orm: OrmSession):
        setattr(cls, "orm", orm)
