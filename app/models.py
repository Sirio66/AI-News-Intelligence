from sqlalchemy import Column, Integer, String, Text, Float
from .database import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    score = Column(Float, default=0.0)