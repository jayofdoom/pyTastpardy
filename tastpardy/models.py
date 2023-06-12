from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create base class
Base = declarative_base()

# Define table
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Question(Base):
    __tablename__ = 'questions'
    id = Column(String, primary_key=True)
    category_id = Column(ForeignKey(Category.id))
    difficulty = Column(String)
    aired = Column(String)
    question = Column(String)
    answer = Column(String)
