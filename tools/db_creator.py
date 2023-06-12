import os
import re
import uuid

import yaml

from tastpardy.models import Category, Question
from tastpardy.db import DBClient


def parse_question_string(question_string):
    # Define regular expressions to match the difficulty, air date, and question
    difficulty_regex = r'\$(\d+)'
    air_date_regex = r'aired (\d{4}-\d{2}-\d{2})'
    question_regex = r'\'(.*)\''

    # Extract the difficulty, air date, and question using regular expressions
    difficulty_match = re.search(difficulty_regex, question_string)
    air_date_match = re.search(air_date_regex, question_string)
    question_match = re.search(question_regex, question_string)

    if not difficulty_match or not air_date_match or not question_match:
        raise ValueError('Invalid question string: %s', question_string)

    # Return the extracted values as a tuple
    return (
        int(difficulty_match.group(1)),
        air_date_match.group(1),
        question_match.group(1)
    )


# Load YAML file
script_dir = os.path.dirname(__file__)
question_dir = os.path.join(script_dir, 'Questions')
with open(
    os.path.join(question_dir, 'categories.yml'), 'r') as f:
    data = yaml.safe_load(f)

client = DBClient()
session = client.get_session()

# Insert data
for category in data['trivia_categories']:
    questions_path = os.path.join(question_dir, "questions_{}.yml".format(category['id']))
    if os.path.exists(questions_path):
        session.add(Category(
            id=int(category['id']),
            name=category['name']
        ))
        with open(questions_path) as q:
            questions = yaml.safe_load(q)
            for question in questions['questions']:
                try:
                    difficulty, air_date, question_parsed = parse_question_string(question['question'])
                except ValueError as e:
                    print("Error processing question {}. Skipping.".format(question))
                    continue
                session.add(Question(
                    id=str(uuid.uuid4()),
                    category_id=int(category['id']),
                    difficulty=str("${}".format(difficulty)),
                    aired=air_date,
                    question=question_parsed,
                    answer=question['correct_answer']
                ))
    else:
        print("No questions for category {}.".format(category['id']))
        print(questions_path)

session.commit()