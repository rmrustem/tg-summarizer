from datetime import datetime

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)
    chat_id: Mapped[int] = mapped_column(index=True, nullable=False)
    message_id: Mapped[int] = mapped_column(index=True, nullable=False)
    user: Mapped[str] = mapped_column(index=True, nullable=False)
    text: Mapped[str] = mapped_column(nullable=True)
    created: Mapped[datetime]
