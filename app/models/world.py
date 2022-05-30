import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from ..controllers.database import Base


class World(Base):
    __tablename__ = 'worlds'

    id = sa.Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String)
    cover_image = sa.Column(sa.String)
    map_image = sa.Column(sa.String, nullable=False)
    creator_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    creator = relationship('User', lazy='joined')
    locations = relationship('Location', lazy='joined')

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'id={self.id!s} '
            f'name={self.name}'
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
