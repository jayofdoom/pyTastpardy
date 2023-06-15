from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create base class
Base = declarative_base()

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


class Player(Base):  # type: ignore
    __tablename__ = 'players'
    id = Column(String, primary_key=True)
    name = Column(String)
    score = Column(Integer)
    cur_game_score = Column(Integer)
    cur_game_id = Column(String)

