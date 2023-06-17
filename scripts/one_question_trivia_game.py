from fuzzywuzzy import fuzz
from sqlalchemy import func

from tastpardy.db import DBClient
from tastpardy.models import Question

session = DBClient().get_session()

# Get a random question from the database
question = session.query(Question).order_by(func.random()).first()

if not question:
    raise ValueError("No questions in the database?!")

# Ask the user the question
print(question.question)
answer = input("Your answer: ")

# Check if the user's answer is close enough to the correct answer
if fuzz.token_set_ratio(answer.lower(), question.answer.lower()) >= 80:  # type: ignore
    print("Correct! The answer is:", question.answer)
else:
    print("Incorrect. The correct answer is:", question.answer)
