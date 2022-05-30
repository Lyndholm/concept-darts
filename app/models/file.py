import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import text

from app.controllers.database import Base


class File(Base):
    __tablename__ = 'files'

    filename = sa.Column(sa.String, primary_key=True, nullable=False)
    author_id = sa.Column(UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'))
    uploaded_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=text('NOW()'))

    author = relationship('User', lazy='joined')

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__}: '
            f'name={self.filename} '
            f'>'
        )

    __mapper_args__ = {'eager_defaults': True}
