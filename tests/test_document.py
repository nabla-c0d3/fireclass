from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from google.cloud import firestore

from fireclass.document import (
    initialize_with_firestore_client,
    _discard_firestore_client,
    FirestoreClientNotConfigured,
    DocumentNotCreatedInDatabase,
    DocumentAlreadyCreatedInDatabase,
)

import pytest

from fireclass.document import Document, DocumentNotFound


class UserMembershipLevelEnum(Enum):
    NONE = 1
    INTERMEDIATE = 2
    FULL = 3


@dataclass
class User(Document):
    """The model we use for our tests; it has a field of each type.
    """

    email_address: str = "test@test.com"
    family_members_count: int = 5
    last_login_date: datetime = datetime.utcnow().replace(tzinfo=timezone.utc)
    membership: UserMembershipLevelEnum = UserMembershipLevelEnum.FULL
    is_active: bool = True


@pytest.fixture
def setup_firestore_db():
    # Use a dedicated Firestore DB setup in GCP
    db = firestore.Client.from_service_account_json("travis-ci-test-suite-service-account.json")
    initialize_with_firestore_client(db)

    # Run the test case
    yield

    # Clear all the documents created by the test case
    for user in User.stream():
        user.delete()

    for user in UserWithOptionalTypes.stream():
        user.delete()

    # Discard the handle to the DB
    _discard_firestore_client()


class TestDocument:
    def test_not_initialized(self):
        # Given a document
        user = User()

        # When saving it to the DB but the DB firestore client was not supplied
        # It fails
        with pytest.raises(FirestoreClientNotConfigured):
            user.create()

    def test_document_create_get_and_delete(self, setup_firestore_db):
        # Given a document
        user = User()

        # When saving it to the DB without providing an ID
        # It succeeds
        user.create()

        # And the document can be retrieved from the DB
        retrieved_user = User.get_document(user.id)
        assert user == retrieved_user

        # And the document can be deleted from the DB
        User.delete_document(user.id)
        with pytest.raises(DocumentNotFound):
            User.get_document(user.id)

    def test_document_create_with_id(self, setup_firestore_db):
        # Given a document
        user = User()

        # When saving it to the DB with a specific ID
        # It succeeds
        document_id = "123"
        user.create(document_id=document_id)

        # And the document can be retrieved from the DB
        retrieved_user = User.get_document(document_id)
        assert user == retrieved_user

    def test_document_create_but_already_created(self, setup_firestore_db):
        # Given a document already saved to the DB
        user = User()
        user.create()

        # When trying to create it again
        # It fails
        with pytest.raises(DocumentAlreadyCreatedInDatabase):
            user.create()

    def test_document_update(self, setup_firestore_db):
        # Given a document in the DB
        user = User(email_address="1@2.com", is_active=True)
        user.create()

        # When updating some of its fields
        new_email_address = "456@7.com"
        new_is_active = False
        user.email_address = new_email_address
        user.is_active = new_is_active

        # And the saving the updated document to the DB
        # It succeeds
        user.update()

        # And the updated fields were saved
        retrieved_user = User.get_document(user.id)
        assert new_email_address == retrieved_user.email_address
        assert new_is_active == retrieved_user.is_active

    def test_document_update_but_not_created_yet(self, setup_firestore_db):
        # Given a document that hasn't been saved to the DB
        user = User()

        # When updating a field
        user.email_address = "456@7.com"

        # And the saving the updated document to the DB
        # It fails because the document hasn't been created in the DB
        with pytest.raises(DocumentNotCreatedInDatabase):
            user.update()

    def test_document_delete_but_not_created_yet(self, setup_firestore_db):
        # Given a document that hasn't been saved to the DB
        user = User()

        # When trying to delete the document
        # It fails because the document hasn't been created in the DB
        with pytest.raises(DocumentNotCreatedInDatabase):
            user.delete()

    def test_get(self, setup_firestore_db):
        # Given a bunch of documents
        users_count = 5
        saved_user_ids = set()
        for _ in range(users_count):
            user = User()
            user.create()
            saved_user_ids.add(user.id)

        # When retrieving every document in the collection
        # It succeeds
        retrieved_users = [user for user in User.stream()]
        assert 5 == len(retrieved_users)
        assert saved_user_ids == {user.id for user in retrieved_users}

    def test_where_with_enum_field(self, setup_firestore_db):
        # Given a bunch of documents
        users_count = 5
        for _ in range(users_count):
            user = User(email_address="12@34.com")
            user.create()

        # And two documents with a specific field value
        membership = UserMembershipLevelEnum.INTERMEDIATE
        user_to_return1 = User(membership=membership)
        user_to_return1.create()
        user_to_return2 = User(membership=membership)
        user_to_return2.create()

        # When querying for this specific value
        query = User.where("membership", "==", membership)

        # It succeeds
        found_users = [user for user in query.stream()]

        # And the right documents are returned
        assert 2 == len(found_users)
        expected_users = {user_to_return1.id: user_to_return1, user_to_return2.id: user_to_return2}
        for user in found_users:
            assert asdict(expected_users[user.id]) == asdict(user)

    def test_where_with_str_field(self, setup_firestore_db):
        # Given a bunch of documents
        users_count = 5
        for _ in range(users_count):
            user = User(email_address="12@34.com")
            user.create()

        # And two documents with a specific field value that's an Enum
        email_address = "unique@test.com"
        user_to_return1 = User(email_address=email_address)
        user_to_return1.create()
        user_to_return2 = User(email_address=email_address)
        user_to_return2.create()

        # When querying for this specific value
        query = User.where("email_address", "==", email_address)

        # It succeeds
        found_users = [user for user in query.stream()]

        # And the right documents are returned
        assert 2 == len(found_users)
        expected_users = {user_to_return1.id: user_to_return1, user_to_return2.id: user_to_return2}
        for user in found_users:
            assert asdict(expected_users[user.id]) == asdict(user)

    def test_where_with_limit(self, setup_firestore_db):
        # Given a bunch of documents
        users_count = 5
        for _ in range(users_count):
            user = User(is_active=False)
            user.create()

        # When querying for a specific value
        query = User.where("is_active", "==", False)

        # With a limit of 2 documents
        query = query.limit(2)

        # It succeeds
        found_users = [user for user in query.stream()]

        # And the right number of documents is returned
        assert 2 == len(found_users)

    def test_where_with_wrong_field_name(self, setup_firestore_db):
        # When querying for a non-existent field
        # It fails
        with pytest.raises(TypeError):
            User.where("wrong_field_name", "==", "123").stream()

    def test_where_with_wrong_field_value_type(self, setup_firestore_db):
        # When querying for a field by supplying a value with the wrong type
        # It fails
        with pytest.raises(TypeError):
            User.where("is_active", "==", "not a bool").stream()

    def test_multiple_where_chained(self, setup_firestore_db):
        # Given a bunch of users that all have the same address and membership
        email_address = "unique@test.com"
        for _ in range(5):
            user = User(email_address=email_address, membership=UserMembershipLevelEnum.NONE)
            user.create()

        # And one user with the same email but a different membership
        user_to_return = User(email_address=email_address, membership=UserMembershipLevelEnum.FULL)
        user_to_return.create()

        # When using a compound query (ie. multiple where()) to fetch that one user
        query = User.where("email_address", "==", email_address).where("membership", "==", UserMembershipLevelEnum.FULL)

        # It succeeds
        found_users = [user for user in query.stream()]

        # And the right user was returned
        assert 1 == len(found_users)
        assert asdict(found_users[0]) == asdict(user_to_return)


@dataclass
class UserWithOptionalTypes(Document):
    email_address: Optional[str] = "test@test.com"
    family_members_count: Optional[int] = 5
    last_login_date: Optional[datetime] = datetime.utcnow().replace(tzinfo=timezone.utc)
    membership: Optional[UserMembershipLevelEnum] = UserMembershipLevelEnum.FULL
    is_active: Optional[bool] = True


class TestDocumentWithOptionalTypes:
    def test_document_create_get_and_delete(self, setup_firestore_db):
        # Given a document
        user = UserWithOptionalTypes()

        # When saving it to the DB without providing an ID
        # It succeeds
        user.create()

        # And the document can be retrieved from the DB
        retrieved_user = UserWithOptionalTypes.get_document(user.id)
        assert user == retrieved_user

        # And the document can be deleted from the DB
        UserWithOptionalTypes.delete_document(user.id)
        with pytest.raises(DocumentNotFound):
            UserWithOptionalTypes.get_document(user.id)

    def test_document_create_get_and_delete_with_none_values(self, setup_firestore_db):
        # Given a document with None values
        user = UserWithOptionalTypes(
            email_address=None, family_members_count=None, last_login_date=None, membership=None, is_active=None
        )

        # When saving it to the DB without providing an ID
        # It succeeds
        user.create()

        # And the document can be retrieved from the DB
        retrieved_user = UserWithOptionalTypes.get_document(user.id)
        assert user == retrieved_user

        # And the document can be deleted from the DB
        UserWithOptionalTypes.delete_document(user.id)
        with pytest.raises(DocumentNotFound):
            UserWithOptionalTypes.get_document(user.id)

    def test_where_with_none_value(self, setup_firestore_db):
        # Given a bunch of documents
        users_count = 5
        for _ in range(users_count):
            user = UserWithOptionalTypes(email_address="12@34.com")
            user.create()

        # And two documents with a specific field set to None
        user_to_return1 = UserWithOptionalTypes(email_address=None)
        user_to_return1.create()
        user_to_return2 = UserWithOptionalTypes(email_address=None)
        user_to_return2.create()

        # When querying for the None value
        query = UserWithOptionalTypes.where("email_address", "==", None)

        # It succeeds
        found_users = [user for user in query.stream()]

        # And the right documents are returned
        assert 2 == len(found_users)
        expected_users = {user_to_return1.id: user_to_return1, user_to_return2.id: user_to_return2}
        for user in found_users:
            assert asdict(expected_users[user.id]) == asdict(user)
