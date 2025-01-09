from sqlmodel import create_engine, Session as OrmSession

engine = create_engine("sqlite:///database.db")


def new_session() -> OrmSession:
    """
    Generate a new ORM session.

    :returns: the new ORM session.
    """
    return OrmSession(engine)
