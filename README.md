[![Build Status](https://travis-ci.org/nabla-c0d3/fireclass.svg?branch=master)](https://travis-ci.org/nabla-c0d3/fireclass)

# Fireclass

Firestore + Dataclass: declare and interact with your Firestore models using dataclasses.

## Installation

`pip install fireclass`

## Sample usage

```python
from dataclasses import dataclass
from google.cloud import firestore
from fireclass.document import Document, initialize_with_firestore_client


# Define a new type of document as a dataclass
@dataclass
class Person(Document):
    email_address: str
    age: int


# Initialize access to the Firestore DB
client = firestore.Client.from_service_account_json("service-account.json")
initialize_with_firestore_client(client)

# Create a new person
person = Person(email_address='test@test.com', age=30)

# Save the person to the DB
person.create()

# Update a field
person.age = 31
person.update()

# Fetch this specific person
fetched_person = Person.get_document(person.id)

# Query for persons
for found_person in Person.where("age", "==", 31).stream():
    print(found_person)

# Delete the person from the DB
person.delete()
```
