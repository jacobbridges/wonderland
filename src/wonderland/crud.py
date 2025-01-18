from typing import Any, Sequence

from sqlmodel import Session, select

from src.wonderland.models import (
    User, UserCreate,
    Land, LandCreate,
    Room, RoomCreate,
    RoomPortal, RoomPortalCreate,
    Thing, ThingCreate,
)


# +---------------------------------------------------------------------------+
# |                                  U S E R                                  |
# +---------------------------------------------------------------------------+
def create_user(*, session: Session, data: UserCreate) -> User:
    record = User.model_validate(data)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def update_user(*, session: Session, user: User, field: str, value: Any) -> User:
    user.sqlmodel_update({field: value})
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_name(*, session: Session, name: str) -> User | None:
    statement = select(User).where(User.name == name)
    session_user = session.exec(statement).first()
    return session_user


# +---------------------------------------------------------------------------+
# |                                  L A N D                                  |
# +---------------------------------------------------------------------------+
def create_land(*, session: Session, data: LandCreate) -> Land:
    record = Land.model_validate(data)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_land(*, session: Session, land_id: int) -> Land | None:
    statement = select(Land).where(Land.id == land_id)
    land = session.exec(statement).first()
    return land


def list_lands_by_user(*, session: Session, user_id: int) -> Sequence[Land]:
    statement = select(Land).where(Land.owner_id == user_id)
    lands = session.exec(statement).all()
    return lands


# +---------------------------------------------------------------------------+
# |                                 T H I N G                                 |
# +---------------------------------------------------------------------------+
def create_thing_for_user(*, session: Session, data: ThingCreate, user_id: int) -> Thing:
    record = Thing.model_validate(data, update={"user_id": user_id})
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def create_thing_for_room(*, session: Session, data: ThingCreate, room_id: int) -> Thing:
    record = Thing.model_validate(data, update={"room_id": room_id})
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def create_thing_for_thing(*, session: Session, data: ThingCreate, thing_id: int) -> Thing:
    record = Thing.model_validate(data, update={"thing_id": thing_id})
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def list_things_by_room(*, session: Session, room_id: int) -> Sequence[Thing]:
    statement = select(Thing).where(Thing.room_id == room_id)
    things = session.exec(statement).all()
    return things


def list_things_by_name(*, session: Session, name: str, room_id: int) -> Sequence[Thing]:
    statement = select(Thing).where(Thing.name == name, Thing.room_id == room_id)
    things = session.exec(statement).all()
    return things


# +---------------------------------------------------------------------------+
# |                                  R O O M                                  |
# +---------------------------------------------------------------------------+
def create_room(*, session: Session, data: RoomCreate, land_id: int) -> Room:
    record = Room.model_validate(data, update={"land_id": land_id})
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def create_room_portal(*, session: Session, data: RoomPortalCreate) -> RoomPortal:
    record = RoomPortal.model_validate(data)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_room(*, session: Session, room_id: int) -> Room | None:
    statement = select(Room).where(Room.id == room_id)
    room = session.exec(statement).one()
    return room
