import typing as t

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ARRAY


# +---------------------------------------------------------------------------+
# |                                  U S E R                                  |
# +---------------------------------------------------------------------------+
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    room_id: int | None = Field(default=None, foreign_key="room.id")
    room: t.Optional["Room"] | None = Relationship(back_populates="users")


class UserCreate(SQLModel):
    name: str


# +---------------------------------------------------------------------------+
# |                                  L A N D                                  |
# +---------------------------------------------------------------------------+
class Land(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    owner_id: int = Field(foreign_key="owner.id")
    owner: User = Relationship(back_populates="lands")


class LandCreate(SQLModel):
    name: str
    owner_id: int


# +---------------------------------------------------------------------------+
# |                                 T H I N G                                 |
# +---------------------------------------------------------------------------+
class Thing(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    room_id: int | None = Field(default=None, foreign_key="room.id")
    room: t.Optional["Room"] = Relationship(back_populates="things")
    container_id: int | None = Field(default=None, foreign_key="container.id")
    container: t.Optional["Thing"] = Relationship(back_populates="inventory")
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="things")


class ThingCreate(SQLModel):
    name: str


# +---------------------------------------------------------------------------+
# |                                  R O O M                                  |
# +---------------------------------------------------------------------------+
class Room(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    land_id: int | None = Field(default=None, foreign_key="land.id")
    land: Land = Relationship(back_populates="rooms")


class RoomCreate(SQLModel):
    name: str
    description: str | None


class RoomPortal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None
    description: str | None
    is_locked: bool = Field(default=False)
    key_id: int | None = Field(default=None, foreign_key="key.id")
    key: Thing | None = Relationship(back_populates="unlocks")
    source_id: int | None = Field(default=None, foreign_key="source.id")
    source: Room | None = Relationship(back_populates="exits")
    target_id: int | None = Field(default=None, foreign_key="target.id")
    target: Room | None = Relationship(back_populates="entrances")


class RoomPortalCreate(SQLModel):
    name: str | None
    source_id: int
    target_id: int
