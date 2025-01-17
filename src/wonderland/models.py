import typing as t

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, ARRAY


# +---------------------------------------------------------------------------+
# |                                  U S E R                                  |
# +---------------------------------------------------------------------------+
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None)
    room_id: int | None = Field(default=None, foreign_key="room.id")
    room: t.Optional["Room"] | None = Relationship(back_populates="users")
    lands: list["Land"] = Relationship(back_populates="owner")
    things: list["Thing"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    name: str


# +---------------------------------------------------------------------------+
# |                                  L A N D                                  |
# +---------------------------------------------------------------------------+
class Land(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str | None
    owner_id: int | None = Field(default=None, foreign_key="user.id")
    owner: User | None = Relationship(back_populates="lands")
    rooms: list["Room"] = Relationship(back_populates="land")


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
    container_id: int | None = Field(default=None, foreign_key="thing.id")
    container: t.Optional["Thing"] = Relationship(back_populates="inventory", sa_relationship_kwargs={"remote_side": "Thing.id"})
    inventory: list["Thing"] = Relationship(back_populates="container")
    user_id: int | None = Field(default=None, foreign_key="user.id")
    user: User | None = Relationship(back_populates="things")
    unlocks: t.Optional["RoomPortal"] = Relationship(back_populates="key")


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
    users: list[User] = Relationship(back_populates="room")
    things: list[Thing] = Relationship(back_populates="room")
    exits: list["RoomPortal"] = Relationship(back_populates="source", sa_relationship_kwargs={"foreign_keys": "RoomPortal.source_id"})


class RoomCreate(SQLModel):
    name: str
    description: str | None


class RoomPortal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str | None
    description: str | None
    is_locked: bool = Field(default=False)
    key_id: int | None = Field(default=None, foreign_key="thing.id")
    key: Thing | None = Relationship(back_populates="unlocks")
    source_id: int | None = Field(default=None, foreign_key="room.id")
    source: Room | None = Relationship(back_populates="exits", sa_relationship_kwargs={"foreign_keys": "RoomPortal.source_id"})
    target_id: int | None = Field(default=None, foreign_key="room.id")


class RoomPortalCreate(SQLModel):
    name: str | None
    source_id: int
    target_id: int
