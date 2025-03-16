from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from summarizer.config import settings


def set_database_path() -> URL:
    if settings.db_host:
        return URL.create(
            "postgresql",
            username=settings.db_user,
            password=settings.db_password,
            host=settings.db_host,
            port=int(settings.db_port),
            database=settings.db_database,
            query={"target_session_attrs": "read-write"},
        )
    if settings.db_test:
        return URL.create("sqlite", database="tests.db")
    return URL.create("sqlite", database="local.db")


engine = create_engine(
    set_database_path(),
    pool_recycle=300,
    pool_pre_ping=True,
)

Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
