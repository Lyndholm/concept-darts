import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from app.controllers.database import Base


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    username = sa.Column(sa.String, nullable=False, unique=True)
    first_name = sa.Column(sa.String, nullable=False)
    last_name = sa.Column(sa.String, nullable=False)
    additional_name = sa.Column(sa.String)
    date_of_birth = sa.Column(sa.DATE, nullable=True)
    phone_number = sa.Column(sa.String(15))
    email = sa.Column(sa.String, nullable=False, unique=True)
    password = sa.Column(sa.String, nullable=False)
    avatar_image = sa.Column(sa.String)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

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
