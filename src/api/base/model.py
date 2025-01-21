from utils.dependency import db
import sqlalchemy as sa
from uuid import uuid4
class BaseModel(db.Model):
    """
    Base model class for all models in the application.

    Contains common fields and methods used by all models.

    Fields:
        id: A unique identifier for the model.
        user_id: The UUID of the user who created the model.
        created_at: The timestamp when the model was created.
        updated_at: The timestamp when the model was last updated.
    """
    __abstract__ = True
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    entity_id = sa.Column(sa.UUID(as_uuid=True), nullable=False, default=uuid4, unique=True)
    created_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now())
    updated_at = sa.Column(sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now())
    
