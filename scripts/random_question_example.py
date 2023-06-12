import time

from sqlalchemy import func

from tastpardy.db import DBClient
from tastpardy.models import Category, Question

session = DBClient().get_session()
question = session.query(Question).order_by(func.random()).limit(1).one()
print("This question was first aired in {} in the category {} for {}.".format(
    question.aired, question.category.name, question.difficulty))
print(question.question)
print("I'll give you five seconds to think about it.")
time.sleep(5)
print("The answer was: What is {}. I hope you got it right!".format(question.answer))