# Fireclass

[![Python Version](https://img.shields.io/pypi/pyversions/fireclass.svg)](https://pypi.org/project/fireclass/)
[![PyPi Version](https://img.shields.io/pypi/v/fireclass.svg)](https://pypi.org/project/fireclass/)
[![Build Status](https://travis-ci.org/nabla-c0d3/fireclass.svg?branch=master)](https://travis-ci.org/nabla-c0d3/fireclass)

Firestore + Dataclass: declare and interact with your Firestore models using dataclasses.

## Installation

`pip install fireclass`

## Sample usage

```python
from dataclasses import dataclass
from enum import Enum

from google.cloud import firestore
from fireclass import Document, initialize_with_firestore_client


class MembershipLevelEnum(Enum):
    NONE = 1
    INTERMEDIATE = 2
    FULL = 3


# Define a new type of document as a dataclass
@dataclass
class Person(Document):
    email_address: str
    age: int

    # Enum fields are supported
    membership: MembershipLevelEnum


# Initialize access to the Firestore DB
client = firestore.Client.from_service_account_json("travis-ci-test-suite-service-account.json")
initialize_with_firestore_client(client)

# Create a new person
person = Person(email_address="test@test.com", age=30, membership=MembershipLevelEnum.INTERMEDIATE)

# Save the person to the DB
person.create()

# Update some fields
person.age = 31
person.membership = MembershipLevelEnum.NONE
person.update()

# Fetch this specific person
fetched_person = Person.get_document(person.id)

# Query for persons
for found_person in Person.where("age", "==", 31).stream():
    print(found_person)

# Delete the document from the DB
person.delete()
```
