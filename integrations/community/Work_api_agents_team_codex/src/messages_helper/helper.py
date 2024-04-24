# Importing models module from uagents library
from uagents import Model

# Defining classes for handling request and response
class Random_result(Model):
    word: str
    results: list
    syllables: dict
    pronunciation: dict
    
class Random_search(Model):
    pass
    
class Given_word(Model):
    word: str
    
class Result(Model):
    word: str
    result : list
    syllables: dict
    pronunciation : dict 
    
class assigned_word(Model):
    word: str
    syllables: dict
    pronunciation: dict
    synonyms: str
    part_of_speech: str
    types_of: str
    examples: str
    
    
class Request(Model):
    text: str


class Error(Model):
    error: str


class Data(Model):
    generated_text: str
