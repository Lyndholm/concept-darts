import uuid

from sqlalchemy import DATE, TIMESTAMP, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from ..controllers.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    username = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    additional_name = Column(String)
    date_of_birth = Column(DATE, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    avatar_image = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    worlds = relationship('World', lazy='joined', primaryjoin='User.id==World.creator_id', viewonly=True)
    locations = relationship('Location', lazy='joined', primaryjoin='User.id==Location.creator_id', viewonly=True)

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'id={self.id!s} '
            f'email={self.email}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
