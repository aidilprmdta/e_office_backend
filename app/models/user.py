from sqlalchemy import Column, Integer, String
from app.config.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    nama = Column(
        String,
        nullable=True
    )

    role = Column(
        String,
        nullable=False
    )