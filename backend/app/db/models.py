from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid
import os

Base = declarative_base()


class SMEOwnership(Base):
    __tablename__ = "sme_ownership"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    system_name = Column(String, nullable=False, index=True)
    owner_name = Column(String, nullable=False)
    owner_team = Column(String)
    owner_email = Column(String)
    expertise_tags = Column(Text)  # comma-separated simple list
    related_doc_id = Column(String, nullable=True)


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)

    # Use pgvector Vector when connected to Postgres, otherwise fall back to Text
    if os.getenv("DATABASE_URL", "sqlite:///./dev.db").startswith("sqlite"):
        embedding = Column(Text, nullable=True)
    else:
        try:
            from pgvector.sqlalchemy import Vector

            dim = int(os.getenv("EMBEDDING_DIM", "1536"))
            embedding = Column(Vector(dim), nullable=True)
        except Exception:
            # If pgvector isn't available for some reason, store as text
            embedding = Column(Text, nullable=True)

    source = Column(Text, nullable=True)

