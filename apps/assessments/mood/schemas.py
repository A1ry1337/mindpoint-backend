from ninja import Schema
from datetime import date

class MoodInput(Schema):
    score: int  # оценка 1-5

class MoodOutput(Schema):
    date: date
    score: int
