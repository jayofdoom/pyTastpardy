from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.decl_api import DeclarativeMeta

# Create base class
Base : DeclarativeMeta = declarative_base()

# Define table
class Category(Base):  # type: ignore
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Question(Base):  # type: ignore
    __tablename__ = 'questions'
    id = Column(String, primary_key=True)
    category_id = Column(ForeignKey(Category.id))  # type: ignore
    category = relationship(Category)
    difficulty = Column(String)
    aired = Column(String)
    question = Column(String)
    answer = Column(String)
