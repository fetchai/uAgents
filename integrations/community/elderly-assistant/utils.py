from dataclasses import dataclass
import re
from random import choice


@dataclass
class Call:
    date: str
    time: str
    call: str


@dataclass
class Doorbell:
    date: str
    time: str
    visitor: str


@dataclass
class Summary:
    Summary: str
    Date: str
    Time: str


def read_text_from_file(file_path):
    with open(file_path, "r") as file:
        text = file.read()
    return text


def parse_calls(text):
    calls = re.findall(
        r"Date: (\d+-[a-zA-Z]+-\d{4}), Time: (\d+:\d+ [AP]M)\s+Call: (.+)", text
    )
    return [Call(date, time, call) for date, time, call in calls]


def parse_doorbells(text):
    doorbells = re.findall(
        r"Date: (\d+-[a-zA-Z]+-\d{4}), Time: (\d+:\d+ [AP]M)\s+Visitor: (.+)", text
    )
    return [Doorbell(date, time, visitor) for date, time, visitor in doorbells]


def pick_random_call(file_path):
    text = read_text_from_file(file_path)
    calls = parse_calls(text)
    random_call = choice(calls)
    return random_call


def parse_summary(msg):
    response_data = dict(re.findall(r"(\w+):\s*(.*)", msg))
    res = Summary(**response_data)
    return res
