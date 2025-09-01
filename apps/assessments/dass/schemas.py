from typing import Dict

from ninja import Schema
from datetime import date

class Dass9Input(Schema):
    depression: int
    stress: int
    anxiety: int

class Dass9Output(Schema):
    date: date
    depression: int
    stress: int
    anxiety: int

class QuestionOutput(Schema):
    id: int
    text: str
    type: str
    answers: Dict[int, str]